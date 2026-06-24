from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class Album(Base):
    __tablename__ = "albums"

    id: Mapped[int] = mapped_column(primary_key=True)
    t_level_id: Mapped[int] = mapped_column(ForeignKey("t_levels.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    icon: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    t_level: Mapped["TLevel"] = relationship()
    sides: Mapped[list["Side"]] = relationship(
        back_populates="album",
        order_by="Side.position",
        cascade="all, delete-orphan",
    )


class Side(Base):
    __tablename__ = "sides"

    id: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int] = mapped_column(ForeignKey("albums.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    position: Mapped[int] = mapped_column(Integer)

    album: Mapped["Album"] = relationship(back_populates="sides")
    side_contents: Mapped[list["SideContent"]] = relationship(
        back_populates="side",
        order_by="SideContent.position",
        cascade="all, delete-orphan",
    )


class SideContent(Base):
    __tablename__ = "side_content"

    side_id: Mapped[int] = mapped_column(ForeignKey("sides.id"), primary_key=True)
    content_id: Mapped[int] = mapped_column(
        ForeignKey("content.id"), primary_key=True, index=True
    )
    position: Mapped[int] = mapped_column(Integer)

    side: Mapped["Side"] = relationship(back_populates="side_contents")
    content: Mapped["Content"] = relationship()


class AlbumEnrolment(Base):
    __tablename__ = "album_enrolments"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    album_id: Mapped[int] = mapped_column(ForeignKey("albums.id"), primary_key=True)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship()
    album: Mapped["Album"] = relationship()
