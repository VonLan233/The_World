"""Tests for personality → behaviour profile mapping and prompt generation."""

import pytest

from the_world.ai.personality import (
    BehaviorProfile,
    build_interaction_prompt,
    build_system_prompt,
    personality_to_behavior,
)


class TestPersonalityToBehavior:
    """Verify Big Five → BehaviorProfile mapping."""

    def test_high_extraversion_high_openness(self):
        p = {"openness": 0.8, "conscientiousness": 0.5, "extraversion": 0.8,
             "agreeableness": 0.5, "neuroticism": 0.5}
        bp = personality_to_behavior(p)
        assert isinstance(bp, BehaviorProfile)
        assert "enthusiastic" in bp.speech_style

    def test_low_extraversion(self):
        p = {"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.2,
             "agreeableness": 0.5, "neuroticism": 0.5}
        bp = personality_to_behavior(p)
        assert "quiet" in bp.speech_style or "reserved" in bp.speech_style

    def test_high_neuroticism(self):
        p = {"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5,
             "agreeableness": 0.5, "neuroticism": 0.9}
        bp = personality_to_behavior(p)
        assert "intense" in bp.emotional_range or "stressed" in bp.emotional_range

    def test_low_neuroticism(self):
        p = {"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5,
             "agreeableness": 0.5, "neuroticism": 0.1}
        bp = personality_to_behavior(p)
        assert "calm" in bp.emotional_range or "stable" in bp.emotional_range

    def test_high_conscientiousness(self):
        p = {"openness": 0.5, "conscientiousness": 0.9, "extraversion": 0.5,
             "agreeableness": 0.5, "neuroticism": 0.5}
        bp = personality_to_behavior(p)
        assert "methodical" in bp.decision_style or "disciplin" in bp.decision_style

    def test_default_values(self):
        """All-0.5 personality should give 'balanced' descriptions."""
        p = {"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5,
             "agreeableness": 0.5, "neuroticism": 0.5}
        bp = personality_to_behavior(p)
        assert bp.speech_style  # non-empty
        assert bp.social_tendency
        assert bp.emotional_range
        assert bp.decision_style
        assert bp.curiosity_level

    def test_missing_keys_uses_defaults(self):
        bp = personality_to_behavior({})
        assert bp.speech_style  # should not crash


class TestBuildSystemPrompt:
    def test_contains_character_name(self):
        prompt = build_system_prompt(
            "Alice", {"openness": 0.5, "extraversion": 0.5}, "happy", "eating", "Cafe"
        )
        assert "Alice" in prompt

    def test_contains_mood_and_location(self):
        prompt = build_system_prompt(
            "Bob", {"neuroticism": 0.8}, "stressed", "working", "Office"
        )
        assert "stressed" in prompt
        assert "Office" in prompt


class TestBuildInteractionPrompt:
    def test_basic_structure(self):
        prompt = build_interaction_prompt(
            "Alice", "Bob", "daily_conversation", "friends", ["Met yesterday"]
        )
        assert "Alice" in prompt
        assert "Bob" in prompt
        assert "Met yesterday" in prompt

    def test_empty_memories(self):
        prompt = build_interaction_prompt("A", "B", "greeting", "", [])
        assert "A encounters B" in prompt

    def test_relationship_context_included(self):
        prompt = build_interaction_prompt("A", "B", "greeting", "best friends", [])
        assert "best friends" in prompt
