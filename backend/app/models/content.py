import enum
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class ContentType(enum.StrEnum):
    article = "article"
    audio = "audio"
    video = "video"


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)


class ContentTag(Base):
    __tablename__ = "content_tags"

    content_id: Mapped[int] = mapped_column(ForeignKey("content.id"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), primary_key=True)

    tag: Mapped["Tag"] = relationship()


class Content(Base):
    __tablename__ = "content"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str | None] = mapped_column(Text)
    content_type: Mapped[ContentType] = mapped_column(Enum(ContentType))
    media_url: Mapped[str | None] = mapped_column(String(500))
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    t_level_id: Mapped[int | None] = mapped_column(ForeignKey("t_levels.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)
    embedding_generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    topic: Mapped["Topic"] = relationship()
    t_level: Mapped["TLevel | None"] = relationship()
    content_tags: Mapped[list["ContentTag"]] = relationship(cascade="all, delete-orphan")
