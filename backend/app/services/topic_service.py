from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.t_level import TLevel
from app.models.topic import Topic
from app.schemas.topic import TLevelResponse, TopicDetailResponse, TopicResponse


async def list_topics(db: AsyncSession) -> list[TopicResponse]:
    result = await db.execute(select(Topic).order_by(Topic.name))
    return [TopicResponse.model_validate(t) for t in result.scalars().all()]


async def get_topic_by_slug(db: AsyncSession, slug: str) -> TopicDetailResponse:
    result = await db.execute(select(Topic).where(Topic.slug == slug))
    topic = result.scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    t_level_result = await db.execute(
        select(TLevel).where(TLevel.topic_id == topic.id).order_by(TLevel.name)
    )
    t_levels = [TLevelResponse.model_validate(tl) for tl in t_level_result.scalars().all()]
    return TopicDetailResponse(
        id=topic.id,
        slug=topic.slug,
        name=topic.name,
        description=topic.description,
        accent_colour=topic.accent_colour,
        t_levels=t_levels,
    )


async def get_t_level(db: AsyncSession, topic_slug: str, t_level_id: int) -> TLevelResponse:
    result = await db.execute(
        select(TLevel)
        .join(Topic, TLevel.topic_id == Topic.id)
        .where(Topic.slug == topic_slug, TLevel.id == t_level_id)
    )
    t_level = result.scalar_one_or_none()
    if t_level is None:
        raise HTTPException(status_code=404, detail="T-Level not found")
    return TLevelResponse.model_validate(t_level)
