import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.album import Album, AlbumEnrolment
from app.models.content import Content, ContentType
from app.models.library import UserSnippetSave
from app.models.t_level import TLevel
from app.models.topic import Topic
from app.models.user import User


async def _make_topic(db: AsyncSession) -> Topic:
    topic = Topic(slug="digital", name="Digital", description="D", accent_colour="#000")
    db.add(topic)
    await db.flush()
    return topic


async def _make_t_level(db: AsyncSession, topic_id: int) -> TLevel:
    t_level = TLevel(
        topic_id=topic_id,
        name="Cloud T-Level",
        entry_requirements="5 GCSEs",
        how_to_apply="Apply online",
    )
    db.add(t_level)
    await db.flush()
    return t_level


async def _make_album(db: AsyncSession, t_level_id: int, title: str = "Cloud Album") -> Album:
    album = Album(t_level_id=t_level_id, title=title, description="Desc", icon="cloud")
    db.add(album)
    await db.flush()
    return album


async def _make_snippet(db: AsyncSession, topic_id: int, title: str = "Intro") -> Content:
    snippet = Content(title=title, content_type=ContentType.article, topic_id=topic_id, body="B")
    db.add(snippet)
    await db.flush()
    return snippet


async def test_get_library_returns_enrolled_albums(
    db_session: AsyncSession, current_user: User
) -> None:
    topic = await _make_topic(db_session)
    t_level = await _make_t_level(db_session, topic.id)
    album = await _make_album(db_session, t_level.id)
    db_session.add(AlbumEnrolment(user_id=current_user.id, album_id=album.id))
    await db_session.commit()

    from app.services.library_service import get_library
    result = await get_library(db_session, current_user)

    assert len(result.enrolled_albums) == 1
    assert result.enrolled_albums[0].id == album.id


async def test_get_library_returns_saved_snippets(
    db_session: AsyncSession, current_user: User
) -> None:
    topic = await _make_topic(db_session)
    snippet = await _make_snippet(db_session, topic.id)
    db_session.add(UserSnippetSave(user_id=current_user.id, content_id=snippet.id))
    await db_session.commit()

    from app.services.library_service import get_library
    result = await get_library(db_session, current_user)

    assert len(result.saved_snippets) == 1
    assert result.saved_snippets[0].id == snippet.id


async def test_get_library_returns_empty_when_nothing_saved(
    db_session: AsyncSession, current_user: User
) -> None:
    from app.services.library_service import get_library
    result = await get_library(db_session, current_user)

    assert result.enrolled_albums == []
    assert result.saved_snippets == []


def test_apply_boost_elevates_saved_content():
    from unittest.mock import MagicMock
    from app.services.library_service import _apply_boost

    row_saved = MagicMock()
    row_saved.id = 1
    row_saved.title = "Cloud Basics"
    row_saved.content_type = ContentType.article
    row_saved.album_title = "Cloud T-Level"
    row_saved.distance = 0.2  # similarity = 0.8, boosted = 0.8 * 1.4 = 1.12

    row_unsaved = MagicMock()
    row_unsaved.id = 2
    row_unsaved.title = "Networking"
    row_unsaved.content_type = ContentType.article
    row_unsaved.album_title = None
    row_unsaved.distance = 0.15  # similarity = 0.85 (higher raw, but not boosted)

    results = _apply_boost([row_saved, row_unsaved], boosted_ids={1}, saved_ids={1})

    assert results[0].content_id == 1
    assert results[0].is_saved is True
    assert results[1].content_id == 2
    assert results[1].is_saved is False


def test_apply_boost_deduplicates_by_content_id():
    from unittest.mock import MagicMock
    from app.services.library_service import _apply_boost

    row1 = MagicMock()
    row1.id = 1
    row1.title = "A"
    row1.content_type = ContentType.article
    row1.album_title = "Album A"
    row1.distance = 0.1

    row1_dup = MagicMock()
    row1_dup.id = 1  # duplicate
    row1_dup.title = "A"
    row1_dup.content_type = ContentType.article
    row1_dup.album_title = "Album B"
    row1_dup.distance = 0.2

    results = _apply_boost([row1, row1_dup], boosted_ids=set(), saved_ids=set())
    assert len(results) == 1
    assert results[0].content_id == 1


def test_apply_boost_limits_to_10_results():
    from unittest.mock import MagicMock
    from app.services.library_service import _apply_boost

    rows = []
    for i in range(15):
        row = MagicMock()
        row.id = i
        row.title = f"Snippet {i}"
        row.content_type = ContentType.article
        row.album_title = None
        row.distance = i * 0.05
        rows.append(row)

    results = _apply_boost(rows, boosted_ids=set(), saved_ids=set())
    assert len(results) == 10


async def test_mentor_query_returns_reply_and_sources(
    db_session: AsyncSession, current_user: User
) -> None:
    import json
    from unittest.mock import MagicMock, patch

    topic = await _make_topic(db_session)
    snippet = await _make_snippet(db_session, topic.id, title="Cloud Networking")
    await db_session.commit()

    fake_embed = [0.1] * 1536
    fake_gen_body = json.dumps({
        "results": [{"outputText": "Networking connects computers.", "completionReason": "FINISH"}]
    }).encode()
    mock_gen_response = {"body": MagicMock(read=MagicMock(return_value=fake_gen_body))}

    with (
        patch("app.services.library_service.embed_text", return_value=fake_embed),
        patch("app.services.library_service._fetch_mentor_context") as mock_ctx,
        patch("app.services.library_service.boto3.client") as mock_bedrock,
    ):
        mock_ctx.return_value = [
            {"content_id": snippet.id, "title": snippet.title, "body": snippet.body or ""}
        ]
        mock_bedrock.return_value.invoke_model.return_value = mock_gen_response

        from app.services.library_service import mentor_query
        result = await mentor_query(db_session, "What is networking?", current_user)

    assert "Networking" in result.reply
    assert len(result.sources) >= 1
    assert result.sources[0].title == "Cloud Networking"
