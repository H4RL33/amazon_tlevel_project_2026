import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.library import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import ChatMessageRecord, ChatMessageSource, ChatSessionDetail
from app.services.embedding_service import embed_text, get_bedrock_client
from app.services.library_service import _fetch_mentor_context

TITLE_MAX_LEN = 60


def _derive_title(first_message: str) -> str:
    trimmed = first_message.strip()
    if len(trimmed) <= TITLE_MAX_LEN:
        return trimmed or "New chat"
    return trimmed[: TITLE_MAX_LEN - 1].rstrip() + "…"


async def create_session(db: AsyncSession, user: User) -> ChatSession:
    session = ChatSession(user_id=user.id, title="New chat")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def list_sessions(db: AsyncSession, user: User) -> list[ChatSession]:
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_session_or_404(db: AsyncSession, session_id: int, user: User) -> ChatSession:
    stmt = select(ChatSession).where(
        ChatSession.id == session_id, ChatSession.user_id == user.id
    )
    session = (await db.execute(stmt)).scalar_one_or_none()
    if session is None:
        # 404, not 403 — don't confirm to the caller that a session with this
        # id exists at all if it isn't theirs.
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


async def _get_messages(db: AsyncSession, session_id: int) -> list[ChatMessage]:
    """
    Explicit query rather than lazily touching session.messages: the session
    passed in isn't guaranteed to have that relationship eagerly loaded (e.g.
    right after create_session), and lazy-loading isn't awaitable in an async
    session — it raises MissingGreenlet.
    """
    stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.id)
    return list((await db.execute(stmt)).scalars().all())


async def get_session_detail(db: AsyncSession, session: ChatSession) -> ChatSessionDetail:
    messages = await _get_messages(db, session.id)
    return ChatSessionDetail(
        id=session.id,
        title=session.title,
        messages=[
            ChatMessageRecord(
                id=m.id,
                role=m.role,
                text=m.text,
                sources=(
                    [ChatMessageSource(**s) for s in m.sources] if m.sources is not None else None
                ),
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


def _build_mentor_prompt(message: str, chunks: list[dict[str, Any]]) -> str:
    """
    Canonical Dynamic Mentor prompt template. This is the single source of
    truth going forward — library_service.mentor_query's HTTP route is being
    retired by a later module in this plan, so new callers should build on
    this copy rather than the one in library_service.
    """
    context_text = "\n\n".join(f"{c['title']}: {c['body'][:500]}" for c in chunks)
    return (
        "You are the Dynamic Mentor for Living Campus, an Amazon T-Level education platform.\n"
        "Answer the student's question using the provided context from their learning materials.\n"
        "If the context doesn't cover the question, say so and answer from general knowledge.\n\n"
        f"Context:\n{context_text}\n\n"
        f"Student question: {message}\n\nMentor:"
    )


def _parse_stream_event(raw_bytes: bytes) -> str | None:
    """
    Extract incremental text from one Bedrock InvokeModelWithResponseStream event.
    Nova's native streaming schema wraps each text increment in a
    contentBlockDelta.delta.text field; other event types (contentBlockStart,
    messageStop, metadata) carry no text and are skipped.
    """
    payload = json.loads(raw_bytes)
    delta = payload.get("contentBlockDelta", {}).get("delta", {})
    return delta.get("text")


async def stream_mentor_reply(
    db: AsyncSession, session: ChatSession, message: str, user: User
) -> AsyncIterator[str]:
    settings = get_settings()
    query_vec = embed_text(message)
    if query_vec is None:
        raise HTTPException(status_code=503, detail="The mentor is temporarily unavailable")
    chunks: list[dict[str, Any]] = await _fetch_mentor_context(db, query_vec, user)
    prompt = _build_mentor_prompt(message, chunks)

    response = get_bedrock_client().invoke_model_with_response_stream(
        modelId=settings.BEDROCK_GENERATION_MODEL_ID,
        body=json.dumps(
            {
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {"maxTokens": 512, "temperature": 0.7, "topP": 0.9},
            }
        ),
    )

    full_text_parts: list[str] = []
    try:
        for event in response["body"]:
            raw_bytes = event.get("chunk", {}).get("bytes")
            if raw_bytes is None:
                continue
            text = _parse_stream_event(raw_bytes)
            if text:
                full_text_parts.append(text)
                yield text
    finally:
        # Persist whatever was assembled so far even if the stream raised
        # mid-iteration (Bedrock error, client disconnect, etc.) — we never
        # want to silently drop an exchange the user already partially saw.
        full_text = "".join(full_text_parts) or (
            "I'm sorry, I couldn't generate a response right now."
        )
        sources = [{"content_id": c["content_id"], "title": c["title"]} for c in chunks]

        existing_messages = await _get_messages(db, session.id)
        is_first_message = len(existing_messages) == 0
        db.add(ChatMessage(session_id=session.id, role="user", text=message))
        db.add(
            ChatMessage(session_id=session.id, role="mentor", text=full_text, sources=sources)
        )
        if is_first_message:
            session.title = _derive_title(message)
        await db.commit()
