"""AI Integration layer — bridges the simulation engine with the AI subsystem.

Detects character encounters based on co-location, builds AI contexts,
generates dialogue, and persists memories.

Cognitive layer additions (Phases 1-3):
  - Phase 1: Memory reflection triggered when accumulated importance ≥ threshold.
  - Phase 2: Daily planning triggered at the start of each new game-day.
  - Phase 3: Relationship cache kept on CharacterSim for use by autonomy.py.
"""

from __future__ import annotations

import logging
import time
import uuid
from itertools import combinations
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from the_world.ai.memory import MemoryManager
from the_world.ai.planner import PlanManager
from the_world.ai.router import generate_response
from the_world.ai.types import AIContext, InteractionType
from the_world.config import settings
from the_world.services.relationship_service import RelationshipService
from the_world.simulation.engine import CharacterSim, SimulationEngine

logger = logging.getLogger("the_world.ai.integration")

# How often (in ticks) to check whether reflection should fire per character.
_REFLECTION_CHECK_INTERVAL = 300  # ~5 game-hours


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
    world_lore: str = "",
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
        world_lore=world_lore,
    )


# ---------------------------------------------------------------------------
# Main integration class
# ---------------------------------------------------------------------------

class AIIntegration:
    """Manages the full encounter → dialogue → memory → planning pipeline."""

    def __init__(
        self,
        engine: SimulationEngine,
        db_factory: async_sessionmaker[AsyncSession],
        world_ai_settings: dict | None = None,
        world_lore: str = "",
    ) -> None:
        self.engine = engine
        self.db_factory = db_factory
        self.world_ai_settings = world_ai_settings or {}
        self.world_lore = world_lore
        # Cooldown tracking: frozenset({id_a, id_b}) → last_tick
        self._cooldowns: dict[frozenset[str], int] = {}
        self._cooldown_ticks = settings.AI_INTERACTION_COOLDOWN

        # Phase 1 — reflection: track last reflection tick per character
        self._last_reflection_tick: dict[str, int] = {}

        # Phase 2 — planning: track which game-day was last planned
        self._last_plan_day: int = -1

    def _is_on_cooldown(
        self, id_a: str, id_b: str, tick: int, friendship_score: float = 0.0,
    ) -> bool:
        key = frozenset({id_a, id_b})
        last = self._cooldowns.get(key, -9999)
        cooldown = self._cooldown_ticks
        # Phase 3: high-friendship pairs chat more often
        if friendship_score > 75:
            cooldown = cooldown // 2
        return (tick - last) < cooldown

    def _set_cooldown(self, id_a: str, id_b: str, tick: int) -> None:
        self._cooldowns[frozenset({id_a, id_b})] = tick

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def process_encounters(self, tick: int) -> list[dict[str, Any]]:
        """Full pipeline: detect → context → generate → store memory → evolve
        relationship → return events.

        Also triggers daily planning (Phase 2) and reflection checks (Phase 1).
        """
        # Phase 2 — trigger planning on new game-day
        current_day = self.engine.clock.day
        if current_day != self._last_plan_day:
            await self._trigger_daily_planning(current_day)
            self._last_plan_day = current_day

        pairs = detect_encounters(self.engine)

        dialogue_events: list[dict[str, Any]] = []

        async with self.db_factory() as db:
            memory_mgr = MemoryManager(db)
            rel_svc = RelationshipService(db)

            for csim_a, csim_b in pairs:
                # Get real relationship score (needed for cooldown check too)
                friendship_score = await rel_svc.get_friendship_score(
                    csim_a.id, csim_b.id
                )

                if self._is_on_cooldown(
                    csim_a.id, csim_b.id, tick,
                    friendship_score=friendship_score,
                ):
                    # Still update caches even when on cooldown
                    csim_a.relationship_cache[csim_b.id] = friendship_score
                    csim_b.relationship_cache[csim_a.id] = friendship_score
                    continue

                # Determine interaction count (first meeting?)
                interaction_count = await memory_mgr.get_interaction_count(
                    csim_a.id, csim_b.id
                )

                # Phase 3 — update relationship caches on both characters
                csim_a.relationship_cache[csim_b.id] = friendship_score
                csim_b.relationship_cache[csim_a.id] = friendship_score

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
                    world_lore=self.world_lore,
                )
                response = await generate_response(
                    ctx,
                    interaction_count=interaction_count,
                    world_ai_settings=self.world_ai_settings,
                )

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

            # Phase 1 — check reflection for each character
            for char_id, csim in self.engine.characters.items():
                last_tick = self._last_reflection_tick.get(char_id, 0)
                if tick - last_tick >= _REFLECTION_CHECK_INTERVAL:
                    reflection = await memory_mgr.reflect(
                        character_id=char_id,
                        character_name=csim.name,
                        since_tick=last_tick,
                        current_tick=tick,
                    )
                    if reflection is not None:
                        self._last_reflection_tick[char_id] = tick
                        # Emit a reflection event so the frontend can display it
                        for cb in self.engine._on_event:
                            try:
                                await cb({
                                    "type": "reflection",
                                    "characterId": char_id,
                                    "characterName": csim.name,
                                    "description": (
                                        f"{csim.name} reflects: "
                                        f"{reflection.content[:120]}"
                                    ),
                                    "tick": tick,
                                    "data": {"content": reflection.content},
                                })
                            except Exception:
                                logger.exception("Error emitting reflection event")

            await db.commit()

        return dialogue_events

    # ------------------------------------------------------------------
    # Phase 2 — daily planning
    # ------------------------------------------------------------------

    async def _trigger_daily_planning(self, game_day: int) -> None:
        """Generate (or load) daily plans for every active character."""
        if not self.engine.characters:
            return

        logger.info("Triggering daily planning for game-day %d", game_day)

        try:
            async with self.db_factory() as db:
                planner = PlanManager(db)
                memory_mgr = MemoryManager(db)

                for char_id, csim in self.engine.characters.items():
                    _, mood_label = csim.needs.calculate_mood()
                    recent_mems = await memory_mgr.retrieve_recent(char_id, limit=5)
                    mem_texts = MemoryManager.format_memories_for_prompt(recent_mems)

                    goals = await planner.generate_and_store_plan(
                        character_id=char_id,
                        character_name=csim.name,
                        personality=csim.personality,
                        mood=mood_label,
                        recent_memories=mem_texts,
                        game_day=game_day,
                    )
                    csim.daily_goals = goals

                    if goals:
                        logger.info(
                            "%s day-%d goals: %s", csim.name, game_day, goals
                        )
                        # Emit a planning event for the frontend
                        for cb in self.engine._on_event:
                            try:
                                await cb({
                                    "type": "daily_plan",
                                    "characterId": char_id,
                                    "characterName": csim.name,
                                    "description": (
                                        f"{csim.name}'s plan for day {game_day}: "
                                        f"{', '.join(goals[:3])}"
                                    ),
                                    "tick": self.engine.clock.tick,
                                    "data": {"goals": goals, "game_day": game_day},
                                })
                            except Exception:
                                logger.exception("Error emitting daily_plan event")

                await db.commit()
        except Exception:
            logger.exception("Error during daily planning for day %d", game_day)
