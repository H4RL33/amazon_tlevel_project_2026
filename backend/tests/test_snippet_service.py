import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentType
from app.models.library import UserSnippetSave
from app.models.topic import Topic
from app.models.user import User


async def _make_topic(db: AsyncSession) -> Topic:
    topic = Topic(slug="digital", name="Digital", description="D", accent_colour="#000")
    db.add(topic)
    await db.flush()
    return topic


async def _make_snippet(db: AsyncSession, topic_id: int, title: str = "Intro") -> Content:
    snippet = Content(
        title=title,
        content_type=ContentType.article,
        topic_id=topic_id,
        body="Body text",
    )
    db.add(snippet)
    await db.flush()
    return snippet


async def test_save_snippet_creates_save_row(db_session: AsyncSession, current_user: User) -> None:
    topic = await _make_topic(db_session)
    snippet = await _make_snippet(db_session, topic.id)
    await db_session.commit()

    from app.services.snippet_service import save_snippet

    await save_snippet(db_session, snippet.id, current_user)

    saved = await db_session.get(UserSnippetSave, (current_user.id, snippet.id))
    assert saved is not None


async def test_save_snippet_is_idempotent(db_session: AsyncSession, current_user: User) -> None:
    topic = await _make_topic(db_session)
    snippet = await _make_snippet(db_session, topic.id)
    await db_session.commit()

    from app.services.snippet_service import save_snippet

    await save_snippet(db_session, snippet.id, current_user)
    await save_snippet(db_session, snippet.id, current_user)  # second call must not raise

    from sqlalchemy import func, select

    count = (
        await db_session.execute(
            select(func.count()).where(
                UserSnippetSave.user_id == current_user.id,
                UserSnippetSave.content_id == snippet.id,
            )
        )
    ).scalar_one()
    assert count == 1


async def test_unsave_snippet_removes_save_row(
    db_session: AsyncSession, current_user: User
) -> None:
    topic = await _make_topic(db_session)
    snippet = await _make_snippet(db_session, topic.id)
    db_session.add(UserSnippetSave(user_id=current_user.id, content_id=snippet.id))
    await db_session.commit()

    from app.services.snippet_service import unsave_snippet

    await unsave_snippet(db_session, snippet.id, current_user)

    saved = await db_session.get(UserSnippetSave, (current_user.id, snippet.id))
    assert saved is None


async def test_unsave_snippet_is_no_op_when_not_saved(
    db_session: AsyncSession, current_user: User
) -> None:
    topic = await _make_topic(db_session)
    snippet = await _make_snippet(db_session, topic.id)
    await db_session.commit()

    from app.services.snippet_service import unsave_snippet

    await unsave_snippet(db_session, snippet.id, current_user)  # should not raise


async def test_get_snippet_raises_404_for_unknown_id(db_session: AsyncSession) -> None:
    from app.services.snippet_service import get_snippet

    with pytest.raises(HTTPException) as exc_info:
        await get_snippet(db_session, 9999, user=None)
    assert exc_info.value.status_code == 404


async def test_get_snippet_returns_is_saved_false_for_unauthenticated(
    db_session: AsyncSession,
) -> None:
    topic = await _make_topic(db_session)
    snippet = await _make_snippet(db_session, topic.id)
    await db_session.commit()

    from app.services.snippet_service import get_snippet

    result = await get_snippet(db_session, snippet.id, user=None)
    assert result.is_saved is False


async def test_get_snippet_returns_is_saved_false_for_authenticated_user_who_has_not_saved(
    db_session: AsyncSession, current_user: User
) -> None:
    topic = await _make_topic(db_session)
    snippet = await _make_snippet(db_session, topic.id)
    await db_session.commit()

    from app.services.snippet_service import get_snippet

    result = await get_snippet(db_session, snippet.id, user=current_user)
    assert result.is_saved is False


async def test_get_snippet_returns_is_saved_true_when_saved(
    db_session: AsyncSession, current_user: User
) -> None:
    topic = await _make_topic(db_session)
    snippet = await _make_snippet(db_session, topic.id)
    db_session.add(UserSnippetSave(user_id=current_user.id, content_id=snippet.id))
    await db_session.commit()

    from app.services.snippet_service import get_snippet

    result = await get_snippet(db_session, snippet.id, user=current_user)
    assert result.is_saved is True
