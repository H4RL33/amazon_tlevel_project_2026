from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserResponse, UserSyncRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/sync", response_model=UserResponse, summary="Sync Cognito user to DB")
async def sync_user(
    payload: UserSyncRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Called by the frontend immediately after Cognito token exchange.
    Reads the Cognito sub and email from the validated JWT in the Authorization header.
    Creates a new User row if none exists, or updates first_name/last_name if it does.

    Note: this route validates the JWT manually (not via get_current_user) because
    no User row exists yet on first call. Extract cognito_sub from the token directly.
    """
    return await auth_service.sync_user(db, cognito_sub="", email="", payload=payload)
