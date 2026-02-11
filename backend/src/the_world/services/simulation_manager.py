"""SimulationManager — manages SimulationEngine instances per world."""

from __future__ import annotations

import logging
from typing import Any

from the_world.simulation.engine import SimulationEngine

logger = logging.getLogger("the_world.simulation")


class SimulationManager:
    """Singleton that manages one SimulationEngine per world.

    Stored on ``app.state.sim_manager`` during the FastAPI lifespan.
    """

    def __init__(self) -> None:
        self._engines: dict[str, SimulationEngine] = {}

    # ------------------------------------------------------------------
    # Engine lifecycle
    # ------------------------------------------------------------------

    def get_engine(self, world_id: str) -> SimulationEngine | None:
        return self._engines.get(world_id)

    def get_or_create_engine(
        self,
        world_id: str,
        time_scale: float = 1.0,
        tick_interval_s: float = 1.0,
    ) -> SimulationEngine:
        if world_id not in self._engines:
            engine = SimulationEngine(
                world_id=world_id,
                time_scale=time_scale,
                tick_interval_s=tick_interval_s,
            )
            self._engines[world_id] = engine
            logger.info("Created simulation engine for world %s", world_id)
        return self._engines[world_id]

    def remove_engine(self, world_id: str) -> None:
        engine = self._engines.pop(world_id, None)
        if engine:
            engine.stop()

    def shutdown_all(self) -> None:
        """Stop all running engines (called on app shutdown)."""
        for engine in self._engines.values():
            engine.stop()
        self._engines.clear()
        logger.info("All simulation engines shut down")

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def active_worlds(self) -> list[str]:
        return list(self._engines.keys())
