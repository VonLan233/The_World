"""Relationship API endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from the_world.dependencies import get_db
from the_world.models.character import Character
from the_world.models.relationship import Relationship
from the_world.schemas.relationship import (
    RelationshipListResponse,
    RelationshipResponse,
    RelationshipSummaryItem,
)
from the_world.services.relationship_service import (
    RelationshipService,
    calculate_compatibility,
)

router = APIRouter()


async def _get_character_name(db: AsyncSession, char_id: uuid.UUID) -> str:
    """Look up a character's name by ID, return 'Unknown' if missing."""
    result = await db.execute(
        select(Character.name).where(Character.id == char_id)
    )
    name = result.scalar_one_or_none()
    return name or "Unknown"


async def _get_character_personality(
    db: AsyncSession, char_id: uuid.UUID
) -> dict[str, float] | None:
    """Look up a character's personality JSONB."""
    result = await db.execute(
        select(Character.personality).where(Character.id == char_id)
    )
    return result.scalar_one_or_none()


@router.get("/{character_id}", response_model=RelationshipListResponse)
async def list_relationships(
    character_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RelationshipListResponse:
    """Return all relationships for a character."""
    svc = RelationshipService(db)
    rels = await svc.get_all_for_character(str(character_id))

    items: list[RelationshipSummaryItem] = []
    for rel in rels:
        # Determine which side is the "other" character
        if rel.source_character_id == character_id:
            target_id = rel.target_character_id
        else:
            target_id = rel.source_character_id

        target_name = await _get_character_name(db, target_id)
        items.append(
            RelationshipSummaryItem(
                target_id=target_id,
                target_name=target_name,
                relationship_type=rel.relationship_type,
                friendship_score=rel.friendship_score,
            )
        )

    return RelationshipListResponse(
        character_id=character_id,
        relationships=items,
    )


@router.get(
    "/{character_id}/{target_id}",
    response_model=RelationshipResponse,
)
async def get_relationship(
    character_id: uuid.UUID,
    target_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RelationshipResponse:
    """Return the relationship between two characters, or 404."""
    svc = RelationshipService(db)
    rel = await svc.get_relationship(str(character_id), str(target_id))
    if rel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No relationship found between these characters",
        )

    # Compute compatibility if both characters have personality data
    compat: float | None = None
    pa = await _get_character_personality(db, character_id)
    pb = await _get_character_personality(db, target_id)
    if pa and pb:
        compat = round(calculate_compatibility(pa, pb), 3)

    return RelationshipResponse(
        id=rel.id,
        source_character_id=rel.source_character_id,
        target_character_id=rel.target_character_id,
        friendship_score=rel.friendship_score,
        romance_score=rel.romance_score,
        rivalry_score=rel.rivalry_score,
        relationship_type=rel.relationship_type,
        compatibility=compat,
        created_at=rel.created_at,
        updated_at=rel.updated_at,
    )
