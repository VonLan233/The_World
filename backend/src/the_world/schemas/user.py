"""Pydantic schemas for User endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Payload for registering a new user."""

    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(..., max_length=320)
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Payload for logging in."""

    username: str
    password: str


class UserResponse(BaseModel):
    """Public representation of a user."""

    id: uuid.UUID
    username: str
    email: str
    display_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
