# Cognito Auth + S3 Avatar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the placeholder "Log in" link with a real Cognito Hosted UI login flow, and let a logged-in user upload a profile picture stored in S3 and rendered by `NavBarAvatar`.

**Architecture:** Backend validates Cognito JWTs locally via JWKS (python-jose), upserts a `User` row keyed on `cognito_sub`, and issues presigned S3 URLs for avatar PUT/GET. Frontend does a PKCE authorization-code exchange directly against Cognito (no backend involvement in the OAuth dance itself), then calls `/auth/sync` to get a `UserResponse` and persist it client-side.

**Tech Stack:** FastAPI, SQLAlchemy async, python-jose, boto3, Alembic, SvelteKit, vitest.

**Spec:** `docs/superpowers/specs/2026-06-24-cognito-auth-s3-avatar-design.md`

**Note on infra:** Terraform changes (callback URLs, schema attributes, CORS) are described in the spec and are applied manually by the user — they are not part of this plan, since the worker has no AWS credentials. Backend/frontend tasks below are written against the *contract* (env vars, settings) and don't require the infra to actually be live to pass their own tests.

---

### Task 1: Add `COGNITO_CLIENT_ID` setting

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/.env.example`

- [ ] **Step 1: Add the setting**

In `backend/app/config.py`, add a new field alongside `COGNITO_USER_POOL_ID`:

```python
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_CLIENT_ID: str = ""
```

- [ ] **Step 2: Document it in `.env.example`**

Add to `backend/.env.example`:

```
COGNITO_REGION=eu-west-2
COGNITO_USER_POOL_ID=
COGNITO_CLIENT_ID=
S3_BUCKET_NAME=
AWS_REGION=eu-west-2
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

(`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` are picked up automatically by boto3's default credential chain — no application code needed for them, just document that they must be set for presigned URLs to work locally.)

- [ ] **Step 3: Commit**

```bash
git add backend/app/config.py backend/.env.example
git commit -m "feat: add COGNITO_CLIENT_ID setting"
```

---

### Task 2: Implement real Cognito JWT validation in `get_current_user`

**Files:**
- Modify: `backend/app/dependencies/auth.py`
- Modify: `backend/tests/test_dependencies_auth.py`

This is the core piece everything else depends on. `get_current_user` validates a Cognito `id_token` against the pool's JWKS and resolves it to a `User` row. `decode_id_token` is exported separately so `routers/auth.py` (Task 4) can read claims before a `User` row exists.

- [ ] **Step 1: Write the failing tests**

Replace the full contents of `backend/tests/test_dependencies_auth.py`:

```python
import time

import pytest
from jose import jwk
from jose.utils import base64url_decode
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt as jose_jwt

from app.config import get_settings
from app.dependencies.auth import decode_id_token, get_current_user, get_current_user_optional
from app.models.user import User


@pytest.fixture(scope="module")
def rsa_key_pair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_numbers = private_key.public_key().public_numbers()
    return private_key, public_numbers


@pytest.fixture(scope="module")
def jwks(rsa_key_pair):
    _, public_numbers = rsa_key_pair
    return {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-kid",
                "use": "sig",
                "alg": "RS256",
                "n": jwk.long_to_base64(public_numbers.n).decode("ascii"),
                "e": jwk.long_to_base64(public_numbers.e).decode("ascii"),
            }
        ]
    }


def _make_token(rsa_key_pair, *, audience=None, issuer=None, exp_offset=3600, sub="test-sub"):
    private_key, _ = rsa_key_pair
    settings = get_settings()
    pem = private_key.private_bytes(
        encoding=__import__("cryptography.hazmat.primitives.serialization", fromlist=["Encoding"]).Encoding.PEM,
        format=__import__(
            "cryptography.hazmat.primitives.serialization", fromlist=["PrivateFormat"]
        ).PrivateFormat.PKCS8,
        encryption_algorithm=__import__(
            "cryptography.hazmat.primitives.serialization", fromlist=["NoEncryption"]
        ).NoEncryption(),
    )
    claims = {
        "sub": sub,
        "aud": audience if audience is not None else settings.COGNITO_CLIENT_ID,
        "iss": issuer
        if issuer is not None
        else f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}",
        "exp": int(time.time()) + exp_offset,
        "given_name": "Test",
        "family_name": "User",
        "email": "test@example.com",
    }
    return jose_jwt.encode(claims, pem, algorithm="RS256", headers={"kid": "test-kid"})


@pytest.fixture(autouse=True)
def _settings_and_jwks(monkeypatch, jwks):
    monkeypatch.setattr(get_settings(), "COGNITO_USER_POOL_ID", "test-pool")
    monkeypatch.setattr(get_settings(), "COGNITO_CLIENT_ID", "test-client")
    monkeypatch.setattr(get_settings(), "COGNITO_REGION", "eu-west-2")
    import app.dependencies.auth as auth_module

    monkeypatch.setattr(auth_module, "_get_jwks", lambda: jwks)


async def test_decode_id_token_returns_claims_for_a_valid_token(rsa_key_pair):
    token = _make_token(rsa_key_pair)
    claims = decode_id_token(token)
    assert claims["sub"] == "test-sub"
    assert claims["given_name"] == "Test"


async def test_decode_id_token_rejects_expired_token(rsa_key_pair):
    token = _make_token(rsa_key_pair, exp_offset=-3600)
    with pytest.raises(Exception):
        decode_id_token(token)


async def test_decode_id_token_rejects_wrong_audience(rsa_key_pair):
    token = _make_token(rsa_key_pair, audience="someone-else")
    with pytest.raises(Exception):
        decode_id_token(token)


async def test_decode_id_token_rejects_wrong_issuer(rsa_key_pair):
    token = _make_token(rsa_key_pair, issuer="https://evil.example.com/pool")
    with pytest.raises(Exception):
        decode_id_token(token)


async def test_get_current_user_optional_returns_none_without_authorization_header() -> None:
    result = await get_current_user_optional(authorization=None, db=None)
    assert result is None


async def test_get_current_user_raises_401_for_missing_header() -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization=None, db=None)
    assert exc_info.value.status_code == 401


async def test_get_current_user_resolves_user_by_cognito_sub(db_session, rsa_key_pair):
    user = User(cognito_sub="test-sub", email="test@example.com", first_name="Test", last_name="User")
    db_session.add(user)
    await db_session.commit()

    token = _make_token(rsa_key_pair, sub="test-sub")
    result = await get_current_user(authorization=f"Bearer {token}", db=db_session)
    assert result.cognito_sub == "test-sub"


async def test_get_current_user_raises_401_when_user_row_missing(db_session, rsa_key_pair):
    from fastapi import HTTPException

    token = _make_token(rsa_key_pair, sub="no-such-user")
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization=f"Bearer {token}", db=db_session)
    assert exc_info.value.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && poetry run pytest tests/test_dependencies_auth.py -v`
Expected: FAIL — `decode_id_token` doesn't exist, `get_current_user` still raises `NotImplementedError`.

- [ ] **Step 3: Implement `decode_id_token` and the real dependencies**

Replace the full contents of `backend/app/dependencies/auth.py`:

```python
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
```

Note: `_cached_jwks` (the `lru_cache`-wrapped function) is what production code calls; the test fixture monkeypatches the *uncached* `_get_jwks` name for clarity but actually needs to patch what's called. Fix this before running: patch `_cached_jwks` instead of `_get_jwks` in the test fixture — update `backend/tests/test_dependencies_auth.py`'s `_settings_and_jwks` fixture:

```python
    monkeypatch.setattr(auth_module, "_cached_jwks", lambda: jwks)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && poetry run pytest tests/test_dependencies_auth.py -v`
Expected: PASS (all tests green)

- [ ] **Step 5: Run the full backend test suite to check for regressions**

Run: `cd backend && poetry run pytest -v`
Expected: All other tests still pass (anything depending on `get_current_user`/`get_current_user_optional` raising `NotImplementedError` was already using `dependency_overrides` in `conftest.py`, so router tests are unaffected).

- [ ] **Step 6: Commit**

```bash
git add backend/app/dependencies/auth.py backend/tests/test_dependencies_auth.py
git commit -m "feat: validate Cognito JWTs in get_current_user via JWKS"
```

---

### Task 3: Add `avatar_url` to `UserResponse` and a shared response builder

**Files:**
- Modify: `backend/app/schemas/user.py`
- Modify: `backend/app/services/user_service.py`
- Test: `backend/tests/test_user_service.py` (new)

This adds the field and a `build_user_response` helper that computes a presigned avatar URL from `avatar_s3_key`, used by both `auth_service.sync_user` (Task 4) and `user_service.get_me` (Task 5).

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_user_service.py`:

```python
from app.models.user import User
from app.services.user_service import build_user_response


def test_build_user_response_has_no_avatar_url_when_avatar_s3_key_is_none() -> None:
    user = User(
        id=1,
        cognito_sub="sub-1",
        email="a@example.com",
        first_name="A",
        last_name="B",
        avatar_s3_key=None,
    )
    response = build_user_response(user)
    assert response.avatar_url is None


def test_build_user_response_has_avatar_url_when_avatar_s3_key_is_set(monkeypatch) -> None:
    import app.services.user_service as user_service_module

    monkeypatch.setattr(
        user_service_module,
        "_generate_presigned_get_url",
        lambda key: f"https://example-bucket.s3.amazonaws.com/{key}?signed=1",
    )
    user = User(
        id=1,
        cognito_sub="sub-1",
        email="a@example.com",
        first_name="A",
        last_name="B",
        avatar_s3_key="avatars/1/photo.jpg",
    )
    response = build_user_response(user)
    assert response.avatar_url == "https://example-bucket.s3.amazonaws.com/avatars/1/photo.jpg?signed=1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/test_user_service.py -v`
Expected: FAIL — `avatar_s3_key` is not a valid `User` field yet, `build_user_response` doesn't exist.

- [ ] **Step 3: Add `avatar_s3_key` to the `User` model**

In `backend/app/models/user.py`, add the column:

```python
    last_name: Mapped[str] = mapped_column(String(100))
    avatar_s3_key: Mapped[str | None] = mapped_column(String(500), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **Step 4: Add the migration**

Create `backend/migrations/versions/7a1f3c9d4e21_add_avatar_s3_key_to_users.py`:

```python
"""add avatar_s3_key to users

Revision ID: 7a1f3c9d4e21
Revises: 54474d1c36aa
Create Date: 2026-06-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a1f3c9d4e21'
down_revision: Union[str, Sequence[str], None] = '54474d1c36aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_s3_key", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_s3_key")
```

- [ ] **Step 5: Add `avatar_url` to `UserResponse` and write `build_user_response`**

In `backend/app/schemas/user.py`, add the field:

```python
class UserResponse(BaseModel):
    id: int
    cognito_sub: str
    email: str
    first_name: str
    last_name: str
    avatar_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
```

In `backend/app/services/user_service.py`, add the helper near the top (after imports):

```python
import boto3

from app.config import get_settings
from app.models.user import User
from app.schemas.topic import TopicResponse
from app.schemas.user import UserResponse, UserTopicsRequest


def _generate_presigned_get_url(s3_key: str, expiry_seconds: int = 3600) -> str:
    s3 = boto3.client("s3", region_name=get_settings().AWS_REGION)
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": get_settings().S3_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=expiry_seconds,
    )


def build_user_response(user: User) -> UserResponse:
    avatar_url = _generate_presigned_get_url(user.avatar_s3_key) if user.avatar_s3_key else None
    return UserResponse(
        id=user.id,
        cognito_sub=user.cognito_sub,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        avatar_url=avatar_url,
        created_at=user.created_at,
    )
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && poetry run pytest tests/test_user_service.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/user.py backend/migrations/versions/7a1f3c9d4e21_add_avatar_s3_key_to_users.py backend/app/schemas/user.py backend/app/services/user_service.py backend/tests/test_user_service.py
git commit -m "feat: add avatar_s3_key column and build_user_response helper"
```

---

### Task 4: Implement `sync_user` and the `/auth/sync` route

**Files:**
- Modify: `backend/app/schemas/user.py`
- Modify: `backend/app/services/auth_service.py`
- Modify: `backend/app/routers/auth.py`
- Test: `backend/tests/test_auth_service.py` (new)
- Test: `backend/tests/test_auth_router.py` (new)

- [ ] **Step 1: Write the failing service test**

Create `backend/tests/test_auth_service.py`:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserSyncRequest
from app.services import auth_service


async def test_sync_user_creates_a_new_user_when_none_exists(db_session: AsyncSession) -> None:
    response = await auth_service.sync_user(
        db_session,
        cognito_sub="sub-new",
        email="new@example.com",
        payload=UserSyncRequest(first_name="New", last_name="User"),
    )

    assert response.cognito_sub == "sub-new"
    assert response.first_name == "New"

    result = await db_session.execute(select(User).where(User.cognito_sub == "sub-new"))
    assert result.scalar_one() is not None


async def test_sync_user_updates_name_on_repeat_login(db_session: AsyncSession) -> None:
    await auth_service.sync_user(
        db_session,
        cognito_sub="sub-existing",
        email="existing@example.com",
        payload=UserSyncRequest(first_name="Old", last_name="Name"),
    )

    response = await auth_service.sync_user(
        db_session,
        cognito_sub="sub-existing",
        email="existing@example.com",
        payload=UserSyncRequest(first_name="New", last_name="Name2"),
    )

    assert response.first_name == "New"
    assert response.last_name == "Name2"

    result = await db_session.execute(select(User).where(User.cognito_sub == "sub-existing"))
    rows = result.scalars().all()
    assert len(rows) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/test_auth_service.py -v`
Expected: FAIL with `NotImplementedError`

- [ ] **Step 3: Implement `sync_user`**

Replace the contents of `backend/app/services/auth_service.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && poetry run pytest tests/test_auth_service.py -v`
Expected: PASS

- [ ] **Step 5: Write the failing router test**

Create `backend/tests/test_auth_router.py`:

```python
import time

from httpx import ASGITransport, AsyncClient
from jose import jwt as jose_jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.main import app


async def test_sync_route_extracts_claims_from_bearer_token(
    db_session: AsyncSession, monkeypatch
) -> None:
    monkeypatch.setattr(
        "app.routers.auth.decode_id_token",
        lambda token: {
            "sub": "sub-from-token",
            "email": "fromtoken@example.com",
            "given_name": "Header",
            "family_name": "Claims",
        },
    )

    async def override_get_db():
        yield db_session

    from app.database import get_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/auth/sync",
                json={"first_name": "Header", "last_name": "Claims"},
                headers={"Authorization": "Bearer fake-token"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["cognito_sub"] == "sub-from-token"
    assert response.json()["email"] == "fromtoken@example.com"
```

- [ ] **Step 6: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/test_auth_router.py -v`
Expected: FAIL — route still passes `cognito_sub=""`, `email=""`.

- [ ] **Step 7: Implement the route**

Replace the contents of `backend/app/routers/auth.py`:

```python
from fastapi import APIRouter, Header, HTTPException
from jose.exceptions import JOSEError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

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
```

- [ ] **Step 8: Run test to verify it passes**

Run: `cd backend && poetry run pytest tests/test_auth_router.py -v`
Expected: PASS

- [ ] **Step 9: Run the full backend test suite**

Run: `cd backend && poetry run pytest -v`
Expected: All tests pass.

- [ ] **Step 10: Commit**

```bash
git add backend/app/services/auth_service.py backend/app/routers/auth.py backend/tests/test_auth_service.py backend/tests/test_auth_router.py
git commit -m "feat: implement /auth/sync with real JWT claim extraction"
```

---

### Task 5: Implement `user_service.get_me`, `set_topics`, `get_topics`

**Files:**
- Modify: `backend/app/services/user_service.py`
- Test: `backend/tests/test_user_service.py`

These were already blocking `/users/me` and `/users/me/topics` before this work; needed now because the frontend will call `GET /users/me` on every page load to rehydrate `currentUser` (Task 12).

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_user_service.py`:

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.topic import Topic
from app.models.user import User
from app.schemas.user import UserTopicsRequest
from app.services import user_service


async def _make_topic(db: AsyncSession, slug: str) -> Topic:
    topic = Topic(slug=slug, name=slug, description="...", accent_colour="#000000")
    db.add(topic)
    await db.flush()
    return topic


async def test_get_me_returns_user_response(db_session: AsyncSession) -> None:
    user = User(cognito_sub="sub-x", email="x@example.com", first_name="X", last_name="Y")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await user_service.get_me(db_session, user)
    assert response.cognito_sub == "sub-x"


async def test_set_topics_replaces_existing_interests(db_session: AsyncSession) -> None:
    user = User(cognito_sub="sub-y", email="y@example.com", first_name="X", last_name="Y")
    db_session.add(user)
    await db_session.flush()
    topic_a = await _make_topic(db_session, "topic-a")
    topic_b = await _make_topic(db_session, "topic-b")
    await db_session.commit()

    await user_service.set_topics(db_session, user, UserTopicsRequest(topic_ids=[topic_a.id]))
    result = await user_service.set_topics(
        db_session, user, UserTopicsRequest(topic_ids=[topic_b.id])
    )

    assert [t.id for t in result] == [topic_b.id]


async def test_set_topics_rejects_unknown_topic_id(db_session: AsyncSession) -> None:
    from fastapi import HTTPException

    user = User(cognito_sub="sub-z", email="z@example.com", first_name="X", last_name="Y")
    db_session.add(user)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await user_service.set_topics(db_session, user, UserTopicsRequest(topic_ids=[999]))
    assert exc_info.value.status_code == 422


async def test_get_topics_returns_only_this_users_interests(db_session: AsyncSession) -> None:
    user = User(cognito_sub="sub-w", email="w@example.com", first_name="X", last_name="Y")
    db_session.add(user)
    await db_session.flush()
    topic_a = await _make_topic(db_session, "topic-c")
    await db_session.commit()

    await user_service.set_topics(db_session, user, UserTopicsRequest(topic_ids=[topic_a.id]))
    result = await user_service.get_topics(db_session, user)

    assert [t.id for t in result] == [topic_a.id]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && poetry run pytest tests/test_user_service.py -v`
Expected: FAIL with `NotImplementedError` for the four new tests.

- [ ] **Step 3: Implement the three functions**

In `backend/app/services/user_service.py`, replace `get_me`, `set_topics`, `get_topics`:

```python
from fastapi import HTTPException
from sqlalchemy import delete, select

from app.models.topic import Topic
from app.models.user import UserTopicInterest


async def get_me(db: AsyncSession, current_user: User) -> UserResponse:
    return build_user_response(current_user)


async def set_topics(
    db: AsyncSession, current_user: User, payload: UserTopicsRequest
) -> list[TopicResponse]:
    if payload.topic_ids:
        result = await db.execute(select(Topic.id).where(Topic.id.in_(payload.topic_ids)))
        found_ids = {row[0] for row in result.all()}
        missing = set(payload.topic_ids) - found_ids
        if missing:
            raise HTTPException(status_code=422, detail=f"Unknown topic_ids: {sorted(missing)}")

    await db.execute(
        delete(UserTopicInterest).where(UserTopicInterest.user_id == current_user.id)
    )
    for topic_id in payload.topic_ids:
        db.add(UserTopicInterest(user_id=current_user.id, topic_id=topic_id))
    await db.commit()

    return await get_topics(db, current_user)


async def get_topics(db: AsyncSession, current_user: User) -> list[TopicResponse]:
    result = await db.execute(
        select(Topic)
        .join(UserTopicInterest, UserTopicInterest.topic_id == Topic.id)
        .where(UserTopicInterest.user_id == current_user.id)
    )
    return [TopicResponse.model_validate(topic) for topic in result.scalars().all()]
```

Add the new imports (`fastapi.HTTPException`, `sqlalchemy.delete`/`select`, `app.models.topic.Topic`, `app.models.user.UserTopicInterest`) to the existing import block at the top of the file.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && poetry run pytest tests/test_user_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/user_service.py backend/tests/test_user_service.py
git commit -m "feat: implement get_me, set_topics, get_topics"
```

---

### Task 6: Implement `content_service.get_presigned_url`

**Files:**
- Modify: `backend/app/services/content_service.py`
- Test: `backend/tests/test_content_service.py` (new)

Only `get_presigned_url` — `list_content`, `get_content`, `get_s3_key` are a pre-existing gap unrelated to this spec and stay out of scope.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_content_service.py`:

```python
from app.services import content_service


async def test_get_presigned_url_calls_boto3_generate_presigned_url(monkeypatch) -> None:
    captured = {}

    class FakeS3Client:
        def generate_presigned_url(self, operation, Params, ExpiresIn):
            captured["operation"] = operation
            captured["params"] = Params
            captured["expires_in"] = ExpiresIn
            return "https://example-bucket.s3.amazonaws.com/some-key?signed=1"

    monkeypatch.setattr(content_service.boto3, "client", lambda service, region_name: FakeS3Client())

    url = await content_service.get_presigned_url("some-key", expiry_seconds=120)

    assert url == "https://example-bucket.s3.amazonaws.com/some-key?signed=1"
    assert captured["operation"] == "get_object"
    assert captured["params"]["Key"] == "some-key"
    assert captured["expires_in"] == 120
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/test_content_service.py -v`
Expected: FAIL with `NotImplementedError` (and `AttributeError: module has no attribute 'boto3'` until Step 3 adds the import).

- [ ] **Step 3: Implement it**

In `backend/app/services/content_service.py`, add `import boto3` and `from app.config import get_settings` to the top, then replace `get_presigned_url`:

```python
async def get_presigned_url(s3_key: str, expiry_seconds: int = 900) -> str:
    s3 = boto3.client("s3", region_name=get_settings().AWS_REGION)
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": get_settings().S3_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=expiry_seconds,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && poetry run pytest tests/test_content_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/content_service.py backend/tests/test_content_service.py
git commit -m "feat: implement content_service.get_presigned_url"
```

---

### Task 7: Avatar upload endpoints

**Files:**
- Modify: `backend/app/schemas/user.py`
- Modify: `backend/app/services/user_service.py`
- Modify: `backend/app/routers/users.py`
- Test: `backend/tests/test_user_service.py`
- Test: `backend/tests/test_users_router.py` (new)

- [ ] **Step 1: Write the failing service tests**

Append to `backend/tests/test_user_service.py`:

```python
from app.schemas.user import AvatarUploadUrlRequest


async def test_create_avatar_upload_url_rejects_unsupported_content_type() -> None:
    from fastapi import HTTPException

    user = User(id=1, cognito_sub="sub-1", email="a@example.com", first_name="A", last_name="B")
    with pytest.raises(HTTPException) as exc_info:
        user_service.create_avatar_upload_url(user, AvatarUploadUrlRequest(content_type="text/plain"))
    assert exc_info.value.status_code == 422


async def test_create_avatar_upload_url_returns_a_jpg_key_for_jpeg(monkeypatch) -> None:
    monkeypatch.setattr(
        user_service,
        "_generate_presigned_put_url",
        lambda key, content_type: f"https://example-bucket.s3.amazonaws.com/{key}?put=1",
    )
    user = User(id=42, cognito_sub="sub-1", email="a@example.com", first_name="A", last_name="B")

    result = user_service.create_avatar_upload_url(
        user, AvatarUploadUrlRequest(content_type="image/jpeg")
    )

    assert result.key.startswith("avatars/42/")
    assert result.key.endswith(".jpg")
    assert result.upload_url.endswith("?put=1")


async def test_set_avatar_persists_the_key_and_returns_user_response(db_session: AsyncSession) -> None:
    user = User(cognito_sub="sub-avatar", email="avatar@example.com", first_name="A", last_name="B")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await user_service.set_avatar(db_session, user, "avatars/1/photo.jpg")

    assert user.avatar_s3_key == "avatars/1/photo.jpg"
    assert response.id == user.id
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && poetry run pytest tests/test_user_service.py -v`
Expected: FAIL — `AvatarUploadUrlRequest` doesn't exist, `create_avatar_upload_url`/`set_avatar` don't exist.

- [ ] **Step 3: Add schemas**

In `backend/app/schemas/user.py`, add:

```python
class AvatarUploadUrlRequest(BaseModel):
    content_type: str


class AvatarUploadUrlResponse(BaseModel):
    upload_url: str
    key: str


class AvatarUpdateRequest(BaseModel):
    avatar_s3_key: str
```

- [ ] **Step 4: Implement the service functions**

In `backend/app/services/user_service.py`, add (alongside the existing imports, add `uuid4` from `uuid` and the new schema names):

```python
from uuid import uuid4

from app.schemas.user import (
    AvatarUploadUrlRequest,
    AvatarUploadUrlResponse,
    UserResponse,
    UserSyncRequest,
    UserTopicsRequest,
)

_AVATAR_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def _generate_presigned_put_url(s3_key: str, content_type: str, expiry_seconds: int = 300) -> str:
    s3 = boto3.client("s3", region_name=get_settings().AWS_REGION)
    return s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": get_settings().S3_BUCKET_NAME,
            "Key": s3_key,
            "ContentType": content_type,
        },
        ExpiresIn=expiry_seconds,
    )


def create_avatar_upload_url(
    user: User, payload: AvatarUploadUrlRequest
) -> AvatarUploadUrlResponse:
    extension = _AVATAR_CONTENT_TYPES.get(payload.content_type)
    if extension is None:
        raise HTTPException(status_code=422, detail="Unsupported content type for avatar upload")

    key = f"avatars/{user.id}/{uuid4()}.{extension}"
    upload_url = _generate_presigned_put_url(key, payload.content_type)
    return AvatarUploadUrlResponse(upload_url=upload_url, key=key)


async def set_avatar(db: AsyncSession, current_user: User, avatar_s3_key: str) -> UserResponse:
    current_user.avatar_s3_key = avatar_s3_key
    await db.commit()
    await db.refresh(current_user)
    return build_user_response(current_user)
```

- [ ] **Step 5: Run service tests to verify they pass**

Run: `cd backend && poetry run pytest tests/test_user_service.py -v`
Expected: PASS

- [ ] **Step 6: Write the failing router test**

Create `backend/tests/test_users_router.py`:

```python
from httpx import AsyncClient


async def test_create_avatar_upload_url_returns_upload_url_and_key(
    authenticated_client: AsyncClient, monkeypatch
) -> None:
    import app.services.user_service as user_service_module

    monkeypatch.setattr(
        user_service_module,
        "_generate_presigned_put_url",
        lambda key, content_type: "https://example-bucket.s3.amazonaws.com/signed-put",
    )

    response = await authenticated_client.post(
        "/users/me/avatar-upload-url", json={"content_type": "image/png"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["key"].endswith(".png")
    assert body["upload_url"] == "https://example-bucket.s3.amazonaws.com/signed-put"


async def test_update_avatar_persists_key(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.patch(
        "/users/me/avatar", json={"avatar_s3_key": "avatars/1/photo.jpg"}
    )

    assert response.status_code == 200
    assert response.json()["id"] is not None
```

- [ ] **Step 7: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/test_users_router.py -v`
Expected: FAIL — 404, routes don't exist yet.

- [ ] **Step 8: Add the routes**

In `backend/app/routers/users.py`, add the import and two routes:

```python
from app.schemas.user import (
    AvatarUpdateRequest,
    AvatarUploadUrlRequest,
    AvatarUploadUrlResponse,
    UserResponse,
    UserTopicsRequest,
)


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
```

- [ ] **Step 9: Run test to verify it passes**

Run: `cd backend && poetry run pytest tests/test_users_router.py -v`
Expected: PASS

- [ ] **Step 10: Run the full backend test suite**

Run: `cd backend && poetry run pytest -v`
Expected: All tests pass.

- [ ] **Step 11: Commit**

```bash
git add backend/app/schemas/user.py backend/app/services/user_service.py backend/app/routers/users.py backend/tests/test_user_service.py backend/tests/test_users_router.py
git commit -m "feat: add avatar upload-url and update endpoints"
```

---

### Task 8: Frontend `UserResponse` type + story file updates

**Files:**
- Modify: `frontend/src/lib/api/types.ts`
- Modify: `frontend/src/lib/components/NavBarAvatar.story.svelte`
- Modify: `frontend/src/lib/components/Navbar.story.svelte`

- [ ] **Step 1: Update the type**

In `frontend/src/lib/api/types.ts`:

```typescript
export interface UserResponse {
  id: number;
  cognito_sub: string;
  email: string;
  first_name: string;
  last_name: string;
  avatar_url: string | null;
  created_at: string;
}
```

- [ ] **Step 2: Fix the two story files**

In `frontend/src/lib/components/NavBarAvatar.story.svelte`, add `avatar_url: null,` to the `user` object literal (after `last_name`).

In `frontend/src/lib/components/Navbar.story.svelte`, find the `UserResponse` literal and add `avatar_url: null,` the same way.

- [ ] **Step 3: Run typecheck**

Run: `cd frontend && npm run check`
Expected: No new type errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/api/types.ts frontend/src/lib/components/NavBarAvatar.story.svelte frontend/src/lib/components/Navbar.story.svelte
git commit -m "feat: add avatar_url to UserResponse type"
```

---

### Task 9: Implement `lib/api/auth.ts` (PKCE login, code exchange, sign out)

**Files:**
- Modify: `frontend/src/lib/api/auth.ts`
- Test: `frontend/src/lib/api/auth.test.ts` (new)

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/lib/api/auth.test.ts`:

```typescript
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { exchangeCode, getCognitoLoginUrl, signOut, syncUser } from './auth';
import { TOKEN_KEY } from './client';

describe('getCognitoLoginUrl', () => {
  it('builds a Hosted UI authorize URL with PKCE params and stores the verifier', () => {
    const url = getCognitoLoginUrl();

    expect(url).toContain('/login?');
    expect(url).toContain('response_type=code');
    expect(url).toContain('code_challenge=');
    expect(url).toContain('code_challenge_method=S256');
    expect(sessionStorage.getItem('pkce_code_verifier')).toBeTruthy();
  });
});

describe('exchangeCode', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    sessionStorage.clear();
  });

  it('POSTs to the Cognito token endpoint with the stored code_verifier', async () => {
    sessionStorage.setItem('pkce_code_verifier', 'stored-verifier');
    const tokenResponse = {
      access_token: 'a',
      id_token: 'b',
      refresh_token: 'c',
      expires_in: 3600,
      token_type: 'Bearer',
    };
    const mockFetch = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(tokenResponse), { status: 200 }));
    vi.stubGlobal('fetch', mockFetch);

    const result = await exchangeCode('auth-code-123');

    expect(result).toEqual(tokenResponse);
    const [, init] = mockFetch.mock.calls[0];
    expect(init.body).toContain('code=auth-code-123');
    expect(init.body).toContain('code_verifier=stored-verifier');
  });
});

describe('syncUser', () => {
  beforeEach(() => {
    localStorage.setItem(TOKEN_KEY, 'fake-id-token');
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    localStorage.clear();
  });

  it('POSTs to /auth/sync with the stored id_token as a bearer header', async () => {
    const user = {
      id: 1,
      cognito_sub: 'sub-1',
      email: 'a@example.com',
      first_name: 'A',
      last_name: 'B',
      avatar_url: null,
      created_at: new Date().toISOString(),
    };
    const mockFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(user), { status: 200 }));
    vi.stubGlobal('fetch', mockFetch);

    const result = await syncUser('A', 'B');

    expect(result).toEqual(user);
    const [, init] = mockFetch.mock.calls[0];
    expect(init.headers.Authorization).toBe('Bearer fake-id-token');
  });
});

describe('signOut', () => {
  it('clears the stored token', () => {
    localStorage.setItem(TOKEN_KEY, 'fake-id-token');
    signOut();
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/lib/api/auth.test.ts`
Expected: FAIL — current `auth.ts` throws `Error('not implemented')` for everything.

- [ ] **Step 3: Implement `auth.ts`**

Replace the full contents of `frontend/src/lib/api/auth.ts`:

```typescript
import { TOKEN_KEY } from './client';
import type { UserResponse } from './types';

export interface TokenResponse {
  access_token: string;
  id_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
}

const PKCE_VERIFIER_KEY = 'pkce_code_verifier';

function base64UrlEncode(bytes: Uint8Array): string {
  return btoa(String.fromCharCode(...bytes))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

function generateCodeVerifier(): string {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return base64UrlEncode(bytes);
}

async function generateCodeChallenge(verifier: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier));
  return base64UrlEncode(new Uint8Array(digest));
}

export function getCognitoLoginUrl(): string {
  const domain = import.meta.env.VITE_COGNITO_DOMAIN;
  const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID;
  const redirectUri = import.meta.env.VITE_COGNITO_REDIRECT_URI;

  const verifier = generateCodeVerifier();
  sessionStorage.setItem(PKCE_VERIFIER_KEY, verifier);

  // Hosted UI requires the challenge synchronously available in the URL we return;
  // since SHA-256 digesting is async, callers that need the *real* challenge should
  // await buildLoginUrl() instead — but for the common case (a click handler can't
  // await before navigating) we compute the challenge eagerly here and accept the
  // unused Promise: browsers resolve crypto.subtle.digest fast enough in practice,
  // and login is a full-page navigation so a few extra ms is invisible.
  const challengePromise = generateCodeChallenge(verifier);
  let challenge = '';
  challengePromise.then((value) => {
    challenge = value;
  });

  const params = new URLSearchParams({
    client_id: clientId,
    response_type: 'code',
    scope: 'email openid profile',
    redirect_uri: redirectUri,
    code_challenge_method: 'S256',
    code_challenge: challenge,
  });

  return `${domain}/login?${params.toString()}`;
}

export async function exchangeCode(code: string): Promise<TokenResponse> {
  const domain = import.meta.env.VITE_COGNITO_DOMAIN;
  const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID;
  const redirectUri = import.meta.env.VITE_COGNITO_REDIRECT_URI;
  const verifier = sessionStorage.getItem(PKCE_VERIFIER_KEY) ?? '';

  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: clientId,
    code,
    redirect_uri: redirectUri,
    code_verifier: verifier,
  });

  const response = await fetch(`${domain}/oauth2/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: body.toString(),
  });

  return response.json() as Promise<TokenResponse>;
}

export async function syncUser(firstName: string, lastName: string): Promise<UserResponse> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '';
  const token = localStorage.getItem(TOKEN_KEY);

  const response = await fetch(`${baseUrl}/auth/sync`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ first_name: firstName, last_name: lastName }),
  });

  return response.json() as Promise<UserResponse>;
}

export function signOut(): void {
  localStorage.removeItem(TOKEN_KEY);
}
```

This has a known async/sync mismatch for `getCognitoLoginUrl` (documented in the inline comment) — that's resolved in Step 3 of Task 11, where the Navbar awaits a small wrapper instead of calling this synchronously. Revisit: actually fix it properly now rather than shipping a race condition — see Step 4.

- [ ] **Step 4: Fix the PKCE challenge race properly**

The comment above describes a real bug, not an acceptable tradeoff — don't ship it. Replace `getCognitoLoginUrl` with an async version, and update its one call site in Task 11 accordingly:

```typescript
export async function getCognitoLoginUrl(): Promise<string> {
  const domain = import.meta.env.VITE_COGNITO_DOMAIN;
  const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID;
  const redirectUri = import.meta.env.VITE_COGNITO_REDIRECT_URI;

  const verifier = generateCodeVerifier();
  sessionStorage.setItem(PKCE_VERIFIER_KEY, verifier);
  const challenge = await generateCodeChallenge(verifier);

  const params = new URLSearchParams({
    client_id: clientId,
    response_type: 'code',
    scope: 'email openid profile',
    redirect_uri: redirectUri,
    code_challenge_method: 'S256',
    code_challenge: challenge,
  });

  return `${domain}/login?${params.toString()}`;
}
```

Update the test in `auth.test.ts` for `getCognitoLoginUrl` to `await` it:

```typescript
describe('getCognitoLoginUrl', () => {
  it('builds a Hosted UI authorize URL with PKCE params and stores the verifier', async () => {
    const url = await getCognitoLoginUrl();

    expect(url).toContain('/login?');
    expect(url).toContain('response_type=code');
    expect(url).toContain('code_challenge=');
    expect(url).toContain('code_challenge_method=S256');
    expect(sessionStorage.getItem('pkce_code_verifier')).toBeTruthy();
  });
});
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/lib/api/auth.test.ts`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/api/auth.ts frontend/src/lib/api/auth.test.ts
git commit -m "feat: implement Cognito PKCE login, code exchange, and sign out"
```

---

### Task 10: Attach bearer token in `apiFetch`

**Files:**
- Modify: `frontend/src/lib/api/client.ts`
- Modify: `frontend/src/lib/api/client.test.ts`

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/lib/api/client.test.ts`:

```typescript
import { TOKEN_KEY } from './client';

describe('apiFetch auth header', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    localStorage.clear();
  });

  it('attaches an Authorization header when a token is stored', async () => {
    localStorage.setItem(TOKEN_KEY, 'stored-token');
    const mockFetch = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }));
    vi.stubGlobal('fetch', mockFetch);

    await apiFetch('/users/me');

    const [, init] = mockFetch.mock.calls[0];
    expect(init.headers.Authorization).toBe('Bearer stored-token');
  });

  it('omits the Authorization header when no token is stored', async () => {
    const mockFetch = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }));
    vi.stubGlobal('fetch', mockFetch);

    await apiFetch('/topics/');

    const [, init] = mockFetch.mock.calls[0];
    expect(init.headers.Authorization).toBeUndefined();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/lib/api/client.test.ts`
Expected: FAIL — no `Authorization` header is set today.

- [ ] **Step 3: Implement it**

Replace the contents of `frontend/src/lib/api/client.ts`:

```typescript
export const TOKEN_KEY = 'id_token';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '';
  const token = localStorage.getItem(TOKEN_KEY);

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string>),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    throw new ApiError(response.status, `Request to ${path} failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}
```

- [ ] **Step 4: Run all client tests to verify they pass**

Run: `cd frontend && npx vitest run src/lib/api/client.test.ts`
Expected: PASS (including the two pre-existing tests, which don't set a token and don't assert on header *absence* of unrelated keys, so they're unaffected)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/api/client.ts frontend/src/lib/api/client.test.ts
git commit -m "feat: attach stored bearer token to every API request"
```

---

### Task 11: `/auth/callback` route + Navbar login link

**Files:**
- Create: `frontend/src/routes/auth/callback/+page.svelte`
- Modify: `frontend/src/lib/components/Navbar.svelte`

- [ ] **Step 1: Create the callback route**

Create `frontend/src/routes/auth/callback/+page.svelte`:

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { exchangeCode, syncUser } from '$lib/api/auth';
  import { TOKEN_KEY } from '$lib/api/client';
  import { currentUser } from '$lib/stores/user';
  import PageCard from '$lib/components/PageCard.svelte';

  let error: string | null = null;

  onMount(async () => {
    const code = $page.url.searchParams.get('code');
    if (!code) {
      error = 'No authorization code was returned by Cognito.';
      return;
    }

    try {
      const tokens = await exchangeCode(code);
      localStorage.setItem(TOKEN_KEY, tokens.id_token);

      const claims = JSON.parse(atob(tokens.id_token.split('.')[1]));
      const user = await syncUser(claims.given_name ?? '', claims.family_name ?? '');
      currentUser.set(user);

      await goto('/');
    } catch {
      error = 'Sign-in failed. Please try again.';
    }
  });
</script>

<PageCard as="main">
  <div class="content">
    {#if error}
      <h1>Sign-in failed</h1>
      <p>{error}</p>
      <a href="/login">Back to sign in</a>
    {:else}
      <p>Signing you in...</p>
    {/if}
  </div>
</PageCard>

<style>
  .content {
    max-width: 900px;
    margin: 0 auto;
  }
</style>
```

- [ ] **Step 2: Wire the Navbar login link to the async login URL**

In `frontend/src/lib/components/Navbar.svelte`, replace the `<script>` block and the login `NavLink`:

```svelte
<script lang="ts">
  import NavLink from '$lib/components/NavLink.svelte';
  import NavBarAvatar from '$lib/components/NavBarAvatar.svelte';
  import PageCard from '$lib/components/PageCard.svelte';
  import { currentUser } from '$lib/stores/user';
  import { getCognitoLoginUrl } from '$lib/api/auth';

  async function handleLoginClick(event: MouseEvent) {
    event.preventDefault();
    window.location.href = await getCognitoLoginUrl();
  }
</script>
```

Replace the `{:else}` branch in the template:

```svelte
      {#if $currentUser}
        <NavBarAvatar user={$currentUser} />
      {:else}
        <a href="/login" class="login-link" on:click={handleLoginClick}>Log in</a>
      {/if}
```

Add matching styling for `.login-link` near the existing `<style>` block, matching `NavLink`'s general look (reuse the project's existing nav link colour/weight — check `NavLink.svelte`'s rendered styles and match them rather than inventing new ones):

```svelte
<style>
  /* ...existing styles... */

  .login-link {
    color: inherit;
    text-decoration: none;
    font-size: 0.9375rem;
    font-weight: 500;
  }
</style>
```

- [ ] **Step 3: Manual check (no automated test for this Svelte component — project convention)**

Run: `cd frontend && npm run dev` then visit `http://localhost:5173` (or whatever port vite prints) and confirm the page renders without console errors and "Log in" is clickable. Full Cognito round-trip verification happens in Task 13 once terraform is applied.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/auth/callback/+page.svelte frontend/src/lib/components/Navbar.svelte
git commit -m "feat: add /auth/callback route and wire Navbar login link to Cognito"
```

---

### Task 12: Rehydrate `currentUser` on app load + `lib/api/users.ts`

**Files:**
- Create: `frontend/src/lib/api/users.ts`
- Test: `frontend/src/lib/api/users.test.ts` (new)
- Modify: `frontend/src/routes/+layout.svelte`

Without this, refreshing the page after logging in would show a logged-out Navbar even though a valid token is still in `localStorage` — a visible bug in a live demo.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/lib/api/users.test.ts`:

```typescript
import { afterEach, describe, expect, it, vi } from 'vitest';
import { getMe, requestAvatarUploadUrl, updateAvatar } from './users';
import type { UserResponse } from './types';

const user: UserResponse = {
  id: 1,
  cognito_sub: 'sub-1',
  email: 'a@example.com',
  first_name: 'A',
  last_name: 'B',
  avatar_url: null,
  created_at: new Date().toISOString(),
};

describe('getMe', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('calls GET /users/me', async () => {
    const mockFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(user), { status: 200 }));
    vi.stubGlobal('fetch', mockFetch);

    const result = await getMe();

    expect(result).toEqual(user);
    expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/users/me'), expect.any(Object));
  });
});

describe('requestAvatarUploadUrl', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('POSTs the content type and returns the upload url and key', async () => {
    const body = { upload_url: 'https://example.com/put', key: 'avatars/1/x.png' };
    const mockFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status: 200 }));
    vi.stubGlobal('fetch', mockFetch);

    const result = await requestAvatarUploadUrl('image/png');

    expect(result).toEqual(body);
    const [, init] = mockFetch.mock.calls[0];
    expect(init.body).toContain('image/png');
  });
});

describe('updateAvatar', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('PATCHes the avatar_s3_key and returns the updated user', async () => {
    const mockFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(user), { status: 200 }));
    vi.stubGlobal('fetch', mockFetch);

    const result = await updateAvatar('avatars/1/x.png');

    expect(result).toEqual(user);
    const [, init] = mockFetch.mock.calls[0];
    expect(init.method).toBe('PATCH');
    expect(init.body).toContain('avatars/1/x.png');
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/lib/api/users.test.ts`
Expected: FAIL — `./users` module doesn't exist.

- [ ] **Step 3: Implement `lib/api/users.ts`**

Create `frontend/src/lib/api/users.ts`:

```typescript
import { apiFetch } from './client';
import type { UserResponse } from './types';

export interface AvatarUploadUrlResponse {
  upload_url: string;
  key: string;
}

export async function getMe(): Promise<UserResponse> {
  return apiFetch<UserResponse>('/users/me');
}

export async function requestAvatarUploadUrl(contentType: string): Promise<AvatarUploadUrlResponse> {
  return apiFetch<AvatarUploadUrlResponse>('/users/me/avatar-upload-url', {
    method: 'POST',
    body: JSON.stringify({ content_type: contentType }),
  });
}

export async function updateAvatar(avatarS3Key: string): Promise<UserResponse> {
  return apiFetch<UserResponse>('/users/me/avatar', {
    method: 'PATCH',
    body: JSON.stringify({ avatar_s3_key: avatarS3Key }),
  });
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/lib/api/users.test.ts`
Expected: PASS

- [ ] **Step 5: Rehydrate `currentUser` in the root layout**

In `frontend/src/routes/+layout.svelte`, add to the `<script>` block (near the top, after existing imports):

```svelte
  import { onMount } from 'svelte';
  import { TOKEN_KEY } from '$lib/api/client';
  import { getMe } from '$lib/api/users';
  import { currentUser } from '$lib/stores/user';

  onMount(async () => {
    if (localStorage.getItem(TOKEN_KEY)) {
      try {
        currentUser.set(await getMe());
      } catch {
        localStorage.removeItem(TOKEN_KEY);
      }
    }
  });
```

- [ ] **Step 6: Manual check**

Run: `cd frontend && npm run dev`, open devtools, run `localStorage.setItem('id_token', 'garbage')`, reload — confirm no crash and the token gets cleared (since `/users/me` will 401 against a real or stubbed backend). This can't be fully verified against a real Cognito token until Task 13.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/lib/api/users.ts frontend/src/lib/api/users.test.ts frontend/src/routes/+layout.svelte
git commit -m "feat: rehydrate currentUser from stored token on app load"
```

---

### Task 13: `NavBarAvatar` image rendering + Settings avatar upload UI

**Files:**
- Modify: `frontend/src/lib/components/NavBarAvatar.svelte`
- Modify: `frontend/src/routes/settings/+page.svelte`

No automated tests for `.svelte` components in this project (verified: no testing-library/jsdom component test setup exists) — verify both manually in the browser per Step 4.

- [ ] **Step 1: Add the image branch to `NavBarAvatar`**

In `frontend/src/lib/components/NavBarAvatar.svelte`, replace the avatar button markup:

```svelte
  <button class="avatar-button" on:click={toggle} aria-label="User menu" aria-expanded={open}>
    {#if user.avatar_url}
      <img src={user.avatar_url} alt="" class="avatar avatar-image" />
    {:else}
      <span class="avatar">{initials}</span>
    {/if}
  </button>
```

Add to `<style>`:

```svelte
  .avatar-image {
    object-fit: cover;
  }
```

(`alt=""` is correct here, not a missing-alt-text bug: the avatar is decorative next to the same information conveyed by the "User menu" `aria-label` on its parent button.)

- [ ] **Step 2: Build the Settings avatar upload UI**

Replace the contents of `frontend/src/routes/settings/+page.svelte`:

```svelte
<script lang="ts">
  import PageCard from '$lib/components/PageCard.svelte';
  import { requestAvatarUploadUrl, updateAvatar } from '$lib/api/users';
  import { currentUser } from '$lib/stores/user';

  let uploading = false;
  let error: string | null = null;
  let fileInput: HTMLInputElement;

  async function handleFileChange() {
    const file = fileInput.files?.[0];
    if (!file) return;

    uploading = true;
    error = null;
    try {
      const { upload_url, key } = await requestAvatarUploadUrl(file.type);

      const putResponse = await fetch(upload_url, {
        method: 'PUT',
        headers: { 'Content-Type': file.type },
        body: file,
      });
      if (!putResponse.ok) {
        throw new Error('Upload to S3 failed');
      }

      const updatedUser = await updateAvatar(key);
      currentUser.set(updatedUser);
    } catch {
      error = 'Could not upload your profile picture. Please try again.';
    } finally {
      uploading = false;
    }
  }
</script>

<PageCard as="main">
  <div class="content">
    <h1>Settings</h1>

    <section>
      <h2>Profile picture</h2>
      {#if $currentUser?.avatar_url}
        <img src={$currentUser.avatar_url} alt="Your current profile picture" class="preview" />
      {/if}
      <label for="avatar-input">Upload a new profile picture</label>
      <input
        id="avatar-input"
        type="file"
        accept="image/jpeg,image/png,image/webp"
        bind:this={fileInput}
        on:change={handleFileChange}
        disabled={uploading}
      />
      {#if uploading}
        <p>Uploading...</p>
      {/if}
      {#if error}
        <p role="alert">{error}</p>
      {/if}
    </section>
  </div>
</PageCard>

<style>
  .content {
    max-width: 900px;
    margin: 0 auto;
  }

  .preview {
    width: 96px;
    height: 96px;
    border-radius: 50%;
    object-fit: cover;
    display: block;
    margin-bottom: 1rem;
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
  }
</style>
```

- [ ] **Step 3: Run the frontend test suite to check for regressions**

Run: `cd frontend && npx vitest run`
Expected: All tests pass (no component tests exist for either modified file, so this just confirms nothing else broke).

- [ ] **Step 4: Manual verification**

Run: `cd frontend && npm run dev`. Without real Cognito infra yet, this confirms the Settings page renders, the file input is keyboard-accessible (tab to it, Enter/Space opens the file picker per native `<input type=file>` behaviour — no custom JS needed), and there are no console errors. Full upload-flow verification happens once terraform is applied (Task 14).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/components/NavBarAvatar.svelte frontend/src/routes/settings/+page.svelte
git commit -m "feat: render avatar image and add Settings profile picture upload"
```

---

### Task 14: End-to-end manual verification against real Cognito

**Prerequisite:** the user has run `terraform apply` (per the design spec's Terraform section) and populated `backend/.env` (`COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) and `docker-compose.yml`'s `VITE_COGNITO_DOMAIN`/`VITE_COGNITO_CLIENT_ID` build args with real values.

This task has no code changes — it's the spec's required manual walkthrough before calling the feature done.

- [ ] **Step 1: Run migrations**

```bash
docker compose up --build -d
docker compose exec backend poetry run alembic upgrade head
```

- [ ] **Step 2: Walk the flow in a browser**

1. Visit `http://localhost:3000`, click "Log in".
2. Confirm redirect to the real Cognito Hosted UI; sign up with a test email, first name, last name.
3. Confirm redirect back to `http://localhost:3000/auth/callback`, then to `/`.
4. Confirm the Navbar now shows initials instead of "Log in".
5. Go to `/settings`, upload a small JPEG/PNG.
6. Confirm the Navbar avatar switches from initials to the uploaded image.
7. Refresh the page — confirm still logged in and the avatar persists (rehydration from Task 12).
8. Open the uploaded image's `avatar_url` directly in a new tab — confirm it loads (proves it's genuinely served from S3, not a local blob URL).

- [ ] **Step 3: Note any deviations**

If any step fails, fix forward with a new task/commit rather than reopening earlier ones — record what broke for the next sub-project's planning.

---

## Self-review notes

- **Spec coverage:** infra (documented, manual), JWT validation (Task 2), `/auth/sync` (Task 4), `get_me`/topics (Task 5), `get_presigned_url` (Task 6), avatar upload/persist endpoints (Task 7), migration (Task 3), frontend PKCE/login/callback (Tasks 9, 11), bearer header (Task 10), `NavBarAvatar` image branch + Settings upload UI (Task 13), rehydration corollary (Task 12), manual e2e (Task 14) — all covered.
- **Type consistency checked:** `UserResponse.avatar_url` (backend Pydantic, Task 3) ↔ `UserResponse.avatar_url` (frontend TS, Task 8) ↔ all literals updated (Task 8). `AvatarUploadUrlRequest`/`Response`/`AvatarUpdateRequest` names match between schema (Task 7 Step 3), service (Task 7 Step 4), router (Task 7 Step 8), and the frontend's separately-named `AvatarUploadUrlResponse` interface in `users.ts` (Task 12) — same shape, intentionally independent types since frontend doesn't import backend schemas.
- **Out of scope, confirmed not touched:** `content_service.list_content`/`get_content`/`get_s3_key`, `Button.svelte`, ECS/ALB deploy path.
