"""Tests for the /api/v1/auth endpoints (register, login, me)."""

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    """POST /api/v1/auth/register returns 201 with AuthResponse (token + user)."""
    payload = {
        "username": "aurora_starlight",
        "email": "aurora@theworld.test",
        "password": "V3ryStr0ngPass!",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)

    assert resp.status_code == 201
    data = resp.json()
    # Token fields
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0
    # Nested user (camelCase)
    user = data["user"]
    assert user["username"] == "aurora_starlight"
    assert user["email"] == "aurora@theworld.test"
    assert user["displayName"] == "aurora_starlight"
    assert "id" in user
    assert "createdAt" in user
    # Password must never leak
    assert "password" not in data
    assert "hashedPassword" not in data


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient) -> None:
    """Registering the same username twice returns 409."""
    user = {
        "username": "duplicate_user",
        "email": "dup1@theworld.test",
        "password": "Password1234!",
    }
    resp1 = await client.post("/api/v1/auth/register", json=user)
    assert resp1.status_code == 201

    # Same username, different email
    user2 = {**user, "email": "dup2@theworld.test"}
    resp2 = await client.post("/api/v1/auth/register", json=user2)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Registering the same email twice returns 409."""
    user = {
        "username": "user_alpha",
        "email": "same@theworld.test",
        "password": "Password1234!",
    }
    resp1 = await client.post("/api/v1/auth/register", json=user)
    assert resp1.status_code == 201

    # Different username, same email
    user2 = {**user, "username": "user_beta"}
    resp2 = await client.post("/api/v1/auth/register", json=user2)
    assert resp2.status_code == 409


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    """Register then login returns 200 with AuthResponse (token + user)."""
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "login_user",
            "email": "login@theworld.test",
            "password": "MySecretPass99!",
        },
    )

    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "login_user", "password": "MySecretPass99!"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0
    # User nested
    assert data["user"]["username"] == "login_user"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    """Login with wrong password returns 401."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "wrongpass_user",
            "email": "wrongpass@theworld.test",
            "password": "CorrectPassword1!",
        },
    )

    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "wrongpass_user", "password": "TotallyWrong!"},
    )

    assert resp.status_code == 401
    assert "Incorrect username or password" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient) -> None:
    """Login with a username that does not exist returns 401."""
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "ghost_user", "password": "NoAccount123!"},
    )

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /me (current user)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """GET /api/v1/auth/me with valid token returns 200 + UserResponse (camelCase)."""
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
    assert "id" in data
    assert "createdAt" in data


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient) -> None:
    """GET /api/v1/auth/me without a token returns 401."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
