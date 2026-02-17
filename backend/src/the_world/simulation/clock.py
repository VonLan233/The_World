"""Game clock — tracks in-game time (minutes, hours, days, seasons)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict

MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
MINUTES_PER_DAY = MINUTES_PER_HOUR * HOURS_PER_DAY  # 1440
DAYS_PER_SEASON = 28
MINUTES_PER_SEASON = MINUTES_PER_DAY * DAYS_PER_SEASON  # 40320

SEASONS: list[str] = ["spring", "summer", "autumn", "winter"]


class ClockState(TypedDict):
    """Matches ``shared/types/simulation.ts → ClockState``."""

    currentTick: int
    currentHour: int
    currentDay: int
    currentSeason: str
    isPaused: bool


@dataclass
class GameClock:
    """Simple in-game clock driven by discrete ticks (1 tick = 1 game minute)."""

    tick: int = 0
    paused: bool = True

    # Derived (recomputed on every advance)
    _hour: int = field(init=False, default=0)
    _day: int = field(init=False, default=1)
    _season_index: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        self._recompute()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def hour(self) -> int:
        return self._hour

    @property
    def minute(self) -> int:
        return self.tick % MINUTES_PER_HOUR

    @property
    def day(self) -> int:
        return self._day

    @property
    def season(self) -> str:
        return SEASONS[self._season_index]

    @property
    def day_of_season(self) -> int:
        """1-indexed day within the current season (1-28)."""
        return ((self._day - 1) % DAYS_PER_SEASON) + 1

    @property
    def is_daytime(self) -> bool:
        """06:00 – 21:59 is daytime."""
        return 6 <= self._hour < 22

    @property
    def is_night(self) -> bool:
        return not self.is_daytime

    # ------------------------------------------------------------------
    # Advance
    # ------------------------------------------------------------------

    def advance(self, minutes: int = 1) -> None:
        """Advance the clock by *minutes* game-minutes."""
        self.tick += minutes
        self._recompute()

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_clock_state(self) -> ClockState:
        """Return a dict matching the frontend ``ClockState`` interface."""
        return ClockState(
            currentTick=self.tick,
            currentHour=self._hour,
            currentDay=self._day,
            currentSeason=self.season,
            isPaused=self.paused,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _recompute(self) -> None:
        total_minutes = self.tick
        self._hour = (total_minutes // MINUTES_PER_HOUR) % HOURS_PER_DAY
        total_days = total_minutes // MINUTES_PER_DAY
        self._day = total_days + 1  # 1-indexed
        self._season_index = (total_days // DAYS_PER_SEASON) % len(SEASONS)
