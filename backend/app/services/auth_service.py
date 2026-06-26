from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserResponse, UserSyncRequest
from app.services.user_service import build_user_response


async def sync_user(
    db: AsyncSession,
    cognito_sub: str,
    email: str,
    payload: UserSyncRequest,
) -> UserResponse:
    """
    Create or update a User row after Cognito login.

    - If a User with cognito_sub already exists: update first_name and last_name, return it.
    - If no User exists: create a new row with the provided cognito_sub, email,
      first_name, and last_name.
    - Never raise on duplicate — this endpoint is called on every login.
    - Return a UserResponse (never expose hashed passwords or internal fields).
    """
    result = await db.execute(select(User).where(User.cognito_sub == cognito_sub))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            cognito_sub=cognito_sub,
            email=email,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
        db.add(user)
    else:
        user.first_name = payload.first_name
        user.last_name = payload.last_name

    await db.commit()
    await db.refresh(user)
    return build_user_response(user)
