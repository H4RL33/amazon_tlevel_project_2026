import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.chat import ChatMessageRequest, ChatSessionDetail, ChatSessionSummary
from app.schemas.library import ContentSearchResult, LibraryResponse
from app.services import chat_service, library_service

router = APIRouter(prefix="/library", tags=["library"])


@router.get("/", response_model=LibraryResponse, summary="Get user's library")
async def get_library(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LibraryResponse:
    return await library_service.get_library(db, current_user)


@router.get(
    "/search",
    response_model=list[ContentSearchResult],
    summary="Semantic search across catalogue",
)
async def search(
    q: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ContentSearchResult]:
    return await library_service.semantic_search(db, q, current_user)


@router.get("/chats", response_model=list[ChatSessionSummary], summary="List chat sessions")
async def list_chats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ChatSessionSummary]:
    sessions = await chat_service.list_sessions(db, current_user)
    return [ChatSessionSummary.model_validate(s) for s in sessions]


@router.post("/chats", response_model=ChatSessionSummary, summary="Create a new chat session")
async def create_chat(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionSummary:
    session = await chat_service.create_session(db, current_user)
    return ChatSessionSummary.model_validate(session)


@router.get("/chats/{session_id}", response_model=ChatSessionDetail, summary="Get chat session detail")
async def get_chat(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionDetail:
    session = await chat_service.get_session_or_404(db, session_id, current_user)
    return await chat_service.get_session_detail(db, session)


@router.post("/chats/{session_id}/messages", summary="Send a message, stream the mentor's reply")
async def post_chat_message(
    session_id: int,
    body: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    session = await chat_service.get_session_or_404(db, session_id, current_user)

    async def event_generator():
        async for delta in chat_service.stream_mentor_reply(db, session, body.message, current_user):
            yield f"data: {json.dumps({'delta': delta})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
