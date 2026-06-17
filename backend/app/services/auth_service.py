from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserResponse, UserSyncRequest


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
    raise NotImplementedError
