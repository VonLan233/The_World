"""Utility-based autonomous decision system for characters."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from the_world.simulation.activities import (
    IDLE,
    WALK_TO,
    Activity,
    activities_for_location,
)
from the_world.simulation.needs import NEED_NAMES, NeedsManager

if TYPE_CHECKING:
    pass


def choose_activity(
    needs: NeedsManager,
    personality: dict[str, float],
    location_type: str,
    available_locations: dict[str, str] | None = None,
) -> tuple[Activity, str | None]:
    """Pick the best activity for a character.

    Returns ``(activity, destination)`` where *destination* is ``None`` unless
    the chosen activity is ``walk_to`` (in which case it is the location name
    to move to).

    Parameters
    ----------
    needs:
        Current needs state.
    personality:
        Big-Five personality dict (keys like ``openness``, values 0-1).
    location_type:
        The ``location_type`` of the character's current location.
    available_locations:
        Mapping of ``location_name → location_type`` for all locations in
        the world.  Needed so we can figure out *where* to go when the
        character decides to relocate.
    """
    available_locations = available_locations or {}

    # ------------------------------------------------------------------
    # 1.  Emergency overrides
    # ------------------------------------------------------------------
    if needs.energy < 10:
        # Must sleep — go home if not there
        if location_type == "home":
            from the_world.simulation.activities import SLEEP
            return SLEEP, None
        return WALK_TO, _find_location("home", available_locations)

    if needs.hunger < 15:
        if location_type in ("home", "restaurant"):
            from the_world.simulation.activities import EAT
            return EAT, None
        dest = _find_location("restaurant", available_locations) or _find_location("home", available_locations)
        return WALK_TO, dest

    # ------------------------------------------------------------------
    # 2.  Score every available activity
    # ------------------------------------------------------------------
    candidates = activities_for_location(location_type)
    if not candidates:
        candidates = [IDLE]

    urgency = needs.get_urgency_scores()
    scored: list[tuple[float, Activity]] = []

    for act in candidates:
        score = _score_activity(act, urgency, personality)
        scored.append((score, act))

    # ------------------------------------------------------------------
    # 3.  Check if relocating would be much better
    # ------------------------------------------------------------------
    best_local = max(scored, key=lambda t: t[0])

    # Evaluate best activity across *all* locations
    best_remote_score = 0.0
    best_remote_dest: str | None = None
    for loc_name, loc_type in available_locations.items():
        if loc_type == location_type:
            continue  # already scored locally
        for act in activities_for_location(loc_type):
            s = _score_activity(act, urgency, personality)
            if s > best_remote_score:
                best_remote_score = s
                best_remote_dest = loc_name

    # Only walk if remote option is meaningfully better
    if best_remote_dest and best_remote_score > best_local[0] + 0.15:
        return WALK_TO, best_remote_dest

    return best_local[1], None


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

_URGENCY_WEIGHT = 0.50
_PERSONALITY_WEIGHT = 0.30
_RANDOM_WEIGHT = 0.20


def _score_activity(
    activity: Activity,
    urgency: dict[str, float],
    personality: dict[str, float],
) -> float:
    """Compute a utility score for *activity* given current urgency & personality."""
    # --- Urgency component (how much does this activity help urgent needs?) ---
    urgency_score = 0.0
    if activity.need_effects:
        for need_name, delta in activity.need_effects.items():
            if need_name in urgency and delta > 0:
                urgency_score += urgency[need_name] * (delta / 100.0)
    # Normalise to [0, 1] range (roughly)
    urgency_score = min(urgency_score, 1.0)

    # --- Personality affinity component ---
    personality_score = 0.0
    if activity.personality_affinity:
        total = 0.0
        for trait, weight in activity.personality_affinity.items():
            trait_val = personality.get(trait, 0.5)
            total += trait_val * weight
        personality_score = total / max(len(activity.personality_affinity), 1)
    personality_score = min(personality_score, 1.0)

    # --- Random factor ---
    random_score = random.random()

    return (
        _URGENCY_WEIGHT * urgency_score
        + _PERSONALITY_WEIGHT * personality_score
        + _RANDOM_WEIGHT * random_score
    )


def _find_location(
    location_type: str,
    available_locations: dict[str, str],
) -> str | None:
    """Find the first location name with the given type."""
    for name, ltype in available_locations.items():
        if ltype == location_type:
            return name
    return None
