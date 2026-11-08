from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import AuthUser
from app.llm import LLMError, get_llm
from app.llm.gemini import GeminiProvider
from app.main import app
from app.schemas.cv import ParsedCv, ParsedSkill
from app.services.storage import StorageError, get_storage

FIXTURES = Path(__file__).parent / "fixtures"


class FakeLLM:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.fail = False
        self.result = ParsedCv(
            cgpa=3.62,
            skills=[
                ParsedSkill(name="Python", level=3, evidence="RNA-seq plots"),
                ParsedSkill(name="py", level=4, evidence="alias of Python, higher level"),
                ParsedSkill(name="  gel   electrophoresis ", level=2, evidence="lab volunteer"),
                ParsedSkill(name="Basket Weaving", level=1, evidence="hobby"),
            ],
        )

    def generate_structured(self, system: str, prompt: str, schema: type[BaseModel]) -> ParsedCv:
        self.calls.append(prompt)
        if self.fail:
            raise LLMError("boom")
        return self.result


class FakeStorage:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.deleted: list[str] = []

    def upload(self, path: str, data: bytes, content_type: str) -> None:
        self.files[path] = data

    def delete(self, path: str) -> None:
        self.deleted.append(path)
        self.files.pop(path, None)

    def signed_url(self, path: str) -> str:
        if path not in self.files:
            raise StorageError("missing")
        return f"https://storage.example/sign/{path}?t=x"


@pytest.fixture
def llm() -> Iterator[FakeLLM]:
    fake = FakeLLM()
    app.dependency_overrides[get_llm] = lambda: fake
    yield fake


@pytest.fixture
def storage() -> Iterator[FakeStorage]:
    fake = FakeStorage()
    app.dependency_overrides[get_storage] = lambda: fake
    yield fake


@pytest.fixture
def ready(client: TestClient, user: AuthUser, profile_body: dict[str, object]) -> TestClient:
    client.put("/me/profile", json=profile_body)
    return client


def _post(client: TestClient, name: str, content: bytes | None = None) -> object:
    data = content if content is not None else (FIXTURES / name).read_bytes()
    return client.post("/me/cv", files={"file": (name, data, "application/octet-stream")})


def test_consent_is_recorded(ready: TestClient) -> None:
    assert ready.post("/me/consent").status_code == 204
    first = ready.get("/me/profile").json()["consent_at"]
    assert first is not None
    ready.post("/me/consent")
    assert ready.get("/me/profile").json()["consent_at"] == first  # not re-stamped


def test_upload_requires_consent(ready: TestClient, llm: FakeLLM, storage: FakeStorage) -> None:
    res = _post(ready, "bio_student.pdf")
    assert res.status_code == 403  # type: ignore[attr-defined]
    assert res.json()["detail"]["code"] == "consent_required"  # type: ignore[attr-defined]
    assert not llm.calls and not storage.files


def test_upload_requires_profile(
    client: TestClient, user: AuthUser, llm: FakeLLM, storage: FakeStorage
) -> None:
    assert _post(client, "bio_student.pdf").status_code == 409  # type: ignore[attr-defined]


def test_pdf_becomes_reviewable_profile(
    ready: TestClient, llm: FakeLLM, storage: FakeStorage, user: AuthUser
) -> None:
    ready.post("/me/consent")
    res = _post(ready, "bio_student.pdf")
    assert res.status_code == 201  # type: ignore[attr-defined]
    body = res.json()  # type: ignore[attr-defined]

    matched = {m["name"]: m for m in body["matched"]}
    assert matched["Python"]["level"] == 4  # alias merged, highest level wins
    assert matched["Gel Electrophoresis"]["level"] == 2  # whitespace/case normalised
    assert [u["name"] for u in body["unmatched"]] == ["Basket Weaving"]
    assert "Rahim Uddin" in llm.calls[0]
    assert list(storage.files) == [f"{user.id}/{body['cv_id']}.pdf"]

    latest = ready.get("/me/cv/latest").json()
    assert latest["cv_id"] == body["cv_id"]
    assert latest["matched"] == body["matched"]


def test_docx_is_accepted(ready: TestClient, llm: FakeLLM, storage: FakeStorage) -> None:
    ready.post("/me/consent")
    assert _post(ready, "business_student.docx").status_code == 201  # type: ignore[attr-defined]
    assert "Nusrat Jahan" in llm.calls[0]
    assert next(iter(storage.files)).endswith(".docx")


def test_confirm_saves_cv_skills_and_skips_unknown_ids(
    ready: TestClient, llm: FakeLLM, storage: FakeStorage
) -> None:
    ready.post("/me/consent")
    body = _post(ready, "bio_student.pdf").json()  # type: ignore[attr-defined]
    chosen = [{"skill_id": m["skill_id"], "level": m["level"]} for m in body["matched"]]
    res = ready.post("/me/cv/confirm", json={"skills": [*chosen, {"skill_id": 999999, "level": 2}]})
    assert res.json() == {"saved": len(chosen)}
    saved = {s["name"]: s for s in ready.get("/me/skills").json()}
    assert saved["Python"]["source"] == "cv" and saved["Python"]["level"] == 4


def test_confirm_rejects_bad_level(ready: TestClient) -> None:
    res = ready.post("/me/cv/confirm", json={"skills": [{"skill_id": 1, "level": 9}]})
    assert res.status_code == 422


@pytest.mark.parametrize(
    ("name", "content", "status", "code"),
    [
        ("scanned.pdf", None, 422, "no_text"),
        ("notes.txt", b"just plain text, not a cv" * 10, 422, "wrong_file_type"),
        ("empty.pdf", b"", 422, "empty"),
        ("big.pdf", b"%PDF-" + b"0" * (5 * 1024 * 1024), 413, "too_large"),
        ("broken.pdf", b"%PDF-1.4 this is not really a pdf", 422, "unreadable"),
    ],
)
def test_bad_files_get_friendly_errors(
    ready: TestClient,
    llm: FakeLLM,
    storage: FakeStorage,
    name: str,
    content: bytes | None,
    status: int,
    code: str,
) -> None:
    ready.post("/me/consent")
    res = _post(ready, name, content)
    assert res.status_code == status  # type: ignore[attr-defined]
    assert res.json()["detail"]["code"] == code  # type: ignore[attr-defined]
    assert not llm.calls and not storage.files  # failures never reach the LLM or storage


def test_llm_failure_is_clean_and_stores_nothing(
    ready: TestClient, llm: FakeLLM, storage: FakeStorage, db: Session
) -> None:
    ready.post("/me/consent")
    llm.fail = True
    res = _post(ready, "bio_student.pdf")
    assert res.status_code == 502  # type: ignore[attr-defined]
    assert res.json()["detail"]["code"] == "parse_failed"  # type: ignore[attr-defined]
    assert not storage.files
    assert db.execute(text("SELECT count(*) FROM cv_uploads")).scalar_one() == 0


def test_signed_url_comes_from_storage(
    ready: TestClient, llm: FakeLLM, storage: FakeStorage
) -> None:
    ready.post("/me/consent")
    _post(ready, "bio_student.pdf")
    assert ready.get("/me/cv/latest/url").json()["url"].startswith("https://storage.example/")


def test_no_cv_yet_is_404(ready: TestClient, storage: FakeStorage) -> None:
    assert ready.get("/me/cv/latest").status_code == 404
    assert ready.get("/me/cv/latest/url").status_code == 404


def test_delete_my_data_removes_rows_and_files(
    ready: TestClient, llm: FakeLLM, storage: FakeStorage, db: Session
) -> None:
    ready.post("/me/consent")
    body = _post(ready, "bio_student.pdf").json()  # type: ignore[attr-defined]
    ready.post(
        "/me/cv/confirm",
        json={"skills": [{"skill_id": body["matched"][0]["skill_id"], "level": 2}]},
    )
    assert ready.delete("/me/data").status_code == 204
    assert not storage.files and len(storage.deleted) == 1
    for table in ("profiles", "cv_uploads", "profile_skills"):
        assert db.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 0


def test_gemini_retries_once_then_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import Settings

    provider = GeminiProvider(Settings(gemini_api_key="k", llm_model="m"))
    replies = iter(["not json", "still not json"])
    monkeypatch.setattr(provider, "_call", lambda *_a: next(replies))
    with pytest.raises(LLMError):
        provider.generate_structured("s", "p", ParsedCv)


def test_gemini_second_attempt_can_succeed(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import Settings

    provider = GeminiProvider(Settings(gemini_api_key="k", llm_model="m"))
    replies = iter(['{"cgpa": 9}', '{"cgpa": 3.1}'])  # first violates cgpa <= 4
    monkeypatch.setattr(provider, "_call", lambda *_a: next(replies))
    assert provider.generate_structured("s", "p", ParsedCv).cgpa == 3.1
