from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.album import Album, Side, SideContent
from app.models.content import Content, ContentType
from app.models.t_level import TLevel
from app.models.topic import Topic
from app.models.user import User


async def _make_album_with_side_and_snippet(db: AsyncSession) -> Album:
    topic = Topic(
        slug="digital-production",
        name="Digital Production",
        description="...",
        accent_colour="#0066CC",
    )
    db.add(topic)
    await db.flush()
    t_level = TLevel(
        topic_id=topic.id,
        name="Digital Production",
        entry_requirements="...",
        how_to_apply="...",
    )
    db.add(t_level)
    await db.flush()
    album = Album(t_level_id=t_level.id, title="Cloud Computing", description="...", icon="cloud")
    db.add(album)
    await db.flush()
    side = Side(album_id=album.id, title="Side A", position=0)
    db.add(side)
    await db.flush()
    content = Content(
        title="What is the cloud?", content_type=ContentType.article, topic_id=topic.id
    )
    db.add(content)
    await db.flush()
    db.add(SideContent(side_id=side.id, content_id=content.id, position=0))
    await db.commit()
    return album


async def test_list_albums(client: AsyncClient, db_session: AsyncSession) -> None:
    await _make_album_with_side_and_snippet(db_session)

    response = await client.get("/albums/")

    assert response.status_code == 200
    assert response.json()[0]["title"] == "Cloud Computing"


async def test_get_album_detail_anonymous_omits_progress_fields(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    album = await _make_album_with_side_and_snippet(db_session)

    response = await client.get(f"/albums/{album.id}")

    assert response.status_code == 200
    body = response.json()
    assert "enrolled" not in body
    assert "progress_pct" not in body
    assert body["sides"][0]["snippets"][0]["title"] == "What is the cloud?"


async def test_get_album_detail_authenticated_includes_enrolled_field(
    authenticated_client: AsyncClient, db_session: AsyncSession
) -> None:
    album = await _make_album_with_side_and_snippet(db_session)

    response = await authenticated_client.get(f"/albums/{album.id}")

    assert response.status_code == 200
    assert response.json()["enrolled"] is False


async def test_get_album_detail_404(client: AsyncClient) -> None:
    response = await client.get("/albums/999")
    assert response.status_code == 404


async def test_enrol_then_unenrol(
    authenticated_client: AsyncClient, db_session: AsyncSession, current_user: User
) -> None:
    album = await _make_album_with_side_and_snippet(db_session)

    enrol_response = await authenticated_client.post(f"/albums/{album.id}/enrol")
    assert enrol_response.status_code == 204

    detail_response = await authenticated_client.get(f"/albums/{album.id}")
    assert detail_response.json()["enrolled"] is True

    unenrol_response = await authenticated_client.delete(f"/albums/{album.id}/enrol")
    assert unenrol_response.status_code == 204

    detail_response_2 = await authenticated_client.get(f"/albums/{album.id}")
    assert detail_response_2.json()["enrolled"] is False
