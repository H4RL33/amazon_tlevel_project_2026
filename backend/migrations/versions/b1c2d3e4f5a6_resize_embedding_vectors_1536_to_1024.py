"""resize embedding vectors from 1536 to 1024 (titan-embed-text-v2)

Revision ID: b1c2d3e4f5a6
Revises: a3f8b2c1d9e5
Create Date: 2026-06-29 19:00:00.000000

"""

from alembic import op

revision = "b1c2d3e4f5a6"
down_revision = "a3f8b2c1d9e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Clear existing embeddings first — they were generated with v1 (1536-dim)
    # and are incompatible with v2 (1024-dim). Re-run seed.py after this migration.
    op.execute("UPDATE content SET embedding = NULL, embedding_generated_at = NULL")
    op.execute("UPDATE albums SET embedding = NULL, embedding_generated_at = NULL")

    op.execute("ALTER TABLE content ALTER COLUMN embedding TYPE vector(1024) USING NULL")
    op.execute("ALTER TABLE albums ALTER COLUMN embedding TYPE vector(1024) USING NULL")


def downgrade() -> None:
    op.execute("UPDATE content SET embedding = NULL, embedding_generated_at = NULL")
    op.execute("UPDATE albums SET embedding = NULL, embedding_generated_at = NULL")

    op.execute("ALTER TABLE content ALTER COLUMN embedding TYPE vector(1536) USING NULL")
    op.execute("ALTER TABLE albums ALTER COLUMN embedding TYPE vector(1536) USING NULL")
