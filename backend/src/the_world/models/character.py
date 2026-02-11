"""Character ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from the_world.db.base import Base


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    species: Mapped[str] = mapped_column(String(64), default="human", nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pronouns: Mapped[str] = mapped_column(String(32), default="they/them", nullable=False)
    sprite_key: Mapped[str] = mapped_column(String(64), default="default", nullable=False)
    portrait_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Rich JSON fields
    personality: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    appearance: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    background: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    sim_state: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    skills: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Flags
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active_in_sim: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    import_source: Mapped[str | None] = mapped_column(String(256), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    owner = relationship("User", backref="characters", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Character(id={self.id!r}, name={self.name!r})>"
