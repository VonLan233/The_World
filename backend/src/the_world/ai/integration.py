"""AI Integration layer — bridges the simulation engine with the AI subsystem.

Detects character encounters based on co-location, builds AI contexts,
generates dialogue, and persists memories.
"""

from __future__ import annotations

import logging
import time
import uuid
from itertools import combinations
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from the_world.ai.memory import MemoryManager
from the_world.ai.router import generate_response
from the_world.ai.types import AIContext, InteractionType
from the_world.config import settings
from the_world.services.relationship_service import RelationshipService
from the_world.simulation.engine import CharacterSim, SimulationEngine

logger = logging.getLogger("the_world.ai.integration")


# ---------------------------------------------------------------------------
# Encounter detection
# ---------------------------------------------------------------------------

def detect_encounters(
    engine: SimulationEngine,
) -> list[tuple[CharacterSim, CharacterSim]]:
    """Return pairs of characters at the same location."""
    by_location: dict[str, list[CharacterSim]] = {}
    for csim in engine.characters.values():
        by_location.setdefault(csim.current_location, []).append(csim)

    pairs: list[tuple[CharacterSim, CharacterSim]] = []
    for chars in by_location.values():
        if len(chars) >= 2:
            for a, b in combinations(chars, 2):
                pairs.append((a, b))
    return pairs


def build_ai_context(
    csim: CharacterSim,
    target: CharacterSim,
    interaction_type: InteractionType,
    memories: list[str],
    relationship_score: float,
    tick: int,
) -> AIContext:
    """Construct an ``AIContext`` from engine state."""
    mood_score, mood_label = csim.needs.calculate_mood()
    return AIContext(
        character_id=csim.id,
        character_name=csim.name,
        personality=csim.personality,
        mood=mood_label,
        mood_score=mood_score,
        current_activity=csim.current_activity,
        current_location=csim.current_location,
        interaction_type=interaction_type,
        target_name=target.name,
        target_personality=target.personality,
        relationship_score=relationship_score,
        memories=memories,
        sim_tick=tick,
    )


# ---------------------------------------------------------------------------
# Main integration class
# ---------------------------------------------------------------------------

class AIIntegration:
    """Manages the full encounter → dialogue → memory pipeline."""

    def __init__(
        self,
        engine: SimulationEngine,
        db_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.engine = engine
        self.db_factory = db_factory
        # Cooldown tracking: frozenset({id_a, id_b}) → last_tick
        self._cooldowns: dict[frozenset[str], int] = {}
        self._cooldown_ticks = settings.AI_INTERACTION_COOLDOWN

    def _is_on_cooldown(self, id_a: str, id_b: str, tick: int) -> bool:
        key = frozenset({id_a, id_b})
        last = self._cooldowns.get(key, -9999)
        return (tick - last) < self._cooldown_ticks

    def _set_cooldown(self, id_a: str, id_b: str, tick: int) -> None:
        self._cooldowns[frozenset({id_a, id_b})] = tick

    async def process_encounters(self, tick: int) -> list[dict[str, Any]]:
        """Full pipeline: detect → context → generate → store memory → evolve relationship → return events."""
        pairs = detect_encounters(self.engine)
        if not pairs:
            return []

        dialogue_events: list[dict[str, Any]] = []

        async with self.db_factory() as db:
            memory_mgr = MemoryManager(db)
            rel_svc = RelationshipService(db)

            for csim_a, csim_b in pairs:
                if self._is_on_cooldown(csim_a.id, csim_b.id, tick):
                    continue

                # Determine interaction count (first meeting?)
                interaction_count = await memory_mgr.get_interaction_count(
                    csim_a.id, csim_b.id
                )

                # Get real relationship score
                friendship_score = await rel_svc.get_friendship_score(
                    csim_a.id, csim_b.id
                )

                if interaction_count == 0:
                    itype = InteractionType.FIRST_MEETING
                else:
                    itype = InteractionType.DAILY_CONVERSATION

                # Retrieve relevant memories
                relevant = await memory_mgr.retrieve_relevant(
                    csim_a.id, tick, limit=3, target_character_id=csim_b.id
                )
                mem_texts = MemoryManager.format_memories_for_prompt(relevant)

                # Add recent interaction summaries as extra context
                rel = await rel_svc.get_relationship(csim_a.id, csim_b.id)
                if rel is not None:
                    summaries = rel_svc.get_recent_summaries(rel, limit=3)
                    for s in summaries:
                        mem_texts.append(f"[interaction] {s}")

                # Build context and generate
                ctx = build_ai_context(
                    csim_a, csim_b, itype, mem_texts,
                    relationship_score=friendship_score,
                    tick=tick,
                )
                response = await generate_response(ctx, interaction_count=interaction_count)

                # Store memory if worthy
                if response.memory_worthy:
                    await memory_mgr.create_memory(
                        character_id=csim_a.id,
                        memory_type="interaction",
                        content=f"Said to {csim_b.name}: {response.dialogue}",
                        sim_timestamp=tick,
                        importance=response.importance,
                        emotional_valence=response.emotional_valence,
                        context={"target_character_id": csim_b.id},
                    )

                # Evolve relationship after interaction
                interaction_quality = response.emotional_valence  # [-1, 1]
                _, milestones = await rel_svc.evolve_after_interaction(
                    csim_a.id,
                    csim_b.id,
                    interaction_quality,
                    csim_a.personality,
                    csim_b.personality,
                )

                # Record interaction summary
                summary_text = (
                    f"{csim_a.name} said to {csim_b.name}: "
                    f"{response.dialogue[:80]}"
                )
                await rel_svc.update_interaction_summary(
                    csim_a.id, csim_b.id, tick, summary_text
                )

                # Emit relationship_update events for milestones
                if milestones:
                    for ms in milestones:
                        for cb in self.engine._on_event:
                            try:
                                await cb({
                                    "type": "relationship_update",
                                    "characterId": csim_a.id,
                                    "characterName": csim_a.name,
                                    "description": (
                                        f"Relationship milestone with "
                                        f"{csim_b.name}: {ms}"
                                    ),
                                    "tick": tick,
                                    "data": {
                                        "targetId": csim_b.id,
                                        "targetName": csim_b.name,
                                        "milestone": ms,
                                        "friendshipScore": (
                                            await rel_svc.get_friendship_score(
                                                csim_a.id, csim_b.id
                                            )
                                        ),
                                    },
                                })
                            except Exception:
                                logger.exception("Error emitting relationship event")

                    # Override interaction type for milestone
                    itype = InteractionType.RELATIONSHIP_MILESTONE

                self._set_cooldown(csim_a.id, csim_b.id, tick)

                dialogue_events.append({
                    "id": str(uuid.uuid4()),
                    "speakerName": csim_a.name,
                    "speakerId": csim_a.id,
                    "targetName": csim_b.name,
                    "targetId": csim_b.id,
                    "dialogue": response.dialogue,
                    "tierUsed": response.tier_used.value,
                    "tick": tick,
                    "timestamp": time.time(),
                    "location": csim_a.current_location,
                })

            await db.commit()

        return dialogue_events
