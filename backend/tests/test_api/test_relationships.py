"""Tests for the /api/v1/relationships endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from tests.conftest import register_and_login

SAMPLE_CHARACTER = {
    "name": "Test Character",
    "species": "human",
    "personalityTraits": {
        "openness": 80,
        "conscientiousness": 60,
        "extraversion": 70,
        "agreeableness": 75,
        "neuroticism": 30,
    },
    "isPublic": True,
}


async def _create_two_characters(
    client: AsyncClient, auth_headers: dict[str, str]
) -> tuple[str, str]:
    """Create two characters and return their IDs."""
    resp_a = await client.post(
        "/api/v1/characters/",
        json={**SAMPLE_CHARACTER, "name": "Alice"},
        headers=auth_headers,
    )
    resp_b = await client.post(
        "/api/v1/characters/",
        json={**SAMPLE_CHARACTER, "name": "Bob"},
        headers=auth_headers,
    )
    return resp_a.json()["id"], resp_b.json()["id"]


@pytest.mark.asyncio
async def test_list_relationships_empty(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    """GET /api/v1/relationships/{id} with no relationships returns empty list."""
    resp = await client.post(
        "/api/v1/characters/",
        json=SAMPLE_CHARACTER,
        headers=auth_headers,
    )
    char_id = resp.json()["id"]

    resp = await client.get(f"/api/v1/relationships/{char_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["characterId"] == char_id
    assert data["relationships"] == []


@pytest.mark.asyncio
async def test_get_relationship_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    """GET /api/v1/relationships/{a}/{b} returns 404 when no relationship exists."""
    id_a, id_b = await _create_two_characters(client, auth_headers)

    resp = await client.get(f"/api/v1/relationships/{id_a}/{id_b}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_relationship_nonexistent_char(client: AsyncClient) -> None:
    """GET /api/v1/relationships/{random}/{random} returns 404."""
    fake_a = str(uuid.uuid4())
    fake_b = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/relationships/{fake_a}/{fake_b}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_relationships_with_data(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    """After creating a relationship in the DB, list endpoint returns it."""
    id_a, id_b = await _create_two_characters(client, auth_headers)

    # Seed a relationship via the service layer directly
    from tests.conftest import TestSessionLocal
    from the_world.services.relationship_service import RelationshipService

    async with TestSessionLocal() as session:
        svc = RelationshipService(session)
        await svc.get_or_create(id_a, id_b)
        await session.commit()

    resp = await client.get(f"/api/v1/relationships/{id_a}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["relationships"]) == 1
    assert data["relationships"][0]["targetName"] == "Bob"
