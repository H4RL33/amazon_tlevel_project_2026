from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class TLevel(Base):
    __tablename__ = "t_levels"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    entry_requirements: Mapped[str] = mapped_column(Text)
    how_to_apply: Mapped[str] = mapped_column(Text)

    topic: Mapped["Topic"] = relationship()
