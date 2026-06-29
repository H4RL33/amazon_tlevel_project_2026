import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.album import Album
from app.models.t_level import TLevel
from app.models.topic import Topic
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


async def test_get_topic_by_slug_returns_topic_with_t_levels_and_albums(
    db_session: AsyncSession,
) -> None:
    topic = await _make_topic(db_session, slug="digital", name="Digital")
    t_level = await _make_t_level(db_session, topic.id, name="Cloud Computing")
    album = Album(
        t_level_id=t_level.id,
        title="Intro to Cloud",
        description="An intro album",
        icon="cloud",
    )
    db_session.add(album)
    await db_session.commit()

    result = await topic_service.get_topic_by_slug(db_session, "digital")

    assert result.slug == "digital"
    assert result.name == "Digital"
    assert len(result.t_levels) == 1
    assert result.t_levels[0].name == "Cloud Computing"
    assert len(result.t_levels[0].albums) == 1
    assert result.t_levels[0].albums[0].title == "Intro to Cloud"
    assert result.t_levels[0].albums[0].topic_id == topic.id


async def test_get_topic_by_slug_returns_empty_t_levels_when_none(
    db_session: AsyncSession,
) -> None:
    await _make_topic(db_session, slug="finance", name="Finance")
    await db_session.commit()

    result = await topic_service.get_topic_by_slug(db_session, "finance")

    assert result.slug == "finance"
    assert result.t_levels == []


async def test_get_topic_by_slug_raises_404_for_unknown_slug(db_session: AsyncSession) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await topic_service.get_topic_by_slug(db_session, "nonexistent")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Topic not found"
