"""Character CRUD router.

Handles the mapping between:
- Frontend camelCase JSON  <-->  Pydantic schemas (snake_case internally)
- Pydantic schemas         <-->  SQLAlchemy ORM models (different field names)
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from the_world.api.v1.auth import get_current_user
from the_world.dependencies import get_db
from the_world.models.character import Character
from the_world.models.user import User
from the_world.schemas.character import (
    CharacterCreate,
    CharacterResponse,
    CharacterUpdate,
    PersonalityTraits,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# ORM <-> Schema conversion helpers
# ---------------------------------------------------------------------------

def _orm_to_response(char: Character) -> CharacterResponse:
    """Convert an ORM Character instance to the API response schema."""
    personality_data = char.personality or {}
    background_data = char.background or {}
    skills_data = char.skills or {}

    # Build PersonalityTraits from the JSONB dict
    trait_fields = {
        k: v for k, v in personality_data.items()
        if k in PersonalityTraits.model_fields
    }
    personality_traits = PersonalityTraits(**trait_fields) if trait_fields else PersonalityTraits()

    return CharacterResponse(
        id=char.id,
        user_id=char.owner_id,
        name=char.name,
        description=char.short_description or "",
        species=char.species,
        age=char.age,
        pronouns=char.pronouns,
        avatar_url=char.portrait_url,
        personality_traits=personality_traits,
        backstory=background_data.get("backstory", ""),
        interests=background_data.get("interests", []),
        skills=list(skills_data.keys()) if isinstance(skills_data, dict) else [],
        is_public=char.is_public,
        sim_state=char.sim_state if char.sim_state else None,
        created_at=char.created_at,
        updated_at=char.updated_at,
    )


# ---------------------------------------------------------------------------
# Public gallery (no auth required)
# ---------------------------------------------------------------------------

@router.get("/public", response_model=list[CharacterResponse])
async def list_public_characters(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
    offset: int = 0,
) -> list[CharacterResponse]:
    """Return publicly visible characters."""
    result = await db.execute(
        select(Character)
        .where(Character.is_public.is_(True))
        .order_by(Character.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [_orm_to_response(c) for c in result.scalars().all()]


# ---------------------------------------------------------------------------
# Authenticated CRUD
# ---------------------------------------------------------------------------

@router.post("/", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(
    body: CharacterCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CharacterResponse:
    """Create a new character owned by the current user."""
    character = Character(
        owner_id=current_user.id,
        name=body.name,
        species=body.species,
        age=body.age,
        pronouns=body.pronouns,
        short_description=body.description,
        personality=body.personality_traits.model_dump(),
        appearance={},
        background={
            "backstory": body.backstory,
            "interests": body.interests,
        },
        skills={skill: 0 for skill in body.skills},
        is_public=body.is_public,
    )
    db.add(character)
    await db.flush()
    await db.refresh(character)
    return _orm_to_response(character)


@router.get("/", response_model=list[CharacterResponse])
async def list_my_characters(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[CharacterResponse]:
    """List all characters owned by the current user."""
    result = await db.execute(
        select(Character)
        .where(Character.owner_id == current_user.id)
        .order_by(Character.created_at.desc())
    )
    return [_orm_to_response(c) for c in result.scalars().all()]


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CharacterResponse:
    """Get a single character by ID."""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    return _orm_to_response(character)


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: uuid.UUID,
    body: CharacterUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CharacterResponse:
    """Update a character (must be the owner)."""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    if character.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the character owner")

    update_data = body.model_dump(exclude_unset=True)

    # Map schema fields -> ORM fields
    field_mapping = {
        "description": "short_description",
        "avatar_url": "portrait_url",
    }
    for schema_field, orm_field in field_mapping.items():
        if schema_field in update_data:
            update_data[orm_field] = update_data.pop(schema_field)

    # Handle personality_traits -> personality JSONB
    if "personality_traits" in update_data:
        traits = update_data.pop("personality_traits")
        character.personality = {**(character.personality or {}), **traits}

    # Handle backstory -> background.backstory
    if "backstory" in update_data:
        bg = dict(character.background or {})
        bg["backstory"] = update_data.pop("backstory")
        character.background = bg

    # Handle interests -> background.interests
    if "interests" in update_data:
        bg = dict(character.background or {})
        bg["interests"] = update_data.pop("interests")
        character.background = bg

    # Handle skills -> skills JSONB
    if "skills" in update_data:
        new_skills = update_data.pop("skills")
        character.skills = {skill: 0 for skill in new_skills}

    # Apply remaining simple field updates
    for field, value in update_data.items():
        setattr(character, field, value)

    await db.flush()
    await db.refresh(character)
    return _orm_to_response(character)


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
