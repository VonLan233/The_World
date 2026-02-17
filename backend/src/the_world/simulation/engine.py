"""Core simulation engine — orchestrates the game loop via SimPy + asyncio."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

import simpy

from the_world.simulation.activities import IDLE, SLEEP, WALK_TO, Activity
from the_world.simulation.autonomy import choose_activity
from the_world.simulation.clock import GameClock
from the_world.simulation.event_scheduler import EventScheduler
from the_world.simulation.needs import NeedsManager

logger = logging.getLogger("the_world.simulation")


# ---------------------------------------------------------------------------
# Per-character simulation wrapper
# ---------------------------------------------------------------------------

@dataclass
class CharacterSim:
    """In-memory representation of a character inside the simulation."""

    id: str
    name: str
    personality: dict[str, float]
    needs: NeedsManager = field(default_factory=NeedsManager)
    current_activity: str = "idle"
    current_location: str = "Home"
    current_location_type: str = "home"
    position_x: float = 100.0
    position_y: float = 300.0

    def to_state_update(self) -> dict[str, Any]:
        """Return a ``CharacterStateUpdate``-compatible dict."""
        mood_score, mood_label = self.needs.calculate_mood()
        return {
            "characterId": self.id,
            "needs": self.needs.to_dict(),
            "currentActivity": self.current_activity,
            "currentLocation": self.current_location,
            "mood": mood_label,
            "moodScore": mood_score,
            "position": {"x": self.position_x, "y": self.position_y},
        }


# ---------------------------------------------------------------------------
# Simulation engine
# ---------------------------------------------------------------------------

EventCallback = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


class SimulationEngine:
    """Drives the discrete-event simulation for a single world.

    Uses ``simpy.Environment`` for scheduling character processes and an
    ``asyncio.Task`` for the real-time tick loop.
    """

    def __init__(
        self,
        world_id: str,
        time_scale: float = 1.0,
        tick_interval_s: float = 1.0,
    ) -> None:
        self.world_id = world_id
        self.time_scale = time_scale
        self.tick_interval_s = tick_interval_s

        # SimPy environment (1 unit = 1 game minute)
        self.env = simpy.Environment()
        self.clock = GameClock()

        # Characters indexed by id
        self.characters: dict[str, CharacterSim] = {}

        # Locations: name → {type, position_x, position_y, available_activities}
        self.locations: dict[str, dict[str, Any]] = {}
        # Quick lookup: name → type
        self._loc_name_to_type: dict[str, str] = {}

        self.paused = True
        self.running = False
        self._task: asyncio.Task[None] | None = None

        # Callbacks invoked on every tick / event / encounter
        self._on_tick: list[EventCallback] = []
        self._on_event: list[EventCallback] = []
        self._on_encounter: list[EventCallback] = []
        self._encounter_counter: int = 0

        # Random event system
        self.event_scheduler = EventScheduler(clock=self.clock)
        self._event_check_counter: int = 0
        self._enable_random_events: bool = True
        self._character_birthdays: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Location management
    # ------------------------------------------------------------------

    def add_location(
        self,
        name: str,
        location_type: str,
        position_x: float,
        position_y: float,
        available_activities: list[str] | None = None,
    ) -> None:
        self.locations[name] = {
            "type": location_type,
            "position_x": position_x,
            "position_y": position_y,
            "available_activities": available_activities or [],
        }
        self._loc_name_to_type[name] = location_type

    # ------------------------------------------------------------------
    # Character management
    # ------------------------------------------------------------------

    def add_character(self, char_id: str, name: str, personality: dict[str, float]) -> CharacterSim:
        """Add a character to the simulation and start its life-process."""
        csim = CharacterSim(id=char_id, name=name, personality=personality)

        # Place at first "home" location if available
        for loc_name, loc_data in self.locations.items():
            if loc_data["type"] == "home":
                csim.current_location = loc_name
                csim.current_location_type = loc_data["type"]
                csim.position_x = loc_data["position_x"]
                csim.position_y = loc_data["position_y"]
                break

        self.characters[char_id] = csim
        self.env.process(self._character_loop(csim))
        logger.info("Character %s (%s) added to world %s", name, char_id, self.world_id)
        return csim

    def remove_character(self, char_id: str) -> None:
        self.characters.pop(char_id, None)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Unpause the simulation (the asyncio loop must already be running)."""
        if not self.running:
            self.running = True
            self._task = asyncio.get_event_loop().create_task(self._run_loop())
        self.paused = False
        self.clock.paused = False
        logger.info("Simulation %s started", self.world_id)

    def pause(self) -> None:
        self.paused = True
        self.clock.paused = True
        logger.info("Simulation %s paused", self.world_id)

    def resume(self) -> None:
        self.paused = False
        self.clock.paused = False

    def stop(self) -> None:
        self.running = False
        self.paused = True
        self.clock.paused = True
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Simulation %s stopped", self.world_id)

    def set_speed(self, speed: float) -> None:
        """Set the time scale (1 = normal, 2 = 2× faster, etc.)."""
        self.time_scale = max(0.25, min(speed, 10.0))

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def on_tick(self, cb: EventCallback) -> None:
        self._on_tick.append(cb)

    def on_event(self, cb: EventCallback) -> None:
        self._on_event.append(cb)

    def on_encounter(self, cb: EventCallback) -> None:
        """Register a callback invoked periodically to check for encounters."""
        self._on_encounter.append(cb)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def _run_loop(self) -> None:
        """Async main loop — each iteration advances the simulation by 1 game minute."""
        try:
            while self.running:
                if not self.paused and self.characters:
                    steps = max(1, int(self.time_scale))
                    for _ in range(steps):
                        # Advance SimPy by 1 game-minute
                        self.env.run(until=self.env.now + 1)
                        self.clock.advance(1)

                        # Decay needs for every character
                        for csim in self.characters.values():
                            is_sleeping = csim.current_activity == "sleep"
                            csim.needs.decay(1, csim.personality, is_sleeping)

                    # Check for encounters periodically
                    self._encounter_counter += 1
                    if self._encounter_counter % 10 == 0:
                        await self._check_encounters()

                    # Check for random events
                    self._event_check_counter += 1
                    if (
                        self._enable_random_events
                        and self._event_check_counter % self.event_scheduler.check_interval_ticks == 0
                    ):
                        await self._check_random_events()

                    # Broadcast state
                    await self._broadcast_tick()

                await asyncio.sleep(self.tick_interval_s)
        except asyncio.CancelledError:
            pass

    async def _broadcast_tick(self) -> None:
        """Send tick update to all registered callbacks."""
        payload = {
            "type": "tick",
            "worldId": self.world_id,
            "clock": self.clock.to_clock_state(),
            "characters": [c.to_state_update() for c in self.characters.values()],
            "weather": self.event_scheduler.weather.to_dict(),
        }
        for cb in self._on_tick:
            try:
                await cb(payload)
            except Exception:
                logger.exception("Error in tick callback")

    async def _check_encounters(self) -> None:
        """Invoke encounter callbacks with the current tick."""
        payload = {"tick": self.clock.tick}
        for cb in self._on_encounter:
            try:
                await cb(payload)
            except Exception:
                logger.exception("Error in encounter callback")

    async def _emit_event(self, event: dict[str, Any]) -> None:
        for cb in self._on_event:
            try:
                await cb(event)
            except Exception:
                logger.exception("Error in event callback")

    # ------------------------------------------------------------------
    # Random events
    # ------------------------------------------------------------------

    async def _check_random_events(self) -> None:
        """Run the event scheduler and emit any triggered events."""
        events = self.event_scheduler.check_and_fire(
            characters=self.characters,
            locations=self.locations,
            loc_name_to_type=self._loc_name_to_type,
            character_birthdays=self._character_birthdays,
        )
        for event in events:
            await self._emit_event(event)

    def set_character_birthday(self, char_id: str, birth_day: int) -> None:
        """Register a character's birthday (game-day number)."""
        self._character_birthdays[char_id] = birth_day

    # ------------------------------------------------------------------
    # Character life-loop (SimPy process)
    # ------------------------------------------------------------------

    def _character_loop(self, csim: CharacterSim):  # noqa: ANN202  (generator)
        """SimPy process — character repeatedly picks and executes activities."""
        while True:
            if csim.id not in self.characters:
                return  # character removed

            nearby = [
                {"id": o.id, "name": o.name}
                for o in self.characters.values()
                if o.id != csim.id and o.current_location == csim.current_location
            ]

            activity, destination = choose_activity(
                csim.needs,
                csim.personality,
                csim.current_location_type,
                self._loc_name_to_type,
                nearby_characters=nearby if nearby else None,
            )

            # Handle walk_to
            if activity.name == "walk_to" and destination:
                loc = self.locations.get(destination)
                if loc:
                    csim.current_activity = f"walking to {destination}"
                    yield self.env.timeout(activity.duration_minutes)
                    csim.current_location = destination
                    csim.current_location_type = loc["type"]
                    csim.position_x = loc["position_x"]
                    csim.position_y = loc["position_y"]
                    csim.current_activity = "arrived"
                    # Emit location_change event
                    asyncio.ensure_future(self._emit_event({
                        "type": "location_change",
                        "characterId": csim.id,
                        "characterName": csim.name,
                        "description": f"{csim.name} walked to {destination}",
                        "tick": self.clock.tick,
                        "data": {"destination": destination},
                    }))
                    continue

            # Normal activity
            csim.current_activity = activity.name
            asyncio.ensure_future(self._emit_event({
                "type": "activity_start",
                "characterId": csim.id,
                "characterName": csim.name,
                "description": activity.description_template.format(
                    name=csim.name, destination=""
                ),
                "tick": self.clock.tick,
                "data": {"activity": activity.name},
            }))

            yield self.env.timeout(activity.duration_minutes)

            # Apply effects
            if activity.name == "sleep":
                csim.needs.energy = 100.0
            elif activity.name == "shower":
                csim.needs.hygiene = 100.0
            else:
                csim.needs.apply_activity_effect(activity.need_effects)

            # Check for critical needs
            critical = csim.needs.any_critical()
            if critical:
                asyncio.ensure_future(self._emit_event({
                    "type": "need_critical",
                    "characterId": csim.id,
                    "characterName": csim.name,
                    "description": f"{csim.name}'s {critical} is critically low!",
                    "tick": self.clock.tick,
                    "data": {"need": critical, "value": getattr(csim.needs, critical)},
                }))

            csim.current_activity = "idle"

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def get_state(self) -> dict[str, Any]:
        """Return full simulation state (for REST API / initial WS payload)."""
        return {
            "worldId": self.world_id,
            "clock": self.clock.to_clock_state(),
            "characters": [c.to_state_update() for c in self.characters.values()],
            "paused": self.paused,
            "speed": self.time_scale,
            "weather": self.event_scheduler.weather.to_dict(),
        }
