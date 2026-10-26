import os
import uuid
from collections.abc import Callable, Iterator

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from alembic import command
from app.core.auth import AuthUser, get_current_user
from app.db.session import get_db
from app.main import app
from app.seed import seed_reference_data

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/skillbridge_test"
)


def migrate(url: str, revision: str = "head") -> None:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    if revision == "head":
        command.upgrade(cfg, "head")
    else:
        command.downgrade(cfg, revision)


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    eng = create_engine(TEST_DATABASE_URL)
    with eng.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS auth CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    migrate(TEST_DATABASE_URL)
    with Session(eng) as db:
        seed_reference_data(db)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        yield session
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE auth.users CASCADE"))


@pytest.fixture
def make_user(db: Session) -> Callable[[], AuthUser]:
    def _make() -> AuthUser:
        user = AuthUser(id=uuid.uuid4(), email="student@example.com")
        db.execute(text("INSERT INTO auth.users (id) VALUES (:id)"), {"id": user.id})
        db.commit()
        return user

    return _make


@pytest.fixture
def raw_client(db: Session) -> Iterator[TestClient]:
    """Client with the real auth dependency, only the DB session swapped."""
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def client(raw_client: TestClient, make_user: Callable[[], AuthUser]) -> TestClient:
    """Client signed in as a fresh user; call `act_as` to switch users."""
    app.dependency_overrides[get_current_user] = make_user
    return raw_client


@pytest.fixture
def act_as() -> Callable[[AuthUser], None]:
    def _act(user: AuthUser) -> None:
        app.dependency_overrides[get_current_user] = lambda: user

    return _act


@pytest.fixture
def user(make_user: Callable[[], AuthUser], act_as: Callable[[AuthUser], None]) -> AuthUser:
    created = make_user()
    act_as(created)
    return created


@pytest.fixture
def field_id(db: Session) -> int:
    return int(db.execute(text("SELECT id FROM fields ORDER BY id LIMIT 1")).scalar_one())


@pytest.fixture
def profile_body(field_id: int) -> dict[str, object]:
    return {
        "name": "Test Student",
        "university": "University of Dhaka",
        "year": 3,
        "department": "Biochemistry",
        "cgpa": "3.45",
        "track": "research",
        "field_id": field_id,
    }
