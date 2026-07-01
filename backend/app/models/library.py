from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class UserSnippetSave(Base):
    __tablename__ = "user_snippet_saves"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    content_id: Mapped[int] = mapped_column(
        ForeignKey("content.id", ondelete="CASCADE"), primary_key=True
    )
    saved_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="saved_snippets")
    content: Mapped[Content] = relationship()


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    # No User.chat_sessions relationship: sessions are always accessed via
    # chat_service.list_sessions (filtered + paginated), never via user.chat_sessions,
    # so an ORM collection would just be dead weight. Intentional.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # First ~60 chars of the first user message, truncated. Set once at creation
    # of the first message, never regenerated (no extra LLM call just to title a chat).
    title: Mapped[str] = mapped_column(String(60), default="New chat")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.id"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(10))  # "user" | "mentor"
    text: Mapped[str] = mapped_column(Text)
    sources: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)  # mentor messages only
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session: Mapped[ChatSession] = relationship(back_populates="messages")
