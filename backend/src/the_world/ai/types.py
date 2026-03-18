"""Shared data structures for the AI subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AITier(str, Enum):
    """Which AI backend handles a given interaction."""

    TIER1_CLAUDE = "tier1_claude"
    TIER2_OLLAMA = "tier2_ollama"
    TIER3_RULES = "tier3_rules"


class InteractionType(str, Enum):
    """Categories of character interactions used for tier classification."""

    FIRST_MEETING = "first_meeting"
    DAILY_CONVERSATION = "daily_conversation"
    GREETING = "greeting"
    IDLE_CHAT = "idle_chat"
    ACTIVITY_REACTION = "activity_reaction"
    NEED_CRITICAL = "need_critical"
    RELATIONSHIP_MILESTONE = "relationship_milestone"
    MAJOR_DECISION = "major_decision"
    BACKGROUND_NPC = "background_npc"


@dataclass
class AIContext:
    """Aggregated context passed to every AI tier."""

    character_id: str
    character_name: str
    personality: dict[str, float]
    mood: str
    mood_score: float
    current_activity: str
    current_location: str
    interaction_type: InteractionType
    target_name: str = ""
    target_personality: dict[str, float] = field(default_factory=dict)
    relationship_score: float = 0.0
    memories: list[str] = field(default_factory=list)
    sim_tick: int = 0
    world_lore: str = ""


@dataclass
class AIResponse:
    """Unified return format from any AI tier."""

    dialogue: str
    tier_used: AITier
    memory_worthy: bool = False
    importance: float = 0.1
    emotional_valence: float = 0.0
    metadata: dict[str, object] = field(default_factory=dict)
