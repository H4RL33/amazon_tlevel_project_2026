from fastapi import Header

from app.models.user import User


async def get_current_user() -> User:
    # Replace this with a real implementation (local JWT or Cognito) when auth is decided.
    raise NotImplementedError


async def get_current_user_optional(authorization: str | None = Header(default=None)) -> User | None:
    # Anonymous requests (no Authorization header) must succeed as anonymous — used by
    # routes that behave differently for logged-in vs anonymous requests without requiring
    # auth to succeed (e.g. the public Album detail route).
    if authorization is None:
        return None
    # Replace this with a real implementation (local JWT or Cognito) when auth is decided.
    raise NotImplementedError
