"""Minimal end-to-end API flow test for P0 stability acceptance.

Flow:
1) register/login
2) create character
3) update character (PATCH)
4) create world
5) start simulation
6) set speed
7) read simulation state
"""

import pytest
from httpx import AsyncClient

from tests.conftest import register_and_login
from the_world.main import app
from the_world.services.simulation_manager import SimulationManager


@pytest.mark.asyncio
async def test_minimal_flow_api_acceptance(client: AsyncClient) -> None:
    """Run the minimal product flow and assert each step succeeds."""
    # Ensure simulation endpoints have a manager in test context
    sim_manager = SimulationManager()
    app.state.sim_manager = sim_manager

    try:
        auth_headers = await register_and_login(
            client,
            username="flow_user",
            email="flow_user@theworld.test",
            password="FlowPassword1!",
        )

        create_character_resp = await client.post(
            "/api/v1/characters/",
            headers=auth_headers,
            json={
                "name": "Flow Character",
                "species": "human",
                "age": 22,
                "pronouns": "they/them",
                "description": "Created in minimal flow test",
                "personalityTraits": {
                    "openness": 60,
                    "conscientiousness": 55,
                    "extraversion": 50,
                    "agreeableness": 65,
                    "neuroticism": 35,
                    "custom": {},
                },
                "interests": ["reading"],
                "skills": ["Writing"],
                "isPublic": False,
            },
        )
        assert create_character_resp.status_code == 201
        character_id = create_character_resp.json()["id"]

        update_character_resp = await client.patch(
            f"/api/v1/characters/{character_id}",
            headers=auth_headers,
            json={"description": "Updated in minimal flow", "isPublic": True},
        )
        assert update_character_resp.status_code == 200
        assert update_character_resp.json()["description"] == "Updated in minimal flow"
        assert update_character_resp.json()["isPublic"] is True

        create_world_resp = await client.post("/api/v1/worlds/", headers=auth_headers)
        assert create_world_resp.status_code == 201
        world_id = create_world_resp.json()["id"]

        start_resp = await client.post(f"/api/v1/simulation/{world_id}/start")
        assert start_resp.status_code == 200

        speed_resp = await client.post(
            f"/api/v1/simulation/{world_id}/speed",
            json={"speed": 2.0},
        )
        assert speed_resp.status_code == 200
        assert speed_resp.json()["speed"] == 2.0

        state_resp = await client.get(f"/api/v1/simulation/{world_id}/state")
        assert state_resp.status_code == 200
        state = state_resp.json()
        assert state["worldId"] == world_id
        assert "clock" in state
        assert "characters" in state

    finally:
        sim_manager.shutdown_all()
