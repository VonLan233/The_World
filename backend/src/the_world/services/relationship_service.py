"""Relationship service — manages character-to-character bonds.

Provides CRUD, compatibility calculation, score evolution after interactions,
and interaction summary tracking.
"""

from __future__ import annotations

import json
import uuid as uuid_mod
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from the_world.models.relationship import Relationship


def _to_uuid(value: str | uuid_mod.UUID) -> uuid_mod.UUID:
    """Convert a string to uuid.UUID if needed (SQLite compat)."""
    if isinstance(value, uuid_mod.UUID):
        return value
    return uuid_mod.UUID(value)


def _parse_json(raw: Any) -> dict:
    """Safely parse a value that might be a JSON string (SQLite) or dict."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def calculate_compatibility(
    personality_a: dict[str, float],
    personality_b: dict[str, float],
) -> float:
    """Compute Big Five compatibility score between two personalities.

    Returns a value in [-1.0, 1.0].

    - agreeableness similarity → +
    - conscientiousness similarity → +
    - openness similarity → +
    - complementary extraversion → slight +
    - both high neuroticism → -
    """
    score = 0.0

    # Similarity helpers (traits normalised to 0-100, we work in 0-1 range)
    def _sim(trait: str) -> float:
        a = personality_a.get(trait, 50) / 100.0
        b = personality_b.get(trait, 50) / 100.0
        return 1.0 - abs(a - b)

    # Similarity bonuses
    score += _sim("agreeableness") * 0.30
    score += _sim("conscientiousness") * 0.25
    score += _sim("openness") * 0.20

    # Complementary extraversion (moderate difference → slight bonus)
    ext_a = personality_a.get("extraversion", 50) / 100.0
    ext_b = personality_b.get("extraversion", 50) / 100.0
    ext_diff = abs(ext_a - ext_b)
    score += (0.3 - ext_diff) * 0.15  # small bonus when moderate diff

    # Both high neuroticism → penalty
    neu_a = personality_a.get("neuroticism", 50) / 100.0
    neu_b = personality_b.get("neuroticism", 50) / 100.0
    if neu_a > 0.6 and neu_b > 0.6:
        score -= (neu_a + neu_b - 1.2) * 0.5

    # Clamp to [-1, 1]
    return max(-1.0, min(1.0, score))


def classify_type(rel: Relationship) -> str:
    """Determine the relationship type label from scores."""
    if rel.rivalry_score > 50:
        return "rival"
    if rel.romance_score > 50:
        return "romantic"
    if rel.friendship_score > 75:
        return "close_friend"
    if rel.friendship_score > 40:
        return "friend"
    if rel.friendship_score > 15:
        return "acquaintance"
    return "stranger"


class RelationshipService:
    """High-level interface over the Relationship table."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create(
        self, source_id: str, target_id: str
    ) -> Relationship:
        """Idempotent: return existing relationship or create a new one."""
        rel = await self.get_relationship(source_id, target_id)
        if rel is not None:
            return rel

        src_uuid = _to_uuid(source_id)
        tgt_uuid = _to_uuid(target_id)
        rel = Relationship(
            id=uuid_mod.uuid4(),
            source_character_id=src_uuid,
            target_character_id=tgt_uuid,
            friendship_score=0.0,
            romance_score=0.0,
            rivalry_score=0.0,
            relationship_type="stranger",
            interaction_summary={"entries": []},
        )
        self.db.add(rel)
        await self.db.flush()
        return rel

    async def get_relationship(
        self, source_id: str, target_id: str
    ) -> Relationship | None:
        """Query bidirectional — either direction matches."""
        src_uuid = _to_uuid(source_id)
        tgt_uuid = _to_uuid(target_id)
        stmt = select(Relationship).where(
            or_(
                (Relationship.source_character_id == src_uuid)
                & (Relationship.target_character_id == tgt_uuid),
                (Relationship.source_character_id == tgt_uuid)
                & (Relationship.target_character_id == src_uuid),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_for_character(
        self, character_id: str
    ) -> list[Relationship]:
        """Return all relationships where this character is source OR target."""
        char_uuid = _to_uuid(character_id)
        stmt = select(Relationship).where(
            or_(
                Relationship.source_character_id == char_uuid,
                Relationship.target_character_id == char_uuid,
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_friendship_score(
        self, source_id: str, target_id: str
    ) -> float:
        """Quick helper — returns 0.0 if no relationship exists."""
        rel = await self.get_relationship(source_id, target_id)
        if rel is None:
            return 0.0
        return rel.friendship_score

    async def evolve_after_interaction(
        self,
        source_id: str,
        target_id: str,
        interaction_quality: float,
        personality_a: dict[str, float],
        personality_b: dict[str, float],
    ) -> tuple[Relationship, list[str]]:
        """Update friendship_score after an interaction.

        Returns (relationship, milestones) where milestones is a list of
        threshold-crossing descriptions like "+25", "+50", etc.
        """
        rel = await self.get_or_create(source_id, target_id)
        compatibility = calculate_compatibility(personality_a, personality_b)

        old_score = rel.friendship_score
        delta = interaction_quality * 5.0 * (1 + compatibility * 0.3)
        new_score = max(-100.0, min(100.0, old_score + delta))
        rel.friendship_score = new_score

        # Detect milestone crossings (multiples of 25)
        milestones: list[str] = []
        for threshold in [-75, -50, -25, 25, 50, 75]:
            old_crossed = (old_score >= threshold) if threshold > 0 else (old_score <= threshold)
            new_crossed = (new_score >= threshold) if threshold > 0 else (new_score <= threshold)
            if new_crossed and not old_crossed:
                milestones.append(f"{'+' if threshold > 0 else ''}{threshold}")

        # Update type
        rel.relationship_type = classify_type(rel)

        await self.db.flush()
        return rel, milestones

    async def update_interaction_summary(
        self,
        source_id: str,
        target_id: str,
        tick: int,
        summary_text: str,
    ) -> None:
        """Append a summary entry to the interaction_summary JSONB, keeping max 20."""
        rel = await self.get_or_create(source_id, target_id)

        summary = _parse_json(rel.interaction_summary)
        entries = summary.get("entries", [])
        entries.append({"tick": tick, "text": summary_text})

        # Keep only the most recent 20 entries
        if len(entries) > 20:
            entries = entries[-20:]

        # Force SQLAlchemy to detect the change by assigning a new dict
        rel.interaction_summary = {"entries": list(entries)}
        # Mark the column as modified for SQLite TEXT storage
        from sqlalchemy.orm import attributes
        attributes.flag_modified(rel, "interaction_summary")
        await self.db.flush()

    def get_recent_summaries(
        self, rel: Relationship, limit: int = 3
    ) -> list[str]:
        """Return the most recent interaction summary texts."""
        summary = _parse_json(rel.interaction_summary)
        entries = summary.get("entries", [])
        return [e["text"] for e in entries[-limit:]]
