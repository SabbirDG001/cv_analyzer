"""Row Level Security, exercised as the non-superuser `authenticated` role."""

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import DBAPIError


@pytest.fixture
def two_profiles(engine: Engine) -> Iterator[tuple[uuid.UUID, uuid.UUID]]:
    a, b = uuid.uuid4(), uuid.uuid4()
    with engine.begin() as conn:
        field = conn.execute(text("SELECT id FROM fields LIMIT 1")).scalar_one()
        skill = conn.execute(text("SELECT id FROM skills LIMIT 1")).scalar_one()
        for uid, name in ((a, "Alice"), (b, "Bob")):
            conn.execute(text("INSERT INTO auth.users (id) VALUES (:id)"), {"id": uid})
            conn.execute(
                text(
                    "INSERT INTO profiles (id, name, university, year, department, cgpa, track,"
                    " field_id) VALUES (:id, :n, 'DU', 2, 'X', 3.0, 'job', :f)"
                ),
                {"id": uid, "n": name, "f": field},
            )
            conn.execute(
                text(
                    "INSERT INTO profile_skills (profile_id, skill_id, level, source)"
                    " VALUES (:id, :s, 3, 'manual')"
                ),
                {"id": uid, "s": skill},
            )
    yield a, b
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE auth.users CASCADE"))


@contextmanager
def signed_in_as(engine: Engine, user_id: uuid.UUID) -> Iterator[Connection]:
    with engine.connect() as conn:
        trans = conn.begin()
        conn.execute(text("SET LOCAL ROLE authenticated"))
        conn.execute(
            text("SELECT set_config('request.jwt.claim.sub', :s, true)"), {"s": str(user_id)}
        )
        try:
            yield conn
        finally:
            trans.rollback()


def test_user_sees_only_own_rows(engine: Engine, two_profiles: tuple[uuid.UUID, uuid.UUID]) -> None:
    alice, _ = two_profiles
    with signed_in_as(engine, alice) as conn:
        assert conn.execute(text("SELECT id FROM profiles")).scalars().all() == [alice]
        owners = conn.execute(text("SELECT profile_id FROM profile_skills")).scalars().all()
        assert owners == [alice]


def test_user_cannot_modify_other_users_rows(
    engine: Engine, two_profiles: tuple[uuid.UUID, uuid.UUID]
) -> None:
    alice, bob = two_profiles
    with signed_in_as(engine, alice) as conn:
        result = conn.execute(text("UPDATE profiles SET name = 'hacked' WHERE id = :b"), {"b": bob})
        assert result.rowcount == 0
        result = conn.execute(text("DELETE FROM profile_skills WHERE profile_id = :b"), {"b": bob})
        assert result.rowcount == 0


def test_user_cannot_insert_rows_for_someone_else(
    engine: Engine, two_profiles: tuple[uuid.UUID, uuid.UUID]
) -> None:
    alice, bob = two_profiles
    with signed_in_as(engine, alice) as conn, pytest.raises(DBAPIError):
        conn.execute(
            text("INSERT INTO analyses (profile_id) VALUES (:b)"),
            {"b": bob},
        )


def test_no_identity_means_no_rows(
    engine: Engine, two_profiles: tuple[uuid.UUID, uuid.UUID]
) -> None:
    with signed_in_as(engine, uuid.uuid4()) as conn:
        assert conn.execute(text("SELECT count(*) FROM profiles")).scalar_one() == 0


def test_reference_tables_are_read_only(engine: Engine) -> None:
    with signed_in_as(engine, uuid.uuid4()) as conn:
        assert conn.execute(text("SELECT count(*) FROM fields")).scalar_one() >= 3
        assert conn.execute(text("SELECT count(*) FROM skills")).scalar_one() >= 60
    with signed_in_as(engine, uuid.uuid4()) as conn, pytest.raises(DBAPIError):
        conn.execute(text("INSERT INTO fields (slug, name) VALUES ('x', 'X')"))
