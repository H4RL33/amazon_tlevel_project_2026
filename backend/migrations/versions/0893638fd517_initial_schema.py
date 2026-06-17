"""initial schema

Revision ID: 0893638fd517
Revises:
Create Date: 2026-06-17 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0893638fd517"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### topics ###
    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("accent_colour", sa.String(length=7), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_topics_slug"), "topics", ["slug"], unique=True)

    # ### t_levels ###
    op.create_table(
        "t_levels",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("entry_requirements", sa.Text(), nullable=False),
        sa.Column("how_to_apply", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_t_levels_topic_id"), "t_levels", ["topic_id"], unique=False)

    # ### tags ###
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_tags_name"), "tags", ["name"], unique=True)

    # ### users ###
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cognito_sub", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cognito_sub"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_cognito_sub"), "users", ["cognito_sub"], unique=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # ### content ###
    op.create_table(
        "content",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "content_type",
            sa.Enum("article", "audio", "video", name="contenttype"),
            nullable=False,
        ),
        sa.Column("media_url", sa.String(length=500), nullable=True),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("t_level_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"]),
        sa.ForeignKeyConstraint(["t_level_id"], ["t_levels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_content_topic_id"), "content", ["topic_id"], unique=False)
    op.create_index(op.f("ix_content_t_level_id"), "content", ["t_level_id"], unique=False)

    # ### content_tags ###
    op.create_table(
        "content_tags",
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"]),
        sa.PrimaryKeyConstraint("content_id", "tag_id"),
    )

    # ### user_topic_interests ###
    op.create_table(
        "user_topic_interests",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"]),
        sa.PrimaryKeyConstraint("user_id", "topic_id"),
    )

    # ### user_content_progress ###
    op.create_table(
        "user_content_progress",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column(
            "last_viewed_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("progress_pct", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"]),
        sa.PrimaryKeyConstraint("user_id", "content_id"),
    )


def downgrade() -> None:
    op.drop_table("user_content_progress")
    op.drop_table("user_topic_interests")
    op.drop_table("content_tags")
    op.drop_index(op.f("ix_content_t_level_id"), table_name="content")
    op.drop_index(op.f("ix_content_topic_id"), table_name="content")
    op.drop_table("content")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_cognito_sub"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_tags_name"), table_name="tags")
    op.drop_table("tags")
    op.drop_index(op.f("ix_t_levels_topic_id"), table_name="t_levels")
    op.drop_table("t_levels")
    op.drop_index(op.f("ix_topics_slug"), table_name="topics")
    op.drop_table("topics")
    sa.Enum(name="contenttype").drop(op.get_bind())
