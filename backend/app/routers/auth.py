from fastapi import APIRouter, Depends, Header, HTTPException
from jose.exceptions import JOSEError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import decode_id_token
from app.schemas.user import UserResponse, UserSyncRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/sync", response_model=UserResponse, summary="Sync Cognito user to DB")
async def sync_user(
    payload: UserSyncRequest,
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Called by the frontend immediately after Cognito token exchange.
    Reads the Cognito sub and email from the validated JWT in the Authorization header.
    Creates a new User row if none exists, or updates first_name/last_name if it does.
    """
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    try:
        claims = decode_id_token(authorization.removeprefix("Bearer "))
    except JOSEError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    return await auth_service.sync_user(
        db, cognito_sub=claims["sub"], email=claims.get("email", ""), payload=payload
    )
