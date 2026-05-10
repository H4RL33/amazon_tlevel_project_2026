from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class UserContentProgress(Base):
    __tablename__ = "user_content_progress"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("content.id"), primary_key=True)
    last_viewed_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    progress_pct: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship(back_populates="progress")
    content: Mapped["Content"] = relationship()
