from sqlalchemy.ext.asyncio import AsyncSession

from app.models.album import Album
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
