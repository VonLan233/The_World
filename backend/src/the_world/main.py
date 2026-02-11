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
    logger.info("The World is running  [env=%s]", settings.APP_ENV)
    yield
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
