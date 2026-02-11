"""Pydantic schemas for Character endpoints."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CharacterCreate(BaseModel):
    """Payload for creating a new character."""

    name: str = Field(..., min_length=1, max_length=128)
    species: str = Field(default="human", max_length=64)
    age: int | None = None
    pronouns: str = Field(default="they/them", max_length=32)
    personality: dict[str, Any] = Field(default_factory=dict)
    appearance: dict[str, Any] = Field(default_factory=dict)
    background: dict[str, Any] = Field(default_factory=dict)
    short_description: str | None = Field(default=None, max_length=500)


class CharacterUpdate(BaseModel):
    """Payload for updating a character (all fields optional)."""

    name: str | None = Field(default=None, min_length=1, max_length=128)
    species: str | None = Field(default=None, max_length=64)
    age: int | None = None
    pronouns: str | None = Field(default=None, max_length=32)
    personality: dict[str, Any] | None = None
    appearance: dict[str, Any] | None = None
    background: dict[str, Any] | None = None
    short_description: str | None = Field(default=None, max_length=500)
    sprite_key: str | None = Field(default=None, max_length=64)
    portrait_url: str | None = Field(default=None, max_length=512)
    is_public: bool | None = None


class CharacterResponse(BaseModel):
    """Full public representation of a character."""

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    short_description: str | None = None
    species: str
    age: int | None = None
    pronouns: str
    sprite_key: str
    portrait_url: str | None = None
    personality: dict[str, Any]
    appearance: dict[str, Any]
    background: dict[str, Any]
    sim_state: dict[str, Any]
    skills: dict[str, Any]
    is_public: bool
    is_active_in_sim: bool
    import_source: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
