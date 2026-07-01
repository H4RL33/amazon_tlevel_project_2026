import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def test_create_session_returns_new_session_with_default_title(
    db_session: AsyncSession, current_user: User
) -> None:
    from app.services.chat_service import create_session

    session = await create_session(db_session, current_user)

    assert session.id is not None
    assert session.title == "New chat"
    assert session.user_id == current_user.id


async def test_list_sessions_returns_only_current_users_sessions_newest_first(
    db_session: AsyncSession, current_user: User
) -> None:
    from app.models.library import ChatSession
    from app.services.chat_service import list_sessions

    other_user = User(cognito_sub="other", email="other@example.com", first_name="O", last_name="U")
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    s1 = ChatSession(user_id=current_user.id, title="First")
    db_session.add(s1)
    await db_session.commit()
    await db_session.refresh(s1)

    s2 = ChatSession(user_id=current_user.id, title="Second")
    db_session.add(s2)
    await db_session.commit()
    await db_session.refresh(s2)

    db_session.add(ChatSession(user_id=other_user.id, title="Not mine"))
    await db_session.commit()

    # Force s2's updated_at to be later so ordering is deterministic regardless
    # of how fast these commits ran within the same clock tick. ChatSession.updated_at
    # is a naive DateTime column, so this must be a naive datetime too (asyncpg
    # rejects tz-aware values for "timestamp without time zone" columns).
    import datetime

    s2.updated_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=10)
    await db_session.commit()

    sessions = await list_sessions(db_session, current_user)

    assert [s.title for s in sessions] == ["Second", "First"]


async def test_get_session_or_404_raises_for_other_users_session(
    db_session: AsyncSession, current_user: User
) -> None:
    from fastapi import HTTPException

    from app.models.library import ChatSession
    from app.services.chat_service import get_session_or_404

    other_user = User(cognito_sub="other2", email="other2@example.com", first_name="O", last_name="U")
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    session = ChatSession(user_id=other_user.id, title="Not mine")
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    with pytest.raises(HTTPException) as exc_info:
        await get_session_or_404(db_session, session.id, current_user)
    assert exc_info.value.status_code == 404


async def test_get_session_detail_includes_ordered_messages(
    db_session: AsyncSession, current_user: User
) -> None:
    from app.models.library import ChatMessage, ChatSession
    from app.services.chat_service import get_session_detail

    session = ChatSession(user_id=current_user.id, title="Hi")
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    db_session.add_all(
        [
            ChatMessage(session_id=session.id, role="user", text="Hi"),
            ChatMessage(session_id=session.id, role="mentor", text="Hello!"),
        ]
    )
    await db_session.commit()

    detail = await get_session_detail(db_session, session, current_user)

    assert detail.title == "Hi"
    assert [m.text for m in detail.messages] == ["Hi", "Hello!"]


async def test_stream_mentor_reply_persists_user_and_mentor_messages(
    db_session: AsyncSession, current_user: User
) -> None:
    from unittest.mock import patch

    from app.models.library import ChatMessage
    from app.services.chat_service import create_session, stream_mentor_reply

    session = await create_session(db_session, current_user)

    def fake_event_stream():
        yield {"chunk": {"bytes": b'{"contentBlockDelta": {"delta": {"text": "Hello "}}}'}}
        yield {"chunk": {"bytes": b'{"contentBlockDelta": {"delta": {"text": "there."}}}'}}
        yield {"chunk": {"bytes": b'{"messageStop": {}}'}}

    mock_stream_response = {"body": fake_event_stream()}

    with (
        patch("app.services.chat_service.embed_text", return_value=[0.1] * 1024),
        patch("app.services.chat_service._fetch_mentor_context", return_value=[]),
        patch("app.services.chat_service.get_bedrock_client") as mock_get_client,
    ):
        mock_get_client.return_value.invoke_model_with_response_stream.return_value = (
            mock_stream_response
        )

        deltas = []
        async for delta in stream_mentor_reply(db_session, session, "Hi", current_user):
            deltas.append(delta)

    assert deltas == ["Hello ", "there."]

    from sqlalchemy import select

    result = await db_session.execute(
        select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.id)
    )
    messages = result.scalars().all()
    assert [m.role for m in messages] == ["user", "mentor"]
    assert messages[0].text == "Hi"
    assert messages[1].text == "Hello there."

    await db_session.refresh(session)
    assert session.title == "Hi"


async def test_stream_mentor_reply_sets_title_only_on_first_message(
    db_session: AsyncSession, current_user: User
) -> None:
    from unittest.mock import patch

    from app.services.chat_service import create_session, stream_mentor_reply

    session = await create_session(db_session, current_user)

    def fake_event_stream():
        yield {"chunk": {"bytes": b'{"contentBlockDelta": {"delta": {"text": "Hi!"}}}'}}

    with (
        patch("app.services.chat_service.embed_text", return_value=[0.1] * 1024),
        patch("app.services.chat_service._fetch_mentor_context", return_value=[]),
        patch("app.services.chat_service.get_bedrock_client") as mock_get_client,
    ):
        mock_get_client.return_value.invoke_model_with_response_stream.return_value = {
            "body": fake_event_stream()
        }
        async for _ in stream_mentor_reply(db_session, session, "First message", current_user):
            pass

        def fake_event_stream_2():
            yield {"chunk": {"bytes": b'{"contentBlockDelta": {"delta": {"text": "Hi again!"}}}'}}

        mock_get_client.return_value.invoke_model_with_response_stream.return_value = {
            "body": fake_event_stream_2()
        }
        async for _ in stream_mentor_reply(db_session, session, "Second message", current_user):
            pass

    await db_session.refresh(session)
    assert session.title == "First message"
