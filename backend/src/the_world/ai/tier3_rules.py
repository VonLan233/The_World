"""Tier 3 — rule-based template engine (zero external dependencies).

Selects dialogue templates based on interaction type and dominant
personality traits.  Always available as the ultimate fallback.
"""

from __future__ import annotations

import random

from the_world.ai.types import AIContext, AIResponse, AITier, InteractionType

# ---------------------------------------------------------------------------
# Template banks organised by interaction type, then personality variant
# ---------------------------------------------------------------------------

GREETING_TEMPLATES: dict[str, list[str]] = {
    "high_extraversion": [
        "Hey {target}! Great to see you!",
        "Oh, {target}! What's up? I was just thinking about you!",
        "{target}! Come hang out with me!",
    ],
    "low_extraversion": [
        "Oh... hi, {target}.",
        "Hello, {target}.",
        "{target}. *nods quietly*",
    ],
    "high_agreeableness": [
        "Hi {target}, how are you doing today?",
        "Hey {target}! Hope you're having a lovely day!",
        "Good to see you, {target}. Need anything?",
    ],
    "default": [
        "Hey, {target}.",
        "Hi there, {target}.",
        "Oh, {target}. Hello.",
    ],
}

IDLE_CHAT_TEMPLATES: dict[str, list[str]] = {
    "high_openness": [
        "I've been thinking about something fascinating lately...",
        "Have you ever wondered what it would be like to live somewhere completely different?",
        "I read something interesting the other day, {target}.",
    ],
    "high_extraversion": [
        "So, {target}, tell me what's been going on with you!",
        "I'm so bored! Let's do something fun, {target}!",
        "Did you hear what happened? Let me tell you!",
    ],
    "low_extraversion": [
        "...",
        "It's nice and quiet here.",
        "I don't mind the silence, actually.",
    ],
    "default": [
        "Nice weather today, don't you think?",
        "How's everything going, {target}?",
        "Just taking it easy today.",
    ],
}

ACTIVITY_REACTION_TEMPLATES: dict[str, list[str]] = {
    "high_conscientiousness": [
        "I need to finish what I'm doing first.",
        "Let me wrap this up properly before we chat.",
        "I like to stay on schedule.",
    ],
    "low_conscientiousness": [
        "Eh, I can do this later. What's up?",
        "This is boring anyway. Let's talk!",
        "I wasn't really focused on this.",
    ],
    "default": [
        "Oh, hi! I was just {activity}.",
        "Hey {target}, I'm in the middle of {activity}.",
        "Just doing some {activity} here.",
    ],
}

NEED_CRITICAL_TEMPLATES: dict[str, list[str]] = {
    "high_neuroticism": [
        "I really don't feel great right now...",
        "Everything is overwhelming today.",
        "I can't keep going like this...",
    ],
    "low_neuroticism": [
        "I should probably take care of myself soon.",
        "I'm managing, but I could use a break.",
        "Nothing I can't handle, but some rest would be nice.",
    ],
    "default": [
        "I'm not feeling my best right now.",
        "I think I need to take care of something...",
        "Could be better, honestly.",
    ],
}

FIRST_MEETING_TEMPLATES: dict[str, list[str]] = {
    "high_extraversion": [
        "Oh, I don't think we've met! I'm {name}! So nice to meet you, {target}!",
        "A new face! Hi there, I'm {name}!",
        "Hey! You must be {target}! I've been wanting to meet new people!",
    ],
    "low_extraversion": [
        "Um... hi. I'm {name}. I don't think we've met before.",
        "Hello. I'm {name}. You're... {target}, right?",
        "I'm {name}. Nice to meet you.",
    ],
    "default": [
        "Hi, I'm {name}. Nice to meet you, {target}.",
        "Hey {target}, I don't think we've been introduced. I'm {name}.",
        "Hello! I'm {name}. Are you new around here?",
    ],
}

# Map interaction types to template banks
_TEMPLATE_MAP: dict[InteractionType, dict[str, list[str]]] = {
    InteractionType.GREETING: GREETING_TEMPLATES,
    InteractionType.IDLE_CHAT: IDLE_CHAT_TEMPLATES,
    InteractionType.ACTIVITY_REACTION: ACTIVITY_REACTION_TEMPLATES,
    InteractionType.NEED_CRITICAL: NEED_CRITICAL_TEMPLATES,
    InteractionType.FIRST_MEETING: FIRST_MEETING_TEMPLATES,
    InteractionType.DAILY_CONVERSATION: IDLE_CHAT_TEMPLATES,
    InteractionType.BACKGROUND_NPC: GREETING_TEMPLATES,
    InteractionType.RELATIONSHIP_MILESTONE: IDLE_CHAT_TEMPLATES,
    InteractionType.MAJOR_DECISION: IDLE_CHAT_TEMPLATES,
}

# Trait -> (high_key, low_key, threshold_high, threshold_low)
_TRAIT_KEYS: list[tuple[str, str, str, float, float]] = [
    ("extraversion", "high_extraversion", "low_extraversion", 0.65, 0.35),
    ("openness", "high_openness", "low_openness", 0.65, 0.35),
    ("agreeableness", "high_agreeableness", "low_agreeableness", 0.65, 0.35),
    ("conscientiousness", "high_conscientiousness", "low_conscientiousness", 0.65, 0.35),
    ("neuroticism", "high_neuroticism", "low_neuroticism", 0.65, 0.35),
]


def _select_personality_variant(
    templates: dict[str, list[str]],
    personality: dict[str, float],
) -> list[str]:
    """Pick the template list that best matches the character's dominant trait."""
    for trait, high_key, low_key, hi_thresh, lo_thresh in _TRAIT_KEYS:
        val = personality.get(trait, 0.5)
        if val >= hi_thresh and high_key in templates:
            return templates[high_key]
        if val <= lo_thresh and low_key in templates:
            return templates[low_key]
    return templates.get("default", ["..."])


async def generate_rules_response(ctx: AIContext) -> AIResponse:
    """Generate dialogue using personality-driven templates."""
    templates = _TEMPLATE_MAP.get(ctx.interaction_type, GREETING_TEMPLATES)
    variant = _select_personality_variant(templates, ctx.personality)
    template = random.choice(variant)

    dialogue = template.format(
        name=ctx.character_name,
        target=ctx.target_name or "friend",
        activity=ctx.current_activity,
    )

    return AIResponse(
        dialogue=dialogue,
        tier_used=AITier.TIER3_RULES,
        memory_worthy=False,
        importance=0.1,
    )
