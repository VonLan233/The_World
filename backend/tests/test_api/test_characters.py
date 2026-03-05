"""Tests for the /api/v1/characters endpoints (CRUD + public gallery).

Request payloads use camelCase (as the frontend sends them).
Response assertions use camelCase (as the backend returns them).
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.conftest import register_and_login

# ---------------------------------------------------------------------------
# Shared test data (camelCase -- matching frontend payloads)
# ---------------------------------------------------------------------------

SAMPLE_CHARACTER: dict = {
    "name": "Test Character",
    "species": "human",
    "age": 25,
    "pronouns": "she/her",
    "description": "A brave adventurer",
    "backstory": "Born in a small village...",
    "personalityTraits": {
        "openness": 80,
        "conscientiousness": 60,
        "extraversion": 70,
        "agreeableness": 75,
        "neuroticism": 30,
        "custom": {},
    },
    "interests": ["reading", "swordfighting"],
    "skills": ["Cooking", "Athletics"],
    "isPublic": True,
}


def _make_character(**overrides) -> dict:
    """Return a copy of SAMPLE_CHARACTER with optional field overrides."""
    data = {**SAMPLE_CHARACTER, **overrides}
    return data


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_character(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """POST /api/v1/characters/ with auth creates a character (201)."""
    resp = await client.post(
        "/api/v1/characters/", json=SAMPLE_CHARACTER, headers=auth_headers
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Character"
    assert data["species"] == "human"
    assert data["age"] == 25
    assert data["pronouns"] == "she/her"
    assert data["description"] == "A brave adventurer"
    assert data["backstory"] == "Born in a small village..."
    assert data["personalityTraits"]["openness"] == 80
    assert data["interests"] == ["reading", "swordfighting"]
    assert sorted(data["skills"]) == ["Athletics", "Cooking"]
    assert data["isPublic"] is True
    assert "id" in data
    assert "userId" in data
    assert "createdAt" in data
    assert "updatedAt" in data


@pytest.mark.asyncio
async def test_create_character_unauthenticated(client: AsyncClient) -> None:
    """POST /api/v1/characters/ without auth returns 401."""
    resp = await client.post("/api/v1/characters/", json=SAMPLE_CHARACTER)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# List (own characters)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_my_characters(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Create 2 characters, GET /api/v1/characters/ returns both."""
    char1 = _make_character(name="Aria Windwalker")
    char2 = _make_character(name="Zephyr Nightshade")

    await client.post("/api/v1/characters/", json=char1, headers=auth_headers)
    await client.post("/api/v1/characters/", json=char2, headers=auth_headers)

    resp = await client.get("/api/v1/characters/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    names = {c["name"] for c in data}
    assert names == {"Aria Windwalker", "Zephyr Nightshade"}


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_character_by_id(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Create a character then GET /api/v1/characters/{id} returns it."""
    create_resp = await client.post(
        "/api/v1/characters/", json=SAMPLE_CHARACTER, headers=auth_headers
    )
    character_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/characters/{character_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == character_id
    assert resp.json()["name"] == "Test Character"


@pytest.mark.asyncio
async def test_get_nonexistent_character(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """GET /api/v1/characters/{random_uuid} returns 404."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/characters/{fake_id}", headers=auth_headers)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_character(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """PUT /api/v1/characters/{id} updates the character (200)."""
    create_resp = await client.post(
        "/api/v1/characters/", json=SAMPLE_CHARACTER, headers=auth_headers
    )
    character_id = create_resp.json()["id"]

    update_payload = {"name": "Aria Windwalker (Updated)", "age": 30}
    resp = await client.put(
        f"/api/v1/characters/{character_id}", json=update_payload, headers=auth_headers
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Aria Windwalker (Updated)"
    assert data["age"] == 30
    # Unchanged fields should remain the same
    assert data["species"] == "human"
    assert data["pronouns"] == "she/her"


@pytest.mark.asyncio
async def test_patch_character(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """PATCH /api/v1/characters/{id} updates partial fields (200)."""
    create_resp = await client.post(
        "/api/v1/characters/", json=SAMPLE_CHARACTER, headers=auth_headers
    )
    character_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/characters/{character_id}",
        json={"description": "Updated via PATCH", "isPublic": False},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "Updated via PATCH"
    assert data["isPublic"] is False
    assert data["name"] == "Test Character"


@pytest.mark.asyncio
async def test_update_character_not_owner(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """User B cannot update User A's character (403)."""
    # User A (default test user) creates a character
    create_resp = await client.post(
        "/api/v1/characters/", json=SAMPLE_CHARACTER, headers=auth_headers
    )
    character_id = create_resp.json()["id"]

    # Register + login as user B
    user_b_headers = await register_and_login(
        client,
        username="user_b",
        email="userb@theworld.test",
        password="UserBPassword1!",
    )

    # User B attempts to update User A's character
    resp = await client.put(
        f"/api/v1/characters/{character_id}",
        json={"name": "Hijacked!"},
        headers=user_b_headers,
    )
    assert resp.status_code == 403
    assert "Not the character owner" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_character(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """DELETE /api/v1/characters/{id} removes the character (204)."""
    create_resp = await client.post(
        "/api/v1/characters/", json=SAMPLE_CHARACTER, headers=auth_headers
    )
    character_id = create_resp.json()["id"]

    del_resp = await client.delete(
        f"/api/v1/characters/{character_id}", headers=auth_headers
    )
    assert del_resp.status_code == 204

    # Confirm it is gone
    get_resp = await client.get(f"/api/v1/characters/{character_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_character_not_owner(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """User B cannot delete User A's character (403)."""
    # User A creates a character
    create_resp = await client.post(
        "/api/v1/characters/", json=SAMPLE_CHARACTER, headers=auth_headers
    )
    character_id = create_resp.json()["id"]

    # Register + login as user B
    user_b_headers = await register_and_login(
        client,
        username="user_b_del",
        email="userb_del@theworld.test",
        password="UserBPassword1!",
    )

    # User B attempts to delete User A's character
    resp = await client.delete(
        f"/api/v1/characters/{character_id}", headers=user_b_headers
    )
    assert resp.status_code == 403
    assert "Not the character owner" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Public gallery
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_public_gallery(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """GET /api/v1/characters/public returns only public characters."""
    # Create a public character (isPublic=True)
    public_char = _make_character(name="Public Hero", isPublic=True)
    await client.post("/api/v1/characters/", json=public_char, headers=auth_headers)

    # Create a private character
    private_char = _make_character(name="Secret Agent", isPublic=False)
    await client.post("/api/v1/characters/", json=private_char, headers=auth_headers)

    # Gallery should only contain the public character
    resp = await client.get("/api/v1/characters/public")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Public Hero"
