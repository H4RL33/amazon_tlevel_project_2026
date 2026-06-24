from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.album import Album, AlbumEnrolment, Side, SideContent  # noqa: F401
from app.models.progress import UserContentProgress  # noqa: F401
from app.models.t_level import TLevel
from app.models.topic import Topic
from app.models.user import User
from app.schemas.album import (
    AlbumDetailResponse,
    AlbumListResponse,
    SideResponse,
    SnippetSummaryResponse,
)


async def list_albums(
    db: AsyncSession,
    t_level_id: int | None = None,
    topic: str | None = None,
) -> list[AlbumListResponse]:
    stmt = select(Album)
    if t_level_id is not None:
        stmt = stmt.where(Album.t_level_id == t_level_id)
    if topic is not None:
        stmt = (
            stmt.join(TLevel, Album.t_level_id == TLevel.id)
            .join(Topic, TLevel.topic_id == Topic.id)
            .where(Topic.slug == topic)
        )

    result = await db.execute(stmt)
    albums = result.scalars().all()
    return [AlbumListResponse.model_validate(album) for album in albums]


async def get_album_detail(
    db: AsyncSession,
    album_id: int,
    current_user: User | None,
) -> AlbumDetailResponse:
    stmt = (
        select(Album)
        .where(Album.id == album_id)
        .options(
            selectinload(Album.sides)
            .selectinload(Side.side_contents)
            .selectinload(SideContent.content)
        )
    )
    album = (await db.execute(stmt)).scalar_one_or_none()
    if album is None:
        raise HTTPException(status_code=404, detail="Album not found")

    sides = [
        SideResponse(
            id=side.id,
            title=side.title,
            position=side.position,
            snippets=[
                SnippetSummaryResponse.model_validate(sc.content)
                for sc in sorted(side.side_contents, key=lambda sc: sc.position)
            ],
        )
        for side in sorted(album.sides, key=lambda s: s.position)
    ]

    detail = AlbumDetailResponse(
        id=album.id,
        t_level_id=album.t_level_id,
        title=album.title,
        description=album.description,
        icon=album.icon,
        sides=sides,
    )

    if current_user is None:
        return detail

    return await _add_progress_fields(db, detail, album, current_user)


async def _add_progress_fields(
    db: AsyncSession,
    detail: AlbumDetailResponse,
    album: Album,
    current_user: User,
) -> AlbumDetailResponse:
    raise NotImplementedError
