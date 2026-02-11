"""Shared pytest fixtures for The World backend tests."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from the_world.main import app


@pytest.fixture()
async def client() -> AsyncIterator[AsyncClient]:
    """Yield an httpx AsyncClient wired to the FastAPI app (no real server)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
