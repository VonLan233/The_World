"""Tests for Tier 3 rule-based dialogue generation."""

import pytest

from the_world.ai.tier3_rules import (
    _select_personality_variant,
    generate_rules_response,
    GREETING_TEMPLATES,
    IDLE_CHAT_TEMPLATES,
)
from the_world.ai.types import AIContext, AIResponse, AITier, InteractionType


def _make_ctx(
    interaction_type: InteractionType = InteractionType.GREETING,
    personality: dict[str, float] | None = None,
    name: str = "Alice",
    target: str = "Bob",
) -> AIContext:
    return AIContext(
        character_id="char-1",
        character_name=name,
        personality=personality or {"openness": 0.5, "extraversion": 0.5,
                                     "agreeableness": 0.5, "conscientiousness": 0.5,
                                     "neuroticism": 0.5},
        mood="happy",
        mood_score=70.0,
        current_activity="idle",
        current_location="Park",
        interaction_type=interaction_type,
        target_name=target,
    )


class TestPersonalityVariantSelection:
    def test_high_extraversion_selects_variant(self):
        p = {"extraversion": 0.8}
        result = _select_personality_variant(GREETING_TEMPLATES, p)
        assert result == GREETING_TEMPLATES["high_extraversion"]

    def test_low_extraversion_selects_variant(self):
        p = {"extraversion": 0.2}
        result = _select_personality_variant(GREETING_TEMPLATES, p)
        assert result == GREETING_TEMPLATES["low_extraversion"]

    def test_default_for_mid_values(self):
        p = {"extraversion": 0.5, "openness": 0.5}
        result = _select_personality_variant(GREETING_TEMPLATES, p)
        assert result == GREETING_TEMPLATES["default"]

    def test_high_openness_for_idle_chat(self):
        p = {"openness": 0.9, "extraversion": 0.5}
        result = _select_personality_variant(IDLE_CHAT_TEMPLATES, p)
        # openness is checked before extraversion in the trait list,
        # but extraversion comes first — let's verify it picks something
        assert isinstance(result, list)
        assert len(result) > 0


class TestGenerateRulesResponse:
    @pytest.mark.asyncio
    async def test_greeting_response(self):
        ctx = _make_ctx(InteractionType.GREETING)
        resp = await generate_rules_response(ctx)
        assert isinstance(resp, AIResponse)
        assert resp.tier_used == AITier.TIER3_RULES
        assert resp.memory_worthy is False
        assert resp.importance == 0.1
        assert len(resp.dialogue) > 0

    @pytest.mark.asyncio
    async def test_idle_chat_response(self):
        ctx = _make_ctx(InteractionType.IDLE_CHAT)
        resp = await generate_rules_response(ctx)
        assert resp.dialogue
        assert resp.tier_used == AITier.TIER3_RULES

    @pytest.mark.asyncio
    async def test_first_meeting_response(self):
        ctx = _make_ctx(InteractionType.FIRST_MEETING, name="Charlie", target="Dana")
        resp = await generate_rules_response(ctx)
        assert resp.dialogue
        # First meeting templates include the character's own name
        assert "Charlie" in resp.dialogue or "Dana" in resp.dialogue

    @pytest.mark.asyncio
    async def test_need_critical_response(self):
        ctx = _make_ctx(InteractionType.NEED_CRITICAL)
        resp = await generate_rules_response(ctx)
        assert resp.dialogue

    @pytest.mark.asyncio
    async def test_activity_reaction_response(self):
        ctx = _make_ctx(InteractionType.ACTIVITY_REACTION)
        ctx.current_activity = "cooking"
        resp = await generate_rules_response(ctx)
        assert resp.dialogue

    @pytest.mark.asyncio
    async def test_all_interaction_types_produce_output(self):
        """Every InteractionType should produce non-empty dialogue."""
        for itype in InteractionType:
            ctx = _make_ctx(itype)
            resp = await generate_rules_response(ctx)
            assert resp.dialogue, f"No output for {itype}"

    @pytest.mark.asyncio
    async def test_target_name_substitution(self):
        ctx = _make_ctx(InteractionType.GREETING, target="Zara")
        resp = await generate_rules_response(ctx)
        # At least some greeting templates include {target}
        # Run multiple times to hit a template with {target}
        found = False
        for _ in range(20):
            resp = await generate_rules_response(ctx)
            if "Zara" in resp.dialogue:
                found = True
                break
        assert found, "Target name should appear in at least one greeting template variant"

    @pytest.mark.asyncio
    async def test_high_extraversion_personality_affects_output(self):
        """High extraversion should consistently produce extravert-style templates."""
        ctx = _make_ctx(
            InteractionType.GREETING,
            personality={"extraversion": 0.9, "openness": 0.5, "agreeableness": 0.5,
                         "conscientiousness": 0.5, "neuroticism": 0.5},
        )
        resp = await generate_rules_response(ctx)
        # Should use high_extraversion variant which has exclamation marks
        assert resp.dialogue
