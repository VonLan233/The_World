"""Needs system — six core needs (0-100) with decay, recovery, and mood."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict

NEED_NAMES = ("hunger", "energy", "social", "fun", "hygiene", "comfort")

# Base decay rates per game-hour (negative = decays, positive only when sleeping)
BASE_DECAY: dict[str, float] = {
    "hunger": -2.0,
    "energy": -3.0,
    "social": -1.5,
    "fun": -1.0,
    "hygiene": -0.5,
    "comfort": -0.8,
}

# Energy recovery rate per game-hour while sleeping
ENERGY_SLEEP_RATE = 8.0

# Critical thresholds — below these the need is "urgent"
CRITICAL: dict[str, float] = {
    "hunger": 15.0,
    "energy": 10.0,
    "social": 20.0,
    "fun": 15.0,
    "hygiene": 10.0,
    "comfort": 15.0,
}

# Mood label brackets (score → label)
MOOD_BRACKETS: list[tuple[float, str]] = [
    (80, "ecstatic"),
    (60, "happy"),
    (40, "fine"),
    (25, "sad"),
    (10, "miserable"),
    (0, "desperate"),
]


class NeedsDict(TypedDict):
    """Matches ``shared/types/character.ts → CharacterNeeds``."""

    hunger: float
    energy: float
    social: float
    fun: float
    hygiene: float
    comfort: float


@dataclass
class NeedsManager:
    """Manages the six core needs for a single character."""

    hunger: float = 80.0
    energy: float = 100.0
    social: float = 70.0
    fun: float = 60.0
    hygiene: float = 90.0
    comfort: float = 70.0

    def to_dict(self) -> NeedsDict:
        return NeedsDict(
            hunger=round(self.hunger, 1),
            energy=round(self.energy, 1),
            social=round(self.social, 1),
            fun=round(self.fun, 1),
            hygiene=round(self.hygiene, 1),
            comfort=round(self.comfort, 1),
        )

    # ------------------------------------------------------------------
    # Decay
    # ------------------------------------------------------------------

    def decay(
        self,
        minutes: int,
        personality: dict[str, float] | None = None,
        is_sleeping: bool = False,
    ) -> None:
        """Apply time-based decay (or recovery while sleeping).

        *personality* is a dict with Big-Five keys (0-1 scale) used to modify
        decay rates:
        - **extraversion** > 0.5 → social decays faster; < 0.5 → slower
        - **neuroticism** > 0.5 → comfort decays faster
        """
        hours = minutes / 60.0
        p = personality or {}

        for name in NEED_NAMES:
            rate = BASE_DECAY[name]

            # Sleeping: energy recovers instead of decaying
            if is_sleeping and name == "energy":
                rate = ENERGY_SLEEP_RATE

            # Personality modifiers
            if name == "social":
                ext = p.get("extraversion", 0.5)
                # extraversion 0→×0.33, 0.5→×1, 1→×2
                rate *= 0.33 + 1.33 * ext
            elif name == "comfort":
                neu = p.get("neuroticism", 0.5)
                rate *= 0.7 + 0.6 * neu  # 0→×0.7, 0.5→×1, 1→×1.3

            delta = rate * hours
            self._apply(name, delta)

    # ------------------------------------------------------------------
    # Activity effects
    # ------------------------------------------------------------------

    def apply_activity_effect(self, effects: dict[str, float]) -> None:
        """Apply an activity's need effects (e.g. ``{"hunger": 50, "fun": 10}``)."""
        for name, delta in effects.items():
            if name in NEED_NAMES:
                self._apply(name, delta)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_urgency_scores(self) -> dict[str, float]:
        """Return urgency per need: 0 (full) to 1 (empty/critical)."""
        return {name: 1.0 - (self._get(name) / 100.0) for name in NEED_NAMES}

    def is_critical(self, name: str) -> bool:
        return self._get(name) < CRITICAL.get(name, 15.0)

    def any_critical(self) -> str | None:
        """Return the most critical need name, or ``None``."""
        worst: str | None = None
        worst_val = 999.0
        for name in NEED_NAMES:
            val = self._get(name)
            if val < CRITICAL.get(name, 15.0) and val < worst_val:
                worst = name
                worst_val = val
        return worst

    def calculate_mood(self) -> tuple[float, str]:
        """Return ``(mood_score, mood_label)`` based on average needs."""
        avg = sum(self._get(n) for n in NEED_NAMES) / len(NEED_NAMES)
        label = "fine"
        for threshold, lbl in MOOD_BRACKETS:
            if avg >= threshold:
                label = lbl
                break
        return round(avg, 1), label

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, name: str) -> float:
        return float(getattr(self, name))

    def _apply(self, name: str, delta: float) -> None:
        current = self._get(name)
        setattr(self, name, max(0.0, min(100.0, current + delta)))
