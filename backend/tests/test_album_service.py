import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.album import Album, Side, SideContent
from app.models.content import Content, ContentType
from app.models.t_level import TLevel
from app.models.topic import Topic
from app.services import album_service


async def _make_topic_and_t_level(db: AsyncSession) -> TLevel:
    topic = Topic(
        slug="digital-production", name="Digital Production", description="...", accent_colour="#0066CC"
    )
    db.add(topic)
    await db.flush()
    t_level = TLevel(
        topic_id=topic.id,
        name="Digital Production, Design and Development",
        entry_requirements="...",
        how_to_apply="...",
    )
    db.add(t_level)
    await db.flush()
    return t_level


async def test_list_albums_returns_all_albums_by_default(db_session: AsyncSession) -> None:
    t_level = await _make_topic_and_t_level(db_session)
    db_session.add(
        Album(t_level_id=t_level.id, title="Cloud Computing", description="...", icon="cloud")
    )
    await db_session.commit()

    result = await album_service.list_albums(db_session)

    assert len(result) == 1
    assert result[0].title == "Cloud Computing"


async def test_list_albums_filters_by_t_level_id(db_session: AsyncSession) -> None:
    t_level = await _make_topic_and_t_level(db_session)
    db_session.add(
        Album(t_level_id=t_level.id, title="Cloud Computing", description="...", icon="cloud")
    )
    await db_session.commit()

    result = await album_service.list_albums(db_session, t_level_id=t_level.id + 1)

    assert result == []


async def _make_album_with_side_and_snippet(db: AsyncSession) -> Album:
    t_level = await _make_topic_and_t_level(db)
    album = Album(t_level_id=t_level.id, title="Cloud Computing", description="...", icon="cloud")
    db.add(album)
    await db.flush()

    side = Side(album_id=album.id, title="Side A", position=0)
    db.add(side)
    await db.flush()

    content = Content(
        title="What is the cloud?",
        content_type=ContentType.article,
        topic_id=t_level.topic_id,
    )
    db.add(content)
    await db.flush()

    db.add(SideContent(side_id=side.id, content_id=content.id, position=0))
    await db.commit()
    return album


async def test_get_album_detail_returns_404_for_missing_album(db_session: AsyncSession) -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await album_service.get_album_detail(db_session, album_id=999, current_user=None)
    assert exc_info.value.status_code == 404


async def test_get_album_detail_anonymous_includes_sides_but_no_progress(
    db_session: AsyncSession,
) -> None:
    album = await _make_album_with_side_and_snippet(db_session)

    detail = await album_service.get_album_detail(db_session, album.id, current_user=None)

    assert detail.title == "Cloud Computing"
    assert len(detail.sides) == 1
    assert detail.sides[0].snippets[0].title == "What is the cloud?"
    assert detail.enrolled is None
    assert detail.progress_pct is None
