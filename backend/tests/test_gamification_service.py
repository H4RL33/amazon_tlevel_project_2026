from sqlalchemy.ext.asyncio import AsyncSession

from app.models.album import Album, AlbumEnrolment, Side, SideContent
from app.models.content import Content, ContentType
from app.models.progress import UserContentProgress
from app.models.t_level import TLevel
from app.models.topic import Topic
from app.models.user import User
from app.services import gamification_service
from app.services.gamification_service import XP_ALBUM_COMPLETION_BONUS, XP_PER_SNIPPET


async def _make_topic_and_t_level(db: AsyncSession) -> TLevel:
    topic = Topic(slug="digital", name="Digital", description="...", accent_colour="#0066CC")
    db.add(topic)
    await db.flush()
    t_level = TLevel(
        topic_id=topic.id, name="Digital", entry_requirements="...", how_to_apply="..."
    )
    db.add(t_level)
    await db.flush()
    return t_level


async def _make_snippet(db: AsyncSession, topic_id: int, title: str = "Snippet") -> Content:
    snippet = Content(title=title, content_type=ContentType.article, topic_id=topic_id, body="B")
    db.add(snippet)
    await db.flush()
    return snippet


async def _make_album_with_snippets(
    db: AsyncSession, t_level_id: int, snippets: list[Content]
) -> Album:
    album = Album(t_level_id=t_level_id, title="Album", description="D", icon="cloud")
    db.add(album)
    await db.flush()
    side = Side(album_id=album.id, title="Side 1", position=1)
    db.add(side)
    await db.flush()
    for i, snippet in enumerate(snippets):
        db.add(SideContent(side_id=side.id, content_id=snippet.id, position=i))
    await db.flush()
    return album


async def test_get_stats_returns_zero_for_new_user(
    db_session: AsyncSession, current_user: User
) -> None:
    result = await gamification_service.get_stats(db_session, current_user)
    assert result.total_xp == 0
    assert result.level == 1
    assert result.snippets_completed == 0
    assert result.albums_completed == 0


async def test_get_stats_counts_completed_snippets_and_awards_xp(
    db_session: AsyncSession, current_user: User
) -> None:
    t_level = await _make_topic_and_t_level(db_session)
    s1 = await _make_snippet(db_session, t_level.topic_id, "S1")
    s2 = await _make_snippet(db_session, t_level.topic_id, "S2")
    db_session.add(UserContentProgress(user_id=current_user.id, content_id=s1.id, progress_pct=100))
    db_session.add(UserContentProgress(user_id=current_user.id, content_id=s2.id, progress_pct=50))
    await db_session.commit()

    result = await gamification_service.get_stats(db_session, current_user)

    assert result.snippets_completed == 1
    assert result.total_xp == XP_PER_SNIPPET
    assert result.albums_completed == 0


async def test_get_stats_awards_album_completion_bonus_when_all_snippets_done(
    db_session: AsyncSession, current_user: User
) -> None:
    t_level = await _make_topic_and_t_level(db_session)
    s1 = await _make_snippet(db_session, t_level.topic_id, "S1")
    s2 = await _make_snippet(db_session, t_level.topic_id, "S2")
    album = await _make_album_with_snippets(db_session, t_level.id, [s1, s2])
    db_session.add(AlbumEnrolment(user_id=current_user.id, album_id=album.id))
    db_session.add(UserContentProgress(user_id=current_user.id, content_id=s1.id, progress_pct=100))
    db_session.add(UserContentProgress(user_id=current_user.id, content_id=s2.id, progress_pct=100))
    await db_session.commit()

    result = await gamification_service.get_stats(db_session, current_user)

    assert result.snippets_completed == 2
    assert result.albums_completed == 1
    assert result.total_xp == 2 * XP_PER_SNIPPET + XP_ALBUM_COMPLETION_BONUS


async def test_get_stats_does_not_award_album_bonus_when_partially_complete(
    db_session: AsyncSession, current_user: User
) -> None:
    t_level = await _make_topic_and_t_level(db_session)
    s1 = await _make_snippet(db_session, t_level.topic_id, "S1")
    s2 = await _make_snippet(db_session, t_level.topic_id, "S2")
    album = await _make_album_with_snippets(db_session, t_level.id, [s1, s2])
    db_session.add(AlbumEnrolment(user_id=current_user.id, album_id=album.id))
    db_session.add(UserContentProgress(user_id=current_user.id, content_id=s1.id, progress_pct=100))
    await db_session.commit()

    result = await gamification_service.get_stats(db_session, current_user)

    assert result.albums_completed == 0


async def test_get_stats_ignores_unenrolled_albums_even_if_snippets_completed(
    db_session: AsyncSession, current_user: User
) -> None:
    t_level = await _make_topic_and_t_level(db_session)
    s1 = await _make_snippet(db_session, t_level.topic_id, "S1")
    await _make_album_with_snippets(db_session, t_level.id, [s1])
    db_session.add(UserContentProgress(user_id=current_user.id, content_id=s1.id, progress_pct=100))
    await db_session.commit()

    result = await gamification_service.get_stats(db_session, current_user)

    assert result.albums_completed == 0
    assert result.snippets_completed == 1


async def test_get_stats_level_increases_once_xp_crosses_threshold(
    db_session: AsyncSession, current_user: User
) -> None:
    from app.services.gamification_service import XP_PER_LEVEL

    t_level = await _make_topic_and_t_level(db_session)
    snippets_needed = (XP_PER_LEVEL // XP_PER_SNIPPET) + 1
    for i in range(snippets_needed):
        snippet = await _make_snippet(db_session, t_level.topic_id, f"S{i}")
        db_session.add(
            UserContentProgress(user_id=current_user.id, content_id=snippet.id, progress_pct=100)
        )
    await db_session.commit()

    result = await gamification_service.get_stats(db_session, current_user)

    assert result.total_xp > XP_PER_LEVEL
    assert result.level == result.total_xp // XP_PER_LEVEL + 1
    assert result.level >= 2
