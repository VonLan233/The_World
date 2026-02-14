"""Tier 2 — Ollama local LLM integration (~80 % of interactions).

Uses httpx with ``trust_env=False`` to avoid proxy issues on this system.
Raises on connection failure so the router can gracefully degrade to Tier 3.
"""

from __future__ import annotations

import logging

import httpx

from the_world.ai.personality import build_interaction_prompt, build_system_prompt
from the_world.ai.types import AIContext, AIResponse, AITier
from the_world.config import settings

logger = logging.getLogger("the_world.ai.ollama")

# ---------------------------------------------------------------------------
# Module-level httpx client (singleton)
# ---------------------------------------------------------------------------
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client  # noqa: PLW0603
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(trust_env=False, timeout=30.0)
    return _client


async def close_client() -> None:
    """Close the httpx client (call on app shutdown)."""
    global _client  # noqa: PLW0603
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

async def check_ollama_available() -> bool:
    """Return True if the Ollama server is reachable."""
    try:
        resp = await _get_client().get(f"{settings.OLLAMA_URL}/api/tags")
        return resp.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException, OSError):
        return False


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

async def generate_ollama_response(ctx: AIContext) -> AIResponse:
    """Call Ollama ``/api/generate`` and return an ``AIResponse``.

    Raises ``httpx.ConnectError`` / ``httpx.TimeoutException`` on failure
    so the router can fall back to Tier 3.
    """
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

    payload = {
        "model": settings.OLLAMA_MODEL,
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False,
        "options": {
            "num_predict": 150,
            "temperature": 0.8,
        },
    }

    resp = await _get_client().post(
        f"{settings.OLLAMA_URL}/api/generate",
        json=payload,
    )
    resp.raise_for_status()
    data = resp.json()
    dialogue = data.get("response", "").strip()

    if not dialogue:
        raise ValueError("Empty response from Ollama")

    return AIResponse(
        dialogue=dialogue,
        tier_used=AITier.TIER2_OLLAMA,
        memory_worthy=True,
        importance=0.4,
    )
