from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.content import ContentDetailResponse
from app.services import snippet_service

router = APIRouter(prefix="/snippets", tags=["snippets"])


@router.get("/{content_id}", response_model=ContentDetailResponse, summary="Get snippet detail")
async def get_snippet(
    content_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> ContentDetailResponse:
    return await snippet_service.get_snippet(db, content_id, current_user)


@router.post("/{content_id}/save", status_code=204, summary="Save snippet to library")
async def save_snippet(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await snippet_service.save_snippet(db, content_id, current_user)


@router.delete("/{content_id}/save", status_code=204, summary="Remove snippet from library")
async def unsave_snippet(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await snippet_service.unsave_snippet(db, content_id, current_user)
