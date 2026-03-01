"""Shared pytest fixtures for The World backend tests.

Uses an in-memory SQLite database (via aiosqlite) so tests run without
PostgreSQL.  PostgreSQL-specific column types (UUID, JSONB) are compiled
to SQLite-compatible equivalents at the dialect level.
"""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Patch PostgreSQL types *before* any model imports so that the SQLite
# dialect knows how to emit DDL for UUID and JSONB columns.
# ---------------------------------------------------------------------------
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB as PG_JSONB
from sqlalchemy import String, Text

# Teach SQLite how to compile PG_UUID -> CHAR(32)
from sqlalchemy.ext.compiler import compiles

@compiles(PG_UUID, "sqlite")
def _compile_uuid_sqlite(type_, compiler, **kw):  # noqa: N802
    return "CHAR(32)"

@compiles(PG_JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):  # noqa: N802
    return "TEXT"

# ---------------------------------------------------------------------------
# Now safe to import app and models
# ---------------------------------------------------------------------------
from the_world.db.base import Base
# Import all models so metadata.create_all sees every table
import the_world.models  # noqa: F401
from the_world.dependencies import get_db
from the_world.main import app

# ---------------------------------------------------------------------------
# Test engine (in-memory SQLite, async via aiosqlite)
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite://"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Enable foreign-key enforcement for every SQLite connection
@event.listens_for(test_engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
async def _setup_db() -> AsyncIterator[None]:
    """Create all tables before each test and drop them after."""
    # Clear login rate limiter between tests
    from the_world.api.v1.auth import _login_attempts
    _login_attempts.clear()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _override_get_db() -> AsyncIterator[AsyncSession]:
    """Dependency override that yields a test-scoped async session."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture()
async def client() -> AsyncIterator[AsyncClient]:
    """Yield an httpx AsyncClient wired to the FastAPI app with the
    database dependency overridden to use the in-memory SQLite engine."""
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth helper fixtures
# ---------------------------------------------------------------------------

async def register_and_login(
    client: AsyncClient,
    username: str = "testuser",
    email: str = "testuser@example.com",
    password: str = "SecurePass123!",
) -> dict[str, str]:
    """Register a user then log in, returning an Authorization header dict."""
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    data = login_resp.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Create a default test user and return JWT auth headers."""
    return await register_and_login(client)
