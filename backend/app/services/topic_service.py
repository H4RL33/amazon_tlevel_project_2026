from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.topic import TLevelResponse, TopicDetailResponse, TopicResponse


async def list_topics(db: AsyncSession) -> list[TopicResponse]:
    """Return all Topic rows ordered by name."""
    raise NotImplementedError


async def get_topic_by_slug(db: AsyncSession, slug: str) -> TopicDetailResponse:
    """
    Return a single Topic with its list of TLevels.
    Raise HTTP 404 if no Topic exists with the given slug.
    """
    raise NotImplementedError


async def get_t_level(
    db: AsyncSession, topic_slug: str, t_level_id: int
) -> TLevelResponse:
    """
    Return a single TLevel by id, scoped to the given topic_slug.
    Raise HTTP 404 if the TLevel does not exist or does not belong to that topic.
    """
    raise NotImplementedError
