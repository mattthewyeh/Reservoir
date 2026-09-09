"""Prevent overlapping reservations

Revision ID: a4d7f6b2c901
Revises: 616fe554c15f
Create Date: 2026-09-07 23:30:00.000000

"""
from collections.abc import Sequence

from alembic import op


revision: str = "a4d7f6b2c901"
down_revision: str | Sequence[str] | None = "616fe554c15f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply this migration."""
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        """
        ALTER TABLE reservations
        ADD CONSTRAINT no_overlapping_confirmed_reservations
        EXCLUDE USING gist (
            equipment_id WITH =,
            tstzrange(starts_at, ends_at, '[)') WITH &&
        )
        WHERE (status = 'confirmed'::reservation_status)
        """
    )


def downgrade() -> None:
    """Reverse this migration."""
    op.execute(
        """
        ALTER TABLE reservations
        DROP CONSTRAINT no_overlapping_confirmed_reservations
        """
    )
