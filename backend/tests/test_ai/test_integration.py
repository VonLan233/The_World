"""Tests for the AI integration layer (encounter detection, cooldown, pipeline)."""

import uuid
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from the_world.ai.integration import AIIntegration, build_ai_context, detect_encounters
from the_world.ai.types import AIResponse, AITier, InteractionType
from the_world.simulation.engine import CharacterSim, SimulationEngine

# Stable UUIDs for tests
UUID_A = str(uuid.uuid5(uuid.NAMESPACE_DNS, "alice"))
UUID_B = str(uuid.uuid5(uuid.NAMESPACE_DNS, "bob"))
UUID_C = str(uuid.uuid5(uuid.NAMESPACE_DNS, "carol"))


def _make_engine_with_chars() -> SimulationEngine:
    """Create a minimal engine with characters at specified locations."""
    engine = SimulationEngine("test-world")
    return engine


def _make_char(char_id: str, name: str, location: str) -> CharacterSim:
    return CharacterSim(
        id=char_id,
        name=name,
        personality={"openness": 0.5, "extraversion": 0.5, "agreeableness": 0.5,
                     "conscientiousness": 0.5, "neuroticism": 0.5},
        current_location=location,
    )


class TestDetectEncounters:
    def test_same_location_produces_pair(self):
        engine = _make_engine_with_chars()
        engine.characters[UUID_A] = _make_char(UUID_A, "Alice", "Park")
        engine.characters[UUID_B] = _make_char(UUID_B, "Bob", "Park")

        pairs = detect_encounters(engine)
        assert len(pairs) == 1
        ids = {pairs[0][0].id, pairs[0][1].id}
        assert ids == {UUID_A, UUID_B}

    def test_different_locations_no_pair(self):
        engine = _make_engine_with_chars()
        engine.characters[UUID_A] = _make_char(UUID_A, "Alice", "Park")
        engine.characters[UUID_B] = _make_char(UUID_B, "Bob", "Home")

        pairs = detect_encounters(engine)
        assert len(pairs) == 0

    def test_three_at_same_location_produces_three_pairs(self):
        engine = _make_engine_with_chars()
        engine.characters[UUID_A] = _make_char(UUID_A, "Alice", "Cafe")
        engine.characters[UUID_B] = _make_char(UUID_B, "Bob", "Cafe")
        engine.characters[UUID_C] = _make_char(UUID_C, "Carol", "Cafe")

        pairs = detect_encounters(engine)
        assert len(pairs) == 3  # C(3,2) = 3

    def test_empty_engine(self):
        engine = _make_engine_with_chars()
        pairs = detect_encounters(engine)
        assert pairs == []

    def test_single_character(self):
        engine = _make_engine_with_chars()
        engine.characters[UUID_A] = _make_char(UUID_A, "Alice", "Park")
        pairs = detect_encounters(engine)
        assert pairs == []


class TestBuildAIContext:
    def test_builds_correct_context(self):
        a = _make_char(UUID_A, "Alice", "Park")
        b = _make_char(UUID_B, "Bob", "Park")

        ctx = build_ai_context(a, b, InteractionType.GREETING, ["memory1"], 25.0, 100)
        assert ctx.character_name == "Alice"
        assert ctx.target_name == "Bob"
        assert ctx.interaction_type == InteractionType.GREETING
        assert ctx.memories == ["memory1"]
        assert ctx.relationship_score == 25.0
        assert ctx.sim_tick == 100


class TestAIIntegrationCooldown:
    def test_cooldown_prevents_repeat(self):
        engine = _make_engine_with_chars()
        mock_factory = MagicMock()
        ai = AIIntegration(engine, mock_factory)
        ai._cooldown_ticks = 60

        # Not on cooldown initially
        assert ai._is_on_cooldown(UUID_A, UUID_B, 100) is False

        # Set cooldown
        ai._set_cooldown(UUID_A, UUID_B, 100)

        # Should be on cooldown within window
        assert ai._is_on_cooldown(UUID_A, UUID_B, 110) is True

        # Should be off cooldown after window
        assert ai._is_on_cooldown(UUID_A, UUID_B, 161) is False

    def test_cooldown_is_bidirectional(self):
        engine = _make_engine_with_chars()
        mock_factory = MagicMock()
        ai = AIIntegration(engine, mock_factory)

        ai._set_cooldown(UUID_A, UUID_B, 100)
        # a->b and b->a should both be on cooldown
        assert ai._is_on_cooldown(UUID_B, UUID_A, 110) is True


class TestAIIntegrationPipeline:
    @pytest.mark.asyncio
    async def test_process_encounters_empty(self):
        engine = _make_engine_with_chars()
        mock_factory = MagicMock()
        ai = AIIntegration(engine, mock_factory)

        # No characters → no events
        events = await ai.process_encounters(100)
        assert events == []

    @pytest.mark.asyncio
    async def test_process_encounters_with_mock(self):
        engine = _make_engine_with_chars()
        engine.characters[UUID_A] = _make_char(UUID_A, "Alice", "Park")
        engine.characters[UUID_B] = _make_char(UUID_B, "Bob", "Park")

        # Mock the DB session factory
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        # execute() returns a result that handles both .scalars().all() and .scalar_one_or_none()
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        mock_factory = MagicMock(return_value=mock_session)

        ai = AIIntegration(engine, mock_factory)

        # Mock generate_response to return a rules response
        mock_response = AIResponse(
            dialogue="Hi Bob!",
            tier_used=AITier.TIER3_RULES,
            memory_worthy=False,
            importance=0.1,
        )

        # Mock RelationshipService to avoid DB operations
        with patch("the_world.ai.integration.generate_response", AsyncMock(return_value=mock_response)), \
             patch("the_world.ai.integration.RelationshipService") as MockRelSvc:
            mock_rel_instance = MagicMock()
            mock_rel_instance.get_friendship_score = AsyncMock(return_value=0.0)
            mock_rel_instance.get_relationship = AsyncMock(return_value=None)
            mock_rel_instance.evolve_after_interaction = AsyncMock(return_value=(MagicMock(), []))
            mock_rel_instance.update_interaction_summary = AsyncMock()
            MockRelSvc.return_value = mock_rel_instance

            events = await ai.process_encounters(100)
            assert len(events) == 1
            assert events[0]["speakerName"] == "Alice"
            assert events[0]["targetName"] == "Bob"
            assert events[0]["dialogue"] == "Hi Bob!"
            assert events[0]["tierUsed"] == "tier3_rules"

            # Verify relationship service was used
            mock_rel_instance.get_friendship_score.assert_called_once()
            mock_rel_instance.evolve_after_interaction.assert_called_once()
