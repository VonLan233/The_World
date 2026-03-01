"""World CRUD endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from the_world.api.v1.auth import get_current_user
from the_world.dependencies import get_db
from the_world.models.user import User
from the_world.models.world import World
from the_world.simulation.world_seed import seed_default_world

router = APIRouter()


class WorldResponse(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    is_public: bool
    settings: dict

    model_config = {"from_attributes": True}


@router.post("/", response_model=WorldResponse, status_code=201)
async def create_world(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> World:
    """Create a new default world (Starter Town) for the current user."""
    world = await seed_default_world(db, current_user.id)
    return world


@router.get("/", response_model=list[WorldResponse])
async def list_worlds(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[World]:
    """List all worlds owned by the current user."""
    result = await db.execute(
        select(World).where(World.owner_id == current_user.id)
    )
    return list(result.scalars().all())


@router.get("/{world_id}", response_model=WorldResponse)
async def get_world(
    world_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> World:
    """Get a single world by ID."""
    result = await db.execute(
        select(World).where(World.id == world_id, World.owner_id == current_user.id)
    )
    world = result.scalar_one_or_none()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return world
