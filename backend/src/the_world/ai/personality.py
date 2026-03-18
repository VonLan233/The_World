"""Personality-to-prompt utilities.

Maps Big Five trait values (0-1) to natural-language behaviour descriptions
and assembles system / interaction prompts consumed by Tier 1 & 2.
"""

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# BehaviorProfile
# ---------------------------------------------------------------------------

@dataclass
class BehaviorProfile:
    """Human-readable behaviour derived from Big Five scores."""

    speech_style: str
    social_tendency: str
    emotional_range: str
    decision_style: str
    curiosity_level: str


def personality_to_behavior(personality: dict[str, float]) -> BehaviorProfile:
    """Convert 0-1 Big Five values into descriptive strings."""
    o = personality.get("openness", 0.5)
    c = personality.get("conscientiousness", 0.5)
    e = personality.get("extraversion", 0.5)
    a = personality.get("agreeableness", 0.5)
    n = personality.get("neuroticism", 0.5)

    # Speech style (extraversion + openness)
    if e > 0.65 and o > 0.65:
        speech = "enthusiastic and imaginative, uses vivid language"
    elif e > 0.65:
        speech = "talkative and expressive, enjoys conversation"
    elif e < 0.35:
        speech = "quiet and reserved, speaks only when necessary"
    else:
        speech = "balanced and thoughtful in conversation"

    # Social tendency (extraversion + agreeableness)
    if e > 0.65 and a > 0.65:
        social = "outgoing and warm, seeks connection"
    elif e < 0.35 and a < 0.35:
        social = "solitary and independent, prefers being alone"
    elif a > 0.65:
        social = "kind and accommodating, avoids conflict"
    elif a < 0.35:
        social = "blunt and competitive, speaks their mind"
    else:
        social = "sociable but selective with close bonds"

    # Emotional range (neuroticism)
    if n > 0.65:
        emotion = "emotionally intense, easily stressed or excited"
    elif n < 0.35:
        emotion = "calm and emotionally stable"
    else:
        emotion = "moderately emotional, generally steady"

    # Decision style (conscientiousness)
    if c > 0.65:
        decision = "methodical and disciplined, plans ahead"
    elif c < 0.35:
        decision = "spontaneous and flexible, goes with the flow"
    else:
        decision = "balanced between planning and improvising"

    # Curiosity (openness)
    if o > 0.65:
        curiosity = "highly curious, loves exploring new ideas"
    elif o < 0.35:
        curiosity = "practical and traditional, prefers the familiar"
    else:
        curiosity = "open to new things but grounded"

    return BehaviorProfile(
        speech_style=speech,
        social_tendency=social,
        emotional_range=emotion,
        decision_style=decision,
        curiosity_level=curiosity,
    )


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def build_system_prompt(
    name: str,
    personality: dict[str, float],
    mood: str,
    activity: str,
    location: str,
    world_lore: str = "",
) -> str:
    """Generate a character-specific LLM system prompt."""
    bp = personality_to_behavior(personality)
    prompt = (
        f"You are {name}, a character in a life-simulation world.\n"
        f"Personality: {bp.speech_style}; {bp.social_tendency}; "
        f"{bp.emotional_range}; {bp.decision_style}; {bp.curiosity_level}.\n"
        f"Current mood: {mood}. Currently doing: {activity}. Location: {location}.\n"
        "Stay in character. Respond with a single short line of dialogue (1-2 sentences). "
        "Do NOT include action descriptions or quotation marks."
    )
    if world_lore:
        prompt += f"\n\nWorld Setting:\n{world_lore[:1500]}"
    return prompt


def build_interaction_prompt(
    name: str,
    target_name: str,
    interaction_type: str,
    relationship_context: str,
    memories: list[str],
) -> str:
    """Generate the user-side prompt describing the interaction."""
    parts = [f"{name} encounters {target_name}."]
    parts.append(f"Interaction type: {interaction_type}.")

    if relationship_context:
        parts.append(f"Relationship: {relationship_context}.")

    if memories:
        parts.append("Relevant memories:")
        for m in memories:
            parts.append(f"- {m}")

    parts.append(f"What does {name} say to {target_name}?")
    return "\n".join(parts)
