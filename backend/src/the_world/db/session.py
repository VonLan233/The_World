"""Async SQLAlchemy engine and session factory.

Supports both PostgreSQL (production) and SQLite (local dev without Docker).
When using SQLite, PostgreSQL-specific types (UUID, JSONB) are compiled to
SQLite-compatible equivalents.
"""

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from the_world.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# ---------------------------------------------------------------------------
# SQLite compatibility: compile PostgreSQL types to SQLite equivalents
# ---------------------------------------------------------------------------
if _is_sqlite:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB as PG_JSONB
    from sqlalchemy.ext.compiler import compiles

    @compiles(PG_UUID, "sqlite")
    def _compile_uuid_sqlite(type_, compiler, **kw):  # noqa: N802
        return "CHAR(32)"

    @compiles(PG_JSONB, "sqlite")
    def _compile_jsonb_sqlite(type_, compiler, **kw):  # noqa: N802
        return "TEXT"

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
engine_kwargs: dict = {
    "echo": settings.APP_DEBUG,
    "future": True,
}
if not _is_sqlite:
    engine_kwargs["pool_pre_ping"] = True

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

# Enable foreign keys for SQLite
if _is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
