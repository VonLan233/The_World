"""Tests for Tier 1 Claude API integration (mocked SDK)."""

from unittest.mock import patch, MagicMock

import pytest

from the_world.ai.tier1_claude import (
    check_budget,
    consume_budget,
    generate_claude_response,
    is_claude_available,
    reset_daily_budgets,
)
from the_world.ai.types import AIContext, AITier, InteractionType


def _make_ctx() -> AIContext:
    return AIContext(
        character_id="char-1",
        character_name="Alice",
        personality={"openness": 0.7, "extraversion": 0.8, "agreeableness": 0.6,
                     "conscientiousness": 0.5, "neuroticism": 0.3},
        mood="excited",
        mood_score=85.0,
        current_activity="exploring",
        current_location="Park",
        interaction_type=InteractionType.FIRST_MEETING,
        target_name="Bob",
    )


class TestIsClaudeAvailable:
    def test_unavailable_without_key(self):
        with patch("the_world.ai.tier1_claude.settings") as mock_settings:
            mock_settings.CLAUDE_API_KEY = None
            assert is_claude_available() is False

    def test_unavailable_without_sdk(self):
        with patch("the_world.ai.tier1_claude.settings") as mock_settings:
            mock_settings.CLAUDE_API_KEY = "sk-test"
            with patch.dict("sys.modules", {"anthropic": None}):
                # When import fails
                with patch("builtins.__import__", side_effect=ImportError):
                    assert is_claude_available() is False

    def test_available_with_key_and_sdk(self):
        with patch("the_world.ai.tier1_claude.settings") as mock_settings:
            mock_settings.CLAUDE_API_KEY = "sk-test"
            mock_anthropic = MagicMock()
            with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
                assert is_claude_available() is True


class TestBudgetTracking:
    def setup_method(self):
        reset_daily_budgets()

    @pytest.mark.asyncio
    async def test_budget_starts_available(self):
        assert await check_budget("user-1") is True

    @pytest.mark.asyncio
    async def test_budget_exhausted_after_limit(self):
        with patch("the_world.ai.tier1_claude.DAILY_BUDGET", 3):
            for _ in range(3):
                await consume_budget("user-1")
            assert await check_budget("user-1") is False

    @pytest.mark.asyncio
    async def test_budget_per_user(self):
        with patch("the_world.ai.tier1_claude.DAILY_BUDGET", 2):
            await consume_budget("user-1")
            await consume_budget("user-1")
            assert await check_budget("user-1") is False
            assert await check_budget("user-2") is True

    @pytest.mark.asyncio
    async def test_reset_clears_budgets(self):
        await consume_budget("user-1")
        reset_daily_budgets()
        assert await check_budget("user-1") is True


class TestGenerateClaudeResponse:
    @pytest.mark.asyncio
    async def test_successful_response(self):
        reset_daily_budgets()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Hello Bob! I'm Alice, so wonderful to meet you!")]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        mock_anthropic = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        with patch("the_world.ai.tier1_claude.settings") as mock_settings:
            mock_settings.CLAUDE_API_KEY = "sk-test"
            mock_settings.CLAUDE_DAILY_BUDGET = 20
            with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
                ctx = _make_ctx()
                resp = await generate_claude_response(ctx, "user-1")

                assert resp.tier_used == AITier.TIER1_CLAUDE
                assert "Alice" in resp.dialogue
                assert resp.memory_worthy is True
                assert resp.importance == 0.8
