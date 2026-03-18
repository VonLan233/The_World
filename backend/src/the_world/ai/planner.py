"""Daily planning subsystem — generates intention goals for characters each game-day.

Architecture (Phase 2 of the cognitive layer):
  - PlanManager persists goals in the ``character_plans`` table.
  - Goals are generated via LLM (Claude or Ollama) once per game-day.
  - autonomy.choose_activity() boosts activities that match the day's goals.
"""

from __future__ import annotations

import logging
import uuid as uuid_mod

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from the_world.ai.llm_utils import generate_text_llm
from the_world.models.plan import CharacterPlan

logger = logging.getLogger("the_world.ai.planner")


class PlanManager:
    """Manages daily character plans stored in the database."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_plan(self, character_id: str, game_day: int) -> list[str]:
        """Return existing goals for today, or an empty list if none exist."""
        char_uuid = _to_uuid(character_id)
        stmt = select(CharacterPlan).where(
            CharacterPlan.character_id == char_uuid,
            CharacterPlan.game_day == game_day,
        )
        result = await self.db.execute(stmt)
        plan = result.scalar_one_or_none()
        if plan is None:
            return []
        goals = plan.goals
        return goals if isinstance(goals, list) else []

    async def generate_and_store_plan(
        self,
        character_id: str,
        character_name: str,
        personality: dict[str, float],
        mood: str,
        recent_memories: list[str],
        game_day: int,
    ) -> list[str]:
        """Generate a daily plan via LLM and persist it.

        If a plan already exists for this day, the existing goals are returned
        without re-generating (idempotent).

        Returns the list of goal strings (may be empty if LLM is unavailable).
        """
        existing = await self.get_plan(character_id, game_day)
        if existing:
            return existing

        goals = await _generate_goals_llm(
            character_name=character_name,
            personality=personality,
            mood=mood,
            recent_memories=recent_memories,
        )

        if goals:
            char_uuid = _to_uuid(character_id)
            plan = CharacterPlan(
                id=uuid_mod.uuid4(),
                character_id=char_uuid,
                game_day=game_day,
                goals=goals,
            )
            self.db.add(plan)
            await self.db.flush()
            logger.info(
                "Generated plan for %s (day %d): %s", character_name, game_day, goals
            )

        return goals


# ---------------------------------------------------------------------------
# LLM prompt builder
# ---------------------------------------------------------------------------

async def _generate_goals_llm(
    character_name: str,
    personality: dict[str, float],
    mood: str,
    recent_memories: list[str],
) -> list[str]:
    """Ask an LLM to write 3-5 daily intention goals for the character."""
    openness = personality.get("openness", 0.5)
    extraversion = personality.get("extraversion", 0.5)
    conscientiousness = personality.get("conscientiousness", 0.5)

    memory_text = ""
    if recent_memories:
        memory_text = "\nRecent events: " + "; ".join(recent_memories[:3])

    prompt = (
        f"You are {character_name}, a character with personality traits: "
        f"openness={openness:.1f}, extraversion={extraversion:.1f}, "
        f"conscientiousness={conscientiousness:.1f}.\n"
        f"Your current mood is: {mood}.{memory_text}\n\n"
        "Generate a list of 3-5 simple daily intentions for today. "
        "These are personal activities or social plans.\n"
        "Format: one goal per line, starting with a dash (-).\n"
        "Keep each goal concise (5-10 words).\n"
        "Example:\n"
        "- Spend the morning reading at the library\n"
        "- Have lunch at the café\n"
        "- Exercise at the gym\n\n"
        "Your goals:"
    )

    raw = await generate_text_llm(prompt, max_tokens=150)
    if not raw:
        return []

    goals: list[str] = []
    for line in raw.strip().splitlines():
        line = line.strip().lstrip("-•* \t").strip()
        if line and len(line) > 3:
            goals.append(line)
        if len(goals) >= 5:
            break

    return goals


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_uuid(value: str | uuid_mod.UUID) -> uuid_mod.UUID:
    if isinstance(value, uuid_mod.UUID):
        return value
    return uuid_mod.UUID(str(value))
