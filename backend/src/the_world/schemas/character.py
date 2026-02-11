"""Pydantic schemas for Character endpoints.

All response schemas use camelCase aliases for JSON serialization to match
the frontend TypeScript conventions.  Input schemas accept both camelCase
and snake_case thanks to ``populate_by_name=True``.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class PersonalityTraits(BaseModel):
    """Big Five personality traits (0-100) + custom traits."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    openness: float = 50
    conscientiousness: float = 50
    extraversion: float = 50
    agreeableness: float = 50
    neuroticism: float = 50
    custom: dict[str, float] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CharacterCreate(BaseModel):
    """Payload for creating a new character."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=128)
    species: str = Field(default="human", max_length=64)
    pronouns: str = Field(default="they/them", max_length=32)
    age: int | None = None
    description: str = Field(default="", max_length=500)
    backstory: str = ""
    personality_traits: PersonalityTraits = Field(default_factory=PersonalityTraits)
    interests: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    is_public: bool = False


class CharacterUpdate(BaseModel):
    """Payload for updating a character (all fields optional)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str | None = Field(default=None, min_length=1, max_length=128)
    species: str | None = Field(default=None, max_length=64)
    pronouns: str | None = Field(default=None, max_length=32)
    age: int | None = None
    description: str | None = Field(default=None, max_length=500)
    backstory: str | None = None
    personality_traits: PersonalityTraits | None = None
    interests: list[str] | None = None
    skills: list[str] | None = None
    avatar_url: str | None = None
    is_public: bool | None = None


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class CharacterResponse(BaseModel):
    """Full public representation of a character (camelCase JSON output)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str
    species: str
    age: int | None = None
    pronouns: str
    avatar_url: str | None = None
    personality_traits: PersonalityTraits
    backstory: str
    interests: list[str]
    skills: list[str]
    is_public: bool
    sim_state: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
