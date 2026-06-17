from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cognito_sub: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    topic_interests: Mapped[list["UserTopicInterest"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    progress: Mapped[list["UserContentProgress"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserTopicInterest(Base):
    __tablename__ = "user_topic_interests"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), primary_key=True)

    user: Mapped["User"] = relationship(back_populates="topic_interests")
    topic: Mapped["Topic"] = relationship()
