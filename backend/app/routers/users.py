from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.gamification import UserStatsResponse
from app.schemas.topic import TopicResponse
from app.schemas.user import (
    AvatarUpdateRequest,
    AvatarUploadUrlRequest,
    AvatarUploadUrlResponse,
    UserProfileUpdateRequest,
    UserResponse,
    UserTopicsRequest,
)
from app.services import gamification_service, user_service

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


@router.post(
    "/me/avatar-upload-url",
    response_model=AvatarUploadUrlResponse,
    summary="Get a presigned S3 PUT URL for an avatar upload",
)
async def create_avatar_upload_url(
    payload: AvatarUploadUrlRequest,
    current_user: User = Depends(get_current_user),
) -> AvatarUploadUrlResponse:
    return user_service.create_avatar_upload_url(current_user, payload)


@router.patch(
    "/me/avatar",
    response_model=UserResponse,
    summary="Persist the S3 key of an uploaded avatar",
)
async def update_avatar(
    payload: AvatarUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    return await user_service.set_avatar(db, current_user, payload.avatar_s3_key)


@router.patch(
    "/me/profile",
    response_model=UserResponse,
    summary="Update user profile fields (username)",
)
async def update_profile(
    payload: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    return await user_service.update_username(db, current_user, payload.username)


@router.get(
    "/me/stats",
    response_model=UserStatsResponse,
    summary="Get XP/level/completion stats for the current user",
)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserStatsResponse:
    return await gamification_service.get_stats(db, current_user)
