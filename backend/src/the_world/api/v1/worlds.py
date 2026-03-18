"""World CRUD endpoints."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from the_world.api.v1.auth import get_current_user
from the_world.dependencies import get_db
from the_world.models.user import User
from the_world.models.world import World
from the_world.simulation.world_seed import seed_default_world

router = APIRouter()

UPLOADS_DIR = Path("/app/uploads/maps")
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


class WorldUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    lore: str | None = None
    ai_settings: dict | None = None


class WorldResponse(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    is_public: bool
    settings: dict
    description: str | None = None
    lore: str | None = None
    map_url: str | None = None
    ai_settings_configured: bool = False

    model_config = {"from_attributes": True}

    @classmethod
    def from_world(cls, world: World) -> "WorldResponse":
        ai = world.ai_settings or {}
        configured = bool(ai.get("text_api_key") or ai.get("image_api_key"))
        return cls(
            id=world.id,
            name=world.name,
            owner_id=world.owner_id,
            is_public=world.is_public,
            settings=world.settings,
            description=world.description,
            lore=world.lore,
            map_url=world.map_url,
            ai_settings_configured=configured,
        )


@router.post("/", response_model=WorldResponse, status_code=201)
async def create_world(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WorldResponse:
    """Create a new default world (Starter Town) for the current user."""
    world = await seed_default_world(db, current_user.id)
    return WorldResponse.from_world(world)


@router.get("/", response_model=list[WorldResponse])
async def list_worlds(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[WorldResponse]:
    """List all worlds owned by the current user."""
    result = await db.execute(
        select(World).where(World.owner_id == current_user.id)
    )
    return [WorldResponse.from_world(w) for w in result.scalars().all()]


@router.get("/{world_id}", response_model=WorldResponse)
async def get_world(
    world_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WorldResponse:
    """Get a single world by ID."""
    world = await _get_owned_world(world_id, current_user.id, db)
    return WorldResponse.from_world(world)


@router.patch("/{world_id}", response_model=WorldResponse)
async def update_world(
    world_id: uuid.UUID,
    body: WorldUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WorldResponse:
    """Update world name, description, lore, or AI settings."""
    world = await _get_owned_world(world_id, current_user.id, db)

    if body.name is not None:
        world.name = body.name
    if body.description is not None:
        world.description = body.description
    if body.lore is not None:
        world.lore = body.lore
    if body.ai_settings is not None:
        # Merge so callers can update individual keys without wiping others
        existing = dict(world.ai_settings or {})
        existing.update(body.ai_settings)
        world.ai_settings = existing

    await db.commit()
    await db.refresh(world)
    return WorldResponse.from_world(world)


@router.post("/{world_id}/map/upload", response_model=WorldResponse)
async def upload_map(
    world_id: uuid.UUID,
    file: UploadFile,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WorldResponse:
    """Upload a map image (jpg/png/webp, max 10 MB)."""
    world = await _get_owned_world(world_id, current_user.id, db)

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, or WebP images are allowed.")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 10 MB limit.")

    ext = _ext_for_content_type(file.content_type)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOADS_DIR / f"{world_id}{ext}"
    dest.write_bytes(data)

    world.map_url = f"/uploads/maps/{world_id}{ext}"
    await db.commit()
    await db.refresh(world)
    return WorldResponse.from_world(world)


@router.post("/{world_id}/map/generate", response_model=WorldResponse)
async def generate_map(
    world_id: uuid.UUID,
    body: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WorldResponse:
    """Generate a map image via DALL-E using the world's image API key."""
    world = await _get_owned_world(world_id, current_user.id, db)

    ai = world.ai_settings or {}
    api_key = ai.get("image_api_key", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="No image_api_key configured for this world.")

    prompt = body.get("prompt", f"A fantasy world map for a place called {world.name}")

    try:
        from the_world.ai.third_party import generate_image
        image_bytes = await generate_image(prompt, api_key)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Image generation failed: {exc}") from exc

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOADS_DIR / f"{world_id}.png"
    dest.write_bytes(image_bytes)

    world.map_url = f"/uploads/maps/{world_id}.png"
    await db.commit()
    await db.refresh(world)
    return WorldResponse.from_world(world)


class LoreGenerateRequest(BaseModel):
    prompt: str


class LoreGenerateResponse(BaseModel):
    lore: str


@router.post("/{world_id}/lore/generate", response_model=LoreGenerateResponse)
async def generate_lore(
    world_id: uuid.UUID,
    body: LoreGenerateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> LoreGenerateResponse:
    """Generate lore text using the world's text AI configuration.

    Returns the generated text without saving — the client confirms and PATCHes.
    """
    world = await _get_owned_world(world_id, current_user.id, db)

    ai = world.ai_settings or {}
    provider = ai.get("text_provider", "")
    api_key = ai.get("text_api_key", "")
    model = ai.get("text_model")

    if not provider or not api_key:
        raise HTTPException(
            status_code=400,
            detail="No text_provider/text_api_key configured for this world.",
        )

    try:
        from the_world.ai.third_party import generate_text
        lore = await generate_text(body.prompt, provider, api_key, model)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Lore generation failed: {exc}") from exc

    return LoreGenerateResponse(lore=lore)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_owned_world(
    world_id: uuid.UUID,
    owner_id: uuid.UUID,
    db: AsyncSession,
) -> World:
    result = await db.execute(
        select(World).where(World.id == world_id, World.owner_id == owner_id)
    )
    world = result.scalar_one_or_none()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return world


def _ext_for_content_type(ct: str) -> str:
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }.get(ct, ".png")
