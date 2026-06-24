import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.album import Album, AlbumEnrolment, Side, SideContent
from app.models.content import Content, ContentType
from app.models.progress import UserContentProgress
from app.models.t_level import TLevel
from app.models.topic import Topic
from app.models.user import User
from app.services import album_service


async def _make_topic_and_t_level(db: AsyncSession) -> TLevel:
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


async def _make_user(db: AsyncSession) -> User:
    user = User(cognito_sub="sub-1", email="a@example.com", first_name="A", last_name="B")
    db.add(user)
    await db.flush()
    return user


async def test_get_album_detail_authenticated_not_enrolled(db_session: AsyncSession) -> None:
    album = await _make_album_with_side_and_snippet(db_session)
    user = await _make_user(db_session)
    await db_session.commit()

    detail = await album_service.get_album_detail(db_session, album.id, current_user=user)

    assert detail.enrolled is False
    assert detail.progress_pct is None


async def test_get_album_detail_authenticated_enrolled_partial_progress(
    db_session: AsyncSession,
) -> None:
    album = await _make_album_with_side_and_snippet(db_session)
    user = await _make_user(db_session)
    db_session.add(AlbumEnrolment(user_id=user.id, album_id=album.id))
    await db_session.commit()

    detail = await album_service.get_album_detail(db_session, album.id, current_user=user)

    assert detail.enrolled is True
    assert detail.total_count == 1
    assert detail.completed_count == 0
    assert detail.progress_pct == 0


async def test_get_album_detail_authenticated_enrolled_full_progress(
    db_session: AsyncSession,
) -> None:
    album = await _make_album_with_side_and_snippet(db_session)
    user = await _make_user(db_session)
    db_session.add(AlbumEnrolment(user_id=user.id, album_id=album.id))

    await db_session.refresh(album, attribute_names=["sides"])
    await db_session.refresh(album.sides[0], attribute_names=["side_contents"])
    content_id = album.sides[0].side_contents[0].content_id
    db_session.add(UserContentProgress(user_id=user.id, content_id=content_id, progress_pct=100))
    await db_session.commit()

    detail = await album_service.get_album_detail(db_session, album.id, current_user=user)

    assert detail.completed_count == 1
    assert detail.total_count == 1
    assert detail.progress_pct == 100


async def test_enrol_creates_enrolment(db_session: AsyncSession) -> None:
    album = await _make_album_with_side_and_snippet(db_session)
    user = await _make_user(db_session)
    await db_session.commit()

    await album_service.enrol(db_session, album.id, user)

    enrolment = (
        await db_session.execute(
            select(AlbumEnrolment).where(
                AlbumEnrolment.user_id == user.id, AlbumEnrolment.album_id == album.id
            )
        )
    ).scalar_one_or_none()
    assert enrolment is not None


async def test_enrol_twice_is_idempotent(db_session: AsyncSession) -> None:
    album = await _make_album_with_side_and_snippet(db_session)
    user = await _make_user(db_session)
    await db_session.commit()

    await album_service.enrol(db_session, album.id, user)
    await album_service.enrol(db_session, album.id, user)

    count = (
        await db_session.execute(
            select(func.count()).where(
                AlbumEnrolment.user_id == user.id, AlbumEnrolment.album_id == album.id
            )
        )
    ).scalar_one()
    assert count == 1


async def test_enrol_raises_404_for_missing_album(db_session: AsyncSession) -> None:
    from fastapi import HTTPException

    user = await _make_user(db_session)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await album_service.enrol(db_session, album_id=999, user=user)
    assert exc_info.value.status_code == 404


async def test_unenrol_removes_enrolment(db_session: AsyncSession) -> None:
    album = await _make_album_with_side_and_snippet(db_session)
    user = await _make_user(db_session)
    db_session.add(AlbumEnrolment(user_id=user.id, album_id=album.id))
    await db_session.commit()

    await album_service.unenrol(db_session, album.id, user)

    enrolment = (
        await db_session.execute(
            select(AlbumEnrolment).where(
                AlbumEnrolment.user_id == user.id, AlbumEnrolment.album_id == album.id
            )
        )
    ).scalar_one_or_none()
    assert enrolment is None


async def test_unenrol_when_not_enrolled_is_idempotent(db_session: AsyncSession) -> None:
    album = await _make_album_with_side_and_snippet(db_session)
    user = await _make_user(db_session)
    await db_session.commit()

    await album_service.unenrol(db_session, album.id, user)  # should not raise


async def test_add_content_to_side_creates_membership(db_session: AsyncSession) -> None:
    t_level = await _make_topic_and_t_level(db_session)
    album = Album(t_level_id=t_level.id, title="Cloud Computing", description="...", icon="cloud")
    db_session.add(album)
    await db_session.flush()
    side = Side(album_id=album.id, title="Side A", position=0)
    db_session.add(side)
    await db_session.flush()
    content = Content(title="Intro", content_type=ContentType.article, topic_id=t_level.topic_id)
    db_session.add(content)
    await db_session.commit()

    await album_service.add_content_to_side(db_session, side.id, content.id, position=0)

    membership = (
        await db_session.execute(
            select(SideContent).where(
                SideContent.side_id == side.id, SideContent.content_id == content.id
            )
        )
    ).scalar_one_or_none()
    assert membership is not None


async def test_add_content_to_side_can_reuse_snippet_across_albums(
    db_session: AsyncSession,
) -> None:
    t_level = await _make_topic_and_t_level(db_session)
    content = Content(
        title="Shared intro", content_type=ContentType.video, topic_id=t_level.topic_id
    )
    db_session.add(content)
    await db_session.flush()

    album_1 = Album(t_level_id=t_level.id, title="Album 1", description="...", icon="a")
    album_2 = Album(t_level_id=t_level.id, title="Album 2", description="...", icon="b")
    db_session.add_all([album_1, album_2])
    await db_session.flush()
    side_1 = Side(album_id=album_1.id, title="Side A", position=0)
    side_2 = Side(album_id=album_2.id, title="Side A", position=0)
    db_session.add_all([side_1, side_2])
    await db_session.commit()

    await album_service.add_content_to_side(db_session, side_1.id, content.id, position=0)
    await album_service.add_content_to_side(db_session, side_2.id, content.id, position=0)

    count = (
        await db_session.execute(select(func.count()).where(SideContent.content_id == content.id))
    ).scalar_one()
    assert count == 2


async def test_add_content_to_side_moves_within_same_album(db_session: AsyncSession) -> None:
    t_level = await _make_topic_and_t_level(db_session)
    album = Album(t_level_id=t_level.id, title="Cloud Computing", description="...", icon="cloud")
    db_session.add(album)
    await db_session.flush()
    side_a = Side(album_id=album.id, title="Side A", position=0)
    side_b = Side(album_id=album.id, title="Side B", position=1)
    db_session.add_all([side_a, side_b])
    await db_session.flush()
    content = Content(title="Intro", content_type=ContentType.article, topic_id=t_level.topic_id)
    db_session.add(content)
    await db_session.commit()

    await album_service.add_content_to_side(db_session, side_a.id, content.id, position=0)
    await album_service.add_content_to_side(db_session, side_b.id, content.id, position=0)

    count = (
        await db_session.execute(select(func.count()).where(SideContent.content_id == content.id))
    ).scalar_one()
    assert count == 1
    membership = (
        await db_session.execute(select(SideContent).where(SideContent.content_id == content.id))
    ).scalar_one()
    assert membership.side_id == side_b.id
