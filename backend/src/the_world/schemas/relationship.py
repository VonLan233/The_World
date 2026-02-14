"""Pydantic schemas for Relationship endpoints.

All response schemas use camelCase aliases for JSON serialization.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class RelationshipResponse(BaseModel):
    """Full relationship data returned by the API."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: uuid.UUID
    source_character_id: uuid.UUID
    target_character_id: uuid.UUID
    friendship_score: float
    romance_score: float
    rivalry_score: float
    relationship_type: str
    compatibility: float | None = None
    created_at: datetime
    updated_at: datetime


class RelationshipSummaryItem(BaseModel):
    """Lightweight relationship entry for list views."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    target_id: uuid.UUID
    target_name: str
    relationship_type: str
    friendship_score: float


class RelationshipListResponse(BaseModel):
    """All relationships for a given character."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    character_id: uuid.UUID
    relationships: list[RelationshipSummaryItem]
