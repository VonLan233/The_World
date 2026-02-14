"""Tier 1 — Claude API integration (~10 % of interactions).

Used for high-value moments (first meetings, relationship milestones).
Lazy-imports the ``anthropic`` SDK so the app doesn't crash if it's absent.
Includes a simple in-memory daily budget tracker.
"""

from __future__ import annotations

import logging
from datetime import date

from the_world.ai.personality import build_interaction_prompt, build_system_prompt
from the_world.ai.types import AIContext, AIResponse, AITier
from the_world.config import settings

logger = logging.getLogger("the_world.ai.claude")

# ---------------------------------------------------------------------------
# Budget tracking (in-memory, resets daily)
# ---------------------------------------------------------------------------
_daily_usage: dict[str, int] = {}
_usage_date: date | None = None

DAILY_BUDGET: int = settings.CLAUDE_DAILY_BUDGET


def _ensure_date() -> None:
    """Reset counters if the date has changed."""
    global _usage_date  # noqa: PLW0603
    today = date.today()
    if _usage_date != today:
        _daily_usage.clear()
        _usage_date = today


def check_budget(user_id: str) -> bool:
    _ensure_date()
    return _daily_usage.get(user_id, 0) < DAILY_BUDGET


def consume_budget(user_id: str) -> None:
    _ensure_date()
    _daily_usage[user_id] = _daily_usage.get(user_id, 0) + 1


def reset_daily_budgets() -> None:
    _daily_usage.clear()


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------

def is_claude_available() -> bool:
    """Return True if a Claude API key is configured and the SDK is installed."""
    if not settings.CLAUDE_API_KEY:
        return False
    try:
        import anthropic  # noqa: F401
        return True
    except ImportError:
        logger.debug("anthropic SDK not installed — Tier 1 unavailable")
        return False


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

async def generate_claude_response(ctx: AIContext, user_id: str) -> AIResponse:
    """Call the Claude API and return an ``AIResponse``.

    Raises on SDK / network errors so the router can degrade.
    """
    import anthropic  # lazy import

    system_prompt = build_system_prompt(
        name=ctx.character_name,
        personality=ctx.personality,
        mood=ctx.mood,
        activity=ctx.current_activity,
        location=ctx.current_location,
    )

    rel_context = f"score {ctx.relationship_score:.0f}" if ctx.relationship_score else ""
    user_prompt = build_interaction_prompt(
        name=ctx.character_name,
        target_name=ctx.target_name,
        interaction_type=ctx.interaction_type.value,
        relationship_context=rel_context,
        memories=ctx.memories,
    )

    client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    dialogue = message.content[0].text.strip()
    consume_budget(user_id)

    return AIResponse(
        dialogue=dialogue,
        tier_used=AITier.TIER1_CLAUDE,
        memory_worthy=True,
        importance=0.8,
        metadata={"model": "claude-sonnet-4-5-20250929"},
    )
