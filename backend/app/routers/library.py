from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.library import ContentSearchResult, LibraryResponse, MentorRequest, MentorResponse
from app.services import library_service

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


@router.post("/mentor", response_model=MentorResponse, summary="Ask the Dynamic Mentor")
async def mentor(
    body: MentorRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MentorResponse:
    return await library_service.mentor_query(db, body.message, current_user)
