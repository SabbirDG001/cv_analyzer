from collections.abc import Callable

from fastapi.testclient import TestClient

from app.core.auth import AuthUser


def _skill_id(client: TestClient, query: str) -> int:
    return int(client.get("/skills", params={"q": query}).json()[0]["id"])


def test_search_matches_name_and_alias(client: TestClient, user: AuthUser) -> None:
    by_name = [s["name"] for s in client.get("/skills", params={"q": "python"}).json()]
    by_alias = [s["name"] for s in client.get("/skills", params={"q": "dsa"}).json()]
    assert "Python" in by_name
    assert "Data Structures & Algorithms" in by_alias


def test_search_without_query_is_capped(client: TestClient, user: AuthUser) -> None:
    assert len(client.get("/skills").json()) == 20


def test_skill_requires_profile(client: TestClient, user: AuthUser) -> None:
    skill_id = _skill_id(client, "python")
    assert client.put(f"/me/skills/{skill_id}", json={"level": 3}).status_code == 409


def test_set_update_and_delete_skill(
    client: TestClient, user: AuthUser, profile_body: dict[str, object]
) -> None:
    client.put("/me/profile", json=profile_body)
    skill_id = _skill_id(client, "python")

    assert client.put(f"/me/skills/{skill_id}", json={"level": 2}).status_code == 204
    assert client.put(f"/me/skills/{skill_id}", json={"level": 4}).status_code == 204
    skills = client.get("/me/skills").json()
    assert skills == [{"skill_id": skill_id, "name": "Python", "level": 4, "source": "manual"}]

    assert client.delete(f"/me/skills/{skill_id}").status_code == 204
    assert client.get("/me/skills").json() == []
    assert client.delete(f"/me/skills/{skill_id}").status_code == 404


def test_level_bounds_and_unknown_skill(
    client: TestClient, user: AuthUser, profile_body: dict[str, object]
) -> None:
    client.put("/me/profile", json=profile_body)
    skill_id = _skill_id(client, "python")
    assert client.put(f"/me/skills/{skill_id}", json={"level": 6}).status_code == 422
    assert client.put(f"/me/skills/{skill_id}", json={"level": -1}).status_code == 422
    assert client.put("/me/skills/999999", json={"level": 1}).status_code == 404


def test_skills_are_private_per_user(
    client: TestClient,
    act_as: Callable[[AuthUser], None],
    make_user: Callable[[], AuthUser],
    profile_body: dict[str, object],
) -> None:
    alice, bob = make_user(), make_user()
    act_as(alice)
    client.put("/me/profile", json=profile_body)
    skill_id = _skill_id(client, "python")
    client.put(f"/me/skills/{skill_id}", json={"level": 5})

    act_as(bob)
    client.put("/me/profile", json=profile_body)
    assert client.get("/me/skills").json() == []
    assert client.delete(f"/me/skills/{skill_id}").status_code == 404
