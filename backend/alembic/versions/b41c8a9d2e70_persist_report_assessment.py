"""Persist report overall assessment.

Revision ID: b41c8a9d2e70
Revises: 91a7d4c2e6f1
Create Date: 2026-11-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b41c8a9d2e70"
down_revision: Union[str, None] = "91a7d4c2e6f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "research_reports",
        sa.Column("overall_assessment", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("research_reports", "overall_assessment")
