"""CharacterPlan ORM model — daily goals for character autonomous planning."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from the_world.db.base import Base


class CharacterPlan(Base):
    """One row per character per game-day, storing that day's intention goals."""

    __tablename__ = "character_plans"

    __table_args__ = (
        UniqueConstraint("character_id", "game_day", name="uq_character_plan_day"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # The game-day number (from GameClock.day) this plan belongs to.
    game_day: Mapped[int] = mapped_column(Integer, nullable=False)
    # List of goal strings, e.g. ["Read at the library", "Have lunch with Alice"].
    goals: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<CharacterPlan(character={self.character_id!r}, "
            f"day={self.game_day}, goals={self.goals!r})>"
        )
