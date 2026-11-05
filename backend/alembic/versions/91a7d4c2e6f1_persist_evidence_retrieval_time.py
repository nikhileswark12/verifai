"""Persist evidence retrieval timestamps.

Revision ID: 91a7d4c2e6f1
Revises: 7270d031227f
Create Date: 2026-11-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "91a7d4c2e6f1"
down_revision: Union[str, None] = "7270d031227f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evidence",
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evidence", "retrieved_at")
