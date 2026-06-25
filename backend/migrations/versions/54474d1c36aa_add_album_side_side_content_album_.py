"""add album, side, side_content, album_enrolments

Revision ID: 54474d1c36aa
Revises: 0893638fd517
Create Date: 2026-06-22 15:47:36.247525

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "54474d1c36aa"
down_revision: str | Sequence[str] | None = "0893638fd517"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "albums",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("t_level_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("icon", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["t_level_id"], ["t_levels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_albums_t_level_id"), "albums", ["t_level_id"], unique=False)

    op.create_table(
        "sides",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("album_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["album_id"], ["albums.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sides_album_id"), "sides", ["album_id"], unique=False)

    op.create_table(
        "side_content",
        sa.Column("side_id", sa.Integer(), nullable=False),
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["side_id"], ["sides.id"]),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"]),
        sa.PrimaryKeyConstraint("side_id", "content_id"),
    )
    op.create_index(
        op.f("ix_side_content_content_id"), "side_content", ["content_id"], unique=False
    )

    op.create_table(
        "album_enrolments",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("album_id", sa.Integer(), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["album_id"], ["albums.id"]),
        sa.PrimaryKeyConstraint("user_id", "album_id"),
    )


def downgrade() -> None:
    op.drop_table("album_enrolments")
    op.drop_index(op.f("ix_side_content_content_id"), table_name="side_content")
    op.drop_table("side_content")
    op.drop_index(op.f("ix_sides_album_id"), table_name="sides")
    op.drop_table("sides")
    op.drop_index(op.f("ix_albums_t_level_id"), table_name="albums")
    op.drop_table("albums")
