"""Pydantic schemas for User endpoints."""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class UserCreate(BaseModel):
    """Payload for registering a new user."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(..., max_length=320)
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """Payload for logging in."""

    username: str
    password: str


class UserResponse(BaseModel):
    """Public representation of a user."""

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: uuid.UUID
    username: str
    email: str
    display_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    created_at: datetime


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Combined login/register response: token + user profile."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
