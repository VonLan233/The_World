"""Memory manager — CRUD and retrieval for character memories.

Re-uses the existing ``models.memory.Memory`` ORM model.  Relevance
scoring and JSONB context filtering are done in Python to stay
compatible with both PostgreSQL and SQLite dev mode.
"""

from __future__ import annotations

import json
import logging
import math
import uuid as uuid_mod
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from the_world.ai.llm_utils import generate_text_llm
from the_world.models.memory import Memory

logger = logging.getLogger("the_world.ai.memory")

# Accumulated importance sum that triggers a reflection pass.
REFLECTION_THRESHOLD = 150.0


def _to_uuid(value: str | uuid_mod.UUID) -> uuid_mod.UUID:
    """Convert a string to uuid.UUID if needed (SQLite compat)."""
    if isinstance(value, uuid_mod.UUID):
        return value
    return uuid_mod.UUID(value)


class MemoryManager:
    """High-level interface over the Memory table."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create_memory(
        self,
        character_id: str,
        memory_type: str,
        content: str,
        sim_timestamp: int,
        importance: float = 0.5,
        emotional_valence: float = 0.0,
        context: dict[str, Any] | None = None,
    ) -> Memory:
        """Persist a new memory row."""
        char_uuid = _to_uuid(character_id)
        mem = Memory(
            id=uuid_mod.uuid4(),
            character_id=char_uuid,
            memory_type=memory_type,
            content=content,
            sim_timestamp=sim_timestamp,
            importance=importance,
            emotional_valence=emotional_valence,
            context=context or {},
        )
        self.db.add(mem)
        await self.db.flush()
        return mem

    # ------------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------------

    async def retrieve_recent(
        self,
        character_id: str,
        limit: int = 10,
        type_filter: str | None = None,
    ) -> list[Memory]:
        """Return the most recent memories (optionally filtered by type)."""
        char_uuid = _to_uuid(character_id)
        stmt = (
            select(Memory)
            .where(Memory.character_id == char_uuid)
            .order_by(Memory.sim_timestamp.desc())
            .limit(limit)
        )
        if type_filter:
            stmt = stmt.where(Memory.memory_type == type_filter)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def retrieve_relevant(
        self,
        character_id: str,
        current_tick: int,
        limit: int = 5,
        target_character_id: str | None = None,
    ) -> list[Memory]:
        """Return memories ranked by a relevance score.

        Score = importance * exp(-age / 1440) * (1 + |valence|)

        Filtering by target_character_id is done in Python because the
        ``context`` column is stored as TEXT in SQLite dev mode.
        """
        char_uuid = _to_uuid(character_id)
        stmt = (
            select(Memory)
            .where(Memory.character_id == char_uuid)
            .order_by(Memory.sim_timestamp.desc())
            .limit(100)  # fetch a window then re-rank
        )
        result = await self.db.execute(stmt)
        memories = list(result.scalars().all())

        # Optional filter by target
        if target_character_id:
            filtered: list[Memory] = []
            for m in memories:
                ctx = m.context if isinstance(m.context, dict) else _parse_context(m.context)
                if ctx.get("target_character_id") == target_character_id:
                    filtered.append(m)
            memories = filtered or memories  # fall back to all if no match

        def _score(m: Memory) -> float:
            age = max(current_tick - m.sim_timestamp, 0)
            return m.importance * math.exp(-age / 1440) * (1 + abs(m.emotional_valence))

        memories.sort(key=_score, reverse=True)
        return memories[:limit]

    # ------------------------------------------------------------------
    # Interaction counting
    # ------------------------------------------------------------------

    async def get_interaction_count(
        self,
        character_id: str,
        target_character_id: str,
    ) -> int:
        """Count how many interaction memories exist between two characters.

        Uses a broad text search in SQL then refines with Python-side
        context parsing (SQLite compat).
        """
        char_uuid = _to_uuid(character_id)
        stmt = (
            select(Memory)
            .where(Memory.character_id == char_uuid)
            .where(Memory.memory_type == "interaction")
        )
        result = await self.db.execute(stmt)
        memories = list(result.scalars().all())

        count = 0
        for m in memories:
            ctx = m.context if isinstance(m.context, dict) else _parse_context(m.context)
            if ctx.get("target_character_id") == target_character_id:
                count += 1
        return count

    # ------------------------------------------------------------------
    # Reflection (Phase 1 cognitive layer)
    # ------------------------------------------------------------------

    async def reflect(
        self,
        character_id: str,
        character_name: str,
        since_tick: int,
        current_tick: int,
    ) -> "Memory | None":
        """Generate a high-level insight if accumulated importance is high enough.

        Retrieves non-reflection memories created after *since_tick*, sums their
        importance scores, and if the total meets ``REFLECTION_THRESHOLD``, calls
        the LLM to distil a reflection.

        Returns the new reflection ``Memory`` row, or ``None`` if the threshold
        wasn't met or no LLM is available.
        """
        char_uuid = _to_uuid(character_id)
        stmt = (
            select(Memory)
            .where(Memory.character_id == char_uuid)
            .where(Memory.memory_type != "reflection")
            .where(Memory.sim_timestamp > since_tick)
            .order_by(Memory.sim_timestamp.desc())
            .limit(50)
        )
        result = await self.db.execute(stmt)
        memories = list(result.scalars().all())

        if not memories:
            return None

        total_importance = sum(m.importance for m in memories)
        if total_importance < REFLECTION_THRESHOLD:
            return None

        # Build a summarised list of recent memories for the LLM
        mem_lines = [f"- [{m.memory_type}] {m.content}" for m in memories[:15]]
        mem_text = "\n".join(mem_lines)

        prompt = (
            f"You are {character_name}. Review these recent memories:\n"
            f"{mem_text}\n\n"
            "Write a single insightful reflection (2-3 sentences) in first person "
            "about what you've learned, noticed, or how you feel about your life "
            "and relationships recently. Be specific and personal."
        )

        insight = await generate_text_llm(prompt, max_tokens=150)
        if not insight:
            return None

        reflection = await self.create_memory(
            character_id=character_id,
            memory_type="reflection",
            content=insight,
            sim_timestamp=current_tick,
            importance=0.9,
            emotional_valence=0.1,
            context={
                "source_tick_range": [since_tick, current_tick],
                "source_count": len(memories),
            },
        )
        logger.info(
            "Reflection generated for %s: %s…", character_name, insight[:80]
        )
        return reflection

    # ------------------------------------------------------------------
    # Prompt formatting
    # ------------------------------------------------------------------

    @staticmethod
    def format_memories_for_prompt(memories: list[Memory]) -> list[str]:
        """Convert Memory rows into short text lines for LLM prompts."""
        lines: list[str] = []
        for m in memories:
            lines.append(f"[{m.memory_type}] {m.content}")
        return lines


def _parse_context(raw: Any) -> dict[str, Any]:
    """Safely parse context that might be a JSON string (SQLite) or dict."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}
