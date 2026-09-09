"""Add user password hashes

Revision ID: 616fe554c15f
Revises: 486e51595993
Create Date: 2026-09-07 21:04:10.210352

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "616fe554c15f"
down_revision: str | Sequence[str] | None = "486e51595993"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply this migration."""
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=255), nullable=False),
    )


def downgrade() -> None:
    """Reverse this migration."""
    op.drop_column("users", "password_hash")
