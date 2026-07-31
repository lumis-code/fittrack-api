"""add is_admin to users

Revision ID: a7f9d2c4b6e8
Revises: 3253e71fe532
Create Date: 2026-07-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7f9d2c4b6e8'
down_revision: Union[str, None] = '3253e71fe532'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add a non-nullable boolean column with server default false so existing rows get a value.
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    op.drop_column('users', 'is_admin')
