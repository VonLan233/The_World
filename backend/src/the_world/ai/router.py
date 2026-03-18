"""AI Router — core orchestration layer.

Three-step pipeline:
1. classify_interaction  →  decide ideal tier
2. resolve_tier          →  degrade if provider unavailable
3. generate_response     →  call provider, fallback to rules on error
"""

from __future__ import annotations

import logging

from the_world.ai.tier1_claude import (
    check_budget,
    generate_claude_response,
    is_claude_available,
)
from the_world.ai.tier2_ollama import check_ollama_available, generate_ollama_response
from the_world.ai.tier3_rules import generate_rules_response
from the_world.ai.types import AIContext, AIResponse, AITier, InteractionType

logger = logging.getLogger("the_world.ai.router")


# ---------------------------------------------------------------------------
# 1. Classification
# ---------------------------------------------------------------------------

def classify_interaction(
    interaction_type: InteractionType,
    relationship_score: float = 0.0,
    interaction_count: int = 0,
) -> AITier:
    """Decide the ideal tier for this interaction."""

    # First meeting always → Tier 1
    if interaction_count == 0:
        return AITier.TIER1_CLAUDE

    # Explicitly high-value types → Tier 1
    if interaction_type in {
        InteractionType.FIRST_MEETING,
        InteractionType.RELATIONSHIP_MILESTONE,
        InteractionType.MAJOR_DECISION,
    }:
        return AITier.TIER1_CLAUDE

    # Simple / background interactions → Tier 3
    if interaction_type in {
        InteractionType.GREETING,
        InteractionType.IDLE_CHAT,
        InteractionType.BACKGROUND_NPC,
    }:
        return AITier.TIER3_RULES

    # Relationship milestones (score near multiples of 25) → Tier 1
    if relationship_score > 0 and (relationship_score % 25) <= 2:
        return AITier.TIER1_CLAUDE

    # Default → Tier 2 (Ollama)
    return AITier.TIER2_OLLAMA


# ---------------------------------------------------------------------------
# 2. Resolution (degrade chain)
# ---------------------------------------------------------------------------

async def resolve_tier(desired: AITier, user_id: str) -> AITier:
    """Walk the degradation chain: T1 → T2 → T3."""
    if desired == AITier.TIER1_CLAUDE:
        if is_claude_available() and await check_budget(user_id):
            return AITier.TIER1_CLAUDE
        # degrade to T2
        desired = AITier.TIER2_OLLAMA

    if desired == AITier.TIER2_OLLAMA:
        if await check_ollama_available():
            return AITier.TIER2_OLLAMA
        # degrade to T3

    return AITier.TIER3_RULES


# ---------------------------------------------------------------------------
# 3. Main entry point
# ---------------------------------------------------------------------------

async def generate_response(
    ctx: AIContext,
    user_id: str = "system",
    interaction_count: int = 0,
    world_ai_settings: dict | None = None,
) -> AIResponse:
    """Generate an AI response using the three-step pipeline.

    If *world_ai_settings* contains a configured text_provider, it is used
    in place of the server-wide tier system.

    Never raises — always falls back to the rules engine on error.
    """
    # -- Per-world AI override --
    if world_ai_settings:
        provider = world_ai_settings.get("text_provider")
        api_key = world_ai_settings.get("text_api_key", "")
        model = world_ai_settings.get("text_model")
        if provider and api_key:
            try:
                from the_world.ai.third_party import generate_text

                prompt = _build_dialogue_prompt(ctx)
                text = await generate_text(prompt, provider, api_key, model)
                return AIResponse(
                    dialogue=text,
                    tier_used=AITier.TIER1_CLAUDE,  # treat as tier-1 quality
                    memory_worthy=True,
                    importance=0.7,
                    emotional_valence=0.1,
                )
            except Exception:
                logger.exception(
                    "Third-party provider %r failed, falling back to standard tiers",
                    provider,
                )

    desired = classify_interaction(ctx.interaction_type, ctx.relationship_score, interaction_count)
    tier = await resolve_tier(desired, user_id)

    try:
        if tier == AITier.TIER1_CLAUDE:
            return await generate_claude_response(ctx, user_id)
        if tier == AITier.TIER2_OLLAMA:
            return await generate_ollama_response(ctx)
    except Exception:
        logger.exception("Tier %s failed, falling back to rules", tier.value)

    # Ultimate fallback — Tier 3 (never raises)
    return await generate_rules_response(ctx)


def _build_dialogue_prompt(ctx: AIContext) -> str:
    """Build a concise dialogue prompt from the AI context."""
    parts = []
    if ctx.world_lore:
        parts.append(f"World Setting:\n{ctx.world_lore[:1500]}\n")
    parts += [
        f"You are {ctx.character_name}, a character with the following traits: "
        f"openness={ctx.personality.get('openness', 0.5):.1f}, "
        f"extraversion={ctx.personality.get('extraversion', 0.5):.1f}, "
        f"agreeableness={ctx.personality.get('agreeableness', 0.5):.1f}.",
        f"Current mood: {ctx.mood}. Activity: {ctx.current_activity}. "
        f"Location: {ctx.current_location}.",
        f"You are speaking to {ctx.target_name}.",
    ]
    if ctx.memories:
        parts.append("Recent memories: " + "; ".join(ctx.memories[:3]))
    parts.append(
        "Write a single, in-character dialogue line (1-2 sentences). "
        "No narration, no quotation marks around the full response."
    )
    return "\n".join(parts)
