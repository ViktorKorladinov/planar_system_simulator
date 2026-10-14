"""Add random seed of the CP solver to configurations

Revision ID: a1f3c9e2b7d4
Revises: c315891876c7
Create Date: 2026-10-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1f3c9e2b7d4'
down_revision: Union[str, Sequence[str], None] = 'c315891876c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('configurations', sa.Column('random_seed', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('configurations', 'random_seed')
