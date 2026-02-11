"""REST API for simulation control (start, pause, speed, state)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from the_world.services.simulation_manager import SimulationManager

router = APIRouter()


def _get_sim_manager(request: Request) -> SimulationManager:
    mgr: SimulationManager | None = getattr(request.app.state, "sim_manager", None)
    if mgr is None:
        raise HTTPException(status_code=503, detail="Simulation manager not initialised")
    return mgr


class SpeedBody(BaseModel):
    speed: float


@router.post("/{world_id}/start")
async def start_simulation(
    world_id: str,
    mgr: Annotated[SimulationManager, Depends(_get_sim_manager)],
) -> dict[str, Any]:
    """Start (or resume) the simulation for a world."""
    engine = mgr.get_or_create_engine(world_id)

    # Wire WS callbacks if not already done
    from the_world.api.v1.ws import register_engine_callbacks

    if not engine._on_tick:
        register_engine_callbacks(world_id, engine)

    engine.start()
    return engine.get_state()


@router.post("/{world_id}/pause")
async def pause_simulation(
    world_id: str,
    mgr: Annotated[SimulationManager, Depends(_get_sim_manager)],
) -> dict[str, Any]:
    """Pause the simulation for a world."""
    engine = mgr.get_engine(world_id)
    if engine is None:
        raise HTTPException(status_code=404, detail="No simulation running for this world")
    engine.pause()
    return engine.get_state()


@router.post("/{world_id}/speed")
async def set_speed(
    world_id: str,
    body: SpeedBody,
    mgr: Annotated[SimulationManager, Depends(_get_sim_manager)],
) -> dict[str, Any]:
    """Set the simulation speed (1-10×)."""
    engine = mgr.get_engine(world_id)
    if engine is None:
        raise HTTPException(status_code=404, detail="No simulation running for this world")
    engine.set_speed(body.speed)
    return {"speed": engine.time_scale}


@router.get("/{world_id}/state")
async def get_state(
    world_id: str,
    mgr: Annotated[SimulationManager, Depends(_get_sim_manager)],
) -> dict[str, Any]:
    """Get the current simulation state for a world."""
    engine = mgr.get_engine(world_id)
    if engine is None:
        raise HTTPException(status_code=404, detail="No simulation running for this world")
    return engine.get_state()
