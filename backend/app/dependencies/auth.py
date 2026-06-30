import json
import urllib.request
from functools import lru_cache

from fastapi import Depends, Header, HTTPException
from jose import jwt
from jose.exceptions import JOSEError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User


def _get_jwks() -> dict:
    settings = get_settings()
    url = (
        f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"
        f"{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    )
    with urllib.request.urlopen(url) as response:  # noqa: S310
        return json.load(response)


@lru_cache
def _cached_jwks() -> dict:
    return _get_jwks()


def decode_id_token(token: str) -> dict:
    """
    Validate a Cognito id_token against the pool's JWKS and return its claims.
    Raises jose.exceptions.JOSEError (or a subclass) on any validation failure:
    bad signature, expired, wrong audience, wrong issuer, or unknown key id.
    """
    settings = get_settings()
    unverified_header = jwt.get_unverified_header(token)

    jwks = _cached_jwks()
    key = next((k for k in jwks["keys"] if k["kid"] == unverified_header.get("kid")), None)
    if key is None:
        raise JOSEError("No matching JWK found for this token's key id")

    issuer = f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"
    return jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience=settings.COGNITO_CLIENT_ID,
        issuer=issuer,
    )


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    try:
        claims = decode_id_token(authorization.removeprefix("Bearer "))
    except JOSEError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    result = await db.execute(select(User).where(User.cognito_sub == claims["sub"]))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_current_user_optional(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if authorization is None:
        return None
    return await get_current_user(authorization=authorization, db=db)
