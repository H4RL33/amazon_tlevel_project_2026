"""add pgvector embeddings and user_snippet_saves

Revision ID: a3f8b2c1d9e5
Revises: 7a1f3c9d4e21
Create Date: 2026-06-29 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3f8b2c1d9e5"
down_revision: str | Sequence[str] | None = "7a1f3c9d4e21"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column("content", sa.Column("embedding", sa.Text, nullable=True))
    op.add_column("content", sa.Column("embedding_generated_at", sa.DateTime, nullable=True))
    op.execute("ALTER TABLE content ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector")

    op.add_column("albums", sa.Column("embedding", sa.Text, nullable=True))
    op.add_column("albums", sa.Column("embedding_generated_at", sa.DateTime, nullable=True))
    op.execute("ALTER TABLE albums ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector")

    op.create_table(
        "user_snippet_saves",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("content_id", sa.Integer, sa.ForeignKey("content.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("saved_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_snippet_saves")
    op.drop_column("albums", "embedding_generated_at")
    op.drop_column("albums", "embedding")
    op.drop_column("content", "embedding_generated_at")
    op.drop_column("content", "embedding")
