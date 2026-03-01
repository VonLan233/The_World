"""Top-level v1 API router that aggregates all sub-routers."""

from fastapi import APIRouter

from the_world.api.v1 import auth, characters, relationships, simulation, worlds, ws

v1_router = APIRouter()

v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
v1_router.include_router(characters.router, prefix="/characters", tags=["characters"])
v1_router.include_router(relationships.router, prefix="/relationships", tags=["relationships"])
v1_router.include_router(simulation.router, prefix="/simulation", tags=["simulation"])
v1_router.include_router(worlds.router, prefix="/worlds", tags=["worlds"])
v1_router.include_router(ws.router, tags=["websocket"])
