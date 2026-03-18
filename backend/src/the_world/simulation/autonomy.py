"""Utility-based autonomous decision system for characters."""

from __future__ import annotations

import random

from the_world.simulation.activities import (
    IDLE,
    WALK_TO,
    Activity,
    activities_for_location,
)
from the_world.simulation.needs import NeedsManager


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


# Keyword sets used to match daily goals to activities (Phase 2)
_ACTIVITY_KEYWORDS: dict[str, list[str]] = {
    "eat": ["eat", "food", "lunch", "dinner", "breakfast", "café", "cafe", "restaurant", "cook"],
    "sleep": ["sleep", "rest", "bed"],
    "nap": ["nap", "rest", "sleep"],
    "read": ["read", "book", "library"],
    "exercise": ["exercise", "gym", "workout", "fitness", "train", "run"],
    "chat": ["chat", "talk", "friend", "social", "visit", "hang", "convers"],
    "hangout": ["hang", "friend", "social", "visit", "spend time"],
    "deep_talk": ["deep", "talk", "discuss", "catch up", "friend"],
    "group_hangout": ["hang", "group", "together", "party"],
    "work": ["work", "task", "job", "productive"],
    "study": ["study", "learn", "library", "read"],
    "meditate": ["meditat", "relax", "calm", "peace", "mindful"],
    "garden": ["garden", "outside", "park", "nature", "plant"],
    "play_games": ["game", "play", "fun", "entertain"],
    "watch_tv": ["tv", "watch", "relax", "entertain"],
    "cook": ["cook", "meal", "food", "lunch", "dinner"],
}


def _score_plan_alignment(activity: Activity, daily_goals: list[str]) -> float:
    """Return a [0, 1] score for how well *activity* matches the day's goals.

    Uses keyword matching between the activity name and each goal string.
    A score of 1.0 means every goal mentions this activity.
    """
    keywords = _ACTIVITY_KEYWORDS.get(
        activity.name,
        [activity.name.replace("_", " ")],
    )
    matches = 0
    for goal in daily_goals:
        goal_lower = goal.lower()
        for kw in keywords:
            if kw in goal_lower:
                matches += 1
                break

    return min(matches / max(len(daily_goals), 1), 1.0)


# ---------------------------------------------------------------------------
# Main decision function
# ---------------------------------------------------------------------------

def choose_activity(
    needs: NeedsManager,
    personality: dict[str, float],
    location_type: str,
    available_locations: dict[str, str] | None = None,
    nearby_characters: list[dict] | None = None,
    daily_goals: list[str] | None = None,
    nearby_friendship_scores: list[float] | None = None,
    close_friends_elsewhere: dict[str, str] | None = None,
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
    nearby_characters:
        List of dicts with ``id`` and ``name`` for characters at the same
        location.  When present, social activities get a scoring boost.
    daily_goals:
        List of today's intention strings from the planner.  Activities that
        match a goal keyword receive a +20 % score boost (Phase 2).
    nearby_friendship_scores:
        Friendship scores (−100 to 100) for nearby characters.  Scales the
        social activity boost from 0.15 (stranger) to 0.40 (score 100; Phase 3).
    close_friends_elsewhere:
        Phase 3 — maps ``character_id → location_name`` for close friends
        (friendship > 75) that are NOT at the same location.  When present,
        the character is more likely to walk toward a close friend.
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
    has_nearby = bool(nearby_characters)

    # Pre-compute relationship-aware social boost (Phase 3)
    social_boost = 0.15  # baseline when other characters are present
    if nearby_friendship_scores:
        max_score = max(nearby_friendship_scores)
        # Scale from 0.15 (stranger/score 0) to 0.40 (close friend/score 100)
        social_boost = 0.15 + max(0.0, max_score) / 100.0 * 0.25

    scored: list[tuple[float, Activity]] = []

    for act in candidates:
        score = _score_activity(act, urgency, personality)

        # Plan alignment boost (Phase 2)
        if daily_goals:
            alignment = _score_plan_alignment(act, daily_goals)
            score += alignment * 0.20

        # Relationship-aware social boost (Phase 3)
        if has_nearby and "social" in act.need_effects and act.need_effects["social"] > 0:
            score += social_boost

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

    # Phase 3: boost walk-to score toward locations with close friends
    if close_friends_elsewhere:
        for _friend_id, friend_loc in close_friends_elsewhere.items():
            if friend_loc in available_locations:
                # Give a strong social pull toward that location
                friend_pull = 0.35
                if friend_pull > best_remote_score:
                    best_remote_score = friend_pull
                    best_remote_dest = friend_loc

    # Only walk if remote option is meaningfully better
    if best_remote_dest and best_remote_score > best_local[0] + 0.15:
        return WALK_TO, best_remote_dest

    return best_local[1], None
