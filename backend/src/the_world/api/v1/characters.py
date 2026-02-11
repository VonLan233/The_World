"""Character CRUD router."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from the_world.api.v1.auth import get_current_user
from the_world.dependencies import get_db
from the_world.models.character import Character
from the_world.models.user import User
from the_world.schemas.character import CharacterCreate, CharacterResponse, CharacterUpdate

router = APIRouter()


# ---------------------------------------------------------------------------
# Public gallery (no auth required)
# ---------------------------------------------------------------------------

@router.get("/gallery/public", response_model=list[CharacterResponse])
async def list_public_characters(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
    offset: int = 0,
) -> list[Character]:
    """Return publicly visible characters."""
    result = await db.execute(
        select(Character)
        .where(Character.is_public.is_(True))
        .order_by(Character.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Authenticated CRUD
# ---------------------------------------------------------------------------

@router.post("/", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(
    body: CharacterCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Character:
    """Create a new character owned by the current user."""
    character = Character(
        owner_id=current_user.id,
        name=body.name,
        species=body.species,
        age=body.age,
        pronouns=body.pronouns,
        personality=body.personality,
        appearance=body.appearance,
        background=body.background,
        short_description=body.short_description,
    )
    db.add(character)
    await db.flush()
    await db.refresh(character)
    return character


@router.get("/", response_model=list[CharacterResponse])
async def list_my_characters(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Character]:
    """List all characters owned by the current user."""
    result = await db.execute(
        select(Character)
        .where(Character.owner_id == current_user.id)
        .order_by(Character.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Character:
    """Get a single character by ID."""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    return character


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: uuid.UUID,
    body: CharacterUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Character:
    """Update a character (must be the owner)."""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    if character.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the character owner")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(character, field, value)

    await db.flush()
    await db.refresh(character)
    return character


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    character_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a character (must be the owner)."""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    if character.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the character owner")

    await db.delete(character)
    await db.flush()
