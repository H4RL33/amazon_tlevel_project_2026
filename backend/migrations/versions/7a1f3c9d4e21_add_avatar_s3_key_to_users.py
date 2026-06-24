"""add avatar_s3_key to users

Revision ID: 7a1f3c9d4e21
Revises: 54474d1c36aa
Create Date: 2026-06-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a1f3c9d4e21'
down_revision: Union[str, Sequence[str], None] = '54474d1c36aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_s3_key", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_s3_key")
