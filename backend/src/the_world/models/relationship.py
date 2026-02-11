"""Relationship ORM model (character-to-character bonds)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from the_world.db.base import Base


class Relationship(Base):
    __tablename__ = "relationships"
    __table_args__ = (
        UniqueConstraint(
            "source_character_id",
            "target_character_id",
            name="uq_relationship_source_target",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_character_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_character_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    friendship_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    romance_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rivalry_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    relationship_type: Mapped[str] = mapped_column(
        String(64), default="acquaintance", nullable=False
    )
    interaction_summary: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<Relationship(source={self.source_character_id!r}, "
            f"target={self.target_character_id!r}, type={self.relationship_type!r})>"
        )
