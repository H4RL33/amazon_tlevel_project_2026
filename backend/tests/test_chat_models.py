from sqlalchemy import select

from app.models.library import ChatMessage, ChatSession
from app.models.user import User


async def test_chat_session_and_message_persist_and_cascade(db_session, current_user: User) -> None:
    session = ChatSession(user_id=current_user.id, title="What is networking?")
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    msg = ChatMessage(session_id=session.id, role="user", text="What is networking?")
    reply = ChatMessage(
        session_id=session.id,
        role="mentor",
        text="Networking connects computers.",
        sources=[{"content_id": 1, "title": "Cloud Networking"}],
    )
    db_session.add_all([msg, reply])
    await db_session.commit()

    result = await db_session.execute(
        select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.id)
    )
    messages = result.scalars().all()
    assert [m.role for m in messages] == ["user", "mentor"]
    assert messages[1].sources == [{"content_id": 1, "title": "Cloud Networking"}]

    # Deleting the session cascades to its messages.
    await db_session.delete(session)
    await db_session.commit()
    remaining = await db_session.execute(
        select(ChatMessage).where(ChatMessage.session_id == session.id)
    )
    assert remaining.scalars().all() == []


async def test_chat_session_cascades_from_user(db_session, current_user: User) -> None:
    session = ChatSession(user_id=current_user.id, title="test")
    db_session.add(session)
    await db_session.commit()

    await db_session.delete(current_user)
    await db_session.commit()

    result = await db_session.execute(select(ChatSession).where(ChatSession.id == session.id))
    assert result.scalars().all() == []
