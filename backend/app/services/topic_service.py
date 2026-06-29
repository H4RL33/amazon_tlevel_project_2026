from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.t_level import TLevel
from app.models.topic import Topic
from app.schemas.album import AlbumListResponse
from app.schemas.topic import TLevelResponse, TLevelWithAlbumsResponse, TopicDetailResponse, TopicResponse


async def list_topics(db: AsyncSession) -> list[TopicResponse]:
    """Return all Topic rows ordered by name."""
    result = await db.execute(select(Topic).order_by(Topic.name))
    return [TopicResponse.model_validate(t) for t in result.scalars().all()]


async def get_topic_by_slug(db: AsyncSession, slug: str) -> TopicDetailResponse:
    """
    Return a single Topic with its list of TLevels (each with Albums).
    Raise HTTP 404 if no Topic exists with the given slug.
    """
    stmt = (
        select(Topic)
        .where(Topic.slug == slug)
        .options(selectinload(Topic.t_levels).selectinload(TLevel.albums))
    )
    result = await db.execute(stmt)
    topic = result.scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    return TopicDetailResponse(
        id=topic.id,
        slug=topic.slug,
        name=topic.name,
        description=topic.description,
        accent_colour=topic.accent_colour,
        t_levels=[
            TLevelWithAlbumsResponse(
                id=t.id,
                topic_id=t.topic_id,
                name=t.name,
                entry_requirements=t.entry_requirements,
                how_to_apply=t.how_to_apply,
                albums=[
                    AlbumListResponse(
                        id=a.id,
                        t_level_id=a.t_level_id,
                        topic_id=topic.id,
                        title=a.title,
                        description=a.description,
                        icon=a.icon,
                    )
                    for a in t.albums
                ],
            )
            for t in topic.t_levels
        ],
    )


async def get_t_level(db: AsyncSession, topic_slug: str, t_level_id: int) -> TLevelResponse:
    """
    Return a single TLevel by id, scoped to the given topic_slug.
    Raise HTTP 404 if the TLevel does not exist or does not belong to that topic.
    """
    stmt = (
        select(TLevel)
        .join(Topic, TLevel.topic_id == Topic.id)
        .where(TLevel.id == t_level_id, Topic.slug == topic_slug)
    )
    result = await db.execute(stmt)
    t_level = result.scalar_one_or_none()
    if t_level is None:
        raise HTTPException(status_code=404, detail="T-Level not found")
    return TLevelResponse.model_validate(t_level)
