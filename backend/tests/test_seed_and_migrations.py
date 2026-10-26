import json

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.seed import SEED_DIR, seed_reference_data
from tests.conftest import TEST_DATABASE_URL, migrate


def _count(db: Session, table: str) -> int:
    return int(db.execute(text(f"SELECT count(*) FROM {table}")).scalar_one())


def test_seed_files_are_consistent() -> None:
    fields = {f["slug"] for f in json.loads((SEED_DIR / "fields.json").read_text("utf-8"))}
    skills = json.loads((SEED_DIR / "skills.json").read_text("utf-8"))
    names = [s["name"] for s in skills]
    assert len(skills) >= 60
    assert len(names) == len(set(names))
    assert {s["category"] for s in skills} <= fields | {"general"}


def test_seed_is_idempotent(engine: Engine) -> None:
    with Session(engine) as db:
        before = (_count(db, "fields"), _count(db, "skills"))
        seed_reference_data(db)
        assert (_count(db, "fields"), _count(db, "skills")) == before
        assert before[0] == 3


def test_migration_round_trip(engine: Engine) -> None:
    migrate(TEST_DATABASE_URL, "base")
    with Session(engine) as db:
        tables = db.execute(
            text(
                "SELECT count(*) FROM pg_tables"
                " WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
            )
        ).scalar_one()
        assert tables == 0
    migrate(TEST_DATABASE_URL)
    with Session(engine) as db:
        seed_reference_data(db)
        assert _count(db, "skills") >= 60
