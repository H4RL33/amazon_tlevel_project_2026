import asyncio
import time
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User

bearer_scheme = HTTPBearer()

# Module-level JWKS cache — refreshed every hour
_jwks_cache: dict = {}
_jwks_fetched_at: float = 0.0
_JWKS_TTL = 3600.0
_jwks_lock = asyncio.Lock()


async def _fetch_jwks() -> dict:
    global _jwks_cache, _jwks_fetched_at
    if _jwks_cache and (time.monotonic() - _jwks_fetched_at) < _JWKS_TTL:
        return _jwks_cache
    async with _jwks_lock:
        # Re-check after acquiring lock — another coroutine may have fetched already
        if _jwks_cache and (time.monotonic() - _jwks_fetched_at) < _JWKS_TTL:
            return _jwks_cache
        async with httpx.AsyncClient() as http:
            r = await http.get(get_settings().cognito_jwks_url)
            r.raise_for_status()
        _jwks_cache = r.json()
        _jwks_fetched_at = time.monotonic()
    return _jwks_cache


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate Cognito JWT from the Authorization: Bearer header.
    Returns the authenticated User ORM object from the database.
    Raises HTTP 401 if the token is missing, invalid, or expired,
    or if no User row exists for the Cognito sub.
    """
    unauth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        jwks = await _fetch_jwks()
        signing_key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if signing_key is None:
            raise unauth
        settings = get_settings()
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.COGNITO_CLIENT_ID,
        )
        cognito_sub: str | None = payload.get("sub")
        if not cognito_sub:
            raise unauth
    except JWTError:
        raise unauth

    result = await db.execute(select(User).where(User.cognito_sub == cognito_sub))
    user = result.scalar_one_or_none()
    if user is None:
        raise unauth
    return user
