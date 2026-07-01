from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.album import AlbumEnrolment, Side, SideContent
from app.models.progress import UserContentProgress
from app.models.user import User
from app.schemas.gamification import UserStatsResponse

XP_PER_SNIPPET = 10
XP_ALBUM_COMPLETION_BONUS = 50
XP_PER_LEVEL = 100


async def _count_completed_snippets(db: AsyncSession, user: User) -> int:
    result = await db.execute(
        select(func.count()).where(
            UserContentProgress.user_id == user.id,
            UserContentProgress.progress_pct == 100,
        )
    )
    return result.scalar_one()


async def _count_completed_albums(db: AsyncSession, user: User) -> int:
    """
    An enrolled Album counts as completed once every Snippet across all its
    Sides has progress_pct == 100 for this user. An Album with no Snippets
    yet never counts — nothing to complete.
    """
    enrolled_album_ids = (
        (
            await db.execute(
                select(AlbumEnrolment.album_id).where(AlbumEnrolment.user_id == user.id)
            )
        )
        .scalars()
        .all()
    )
    if not enrolled_album_ids:
        return 0

    completed_ids = set(
        (
            await db.execute(
                select(UserContentProgress.content_id).where(
                    UserContentProgress.user_id == user.id,
                    UserContentProgress.progress_pct == 100,
                )
            )
        )
        .scalars()
        .all()
    )

    completed_albums = 0
    for album_id in enrolled_album_ids:
        content_ids = (
            (
                await db.execute(
                    select(SideContent.content_id)
                    .join(Side, Side.id == SideContent.side_id)
                    .where(Side.album_id == album_id)
                )
            )
            .scalars()
            .all()
        )
        if content_ids and all(cid in completed_ids for cid in content_ids):
            completed_albums += 1
    return completed_albums


async def get_stats(db: AsyncSession, user: User) -> UserStatsResponse:
    """
    XP/level are always computed from existing UserContentProgress/
    AlbumEnrolment rows, never stored — consistent with how Album progress
    is computed elsewhere, so there's no denormalised state to keep in sync.
    """
    snippets_completed = await _count_completed_snippets(db, user)
    albums_completed = await _count_completed_albums(db, user)
    total_xp = snippets_completed * XP_PER_SNIPPET + albums_completed * XP_ALBUM_COMPLETION_BONUS
    level = total_xp // XP_PER_LEVEL + 1
    return UserStatsResponse(
        total_xp=total_xp,
        level=level,
        snippets_completed=snippets_completed,
        albums_completed=albums_completed,
    )
