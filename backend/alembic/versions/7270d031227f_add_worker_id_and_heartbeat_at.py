"""Add worker_id and heartbeat_at

Revision ID: 7270d031227f
Revises: 0346253e69dc
Create Date: 2026-08-13 11:06:53.184034

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7270d031227f'
down_revision: Union[str, None] = '0346253e69dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('research_jobs', sa.Column('worker_id', sa.String(), nullable=True))
    op.add_column('research_jobs', sa.Column('heartbeat_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('research_jobs', 'heartbeat_at')
    op.drop_column('research_jobs', 'worker_id')
