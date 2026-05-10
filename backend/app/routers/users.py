from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.topic import TopicResponse
from app.schemas.user import UserResponse, UserTopicsRequest
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    return await user_service.get_me(db, current_user)


@router.put(
    "/me/topics",
    response_model=list[TopicResponse],
    summary="Set user topic interests",
)
async def set_topics(
    payload: UserTopicsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TopicResponse]:
    return await user_service.set_topics(db, current_user, payload)


@router.get(
    "/me/topics",
    response_model=list[TopicResponse],
    summary="Get user topic interests",
)
async def get_topics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TopicResponse]:
    return await user_service.get_topics(db, current_user)
