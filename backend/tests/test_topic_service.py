import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.topic import Topic
from app.models.t_level import TLevel
from app.services import topic_service


async def _make_topic(db: AsyncSession, slug: str = "digital", name: str = "Digital") -> Topic:
    topic = Topic(slug=slug, name=name, description="Desc", accent_colour="#0066CC")
    db.add(topic)
    await db.flush()
    return topic


async def _make_t_level(db: AsyncSession, topic_id: int, name: str = "Cloud Computing") -> TLevel:
    t_level = TLevel(
        topic_id=topic_id,
        name=name,
        entry_requirements="5 GCSEs",
        how_to_apply="Apply online",
    )
    db.add(t_level)
    await db.flush()
    return t_level


async def test_list_topics_returns_all_topics_ordered_by_name(db_session: AsyncSession) -> None:
    await _make_topic(db_session, slug="digital", name="Digital")
    await _make_topic(db_session, slug="business", name="Business")
    await db_session.commit()

    result = await topic_service.list_topics(db_session)

    assert len(result) == 2
    assert result[0].name == "Business"
    assert result[1].name == "Digital"


async def test_list_topics_returns_empty_list_when_no_topics(db_session: AsyncSession) -> None:
    result = await topic_service.list_topics(db_session)
    assert result == []
