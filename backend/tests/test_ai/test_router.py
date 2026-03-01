"""Tests for the AI router (classification, resolution, generation)."""

from unittest.mock import AsyncMock, patch

import pytest

from the_world.ai.router import classify_interaction, generate_response, resolve_tier
from the_world.ai.types import AIContext, AIResponse, AITier, InteractionType


def _make_ctx(
    itype: InteractionType = InteractionType.DAILY_CONVERSATION,
) -> AIContext:
    return AIContext(
        character_id="char-1",
        character_name="Alice",
        personality={"openness": 0.5, "extraversion": 0.5, "agreeableness": 0.5,
                     "conscientiousness": 0.5, "neuroticism": 0.5},
        mood="neutral",
        mood_score=50.0,
        current_activity="idle",
        current_location="Park",
        interaction_type=itype,
        target_name="Bob",
    )


class TestClassifyInteraction:
    def test_first_meeting_count_zero(self):
        """interaction_count==0 should always route to Tier 1."""
        tier = classify_interaction(InteractionType.DAILY_CONVERSATION, 0, interaction_count=0)
        assert tier == AITier.TIER1_CLAUDE

    def test_first_meeting_type(self):
        tier = classify_interaction(InteractionType.FIRST_MEETING, 0, interaction_count=5)
        assert tier == AITier.TIER1_CLAUDE

    def test_relationship_milestone(self):
        tier = classify_interaction(InteractionType.RELATIONSHIP_MILESTONE, 50, interaction_count=10)
        assert tier == AITier.TIER1_CLAUDE

    def test_greeting_goes_to_tier3(self):
        tier = classify_interaction(InteractionType.GREETING, 30, interaction_count=5)
        assert tier == AITier.TIER3_RULES

    def test_idle_chat_goes_to_tier3(self):
        tier = classify_interaction(InteractionType.IDLE_CHAT, 10, interaction_count=3)
        assert tier == AITier.TIER3_RULES

    def test_background_npc_goes_to_tier3(self):
        tier = classify_interaction(InteractionType.BACKGROUND_NPC, 0, interaction_count=1)
        assert tier == AITier.TIER3_RULES

    def test_daily_conversation_goes_to_tier2(self):
        tier = classify_interaction(InteractionType.DAILY_CONVERSATION, 30, interaction_count=5)
        assert tier == AITier.TIER2_OLLAMA

    def test_activity_reaction_goes_to_tier2(self):
        tier = classify_interaction(InteractionType.ACTIVITY_REACTION, 10, interaction_count=2)
        assert tier == AITier.TIER2_OLLAMA

    def test_relationship_milestone_near_25_multiple(self):
        """Score near a multiple of 25 (e.g. 50.5) → Tier 1."""
        tier = classify_interaction(InteractionType.ACTIVITY_REACTION, 50.5, interaction_count=10)
        assert tier == AITier.TIER1_CLAUDE


class TestResolveTier:
    @pytest.mark.asyncio
    async def test_tier1_degrades_to_tier2_without_key(self):
        with patch("the_world.ai.router.is_claude_available", return_value=False):
            with patch("the_world.ai.router.check_ollama_available", AsyncMock(return_value=True)):
                result = await resolve_tier(AITier.TIER1_CLAUDE, "user-1")
                assert result == AITier.TIER2_OLLAMA

    @pytest.mark.asyncio
    async def test_tier1_degrades_to_tier3_without_both(self):
        with patch("the_world.ai.router.is_claude_available", return_value=False):
            with patch("the_world.ai.router.check_ollama_available", AsyncMock(return_value=False)):
                result = await resolve_tier(AITier.TIER1_CLAUDE, "user-1")
                assert result == AITier.TIER3_RULES

    @pytest.mark.asyncio
    async def test_tier2_degrades_to_tier3_when_unavailable(self):
        with patch("the_world.ai.router.check_ollama_available", AsyncMock(return_value=False)):
            result = await resolve_tier(AITier.TIER2_OLLAMA, "user-1")
            assert result == AITier.TIER3_RULES

    @pytest.mark.asyncio
    async def test_tier3_stays_tier3(self):
        result = await resolve_tier(AITier.TIER3_RULES, "user-1")
        assert result == AITier.TIER3_RULES

    @pytest.mark.asyncio
    async def test_tier1_stays_when_available(self):
        with patch("the_world.ai.router.is_claude_available", return_value=True):
            with patch("the_world.ai.router.check_budget", AsyncMock(return_value=True)):
                result = await resolve_tier(AITier.TIER1_CLAUDE, "user-1")
                assert result == AITier.TIER1_CLAUDE


class TestGenerateResponse:
    @pytest.mark.asyncio
    async def test_always_returns_response(self):
        """generate_response should never raise — always falls back to rules."""
        with patch("the_world.ai.router.is_claude_available", return_value=False):
            with patch("the_world.ai.router.check_ollama_available", AsyncMock(return_value=False)):
                ctx = _make_ctx(InteractionType.FIRST_MEETING)
                resp = await generate_response(ctx, interaction_count=0)
                assert isinstance(resp, AIResponse)
                assert resp.tier_used == AITier.TIER3_RULES
                assert len(resp.dialogue) > 0

    @pytest.mark.asyncio
    async def test_greeting_uses_rules_directly(self):
        """Greetings should go directly to Tier 3 without trying Ollama."""
        ctx = _make_ctx(InteractionType.GREETING)
        resp = await generate_response(ctx, interaction_count=5)
        assert resp.tier_used == AITier.TIER3_RULES

    @pytest.mark.asyncio
    async def test_tier2_failure_falls_back_to_rules(self):
        """If Ollama is 'available' but generate fails, should fallback to rules."""
        with patch("the_world.ai.router.is_claude_available", return_value=False):
            with patch("the_world.ai.router.check_ollama_available", AsyncMock(return_value=True)):
                with patch("the_world.ai.router.generate_ollama_response",
                           AsyncMock(side_effect=Exception("Ollama crashed"))):
                    ctx = _make_ctx(InteractionType.DAILY_CONVERSATION)
                    resp = await generate_response(ctx, interaction_count=5)
                    assert resp.tier_used == AITier.TIER3_RULES
