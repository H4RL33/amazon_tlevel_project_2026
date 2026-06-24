from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.album import Album
from app.models.t_level import TLevel
from app.models.topic import Topic
from app.schemas.album import AlbumListResponse


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
