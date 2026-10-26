"""Idempotent loader for reference data: `python -m app.seed`."""

import json
from pathlib import Path
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.session import get_engine
from app.models import Field, Skill

SEED_DIR = Path(__file__).resolve().parent.parent / "seed"


def _load(name: str) -> list[dict[str, Any]]:
    return json.loads((SEED_DIR / name).read_text(encoding="utf-8"))


def seed_reference_data(db: Session) -> tuple[int, int]:
    """Upsert fields and skills by their unique keys; returns (fields, skills) counts."""
    fields = _load("fields.json")
    skills = _load("skills.json")
    stmt = insert(Field).values(fields)
    db.execute(
        stmt.on_conflict_do_update(index_elements=["slug"], set_={"name": stmt.excluded.name})
    )
    stmt = insert(Skill).values(skills)
    db.execute(
        stmt.on_conflict_do_update(
            index_elements=["name"],
            set_={"category": stmt.excluded.category, "aliases": stmt.excluded.aliases},
        )
    )
    db.commit()
    return len(fields), len(skills)


def main() -> None:
    with Session(get_engine()) as db:
        n_fields, n_skills = seed_reference_data(db)
    print(f"Seeded {n_fields} fields and {n_skills} skills")


if __name__ == "__main__":
    main()
