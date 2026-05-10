from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.content import ContentListResponse
from app.schemas.feed import ProgressResponse, ProgressUpdateRequest
from app.services import feed_service

router = APIRouter(tags=["feed"])


@router.get("/feed", response_model=list[ContentListResponse], summary="Personalised feed")
async def get_feed(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ContentListResponse]:
    return await feed_service.get_feed(db, current_user)


@router.get(
    "/progress",
    response_model=list[ProgressResponse],
    summary="Get in-progress content (continue reading)",
)
async def get_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProgressResponse]:
    return await feed_service.get_progress(db, current_user)


@router.post(
    "/progress/{content_id}",
    status_code=204,
    summary="Update reading/listening progress",
)
async def upsert_progress(
    content_id: int,
    payload: ProgressUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await feed_service.upsert_progress(db, current_user, content_id, payload)
