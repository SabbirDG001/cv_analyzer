from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.core.auth import AuthUser


def test_no_profile_returns_404(client: TestClient, user: AuthUser) -> None:
    assert client.get("/me/profile").status_code == 404


def test_create_then_read_profile(
    client: TestClient, user: AuthUser, profile_body: dict[str, object]
) -> None:
    created = client.put("/me/profile", json=profile_body)
    assert created.status_code == 200
    assert created.json()["id"] == str(user.id)

    fetched = client.get("/me/profile").json()
    assert fetched["name"] == "Test Student"
    assert fetched["track"] == "research"
    assert fetched["cgpa"] == "3.45"
    assert fetched["consent_at"] is None


def test_update_profile_overwrites(
    client: TestClient, user: AuthUser, profile_body: dict[str, object]
) -> None:
    client.put("/me/profile", json=profile_body)
    client.put("/me/profile", json={**profile_body, "year": 4, "track": "job"})
    fetched = client.get("/me/profile").json()
    assert (fetched["year"], fetched["track"]) == (4, "job")


@pytest.mark.parametrize(
    "patch",
    [
        {"cgpa": "4.50"},
        {"cgpa": "-1"},
        {"year": 0},
        {"year": 9},
        {"track": "gap-year"},
        {"name": "   "},
        {"field_id": 999999},
    ],
)
def test_invalid_profile_rejected(
    client: TestClient, user: AuthUser, profile_body: dict[str, object], patch: dict[str, object]
) -> None:
    response = client.put("/me/profile", json={**profile_body, **patch})
    assert response.status_code == 422


def test_users_cannot_see_each_others_profiles(
    client: TestClient,
    act_as: Callable[[AuthUser], None],
    make_user: Callable[[], AuthUser],
    profile_body: dict[str, object],
) -> None:
    alice, bob = make_user(), make_user()
    act_as(alice)
    client.put("/me/profile", json=profile_body)
    act_as(bob)
    assert client.get("/me/profile").status_code == 404
    client.put("/me/profile", json={**profile_body, "name": "Bob"})
    act_as(alice)
    assert client.get("/me/profile").json()["name"] == "Test Student"


def test_fields_lists_seeded_fields(client: TestClient, user: AuthUser) -> None:
    slugs = {f["slug"] for f in client.get("/fields").json()}
    assert {"biological-sciences", "computer-science-engineering"} <= slugs
