"""Tests for Tier 2 Ollama integration (mocked httpx)."""

from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from the_world.ai.tier2_ollama import check_ollama_available, generate_ollama_response
from the_world.ai.types import AIContext, AIResponse, AITier, InteractionType


def _make_ctx() -> AIContext:
    return AIContext(
        character_id="char-1",
        character_name="Alice",
        personality={"openness": 0.6, "extraversion": 0.7, "agreeableness": 0.5,
                     "conscientiousness": 0.5, "neuroticism": 0.4},
        mood="happy",
        mood_score=75.0,
        current_activity="walking",
        current_location="Park",
        interaction_type=InteractionType.DAILY_CONVERSATION,
        target_name="Bob",
    )


class TestCheckOllamaAvailable:
    @pytest.mark.asyncio
    async def test_available_when_server_responds(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("the_world.ai.tier2_ollama._get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_get.return_value = mock_client

            result = await check_ollama_available()
            assert result is True

    @pytest.mark.asyncio
    async def test_unavailable_on_connection_error(self):
        import httpx

        with patch("the_world.ai.tier2_ollama._get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
            mock_get.return_value = mock_client

            result = await check_ollama_available()
            assert result is False

    @pytest.mark.asyncio
    async def test_unavailable_on_timeout(self):
        import httpx

        with patch("the_world.ai.tier2_ollama._get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_get.return_value = mock_client

            result = await check_ollama_available()
            assert result is False


class TestGenerateOllamaResponse:
    @pytest.mark.asyncio
    async def test_successful_response(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "Hey Bob! Nice to see you here!"}
        mock_resp.raise_for_status = MagicMock()

        with patch("the_world.ai.tier2_ollama._get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_get.return_value = mock_client

            ctx = _make_ctx()
            resp = await generate_ollama_response(ctx)

            assert isinstance(resp, AIResponse)
            assert resp.tier_used == AITier.TIER2_OLLAMA
            assert resp.dialogue == "Hey Bob! Nice to see you here!"
            assert resp.memory_worthy is True
            assert resp.importance == 0.4

    @pytest.mark.asyncio
    async def test_empty_response_raises(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": ""}
        mock_resp.raise_for_status = MagicMock()

        with patch("the_world.ai.tier2_ollama._get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_get.return_value = mock_client

            ctx = _make_ctx()
            with pytest.raises(ValueError, match="Empty response"):
                await generate_ollama_response(ctx)

    @pytest.mark.asyncio
    async def test_connection_error_propagates(self):
        import httpx

        with patch("the_world.ai.tier2_ollama._get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
            mock_get.return_value = mock_client

            ctx = _make_ctx()
            with pytest.raises(httpx.ConnectError):
                await generate_ollama_response(ctx)
