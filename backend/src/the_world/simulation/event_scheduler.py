"""Event scheduler — weather, seasonal festivals, random encounters, birthdays."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Any

from the_world.simulation.clock import GameClock, MINUTES_PER_HOUR
from the_world.simulation.events import (
    BIRTHDAY,
    RANDOM_EVENTS,
    SEASONAL_EVENTS,
    WEATHER_EVENTS,
    WEATHER_TEMPERATURE,
    WEATHER_TRANSITION_TABLE,
    EventCategory,
    RandomEventDef,
    WeatherState,
    WeatherType,
)

logger = logging.getLogger("the_world.simulation.events")

# Cooldown: same event won't fire again within this many ticks (2 game hours)
EVENT_COOLDOWN_TICKS = 120


@dataclass
class EventScheduler:
    """Checks and fires random events each scheduling cycle."""

    clock: GameClock
    weather: WeatherState = field(default_factory=WeatherState)
    check_interval_ticks: int = 30  # check every 30 ticks (30 game minutes)

    # Internal state
    _last_weather_hour: int = field(init=False, default=-1)
    _last_seasonal_day: int = field(init=False, default=-1)
    _last_seasonal_season: str = field(init=False, default="")
    _fired_birthdays: set[str] = field(init=False, default_factory=set)  # char_id set for current day
    _fired_birthdays_day: int = field(init=False, default=-1)
    _cooldowns: dict[str, int] = field(init=False, default_factory=dict)  # event_id → tick when last fired

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def check_and_fire(
        self,
        characters: dict[str, Any],  # dict[str, CharacterSim]
        locations: dict[str, dict[str, Any]],
        loc_name_to_type: dict[str, str],
        character_birthdays: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        """Run all event checks and return a list of event dicts to emit.

        Each returned dict matches the format expected by ``engine._emit_event()``.
        """
        events: list[dict[str, Any]] = []

        # 1. Weather update (every game hour)
        weather_events = self._check_weather()
        if weather_events:
            # Broadcast weather events to all characters
            for csim in characters.values():
                for we in weather_events:
                    events.append(self._build_event(we, csim))
                    self._apply_effects(csim, we)

        # 2. Seasonal festival (day 14 of each season, 10AM)
        seasonal = self._check_seasonal()
        if seasonal:
            for csim in characters.values():
                events.append(self._build_event(seasonal, csim))
                self._apply_effects(csim, seasonal)

        # 3. Birthday check
        if character_birthdays:
            birthday_events = self._check_birthdays(characters, character_birthdays)
            events.extend(birthday_events)

        # 4. Random events (per character, max 1 per character per check)
        for csim in characters.values():
            loc_type = loc_name_to_type.get(csim.current_location, "")
            rand_event = self._check_random_for_character(csim, loc_type)
            if rand_event:
                events.append(self._build_event(rand_event, csim))
                self._apply_effects(csim, rand_event)

        return events

    # ------------------------------------------------------------------
    # Weather
    # ------------------------------------------------------------------

    def _check_weather(self) -> list[RandomEventDef]:
        """Update weather once per game hour using Markov chain."""
        current_hour = self.clock.hour
        if current_hour == self._last_weather_hour:
            return []
        self._last_weather_hour = current_hour

        season = self.clock.season
        transition_table = WEATHER_TRANSITION_TABLE.get(season, {})
        row = transition_table.get(self.weather.current)
        if not row:
            return []

        old_weather = self.weather.current
        new_weather = self._weighted_choice(row)

        if new_weather == old_weather:
            return []

        self.weather.current = new_weather
        self.weather.temperature_modifier = WEATHER_TEMPERATURE.get(new_weather, 0.0)
        self.weather.changed_at_tick = self.clock.tick

        # Determine which weather event to fire
        triggered: list[RandomEventDef] = []
        if new_weather == WeatherType.rain:
            triggered.append(WEATHER_EVENTS["rain"])
        elif new_weather == WeatherType.storm:
            triggered.append(WEATHER_EVENTS["storm"])
        elif new_weather == WeatherType.snow and season == "winter":
            triggered.append(WEATHER_EVENTS["snow"])
        elif new_weather == WeatherType.clear and season in ("spring", "summer"):
            triggered.append(WEATHER_EVENTS["clear_nice"])

        return triggered

    # ------------------------------------------------------------------
    # Seasonal festivals
    # ------------------------------------------------------------------

    def _check_seasonal(self) -> RandomEventDef | None:
        """Trigger seasonal festival on day 14 at hour 10."""
        day = self.clock.day_of_season
        season = self.clock.season
        hour = self.clock.hour

        if day != 14 or hour != 10:
            return None
        if day == self._last_seasonal_day and season == self._last_seasonal_season:
            return None

        self._last_seasonal_day = day
        self._last_seasonal_season = season
        return SEASONAL_EVENTS.get(season)

    # ------------------------------------------------------------------
    # Birthdays
    # ------------------------------------------------------------------

    def _check_birthdays(
        self,
        characters: dict[str, Any],
        character_birthdays: dict[str, int],
    ) -> list[dict[str, Any]]:
        """Trigger birthday event for characters whose birthday is today at 8AM."""
        events: list[dict[str, Any]] = []
        current_day = self.clock.day
        hour = self.clock.hour

        # Reset birthday tracking on new day
        if current_day != self._fired_birthdays_day:
            self._fired_birthdays.clear()
            self._fired_birthdays_day = current_day

        if hour != 8:
            return events

        for char_id, birth_day in character_birthdays.items():
            if char_id in self._fired_birthdays:
                continue
            if birth_day == current_day:
                csim = characters.get(char_id)
                if csim:
                    self._fired_birthdays.add(char_id)
                    events.append(self._build_event(BIRTHDAY, csim))
                    self._apply_effects(csim, BIRTHDAY)

        return events

    # ------------------------------------------------------------------
    # Random events
    # ------------------------------------------------------------------

    def _check_random_for_character(
        self,
        csim: Any,  # CharacterSim
        location_type: str,
    ) -> RandomEventDef | None:
        """Try to trigger one random event for a character."""
        eligible = self._get_eligible_events(location_type)
        random.shuffle(eligible)

        for event_def in eligible:
            if self._is_on_cooldown(event_def.event_id):
                continue
            if self._roll_probability(event_def, csim.personality):
                self._cooldowns[event_def.event_id] = self.clock.tick
                return event_def

        return None

    def _get_eligible_events(self, location_type: str) -> list[RandomEventDef]:
        """Filter RANDOM_EVENTS by current season, location, time, and weather."""
        eligible: list[RandomEventDef] = []
        season = self.clock.season
        hour = self.clock.hour

        for event_def in RANDOM_EVENTS:
            # Season filter
            if event_def.allowed_seasons and season not in event_def.allowed_seasons:
                continue
            # Location filter
            if event_def.allowed_location_types and location_type not in event_def.allowed_location_types:
                continue
            # Hour filter
            if event_def.allowed_hours is not None:
                start_h, end_h = event_def.allowed_hours
                if start_h <= end_h:
                    if not (start_h <= hour <= end_h):
                        continue
                else:  # wraps around midnight (e.g. 20-4)
                    if not (hour >= start_h or hour <= end_h):
                        continue
            eligible.append(event_def)

        return eligible

    def _roll_probability(
        self,
        event_def: RandomEventDef,
        personality: dict[str, float],
    ) -> bool:
        """Roll probability with personality modifier."""
        prob = event_def.base_probability

        # Apply personality modifiers
        for trait, weight in event_def.personality_modifiers.items():
            trait_val = personality.get(trait, 0.5)
            # trait_val > 0.5 increases prob, < 0.5 decreases
            modifier = 1.0 + weight * (trait_val - 0.5)
            prob *= modifier

        return random.random() < prob

    def _is_on_cooldown(self, event_id: str) -> bool:
        """Check if event was fired recently."""
        last_tick = self._cooldowns.get(event_id)
        if last_tick is None:
            return False
        return (self.clock.tick - last_tick) < EVENT_COOLDOWN_TICKS

    # ------------------------------------------------------------------
    # Effects & building
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_effects(csim: Any, event_def: RandomEventDef) -> None:
        """Apply event need_effects to a character."""
        if event_def.need_effects:
            csim.needs.apply_activity_effect(event_def.need_effects)

    def _build_event(self, event_def: RandomEventDef, csim: Any) -> dict[str, Any]:
        """Build an event dict compatible with engine._emit_event()."""
        return {
            "type": self._event_type_for_category(event_def.category),
            "characterId": csim.id,
            "characterName": csim.name,
            "description": event_def.description_template.format(name=csim.name),
            "tick": self.clock.tick,
            "data": {
                "eventId": event_def.event_id,
                "category": event_def.category.value,
                "title": event_def.title,
                "moodModifier": event_def.mood_modifier,
                "memoryWorthy": event_def.memory_worthy,
                "memoryImportance": event_def.memory_importance,
                "memoryValence": event_def.memory_valence,
            },
        }

    @staticmethod
    def _event_type_for_category(category: EventCategory) -> str:
        return {
            EventCategory.random_encounter: "random_event",
            EventCategory.weather: "weather_change",
            EventCategory.seasonal: "seasonal_event",
            EventCategory.birthday: "birthday_event",
            EventCategory.location: "random_event",
        }[category]

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _weighted_choice(weights: dict[WeatherType, float]) -> WeatherType:
        """Pick a WeatherType using weighted random selection."""
        items = list(weights.items())
        total = sum(w for _, w in items)
        r = random.random() * total
        cumulative = 0.0
        for weather_type, weight in items:
            cumulative += weight
            if r <= cumulative:
                return weather_type
        return items[-1][0]  # fallback
