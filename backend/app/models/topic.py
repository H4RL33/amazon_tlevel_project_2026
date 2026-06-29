from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    accent_colour: Mapped[str] = mapped_column(String(7))

    t_levels: Mapped[list["TLevel"]] = relationship(
        back_populates="topic", order_by="TLevel.id"
    )
