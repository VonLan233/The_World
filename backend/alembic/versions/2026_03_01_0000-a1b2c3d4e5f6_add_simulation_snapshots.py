"""add simulation_snapshots table

Revision ID: a1b2c3d4e5f6
Revises: 149cfeb5cf25
Create Date: 2026-03-01 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "149cfeb5cf25"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "simulation_snapshots",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "world_id",
            sa.UUID(),
            sa.ForeignKey("worlds.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tick", sa.BigInteger(), nullable=False),
        sa.Column("state_data", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_simulation_snapshots_world_id", "simulation_snapshots", ["world_id"]
    )
    op.create_index(
        "ix_simulation_snapshots_tick", "simulation_snapshots", ["tick"]
    )


def downgrade() -> None:
    op.drop_table("simulation_snapshots")
