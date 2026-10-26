import time
import uuid
from collections.abc import Callable
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.core import auth
from app.core.config import Settings, get_settings
from app.main import app

SUPABASE_URL = "https://abc.supabase.co"
ISSUER = f"{SUPABASE_URL}/auth/v1"


def _key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


SIGNING_KEY = _key()


@pytest.fixture(autouse=True)
def configured(monkeypatch: pytest.MonkeyPatch) -> Settings:
    settings = Settings(supabase_url=SUPABASE_URL)
    app.dependency_overrides[get_settings] = lambda: settings
    monkeypatch.setattr(auth, "_signing_key", lambda token, s: SIGNING_KEY.public_key())
    yield settings
    app.dependency_overrides.pop(get_settings, None)


def make_token(**overrides: Any) -> str:
    claims: dict[str, Any] = {
        "sub": str(uuid.uuid4()),
        "email": "a@example.com",
        "aud": "authenticated",
        "iss": ISSUER,
        "exp": int(time.time()) + 3600,
    }
    claims.update(overrides)
    return jwt.encode(claims, SIGNING_KEY, algorithm="RS256")


def test_valid_token_returns_user(configured: Settings) -> None:
    sub = uuid.uuid4()
    user = auth.verify_token(make_token(sub=str(sub)), configured)
    assert user.id == sub
    assert user.email == "a@example.com"


@pytest.mark.parametrize(
    "overrides",
    [
        {"exp": int(time.time()) - 10},
        {"aud": "anon"},
        {"iss": "https://evil.example.com/auth/v1"},
        {"sub": "not-a-uuid"},
    ],
)
def test_invalid_claims_rejected(configured: Settings, overrides: dict[str, Any]) -> None:
    with pytest.raises(auth.HTTPException) as exc:
        auth.verify_token(make_token(**overrides), configured)
    assert exc.value.status_code == 401


def test_bad_signature_rejected(configured: Settings) -> None:
    forged = jwt.encode(
        {"sub": str(uuid.uuid4()), "aud": "authenticated", "iss": ISSUER, "exp": time.time() + 99},
        _key(),
        algorithm="RS256",
    )
    with pytest.raises(auth.HTTPException) as exc:
        auth.verify_token(forged, configured)
    assert exc.value.status_code == 401


def test_unconfigured_auth_returns_503() -> None:
    with pytest.raises(auth.HTTPException) as exc:
        auth.verify_token("x.y.z", Settings(supabase_url=""))
    assert exc.value.status_code == 503


def test_missing_header_is_401(raw_client: TestClient) -> None:
    assert raw_client.get("/me/profile").status_code == 401


def test_garbage_token_is_401(raw_client: TestClient) -> None:
    response = raw_client.get("/me/profile", headers={"Authorization": "Bearer nonsense"})
    assert response.status_code == 401


@pytest.mark.parametrize("path", ["/fields", "/skills", "/me/profile", "/me/skills"])
def test_every_data_route_requires_auth(raw_client: TestClient, path: str) -> None:
    assert raw_client.get(path).status_code == 401


def test_health_is_public(raw_client: TestClient) -> None:
    assert raw_client.get("/health").status_code == 200


def test_real_token_reaches_the_endpoint(
    raw_client: TestClient, make_user: Callable[[], Any]
) -> None:
    user = make_user()
    token = make_token(sub=str(user.id))
    response = raw_client.get("/me/profile", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404  # authenticated, but no profile yet
