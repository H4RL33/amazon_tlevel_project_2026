from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.album import Album, AlbumEnrolment, Side, SideContent
from app.models.progress import UserContentProgress
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
    enrolment_stmt = select(AlbumEnrolment).where(
        AlbumEnrolment.user_id == current_user.id,
        AlbumEnrolment.album_id == album.id,
    )
    enrolment = (await db.execute(enrolment_stmt)).scalar_one_or_none()
    detail.enrolled = enrolment is not None

    if enrolment is None:
        return detail

    content_ids = [sc.content_id for side in album.sides for sc in side.side_contents]
    total_count = len(content_ids)
    detail.total_count = total_count

    if total_count == 0:
        detail.completed_count = 0
        detail.progress_pct = 0
        return detail

    completed_stmt = select(func.count()).where(
        UserContentProgress.user_id == current_user.id,
        UserContentProgress.content_id.in_(content_ids),
        UserContentProgress.progress_pct == 100,
    )
    completed_count = (await db.execute(completed_stmt)).scalar_one()
    detail.completed_count = completed_count
    detail.progress_pct = round(completed_count / total_count * 100)
    return detail


async def enrol(db: AsyncSession, album_id: int, user: User) -> None:
    album = (await db.execute(select(Album).where(Album.id == album_id))).scalar_one_or_none()
    if album is None:
        raise HTTPException(status_code=404, detail="Album not found")

    existing = (
        await db.execute(
            select(AlbumEnrolment).where(
                AlbumEnrolment.user_id == user.id, AlbumEnrolment.album_id == album_id
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return

    db.add(AlbumEnrolment(user_id=user.id, album_id=album_id))
    await db.commit()


async def unenrol(db: AsyncSession, album_id: int, user: User) -> None:
    await db.execute(
        delete(AlbumEnrolment).where(
            AlbumEnrolment.user_id == user.id, AlbumEnrolment.album_id == album_id
        )
    )
    await db.commit()


async def add_content_to_side(
    db: AsyncSession,
    side_id: int,
    content_id: int,
    position: int,
) -> None:
    side = (await db.execute(select(Side).where(Side.id == side_id))).scalar_one_or_none()
    if side is None:
        raise HTTPException(status_code=404, detail="Side not found")

    sibling_side_ids = (
        (await db.execute(select(Side.id).where(Side.album_id == side.album_id))).scalars().all()
    )

    await db.execute(
        delete(SideContent).where(
            SideContent.content_id == content_id,
            SideContent.side_id.in_(sibling_side_ids),
        )
    )
    db.add(SideContent(side_id=side_id, content_id=content_id, position=position))
    await db.commit()
