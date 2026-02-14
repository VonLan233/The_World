"""FastAPI application factory for The World."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from the_world.api.v1.router import v1_router
from the_world.config import settings

logger = logging.getLogger("the_world")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: startup / shutdown logic."""
    # Auto-create tables when using SQLite (local dev without Docker/PostgreSQL)
    if settings.DATABASE_URL.startswith("sqlite"):
        from the_world.db.base import Base
        from the_world.db.session import engine
        import the_world.models  # noqa: F401 — ensure all models are registered

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("SQLite dev mode: tables created automatically")

    # Initialise simulation manager
    from the_world.services.simulation_manager import SimulationManager

    sim_manager = SimulationManager()
    app.state.sim_manager = sim_manager

    logger.info("The World is running  [env=%s]", settings.APP_ENV)
    yield

    # Shutdown
    sim_manager.shutdown_all()

    # Close AI clients
    from the_world.ai.tier2_ollama import close_client as close_ollama_client

    await close_ollama_client()

    logger.info("The World is shutting down.")


def create_app() -> FastAPI:
    """Build and return the FastAPI application instance."""
    app = FastAPI(
        title="The World",
        description="OC life-simulation platform -- watch your characters live, grow, and interact.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # -- CORS (wide-open in dev, lock down for production) --
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.APP_ENV == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -- Routers --
    app.include_router(v1_router, prefix="/api/v1")

    # -- Health check --
    @app.get("/health", tags=["infra"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
