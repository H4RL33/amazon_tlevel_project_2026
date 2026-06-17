# Application Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold all backend routes, models, and services plus all frontend components, pages, and API modules as typed stubs — no business logic — so junior developers can focus on implementation.

**Architecture:** FastAPI backend with SQLAlchemy async ORM, Cognito JWT auth via JWKS validation, 5 routers, and stub services. SvelteKit frontend (adapter-static SPA) with Cognito Hosted UI auth flow, client-side auth guard in layout, persistent sidebar, and typed API modules. All service functions stub with `raise NotImplementedError`. All Svelte component templates stub with comment block only.

**Tech Stack:** Python 3.12 / FastAPI 0.115 / SQLAlchemy 2 async / python-jose / boto3 / pytest-asyncio | SvelteKit 2 / Svelte 4 / TypeScript / marked / Vitest

**Important:** Tasks 1–9 (backend) and Tasks 10–17 (frontend) can be executed in parallel after Task 1. Task 1 is a shared prerequisite.

---

## File Map

```
backend/
├── requirements.txt                  ← updated with new deps
├── .env.example                      ← updated with Cognito + S3 vars
├── pyproject.toml                    ← updated pytest config
├── seed.py                           ← stub seed script
└── app/
    ├── __init__.py
    ├── main.py                       ← FastAPI app, all routers registered
    ├── config.py                     ← pydantic-settings, Cognito + S3 vars
    ├── database.py                   ← async engine, get_db()
    ├── dependencies/
    │   ├── __init__.py
    │   └── auth.py                   ← get_current_user (full JWKS impl)
    ├── models/
    │   ├── __init__.py               ← Base, all model exports
    │   ├── user.py                   ← User, UserTopicInterest
    │   ├── topic.py                  ← Topic
    │   ├── t_level.py                ← TLevel
    │   ├── content.py                ← ContentType enum, Tag, Content, ContentTag
    │   └── progress.py               ← UserContentProgress
    ├── schemas/
    │   ├── __init__.py
    │   ├── user.py                   ← UserSyncRequest, UserResponse, UserTopicsRequest
    │   ├── topic.py                  ← TopicResponse, TopicDetailResponse, TLevelResponse
    │   ├── content.py                ← ContentType, TagResponse, ContentListResponse, ContentDetailResponse
    │   └── feed.py                   ← ProgressResponse, ProgressUpdateRequest
    ├── routers/
    │   ├── __init__.py
    │   ├── auth.py                   ← POST /auth/sync
    │   ├── users.py                  ← GET/PUT /users/me + topics
    │   ├── topics.py                 ← GET /topics + detail + t-levels
    │   ├── content.py                ← GET /content + detail + audio-url
    │   └── feed.py                   ← GET /feed, GET/POST /progress
    └── services/
        ├── __init__.py
        ├── auth_service.py           ← stub: sync_user
        ├── user_service.py           ← stub: get_me, set_topics, get_topics
        ├── topic_service.py          ← stub: list, get_by_slug, get_t_level
        ├── content_service.py        ← stub: list, get, get_presigned_url
        └── feed_service.py           ← stub: get_feed, get_progress, upsert_progress

frontend/src/
├── app.html
├── hooks.server.ts                   ← dev-only stub (adapter-static SPA)
├── lib/
│   ├── api/
│   │   ├── types.ts                  ← all shared TS interfaces
│   │   ├── client.ts                 ← apiFetch wrapper + ApiError
│   │   ├── auth.ts                   ← exchangeCode, syncUser, signOut
│   │   ├── topics.ts                 ← listTopics, getTopic, getTLevel
│   │   ├── content.ts                ← listContent, getContent, getAudioUrl
│   │   ├── feed.ts                   ← getFeed
│   │   └── progress.ts               ← getProgress, updateProgress
│   ├── stores/
│   │   ├── user.ts                   ← currentUser, userTopics
│   │   ├── topics.ts                 ← allTopics
│   │   └── progress.ts               ← continueReading
│   └── components/
│       ├── Button.svelte
│       ├── Card.svelte
│       ├── Badge.svelte
│       ├── ProgressBar.svelte
│       ├── AppShell.svelte
│       ├── Sidebar.svelte
│       ├── Breadcrumb.svelte
│       ├── TopicGrid.svelte
│       ├── TopicCard.svelte
│       ├── PersonalisedFeed.svelte
│       ├── FeedItem.svelte
│       ├── ContinueReading.svelte
│       ├── TLevelList.svelte
│       ├── TLevelListItem.svelte
│       ├── ContentBlock.svelte
│       ├── AudioPlayer.svelte
│       └── VideoPlayer.svelte
└── routes/
    ├── +layout.ts                    ← export const ssr = false
    ├── +page.svelte                  ← landing page stub
    ├── auth/callback/
    │   └── +page.svelte              ← Cognito callback stub
    └── (app)/
        ├── +layout.svelte            ← client-side auth guard + AppShell
        ├── onboarding/+page.svelte
        ├── dashboard/+page.svelte
        ├── topics/[slug]/+page.svelte
        ├── topics/[slug]/t-levels/[id]/+page.svelte
        └── settings/+page.svelte
```

---

## Task 1: Project Foundation

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/.env.example`
- Modify: `backend/pyproject.toml`
- Modify: `frontend/package.json`
- Modify: `frontend/svelte.config.js`

- [ ] **Step 1: Update `backend/requirements.txt`**

```
fastapi==0.115.5
uvicorn[standard]==0.32.1
pydantic-settings==2.6.1
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
python-jose[cryptography]==3.3.0
boto3==1.35.0
httpx==0.28.0
pytest==8.3.3
pytest-asyncio==0.24.0
ruff==0.8.3
```

- [ ] **Step 2: Create `backend/.env.example`**

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/appdb
SECRET_KEY=change-me-in-production
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:5173

# Cognito
COGNITO_REGION=eu-west-2
COGNITO_USER_POOL_ID=eu-west-2_xxxxxxx
COGNITO_CLIENT_ID=your-app-client-id

# S3 (for media pre-signed URLs)
S3_BUCKET_NAME=exeaws26-content
AWS_REGION=eu-west-2
```

- [ ] **Step 3: Update `backend/pyproject.toml`**

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 4: Update `frontend/package.json`** — add `marked` and `svelte-check`

```json
{
  "name": "tlevel-frontend",
  "version": "0.0.1",
  "private": true,
  "scripts": {
    "dev": "vite dev",
    "build": "vite build",
    "preview": "vite preview",
    "check": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json",
    "test": "npm run test:unit",
    "test:unit": "vitest",
    "lint": "prettier --check . && eslint .",
    "format": "prettier --write ."
  },
  "dependencies": {
    "marked": "^12.0.0"
  },
  "devDependencies": {
    "@sveltejs/adapter-static": "^3.0.0",
    "@sveltejs/kit": "^2.0.0",
    "@sveltejs/vite-plugin-svelte": "^3.0.0",
    "@typescript-eslint/eslint-plugin": "^8.0.0",
    "@typescript-eslint/parser": "^8.0.0",
    "eslint": "^9.0.0",
    "eslint-plugin-svelte": "^2.0.0",
    "globals": "^15.0.0",
    "prettier": "^3.0.0",
    "prettier-plugin-svelte": "^3.0.0",
    "svelte": "^4.0.0",
    "svelte-check": "^3.0.0",
    "svelte-eslint-parser": "^0.41.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0",
    "vitest": "^1.0.0"
  },
  "type": "module"
}
```

- [ ] **Step 5: Update `frontend/svelte.config.js`** — enable SPA fallback

```js
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({ fallback: 'index.html' }),
  },
};

export default config;
```

- [ ] **Step 6: Install dependencies**

```bash
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
```

Expected: no errors from either install.

- [ ] **Step 7: Commit**

```bash
git add backend/requirements.txt backend/.env.example backend/pyproject.toml \
  frontend/package.json frontend/svelte.config.js
git commit -m "chore: update deps — add python-jose, boto3, marked; configure SPA fallback"
```

---

## Task 2: Backend Package Structure

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`

- [ ] **Step 1: Create `backend/app/__init__.py`** (empty)

- [ ] **Step 2: Create `backend/app/config.py`**

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    COGNITO_REGION: str
    COGNITO_USER_POOL_ID: str
    COGNITO_CLIENT_ID: str

    S3_BUCKET_NAME: str
    AWS_REGION: str = "eu-west-2"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def cognito_jwks_url(self) -> str:
        return (
            f"https://cognito-idp.{self.COGNITO_REGION}.amazonaws.com"
            f"/{self.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 3: Create `backend/app/database.py`**

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

_engine = create_async_engine(get_settings().DATABASE_URL, echo=False)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:
        yield session
```

- [ ] **Step 4: Verify imports work**

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://x:x@localhost/x \
SECRET_KEY=test \
COGNITO_REGION=eu-west-2 \
COGNITO_USER_POOL_ID=eu-west-2_test \
COGNITO_CLIENT_ID=test \
S3_BUCKET_NAME=test \
python -c "from app.config import get_settings; from app.database import get_db; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add backend/app/
git commit -m "feat(backend): add app package with config and database"
```

---

## Task 3: Backend Models

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/topic.py`
- Create: `backend/app/models/t_level.py`
- Create: `backend/app/models/content.py`
- Create: `backend/app/models/progress.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/__init__.py` (empty), then `backend/tests/test_models.py`:

```python
def test_models_importable():
    from app.models.user import User, UserTopicInterest
    from app.models.topic import Topic
    from app.models.t_level import TLevel
    from app.models.content import Content, Tag, ContentTag, ContentType
    from app.models.progress import UserContentProgress

    assert User.__tablename__ == "users"
    assert Topic.__tablename__ == "topics"
    assert TLevel.__tablename__ == "t_levels"
    assert Content.__tablename__ == "content"
    assert UserContentProgress.__tablename__ == "user_content_progress"
    assert ContentType.article == "article"
    assert ContentType.audio == "audio"
    assert ContentType.video == "video"
```

- [ ] **Step 2: Run test — expect ImportError**

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://x:x@localhost/x SECRET_KEY=test \
COGNITO_REGION=eu-west-2 COGNITO_USER_POOL_ID=eu-west-2_test \
COGNITO_CLIENT_ID=test S3_BUCKET_NAME=test \
pytest tests/test_models.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.models'`

- [ ] **Step 3: Create `backend/app/models/__init__.py`**

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models.user import User, UserTopicInterest  # noqa: E402, F401
from app.models.topic import Topic  # noqa: E402, F401
from app.models.t_level import TLevel  # noqa: E402, F401
from app.models.content import Content, ContentTag, ContentType, Tag  # noqa: E402, F401
from app.models.progress import UserContentProgress  # noqa: E402, F401
```

- [ ] **Step 4: Create `backend/app/models/user.py`**

```python
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cognito_sub: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    topic_interests: Mapped[list["UserTopicInterest"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    progress: Mapped[list["UserContentProgress"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserTopicInterest(Base):
    __tablename__ = "user_topic_interests"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), primary_key=True)

    user: Mapped["User"] = relationship(back_populates="topic_interests")
    topic: Mapped["Topic"] = relationship()
```

- [ ] **Step 5: Create `backend/app/models/topic.py`**

```python
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    accent_colour: Mapped[str] = mapped_column(String(7))
```

- [ ] **Step 6: Create `backend/app/models/t_level.py`**

```python
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class TLevel(Base):
    __tablename__ = "t_levels"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    entry_requirements: Mapped[str] = mapped_column(Text)
    how_to_apply: Mapped[str] = mapped_column(Text)

    topic: Mapped["Topic"] = relationship()
```

- [ ] **Step 7: Create `backend/app/models/content.py`**

```python
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class ContentType(str, enum.Enum):
    article = "article"
    audio = "audio"
    video = "video"


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)


class ContentTag(Base):
    __tablename__ = "content_tags"

    content_id: Mapped[int] = mapped_column(ForeignKey("content.id"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), primary_key=True)

    tag: Mapped["Tag"] = relationship()


class Content(Base):
    __tablename__ = "content"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[ContentType] = mapped_column(Enum(ContentType))
    media_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    t_level_id: Mapped[int | None] = mapped_column(
        ForeignKey("t_levels.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    topic: Mapped["Topic"] = relationship()
    t_level: Mapped["TLevel | None"] = relationship()
    content_tags: Mapped[list["ContentTag"]] = relationship(
        cascade="all, delete-orphan"
    )
```

- [ ] **Step 8: Create `backend/app/models/progress.py`**

```python
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class UserContentProgress(Base):
    __tablename__ = "user_content_progress"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("content.id"), primary_key=True)
    last_viewed_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    progress_pct: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship(back_populates="progress")
    content: Mapped["Content"] = relationship()
```

- [ ] **Step 9: Run test — expect PASS**

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://x:x@localhost/x SECRET_KEY=test \
COGNITO_REGION=eu-west-2 COGNITO_USER_POOL_ID=eu-west-2_test \
COGNITO_CLIENT_ID=test S3_BUCKET_NAME=test \
pytest tests/test_models.py -v
```

Expected: `test_models_importable PASSED`

- [ ] **Step 10: Commit**

```bash
git add backend/app/models/ backend/tests/
git commit -m "feat(backend): add all ORM models (User, Topic, TLevel, Content, Tag, Progress)"
```

---

## Task 4: Backend Schemas

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/schemas/topic.py`
- Create: `backend/app/schemas/content.py`
- Create: `backend/app/schemas/feed.py`
- Modify: `backend/tests/test_models.py` → `backend/tests/test_schemas.py`

- [ ] **Step 1: Write the failing test** — create `backend/tests/test_schemas.py`

```python
def test_schemas_importable():
    from app.schemas.user import UserResponse, UserSyncRequest, UserTopicsRequest
    from app.schemas.topic import TLevelResponse, TopicDetailResponse, TopicResponse
    from app.schemas.content import (
        ContentDetailResponse,
        ContentListResponse,
        ContentType,
        TagResponse,
    )
    from app.schemas.feed import ProgressResponse, ProgressUpdateRequest

    assert ContentType.article == "article"
    assert ContentType.video == "video"

    # Verify field presence via model_fields
    assert "cognito_sub" in UserResponse.model_fields
    assert "accent_colour" in TopicResponse.model_fields
    assert "progress_pct" in ProgressUpdateRequest.model_fields
```

- [ ] **Step 2: Run test — expect ImportError**

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://x:x@localhost/x SECRET_KEY=test \
COGNITO_REGION=eu-west-2 COGNITO_USER_POOL_ID=eu-west-2_test \
COGNITO_CLIENT_ID=test S3_BUCKET_NAME=test \
pytest tests/test_schemas.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create `backend/app/schemas/__init__.py`** (empty)

- [ ] **Step 4: Create `backend/app/schemas/user.py`**

```python
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserSyncRequest(BaseModel):
    first_name: str
    last_name: str


class UserResponse(BaseModel):
    id: int
    cognito_sub: str
    email: str
    first_name: str
    last_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserTopicsRequest(BaseModel):
    topic_ids: list[int]
```

- [ ] **Step 5: Create `backend/app/schemas/topic.py`**

```python
from pydantic import BaseModel


class TLevelResponse(BaseModel):
    id: int
    topic_id: int
    name: str
    entry_requirements: str
    how_to_apply: str

    model_config = {"from_attributes": True}


class TopicResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    accent_colour: str

    model_config = {"from_attributes": True}


class TopicDetailResponse(TopicResponse):
    t_levels: list[TLevelResponse]
```

- [ ] **Step 6: Create `backend/app/schemas/content.py`**

```python
import enum
from datetime import datetime

from pydantic import BaseModel


class ContentType(str, enum.Enum):
    article = "article"
    audio = "audio"
    video = "video"


class TagResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ContentListResponse(BaseModel):
    id: int
    title: str
    content_type: ContentType
    topic_id: int
    t_level_id: int | None
    tags: list[TagResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class ContentDetailResponse(ContentListResponse):
    body: str | None
    media_url: str | None  # Pre-signed S3 URL generated at request time; not stored in DB
```

- [ ] **Step 7: Create `backend/app/schemas/feed.py`**

```python
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.content import ContentListResponse


class ProgressResponse(BaseModel):
    content_id: int
    last_viewed_at: datetime
    progress_pct: int
    content: ContentListResponse

    model_config = {"from_attributes": True}


class ProgressUpdateRequest(BaseModel):
    progress_pct: int = Field(ge=0, le=100)
```

- [ ] **Step 8: Run test — expect PASS**

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://x:x@localhost/x SECRET_KEY=test \
COGNITO_REGION=eu-west-2 COGNITO_USER_POOL_ID=eu-west-2_test \
COGNITO_CLIENT_ID=test S3_BUCKET_NAME=test \
pytest tests/test_schemas.py -v
```

Expected: `test_schemas_importable PASSED`

- [ ] **Step 9: Commit**

```bash
git add backend/app/schemas/ backend/tests/test_schemas.py
git commit -m "feat(backend): add Pydantic schemas for all domain types"
```

---

## Task 5: Backend Auth Dependency + Temporary main.py

**Files:**
- Create: `backend/app/dependencies/__init__.py`
- Create: `backend/app/dependencies/auth.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: Write the failing test** — create `backend/tests/test_auth.py`

```python
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_health_returns_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_missing_token_returns_401(client):
    response = await client.get("/users/me")
    assert response.status_code == 401


async def test_invalid_token_returns_401(client):
    response = await client.get("/users/me", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401
```

- [ ] **Step 2: Run test — expect ImportError**

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://x:x@localhost/x SECRET_KEY=test \
COGNITO_REGION=eu-west-2 COGNITO_USER_POOL_ID=eu-west-2_test \
COGNITO_CLIENT_ID=test S3_BUCKET_NAME=test \
pytest tests/test_auth.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 3: Create `backend/app/dependencies/__init__.py`** (empty)

- [ ] **Step 4: Create `backend/app/dependencies/auth.py`**

```python
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


async def _fetch_jwks() -> dict:
    global _jwks_cache, _jwks_fetched_at
    now = time.monotonic()
    if _jwks_cache and (now - _jwks_fetched_at) < _JWKS_TTL:
        return _jwks_cache
    async with httpx.AsyncClient() as http:
        r = await http.get(get_settings().cognito_jwks_url)
        r.raise_for_status()
    _jwks_cache = r.json()
    _jwks_fetched_at = now
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
```

- [ ] **Step 5: Create `backend/app/main.py`** (initial — full version added in Task 8)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()

app = FastAPI(title="T-Level AWS Academy API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


# Routers registered in Task 8 after all routers are created
```

- [ ] **Step 6: Run test — expect PASS for health and 401 tests**

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://x:x@localhost/x SECRET_KEY=test \
COGNITO_REGION=eu-west-2 COGNITO_USER_POOL_ID=eu-west-2_test \
COGNITO_CLIENT_ID=test S3_BUCKET_NAME=test \
pytest tests/test_auth.py -v
```

Expected:
- `test_health_returns_ok` — PASS
- `test_missing_token_returns_401` — FAIL (route not registered yet — will pass after Task 8)
- `test_invalid_token_returns_401` — FAIL (route not registered yet — will pass after Task 8)

Note these two failures are expected at this stage.

- [ ] **Step 7: Commit**

```bash
git add backend/app/dependencies/ backend/app/main.py backend/tests/conftest.py \
  backend/tests/test_auth.py
git commit -m "feat(backend): add JWKS auth dependency and initial main.py"
```

---

## Task 6: Backend Services (Stubs)

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/auth_service.py`
- Create: `backend/app/services/user_service.py`
- Create: `backend/app/services/topic_service.py`
- Create: `backend/app/services/content_service.py`
- Create: `backend/app/services/feed_service.py`

- [ ] **Step 1: Create `backend/app/services/__init__.py`** (empty)

- [ ] **Step 2: Create `backend/app/services/auth_service.py`**

```python
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
```

- [ ] **Step 3: Create `backend/app/services/user_service.py`**

```python
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.topic import TopicResponse
from app.schemas.user import UserResponse, UserTopicsRequest


async def get_me(db: AsyncSession, current_user: User) -> UserResponse:
    """
    Return the UserResponse for the authenticated user.
    Map the ORM User object to UserResponse (model_config from_attributes handles this).
    """
    raise NotImplementedError


async def set_topics(
    db: AsyncSession, current_user: User, payload: UserTopicsRequest
) -> list[TopicResponse]:
    """
    Replace all UserTopicInterest rows for current_user with the given topic_ids.

    - Delete all existing UserTopicInterest rows for this user.
    - Insert new rows for each id in payload.topic_ids.
    - Raise HTTP 422 if any topic_id does not exist in the topics table.
    - Return the updated list of TopicResponse objects.
    """
    raise NotImplementedError


async def get_topics(
    db: AsyncSession, current_user: User
) -> list[TopicResponse]:
    """
    Return all Topics the current user has expressed interest in.
    Join UserTopicInterest → Topic, filter by current_user.id.
    """
    raise NotImplementedError
```

- [ ] **Step 4: Create `backend/app/services/topic_service.py`**

```python
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.topic import TLevelResponse, TopicDetailResponse, TopicResponse


async def list_topics(db: AsyncSession) -> list[TopicResponse]:
    """Return all Topic rows ordered by name."""
    raise NotImplementedError


async def get_topic_by_slug(db: AsyncSession, slug: str) -> TopicDetailResponse:
    """
    Return a single Topic with its list of TLevels.
    Raise HTTP 404 if no Topic exists with the given slug.
    """
    raise NotImplementedError


async def get_t_level(
    db: AsyncSession, topic_slug: str, t_level_id: int
) -> TLevelResponse:
    """
    Return a single TLevel by id, scoped to the given topic_slug.
    Raise HTTP 404 if the TLevel does not exist or does not belong to that topic.
    """
    raise NotImplementedError
```

- [ ] **Step 5: Create `backend/app/services/content_service.py`**

```python
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.content import ContentDetailResponse, ContentListResponse


async def list_content(
    db: AsyncSession,
    topic_slug: str | None = None,
    t_level_id: int | None = None,
    content_type: str | None = None,
    tag: str | None = None,
) -> list[ContentListResponse]:
    """
    Return Content rows filtered by the provided query parameters.
    All filters are optional and combinable.
    Do not include body or media_url in list results.
    """
    raise NotImplementedError


async def get_content(db: AsyncSession, content_id: int) -> ContentDetailResponse:
    """
    Return a single Content item including body (Markdown) and a fresh
    pre-signed S3 URL in the media_url field (generated via get_presigned_url).
    Raise HTTP 404 if not found.
    """
    raise NotImplementedError


async def get_presigned_url(s3_key: str, expiry_seconds: int = 900) -> str:
    """
    Generate a pre-signed S3 URL for the given S3 key with the given TTL.

    Use boto3:
        import boto3
        s3 = boto3.client("s3", region_name=get_settings().AWS_REGION)
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": get_settings().S3_BUCKET_NAME, "Key": s3_key},
            ExpiresIn=expiry_seconds,
        )
    """
    raise NotImplementedError
```

- [ ] **Step 6: Create `backend/app/services/feed_service.py`**

```python
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.content import ContentListResponse
from app.schemas.feed import ProgressResponse, ProgressUpdateRequest


async def get_feed(
    db: AsyncSession, current_user: User
) -> list[ContentListResponse]:
    """
    Return a personalised list of Content items for the current user.

    Algorithm (implement in this order):
    1. Find all topic_ids from the user's UserTopicInterest rows.
    2. Find all content_ids the user has already started (UserContentProgress).
    3. Return Content rows whose topic_id is in the user's topics,
       ordered by created_at DESC.

    Future enhancement (do not implement now): re-rank by tag overlap with
    the user's engagement history.
    """
    raise NotImplementedError


async def get_progress(
    db: AsyncSession, current_user: User
) -> list[ProgressResponse]:
    """
    Return the user's in-progress Content items (progress_pct < 100),
    ordered by last_viewed_at DESC.
    Join UserContentProgress → Content to populate the nested content field.
    """
    raise NotImplementedError


async def upsert_progress(
    db: AsyncSession,
    current_user: User,
    content_id: int,
    payload: ProgressUpdateRequest,
) -> None:
    """
    Insert or update a UserContentProgress row.

    - If a row exists for (user_id, content_id): update progress_pct and last_viewed_at.
    - If no row exists: insert a new row.
    - Raise HTTP 404 if content_id does not exist in the content table.
    """
    raise NotImplementedError
```

- [ ] **Step 7: Verify services import correctly**

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://x:x@localhost/x SECRET_KEY=test \
COGNITO_REGION=eu-west-2 COGNITO_USER_POOL_ID=eu-west-2_test \
COGNITO_CLIENT_ID=test S3_BUCKET_NAME=test \
python -c "
from app.services.auth_service import sync_user
from app.services.user_service import get_me, set_topics, get_topics
from app.services.topic_service import list_topics, get_topic_by_slug, get_t_level
from app.services.content_service import list_content, get_content, get_presigned_url
from app.services.feed_service import get_feed, get_progress, upsert_progress
print('OK')
"
```

Expected: `OK`

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/
git commit -m "feat(backend): stub all service functions with typed signatures and docstrings"
```

---

## Task 7: Backend Routers

**Files:**
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/auth.py`
- Create: `backend/app/routers/users.py`
- Create: `backend/app/routers/topics.py`
- Create: `backend/app/routers/content.py`
- Create: `backend/app/routers/feed.py`

- [ ] **Step 1: Create `backend/app/routers/__init__.py`** (empty)

- [ ] **Step 2: Create `backend/app/routers/auth.py`**

```python
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
```

- [ ] **Step 3: Create `backend/app/routers/users.py`**

```python
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
```

- [ ] **Step 4: Create `backend/app/routers/topics.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.topic import TLevelResponse, TopicDetailResponse, TopicResponse
from app.services import topic_service

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("/", response_model=list[TopicResponse], summary="List all topic areas")
async def list_topics(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TopicResponse]:
    return await topic_service.list_topics(db)


@router.get(
    "/{slug}", response_model=TopicDetailResponse, summary="Get topic with T-levels"
)
async def get_topic(
    slug: str,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TopicDetailResponse:
    return await topic_service.get_topic_by_slug(db, slug)


@router.get(
    "/{slug}/t-levels/{t_level_id}",
    response_model=TLevelResponse,
    summary="Get T-level detail",
)
async def get_t_level(
    slug: str,
    t_level_id: int,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TLevelResponse:
    return await topic_service.get_t_level(db, slug, t_level_id)
```

- [ ] **Step 5: Create `backend/app/routers/content.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.content import ContentDetailResponse, ContentListResponse
from app.services import content_service

router = APIRouter(prefix="/content", tags=["content"])


@router.get("/", response_model=list[ContentListResponse], summary="List content")
async def list_content(
    topic: str | None = None,
    t_level_id: int | None = None,
    content_type: str | None = None,
    tag: str | None = None,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ContentListResponse]:
    return await content_service.list_content(db, topic, t_level_id, content_type, tag)


@router.get(
    "/{content_id}",
    response_model=ContentDetailResponse,
    summary="Get content item with body and media URL",
)
async def get_content(
    content_id: int,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContentDetailResponse:
    return await content_service.get_content(db, content_id)


@router.get(
    "/{content_id}/audio-url",
    response_model=dict[str, str],
    summary="Get fresh pre-signed S3 URL for audio",
)
async def get_audio_url(
    content_id: int,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    item = await content_service.get_content(db, content_id)
    url = await content_service.get_presigned_url(item.media_url or "")
    return {"url": url}
```

- [ ] **Step 6: Create `backend/app/routers/feed.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.content import ContentListResponse
from app.schemas.feed import ProgressResponse, ProgressUpdateRequest
from app.services import feed_service

router = APIRouter(tags=["feed"])


@router.get("/feed", response_model=list[ContentListResponse], summary="Personalised feed")
async def get_feed(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ContentListResponse]:
    return await feed_service.get_feed(db, current_user)


@router.get(
    "/progress",
    response_model=list[ProgressResponse],
    summary="Get in-progress content (continue reading)",
)
async def get_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProgressResponse]:
    return await feed_service.get_progress(db, current_user)


@router.post(
    "/progress/{content_id}",
    status_code=204,
    summary="Update reading/listening progress",
)
async def upsert_progress(
    content_id: int,
    payload: ProgressUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await feed_service.upsert_progress(db, current_user, content_id, payload)
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/routers/
git commit -m "feat(backend): stub all routers with correct decorators and dependency injection"
```

---

## Task 8: Backend Wiring + Seed Script

**Files:**
- Modify: `backend/app/main.py`
- Create: `backend/seed.py`

- [ ] **Step 1: Update `backend/app/main.py`** — register all routers

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth, content, feed, topics, users

settings = get_settings()

app = FastAPI(title="T-Level AWS Academy API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(topics.router)
app.include_router(content.router)
app.include_router(feed.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 2: Create `backend/seed.py`**

```python
"""
Seed script — populates Topics, TLevels, Tags, and Content from source data.

Run from the backend/ directory:
    python seed.py

Prerequisites:
    - DATABASE_URL must point to a running Postgres instance
    - Run after `alembic upgrade head` (or equivalent table creation)

Structure:
    - Topics and TLevels are hardcoded below — edit this file to change them.
    - Content items should be added as entries in CONTENT_ITEMS below.
      Set body to a Markdown string for articles; set media_url to an S3 key
      for audio/video.

TODO (implement this script):
    1. Create an async engine from DATABASE_URL
    2. For each entry in TOPICS: upsert a Topic row (insert or update by slug)
    3. For each entry in T_LEVELS: upsert a TLevel row
    4. For each entry in TAGS: upsert a Tag row
    5. For each entry in CONTENT_ITEMS: upsert a Content row and its ContentTag rows
    6. Commit and print a summary
"""

import asyncio

TOPICS = [
    {"slug": "digital", "name": "Digital", "description": "# Digital\n\nTODO", "accent_colour": "#3b82f6"},
    {"slug": "business", "name": "Business", "description": "# Business\n\nTODO", "accent_colour": "#10b981"},
    {"slug": "media", "name": "Media", "description": "# Media\n\nTODO", "accent_colour": "#f59e0b"},
    {"slug": "finance", "name": "Finance", "description": "# Finance\n\nTODO", "accent_colour": "#6366f1"},
    {"slug": "engineering", "name": "Engineering", "description": "# Engineering\n\nTODO", "accent_colour": "#ef4444"},
]

T_LEVELS: list[dict] = [
    # {"topic_slug": "digital", "name": "...", "entry_requirements": "...", "how_to_apply": "..."},
]

TAGS: list[dict] = [
    # {"name": "cloud"},
    # {"name": "networking"},
]

CONTENT_ITEMS: list[dict] = [
    # {
    #     "title": "Introduction to Cloud Computing",
    #     "body": "# Introduction\n\nTODO",
    #     "content_type": "article",
    #     "media_url": None,
    #     "topic_slug": "digital",
    #     "t_level_name": None,
    #     "tags": ["cloud"],
    # },
]


async def main() -> None:
    # TODO: implement seed logic (see module docstring)
    raise NotImplementedError("Implement seed.py before running")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/main.py backend/seed.py
git commit -m "feat(backend): wire all routers into main.py; add seed.py stub"
```

---

## Task 9: Backend Route Tests

**Files:**
- Modify: `backend/tests/test_auth.py`

- [ ] **Step 1: Extend `backend/tests/test_auth.py`** with route existence tests

Add the following tests to the existing file (keep the existing fixtures and tests):

```python
async def test_topics_route_requires_auth(client):
    response = await client.get("/topics/")
    assert response.status_code == 401, f"Expected 401, got {response.status_code} — route may not be registered"


async def test_content_route_requires_auth(client):
    response = await client.get("/content/")
    assert response.status_code == 401


async def test_feed_route_requires_auth(client):
    response = await client.get("/feed")
    assert response.status_code == 401


async def test_progress_route_requires_auth(client):
    response = await client.get("/progress")
    assert response.status_code == 401


async def test_users_me_requires_auth(client):
    response = await client.get("/users/me")
    assert response.status_code == 401


async def test_auth_sync_endpoint_exists(client):
    # No auth required — but needs valid JSON body
    response = await client.post("/auth/sync", json={"first_name": "Test", "last_name": "User"})
    # 422 = route exists, body parsed, but service raises NotImplementedError → 500
    # 401 = route exists but requires auth (check router config)
    # 404 = route not registered (failure)
    assert response.status_code != 404, "POST /auth/sync not registered"
```

- [ ] **Step 2: Run all backend tests**

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://x:x@localhost/x SECRET_KEY=test \
COGNITO_REGION=eu-west-2 COGNITO_USER_POOL_ID=eu-west-2_test \
COGNITO_CLIENT_ID=test S3_BUCKET_NAME=test \
pytest tests/ -v
```

Expected: All auth/route-existence tests PASS. `test_missing_token_returns_401` and `test_invalid_token_returns_401` now PASS (routes registered). Model and schema tests PASS. `test_auth_sync_endpoint_exists` may return 500 (NotImplementedError from service) — that is acceptable for a scaffold.

- [ ] **Step 3: Delete `backend/tests/test_placeholder.py`**

```bash
rm backend/tests/test_placeholder.py
```

- [ ] **Step 4: Commit**

```bash
git add backend/tests/
git commit -m "test(backend): add route-existence and auth tests; remove placeholder"
```

---

## Task 10: Frontend Types + API Modules

**Files:**
- Create: `frontend/src/lib/api/types.ts`
- Create/Modify: `frontend/src/lib/api/client.ts`
- Create: `frontend/src/lib/api/auth.ts`
- Create: `frontend/src/lib/api/topics.ts`
- Create: `frontend/src/lib/api/content.ts`
- Create: `frontend/src/lib/api/feed.ts`
- Create: `frontend/src/lib/api/progress.ts`

- [ ] **Step 1: Create `frontend/src/lib/api/types.ts`**

```typescript
export interface UserResponse {
  id: number;
  cognito_sub: string;
  email: string;
  first_name: string;
  last_name: string;
  created_at: string;
}

export interface TopicResponse {
  id: number;
  slug: string;
  name: string;
  description: string;
  accent_colour: string;
}

export interface TLevelResponse {
  id: number;
  topic_id: number;
  name: string;
  entry_requirements: string;
  how_to_apply: string;
}

export interface TopicDetailResponse extends TopicResponse {
  t_levels: TLevelResponse[];
}

export type ContentType = 'article' | 'audio' | 'video';

export interface TagResponse {
  id: number;
  name: string;
}

export interface ContentListResponse {
  id: number;
  title: string;
  content_type: ContentType;
  topic_id: number;
  t_level_id: number | null;
  tags: TagResponse[];
  created_at: string;
}

export interface ContentDetailResponse extends ContentListResponse {
  body: string | null;
  media_url: string | null;
}

export interface ProgressResponse {
  content_id: number;
  last_viewed_at: string;
  progress_pct: number;
  content: ContentListResponse;
}
```

- [ ] **Step 2: Create `frontend/src/lib/api/client.ts`**

```typescript
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function getToken(): string | null {
  if (typeof localStorage === 'undefined') return null;
  return localStorage.getItem('id_token');
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...init.headers,
  };
  const response = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    const text = await response.text().catch(() => response.statusText);
    throw new ApiError(response.status, text);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
```

- [ ] **Step 3: Create `frontend/src/lib/api/auth.ts`**

```typescript
/**
 * Auth API module — Cognito PKCE token exchange and backend user sync.
 *
 * Token exchange flow:
 * 1. Cognito redirects to /auth/callback?code=<code>
 * 2. Call exchangeCode(code) to get tokens from Cognito
 * 3. Store id_token in localStorage as 'id_token'
 * 4. Call syncUser(firstName, lastName) to create/find the DB user
 */
import { apiFetch } from './client';
import type { UserResponse } from './types';

const COGNITO_DOMAIN = import.meta.env.VITE_COGNITO_DOMAIN as string;
const CLIENT_ID = import.meta.env.VITE_COGNITO_CLIENT_ID as string;
const REDIRECT_URI = import.meta.env.VITE_COGNITO_REDIRECT_URI as string;

export interface TokenResponse {
  access_token: string;
  id_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
}

/**
 * Exchange a Cognito authorization code for tokens using PKCE.
 * Stores the id_token in localStorage under 'id_token'.
 * Returns the full token response.
 */
export async function exchangeCode(code: string): Promise<TokenResponse> {
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: CLIENT_ID,
    code,
    redirect_uri: REDIRECT_URI,
  });
  const response = await fetch(`${COGNITO_DOMAIN}/oauth2/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: body.toString(),
  });
  if (!response.ok) throw new Error(`Token exchange failed: ${response.statusText}`);
  const tokens: TokenResponse = await response.json();
  localStorage.setItem('id_token', tokens.id_token);
  return tokens;
}

/**
 * Call POST /auth/sync to create or update the DB user record.
 * Must be called after exchangeCode so the id_token is in localStorage.
 */
export async function syncUser(firstName: string, lastName: string): Promise<UserResponse> {
  return apiFetch<UserResponse>('/auth/sync', {
    method: 'POST',
    body: JSON.stringify({ first_name: firstName, last_name: lastName }),
  });
}

/** Remove the stored token and redirect to the landing page. */
export function signOut(): void {
  localStorage.removeItem('id_token');
  window.location.href = '/';
}
```

- [ ] **Step 4: Create `frontend/src/lib/api/topics.ts`**

```typescript
import { apiFetch } from './client';
import type { TLevelResponse, TopicDetailResponse, TopicResponse } from './types';

export async function listTopics(): Promise<TopicResponse[]> {
  return apiFetch<TopicResponse[]>('/topics/');
}

export async function getTopic(slug: string): Promise<TopicDetailResponse> {
  return apiFetch<TopicDetailResponse>(`/topics/${slug}`);
}

export async function getTLevel(slug: string, tLevelId: number): Promise<TLevelResponse> {
  return apiFetch<TLevelResponse>(`/topics/${slug}/t-levels/${tLevelId}`);
}
```

- [ ] **Step 5: Create `frontend/src/lib/api/content.ts`**

```typescript
import { apiFetch } from './client';
import type { ContentDetailResponse, ContentListResponse } from './types';

export interface ContentFilters {
  topic?: string;
  t_level_id?: number;
  content_type?: 'article' | 'audio' | 'video';
  tag?: string;
}

export async function listContent(filters: ContentFilters = {}): Promise<ContentListResponse[]> {
  const params = new URLSearchParams();
  if (filters.topic) params.set('topic', filters.topic);
  if (filters.t_level_id) params.set('t_level_id', String(filters.t_level_id));
  if (filters.content_type) params.set('content_type', filters.content_type);
  if (filters.tag) params.set('tag', filters.tag);
  const qs = params.toString();
  return apiFetch<ContentListResponse[]>(`/content/${qs ? `?${qs}` : ''}`);
}

export async function getContent(id: number): Promise<ContentDetailResponse> {
  return apiFetch<ContentDetailResponse>(`/content/${id}`);
}

export async function getAudioUrl(id: number): Promise<string> {
  const result = await apiFetch<{ url: string }>(`/content/${id}/audio-url`);
  return result.url;
}
```

- [ ] **Step 6: Create `frontend/src/lib/api/feed.ts`**

```typescript
import { apiFetch } from './client';
import type { ContentListResponse } from './types';

export async function getFeed(): Promise<ContentListResponse[]> {
  return apiFetch<ContentListResponse[]>('/feed');
}
```

- [ ] **Step 7: Create `frontend/src/lib/api/progress.ts`**

```typescript
import { apiFetch } from './client';
import type { ProgressResponse } from './types';

export async function getProgress(): Promise<ProgressResponse[]> {
  return apiFetch<ProgressResponse[]>('/progress');
}

export async function updateProgress(contentId: number, progressPct: number): Promise<void> {
  return apiFetch<void>(`/progress/${contentId}`, {
    method: 'POST',
    body: JSON.stringify({ progress_pct: progressPct }),
  });
}
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/lib/api/
git commit -m "feat(frontend): add shared types and all API modules"
```

---

## Task 11: Frontend Stores

**Files:**
- Create: `frontend/src/lib/stores/user.ts`
- Create: `frontend/src/lib/stores/topics.ts`
- Create: `frontend/src/lib/stores/progress.ts`

- [ ] **Step 1: Create `frontend/src/lib/stores/user.ts`**

```typescript
import { writable } from 'svelte/store';
import type { TopicResponse, UserResponse } from '$lib/api/types';

/** Authenticated user. null when logged out. Set after /auth/sync succeeds. */
export const currentUser = writable<UserResponse | null>(null);

/** The user's chosen topic interests. Set after onboarding or on app load. */
export const userTopics = writable<TopicResponse[]>([]);
```

- [ ] **Step 2: Create `frontend/src/lib/stores/topics.ts`**

```typescript
import { writable } from 'svelte/store';
import type { TopicResponse } from '$lib/api/types';

/** All 5 platform topics. Loaded once on first authenticated page load. */
export const allTopics = writable<TopicResponse[]>([]);
```

- [ ] **Step 3: Create `frontend/src/lib/stores/progress.ts`**

```typescript
import { writable } from 'svelte/store';
import type { ProgressResponse } from '$lib/api/types';

/** User's in-progress content items (progress_pct < 100). Powers the "Continue Reading" section. */
export const continueReading = writable<ProgressResponse[]>([]);
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/stores/
git commit -m "feat(frontend): add user, topics, and progress stores"
```

---

## Task 12: Frontend UI Primitive Components

**Files:**
- Create: `frontend/src/lib/components/Button.svelte`
- Create: `frontend/src/lib/components/Card.svelte`
- Create: `frontend/src/lib/components/Badge.svelte`
- Create: `frontend/src/lib/components/ProgressBar.svelte`

- [ ] **Step 1: Create `frontend/src/lib/components/Button.svelte`**

```svelte
<!--
  Button
  Purpose: Standard interactive button with variant styles.
  Used in: All pages — forms, CTAs, actions.
  Props:
    - variant ('primary' | 'secondary' | 'danger'): visual style.
      primary = AWS blue (#1f6feb), secondary = muted surface (#21262d), danger = red (#ef4444)
    - disabled (boolean): disables interaction, reduces opacity to 0.5
    - type ('button' | 'submit' | 'reset'): HTML button type, default 'button'
  Slots: default — button label text or content
  Events: forwards native 'click' event to parent
  Styling: border-radius 6px, padding 0.5rem 1.25rem, font-size 0.875rem, cursor pointer
-->
<script lang="ts">
  export let variant: 'primary' | 'secondary' | 'danger' = 'primary';
  export let disabled = false;
  export let type: 'button' | 'submit' | 'reset' = 'button';
</script>

<!-- TODO: Implement button template using variant, disabled, and type props -->
<!-- Forward click event: on:click -->
```

- [ ] **Step 2: Create `frontend/src/lib/components/Card.svelte`**

```svelte
<!--
  Card
  Purpose: Surface container for grouped content.
  Used in: Dashboard panels, topic cards, T-level list items, content blocks.
  Props:
    - title (string | undefined): optional heading rendered above the default slot
  Slots:
    - default: main card body content
    - actions: optional footer row for action buttons (right-aligned)
  Styling:
    background #161b22, border-radius 8px, padding 1.5rem,
    box-shadow 0 1px 4px rgba(0,0,0,0.3), border 1px solid #21262d
-->
<script lang="ts">
  export let title: string | undefined = undefined;
</script>

<!-- TODO: Implement card template with optional title, default slot, and actions slot -->
```

- [ ] **Step 3: Create `frontend/src/lib/components/Badge.svelte`**

```svelte
<!--
  Badge
  Purpose: Small pill label for content type or topic name.
  Used in: FeedItem (content type), TopicCard (topic name), TLevelListItem (topic).
  Props:
    - label (string): text displayed inside the badge
    - colour (string | undefined): hex colour used for background at 20% opacity and text.
      If undefined, use #1f6feb (AWS blue).
  Styling:
    display inline-block, border-radius 999px, padding 0.2rem 0.6rem,
    font-size 0.7rem, font-weight 600, letter-spacing 0.03em,
    background = colour at 20% opacity, color = colour
-->
<script lang="ts">
  export let label: string;
  export let colour: string | undefined = undefined;
</script>

<!-- TODO: Implement badge template. Use inline style for dynamic colour. -->
```

- [ ] **Step 4: Create `frontend/src/lib/components/ProgressBar.svelte`**

```svelte
<!--
  ProgressBar
  Purpose: Thin horizontal bar showing reading or listening completion.
  Used in: FeedItem, ContinueReading items, AudioPlayer, VideoPlayer.
  Props:
    - pct (number): completion percentage, 0–100
  Styling:
    height 4px, border-radius 2px, background-track #21262d,
    background-fill #1f6feb, width of fill = pct%
    Do not show label text — the bar is purely visual.
-->
<script lang="ts">
  export let pct: number;
</script>

<!-- TODO: Implement progress bar. Clamp pct to 0–100 before applying width. -->
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/components/
git commit -m "feat(frontend): stub UI primitive components (Button, Card, Badge, ProgressBar)"
```

---

## Task 13: Frontend Layout Components

**Files:**
- Create: `frontend/src/lib/components/AppShell.svelte`
- Create: `frontend/src/lib/components/Sidebar.svelte`
- Create: `frontend/src/lib/components/Breadcrumb.svelte`

- [ ] **Step 1: Create `frontend/src/lib/components/AppShell.svelte`**

```svelte
<!--
  AppShell
  Purpose: Root layout wrapper for all authenticated pages.
  Used in: src/routes/(app)/+layout.svelte — wraps every protected page.
  Props: none — uses <slot /> for page content
  Layout:
    CSS grid with two columns: sidebar (240px fixed) + main content (1fr).
    Full viewport height (height: 100vh). No overflow on the shell itself —
    the content column scrolls independently.
  Styling:
    background #0d1117 (page background)
    The sidebar column contains <Sidebar />; the content column contains <slot />.
-->
<script lang="ts">
  import Sidebar from '$lib/components/Sidebar.svelte';
  import { currentUser } from '$lib/stores/user';
  import { allTopics } from '$lib/stores/topics';
</script>

<!-- TODO: Implement two-column grid layout with Sidebar and <slot /> -->
```

- [ ] **Step 2: Create `frontend/src/lib/components/Sidebar.svelte`**

```svelte
<!--
  Sidebar
  Purpose: Persistent left navigation showing topic links, branding, user info, and settings.
  Used in: AppShell
  Props:
    - user (UserResponse | null): current user — show first_name or "Guest" if null
    - topics (TopicResponse[]): list of all 5 topics to render as nav links
    - activePath (string): current URL path — highlight matching topic link
  Layout (top to bottom):
    1. Branding: "AWS Academy" logo text
    2. Divider
    3. "Dashboard" link → /dashboard
    4. Topic links → /topics/[slug] for each topic.
       Each link has a 3px left border in the topic's accent_colour on hover/active.
    5. Spacer (flex-grow)
    6. User name + email in small text
    7. Settings link → /settings (gear icon or "Settings" text)
  Styling:
    background #0a2540, full height, width 240px, padding 1rem 0.75rem,
    text-primary #c9d1d9, text-muted #8b949e, font-size 0.875rem
    Active link: bold, accent_colour left border, background rgba(31,111,235,0.1)
-->
<script lang="ts">
  import type { TopicResponse, UserResponse } from '$lib/api/types';

  export let user: UserResponse | null;
  export let topics: TopicResponse[];
  export let activePath: string;
</script>

<!-- TODO: Implement sidebar nav. Use <a href=...> links (SvelteKit handles client routing). -->
<!-- Apply active class when activePath starts with the link's href. -->
```

- [ ] **Step 3: Create `frontend/src/lib/components/Breadcrumb.svelte`**

```svelte
<!--
  Breadcrumb
  Purpose: Shows page hierarchy on topic and T-level pages.
  Used in: /topics/[slug]/+page.svelte, /topics/[slug]/t-levels/[id]/+page.svelte
  Props:
    - crumbs (Array<{ label: string; href: string }>): ordered list of breadcrumb items.
      The last item is the current page (rendered as plain text, not a link).
  Example crumbs for a T-level page:
    [{ label: 'Topics', href: '/dashboard' }, { label: 'Digital', href: '/topics/digital' }, { label: 'T-Level Name', href: '' }]
  Styling:
    font-size 0.8rem, color #8b949e, separator ' / ' between items,
    last item color #c9d1d9 (non-linked, current page)
-->
<script lang="ts">
  export let crumbs: Array<{ label: string; href: string }>;
</script>

<!-- TODO: Render crumbs separated by '/'. Make all items except the last into <a> links. -->
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/components/AppShell.svelte \
  frontend/src/lib/components/Sidebar.svelte \
  frontend/src/lib/components/Breadcrumb.svelte
git commit -m "feat(frontend): stub layout components (AppShell, Sidebar, Breadcrumb)"
```

---

## Task 14: Frontend Dashboard Components

**Files:**
- Create: `frontend/src/lib/components/TopicGrid.svelte`
- Create: `frontend/src/lib/components/TopicCard.svelte`
- Create: `frontend/src/lib/components/PersonalisedFeed.svelte`
- Create: `frontend/src/lib/components/FeedItem.svelte`
- Create: `frontend/src/lib/components/ContinueReading.svelte`

- [ ] **Step 1: Create `frontend/src/lib/components/TopicGrid.svelte`**

```svelte
<!--
  TopicGrid
  Purpose: Displays all 5 topic area cards in a 2×3 grid (5 topics + 1 "Explore All" card).
  Used in: /dashboard (read-only), /onboarding (selectable multi-select).
  Props:
    - topics (TopicResponse[]): all 5 topics from allTopics store
    - selectable (boolean): when true, cards toggle selected state instead of navigating.
      Used on the onboarding page for topic interest selection.
    - selected (number[]): topic ids currently selected (only used when selectable=true)
  Events:
    - selectionChange: dispatched when selectable=true and user toggles a card.
      Payload: { ids: number[] } — full updated list of selected topic ids.
  Styling:
    CSS grid, 2 columns, gap 1rem.
    When selectable=true, clicking a TopicCard toggles it; no navigation.
    When selectable=false, TopicCard is a link to /topics/[slug].
-->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { TopicResponse } from '$lib/api/types';
  import TopicCard from '$lib/components/TopicCard.svelte';

  export let topics: TopicResponse[];
  export let selectable = false;
  export let selected: number[] = [];

  const dispatch = createEventDispatcher<{ selectionChange: { ids: number[] } }>();
</script>

<!-- TODO: Render a TopicCard for each topic. Handle selectionChange dispatch when selectable. -->
```

- [ ] **Step 2: Create `frontend/src/lib/components/TopicCard.svelte`**

```svelte
<!--
  TopicCard
  Purpose: Single topic area card with name, description excerpt, and accent colour.
  Used in: TopicGrid
  Props:
    - topic (TopicResponse): the topic to display
    - selected (boolean): when true, show a blue ring (box-shadow: 0 0 0 2px #1f6feb)
    - selectable (boolean): when true, render as a button; when false, render as <a>
  Styling:
    Card base + 4px left border in topic.accent_colour.
    Hover: lift with box-shadow 0 4px 12px rgba(0,0,0,0.4), translateY(-2px).
    Selected ring: box-shadow 0 0 0 2px #1f6feb.
    When selectable: cursor pointer, no underline.
    Topic name: font-size 1rem, font-weight 600, color #c9d1d9.
    Description: first 80 chars of topic.description (strip Markdown), color #8b949e, font-size 0.8rem.
-->
<script lang="ts">
  import type { TopicResponse } from '$lib/api/types';

  export let topic: TopicResponse;
  export let selected = false;
  export let selectable = false;
</script>

<!-- TODO: Render card. When selectable=false, wrap in <a href="/topics/{topic.slug}">. -->
<!-- When selectable=true, dispatch 'click' event (parent TopicGrid handles selection logic). -->
```

- [ ] **Step 3: Create `frontend/src/lib/components/PersonalisedFeed.svelte`**

```svelte
<!--
  PersonalisedFeed
  Purpose: Right-column container for the personalised content feed on the dashboard.
  Used in: /dashboard — occupies the right column of the content area.
  Props:
    - items (ContentListResponse[]): feed items from GET /feed
    - userProgress (ProgressResponse[]): current user progress, used to show progress_pct on FeedItems
  Behaviour:
    - If items is empty, show a friendly empty state:
      "Nothing in your feed yet — choose some topics to get started."
    - Each item renders as a FeedItem component.
    - Pass progress_pct to FeedItem if a matching ProgressResponse exists for item.id.
  Styling:
    Scrollable column (overflow-y: auto), gap 0.75rem between FeedItems.
    Heading "For You" in font-size 0.7rem, font-weight 700, letter-spacing 0.08em,
    color #8b949e, margin-bottom 0.75rem.
-->
<script lang="ts">
  import type { ContentListResponse, ProgressResponse } from '$lib/api/types';
  import FeedItem from '$lib/components/FeedItem.svelte';

  export let items: ContentListResponse[];
  export let userProgress: ProgressResponse[];
</script>

<!-- TODO: Implement feed column with "For You" heading, FeedItem list, and empty state. -->
```

- [ ] **Step 4: Create `frontend/src/lib/components/FeedItem.svelte`**

```svelte
<!--
  FeedItem
  Purpose: Single content item card in the personalised feed.
  Used in: PersonalisedFeed
  Props:
    - item (ContentListResponse): the content item to display
    - progressPct (number | null): user's progress on this item (null = not started)
  Layout:
    - Title: font-size 0.9rem, font-weight 600, color #c9d1d9
    - Below title: Badge for content_type + topic accent dot (3px circle in topic colour — look up accent from allTopics store)
    - If progressPct is not null: ProgressBar below the badges
  Behaviour:
    - Clicking navigates to /content/[item.id] (create this route if needed) or
      opens the content inline — leave as a TODO comment for juniors.
  Styling:
    background #161b22, border-radius 6px, padding 0.75rem 1rem,
    border-left 3px solid topic accent_colour, hover darkens background to #1c2128, cursor pointer.
-->
<script lang="ts">
  import type { ContentListResponse } from '$lib/api/types';
  import Badge from '$lib/components/Badge.svelte';
  import ProgressBar from '$lib/components/ProgressBar.svelte';
  import { allTopics } from '$lib/stores/topics';

  export let item: ContentListResponse;
  export let progressPct: number | null;
</script>

<!-- TODO: Implement feed item card. Derive topic accent_colour from $allTopics using item.topic_id. -->
```

- [ ] **Step 5: Create `frontend/src/lib/components/ContinueReading.svelte`**

```svelte
<!--
  ContinueReading
  Purpose: Bottom-left dashboard section showing in-progress content items.
  Used in: /dashboard — occupies the bottom-left of the content area.
  Props:
    - items (ProgressResponse[]): in-progress items from GET /progress (progress_pct < 100)
  Layout:
    Horizontal scroll row of compact cards. Each card shows:
      - content.title (truncated to 2 lines)
      - ProgressBar with item.progress_pct
      - content_type Badge
    If items is empty: show "Nothing in progress yet." in muted text.
  Behaviour:
    Clicking a card should navigate to the content item — leave as a TODO for juniors.
  Styling:
    Heading "Continue Reading" same style as "For You" in PersonalisedFeed.
    Cards: min-width 200px, max-width 250px, background #161b22, border-radius 6px,
    padding 0.75rem, box-shadow 0 1px 3px rgba(0,0,0,0.3).
    Container: display flex, gap 0.75rem, overflow-x auto, padding-bottom 0.5rem.
-->
<script lang="ts">
  import type { ProgressResponse } from '$lib/api/types';
  import Badge from '$lib/components/Badge.svelte';
  import ProgressBar from '$lib/components/ProgressBar.svelte';

  export let items: ProgressResponse[];
</script>

<!-- TODO: Implement horizontal scroll row of in-progress content cards. -->
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/components/TopicGrid.svelte \
  frontend/src/lib/components/TopicCard.svelte \
  frontend/src/lib/components/PersonalisedFeed.svelte \
  frontend/src/lib/components/FeedItem.svelte \
  frontend/src/lib/components/ContinueReading.svelte
git commit -m "feat(frontend): stub dashboard components (TopicGrid, TopicCard, Feed, ContinueReading)"
```

---

## Task 15: Frontend Content + Media Components

**Files:**
- Create: `frontend/src/lib/components/TLevelList.svelte`
- Create: `frontend/src/lib/components/TLevelListItem.svelte`
- Create: `frontend/src/lib/components/ContentBlock.svelte`
- Create: `frontend/src/lib/components/AudioPlayer.svelte`
- Create: `frontend/src/lib/components/VideoPlayer.svelte`

- [ ] **Step 1: Create `frontend/src/lib/components/TLevelList.svelte`**

```svelte
<!--
  TLevelList
  Purpose: Left-column list of T-levels for a topic page.
  Used in: /topics/[slug]/+page.svelte — occupies the left column.
  Props:
    - tLevels (TLevelResponse[]): all T-levels for the current topic
    - activeId (number | null): id of the currently active T-level (if viewing detail)
  Behaviour:
    Each item links to /topics/[slug]/t-levels/[id].
    The item matching activeId is highlighted.
    If tLevels is empty: show "No T-levels available for this topic yet."
  Styling:
    Vertical list, no bullets, gap 2px between items.
    Container: min-width 220px, max-width 260px.
-->
<script lang="ts">
  import type { TLevelResponse } from '$lib/api/types';
  import TLevelListItem from '$lib/components/TLevelListItem.svelte';

  export let tLevels: TLevelResponse[];
  export let activeId: number | null;
</script>

<!-- TODO: Render a TLevelListItem for each tLevel. Pass active={tLevel.id === activeId}. -->
```

- [ ] **Step 2: Create `frontend/src/lib/components/TLevelListItem.svelte`**

```svelte
<!--
  TLevelListItem
  Purpose: Single row in the T-level list for a topic page.
  Used in: TLevelList
  Props:
    - tLevel (TLevelResponse): the T-level to display
    - topicSlug (string): the topic's slug, used to build the href
    - active (boolean): when true, apply active styles
  Styling:
    padding 0.6rem 0.75rem, border-radius 4px, font-size 0.875rem,
    color #c9d1d9, cursor pointer, hover background #21262d.
    Active: font-weight 600, background rgba(31,111,235,0.1),
    border-left 3px solid #1f6feb, color #fff.
    Non-active: border-left 3px solid transparent.
    Include a right-facing chevron (›) at the right edge.
-->
<script lang="ts">
  import type { TLevelResponse } from '$lib/api/types';

  export let tLevel: TLevelResponse;
  export let topicSlug: string;
  export let active: boolean;
</script>

<!-- TODO: Render as <a href="/topics/{topicSlug}/t-levels/{tLevel.id}"> with active styles. -->
```

- [ ] **Step 3: Create `frontend/src/lib/components/ContentBlock.svelte`**

```svelte
<!--
  ContentBlock
  Purpose: Renders a single Content item — Markdown article or media player.
  Used in: /topics/[slug]/+page.svelte (topic-level content),
           /topics/[slug]/t-levels/[id]/+page.svelte (T-level content).
  Props:
    - content (ContentDetailResponse): the full content item including body and media_url
  Behaviour:
    - content_type === 'article': render content.body as Markdown HTML using `marked`.
      Import: import { marked } from 'marked'
      Render: {@html marked(content.body ?? '')}
      Wrap in a div with class "prose" for typography styles.
    - content_type === 'audio': render <AudioPlayer contentId={content.id} src={content.media_url ?? ''} />
    - content_type === 'video': render <VideoPlayer contentId={content.id} src={content.media_url ?? ''} />
  Styling:
    Card wrapper (use Card component), title as h3 (font-size 1rem, font-weight 600).
    Prose styles (apply to .prose): line-height 1.7, color #c9d1d9, font-size 0.95rem,
    h1-h3 color #fff, a color #1f6feb, code background #21262d, border-radius 3px, padding 0.1rem 0.3rem.
-->
<script lang="ts">
  import { marked } from 'marked';
  import type { ContentDetailResponse } from '$lib/api/types';
  import AudioPlayer from '$lib/components/AudioPlayer.svelte';
  import VideoPlayer from '$lib/components/VideoPlayer.svelte';
  import Card from '$lib/components/Card.svelte';

  export let content: ContentDetailResponse;
</script>

<!-- TODO: Implement content rendering — switch on content.content_type. -->
```

- [ ] **Step 4: Create `frontend/src/lib/components/AudioPlayer.svelte`**

```svelte
<!--
  AudioPlayer
  Purpose: Streams audio from a pre-signed S3 URL. Reports progress back to the API.
  Used in: ContentBlock (when content_type === 'audio').
  Props:
    - contentId (number): the Content item's id — used when calling updateProgress
    - src (string): pre-signed S3 URL for the audio file
  Behaviour:
    - Render an HTML <audio> element with controls.
    - On 'timeupdate' event: compute progress_pct = (currentTime / duration) * 100.
      Call updateProgress(contentId, Math.floor(progress_pct)) from $lib/api/progress.ts.
      Throttle: only call updateProgress when progress_pct changes by ≥ 5 points
      (track last reported value in a local variable).
    - On 'ended': call updateProgress(contentId, 100).
    - Show a ProgressBar below the audio element with the current progress_pct.
  Styling:
    width 100%, custom dark-themed audio controls if possible (see MDN for styling tips),
    ProgressBar below with pct bound to local progress_pct variable.
-->
<script lang="ts">
  import { updateProgress } from '$lib/api/progress';
  import ProgressBar from '$lib/components/ProgressBar.svelte';

  export let contentId: number;
  export let src: string;

  let progressPct = 0;
</script>

<!-- TODO: Implement audio element with timeupdate handler and ProgressBar. -->
```

- [ ] **Step 5: Create `frontend/src/lib/components/VideoPlayer.svelte`**

```svelte
<!--
  VideoPlayer
  Purpose: Plays video from a pre-signed S3 URL. Reports progress to the API.
  Used in: ContentBlock (when content_type === 'video').
  Props:
    - contentId (number): the Content item's id
    - src (string): pre-signed S3 URL for the video file
  Behaviour:
    Identical progress reporting pattern to AudioPlayer:
    - On 'timeupdate': compute and throttle updateProgress calls (every 5 pct points).
    - On 'ended': call updateProgress(contentId, 100).
    - Show ProgressBar below the video.
  Styling:
    16:9 aspect ratio container (padding-top: 56.25%, position relative),
    <video> fills the container (position absolute, top 0, left 0, width 100%, height 100%),
    controls attribute enabled, background #000.
    ProgressBar below the aspect-ratio container.
-->
<script lang="ts">
  import { updateProgress } from '$lib/api/progress';
  import ProgressBar from '$lib/components/ProgressBar.svelte';

  export let contentId: number;
  export let src: string;

  let progressPct = 0;
</script>

<!-- TODO: Implement 16:9 video container with timeupdate handler and ProgressBar. -->
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/components/TLevelList.svelte \
  frontend/src/lib/components/TLevelListItem.svelte \
  frontend/src/lib/components/ContentBlock.svelte \
  frontend/src/lib/components/AudioPlayer.svelte \
  frontend/src/lib/components/VideoPlayer.svelte
git commit -m "feat(frontend): stub content and media components (TLevelList, ContentBlock, players)"
```

---

## Task 16: Frontend Routes + Layout

**Files:**
- Create: `frontend/src/routes/+layout.ts`
- Modify: `frontend/src/routes/+page.svelte`
- Create: `frontend/src/routes/auth/callback/+page.svelte`
- Create: `frontend/src/routes/(app)/+layout.svelte`
- Create: `frontend/src/routes/(app)/onboarding/+page.svelte`
- Create: `frontend/src/routes/(app)/dashboard/+page.svelte`
- Create: `frontend/src/routes/(app)/topics/[slug]/+page.svelte`
- Create: `frontend/src/routes/(app)/topics/[slug]/t-levels/[id]/+page.svelte`
- Create: `frontend/src/routes/(app)/settings/+page.svelte`

- [ ] **Step 1: Create `frontend/src/routes/+layout.ts`** — disable SSR globally (SPA mode)

```typescript
export const ssr = false;
export const prerender = false;
```

- [ ] **Step 2: Replace `frontend/src/routes/+page.svelte`** — landing page stub

```svelte
<!--
  Landing Page — /
  Public. No auth required.
  Purpose: Entry point for unauthenticated users.
  Contains:
    1. Hero section: platform name "AWS Academy T-Level Guide", tagline, "Get Started" CTA button.
    2. Brief overview row of the 5 topic areas (icons or colour chips).
  Behaviour:
    "Get Started" button href = cognitoLoginUrl (built below).
    If user is already logged in (id_token in localStorage), redirect to /dashboard on mount.
  Cognito login URL format:
    {VITE_COGNITO_DOMAIN}/oauth2/authorize
      ?client_id={VITE_COGNITO_CLIENT_ID}
      &response_type=code
      &scope=openid+profile+email
      &redirect_uri={encodeURIComponent(VITE_COGNITO_REDIRECT_URI)}
  Styling:
    Full-viewport hero, background #0a2540 (dark navy), white heading (font-size 2.5rem),
    muted subtitle (#8b949e), CTA button uses Button variant='primary'.
    No sidebar on this page.
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Button from '$lib/components/Button.svelte';

  const cognitoLoginUrl =
    `${import.meta.env.VITE_COGNITO_DOMAIN}/oauth2/authorize` +
    `?client_id=${import.meta.env.VITE_COGNITO_CLIENT_ID}` +
    `&response_type=code` +
    `&scope=openid+profile+email` +
    `&redirect_uri=${encodeURIComponent(import.meta.env.VITE_COGNITO_REDIRECT_URI)}`;

  onMount(() => {
    if (localStorage.getItem('id_token')) goto('/dashboard');
  });
</script>

<!-- TODO: Implement hero section with "Get Started" CTA linking to cognitoLoginUrl. -->
```

- [ ] **Step 3: Create `frontend/src/routes/auth/callback/+page.svelte`**

```svelte
<!--
  Auth Callback — /auth/callback
  Public. Receives Cognito redirect after login.
  Purpose: Exchange the Cognito authorization code for tokens, sync user to DB, then redirect.
  Query param: ?code=<authorization_code>
  Implementation steps:
    1. On mount: read `code` from $page.url.searchParams.get('code').
       If code is null: show error "No authorization code received."
    2. Call exchangeCode(code) from $lib/api/auth.ts.
       This stores id_token in localStorage and returns the token response.
    3. Decode the id_token JWT (base64 decode the payload — no verification needed client-side,
       the backend verifies). Extract `email` from payload.given_name / family_name if present.
    4. Call syncUser(firstName, lastName) — use payload.given_name and family_name from the token,
       or fallback to empty strings if not present (user can set them in settings).
    5. Call getTopics() from $lib/api/topics.ts (GET /users/me/topics).
       If the result is an empty array: goto('/onboarding').
       Otherwise: goto('/dashboard').
  Error handling:
    Catch any error from steps 2–5. Show an error message with a link back to / for retry.
  Styling:
    Centred loading spinner during exchange. Dark background (#0d1117).
    Error state: red text with "Something went wrong. Try again." and a link to /.
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { exchangeCode, syncUser } from '$lib/api/auth';

  let error = '';
  let loading = true;

  onMount(async () => {
    // TODO: Implement token exchange flow (see steps in comment above).
  });
</script>

<!-- TODO: Show loading spinner while loading=true. Show error message if error is set. -->
```

- [ ] **Step 4: Create `frontend/src/routes/(app)/+layout.svelte`** — auth guard + AppShell

```svelte
<!--
  App Layout — wraps all /(app)/* routes
  Purpose: Client-side auth guard + mounts AppShell with stores populated.
  Behaviour on mount:
    1. Check localStorage for 'id_token'. If absent: goto('/').
    2. Call listTopics() and store result in $allTopics.
    3. Call GET /users/me and store result in $currentUser.
    4. Call getProgress() and store result in $continueReading.
    If any API call returns 401: clear localStorage, goto('/').
  Styling: none — AppShell handles layout.
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import AppShell from '$lib/components/AppShell.svelte';
  import { listTopics } from '$lib/api/topics';
  import { getProgress } from '$lib/api/progress';
  import { apiFetch } from '$lib/api/client';
  import { ApiError } from '$lib/api/client';
  import type { UserResponse } from '$lib/api/types';
  import { currentUser } from '$lib/stores/user';
  import { allTopics } from '$lib/stores/topics';
  import { continueReading } from '$lib/stores/progress';

  onMount(async () => {
    if (!localStorage.getItem('id_token')) {
      goto('/');
      return;
    }
    try {
      const [topics, user, progress] = await Promise.all([
        listTopics(),
        apiFetch<UserResponse>('/users/me'),
        getProgress(),
      ]);
      allTopics.set(topics);
      currentUser.set(user);
      continueReading.set(progress);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        localStorage.removeItem('id_token');
        goto('/');
      }
    }
  });
</script>

<AppShell>
  <slot />
</AppShell>
```

- [ ] **Step 5: Create `frontend/src/routes/(app)/onboarding/+page.svelte`**

```svelte
<!--
  Onboarding — /onboarding
  Protected. Shown to first-time users after Cognito login.
  Purpose: Let the user select their topic interests before reaching the dashboard.
  Behaviour:
    1. Render TopicGrid with selectable=true.
    2. Show a "Continue" Button (disabled until at least 1 topic is selected).
    3. On submit: call PUT /users/me/topics with selected topic ids via setTopics().
       On success: goto('/dashboard').
  Heading: "What are you interested in?" — subtext: "Choose at least one topic area to personalise your experience."
  Styling:
    Centred content, max-width 700px, margin auto. No sidebar needed (but AppShell wraps it).
-->
<script lang="ts">
  import { goto } from '$app/navigation';
  import { apiFetch } from '$lib/api/client';
  import TopicGrid from '$lib/components/TopicGrid.svelte';
  import Button from '$lib/components/Button.svelte';
  import { allTopics } from '$lib/stores/topics';

  let selectedIds: number[] = [];

  async function submit() {
    // TODO: Call PUT /users/me/topics with selectedIds, then goto('/dashboard')
  }
</script>

<!-- TODO: Implement onboarding page with TopicGrid (selectable) and submit button. -->
```

- [ ] **Step 6: Create `frontend/src/routes/(app)/dashboard/+page.svelte`**

```svelte
<!--
  Dashboard — /dashboard
  Protected.
  Purpose: Main authenticated home page.
  Layout (two-column content area, inside AppShell):
    Left column (flex: 1):
      - TopicGrid (top, read-only, shows user's chosen topics from $userTopics)
      - ContinueReading (bottom, items from $continueReading)
    Right column (width: 320px, fixed):
      - PersonalisedFeed
  Data fetching (on mount):
    - GET /feed → feedItems (local variable)
    - $continueReading and $allTopics already populated by (app)/+layout.svelte
  Styling:
    Content area: display flex, gap 1.5rem, padding 1.5rem.
    Left column scrolls independently. Right column is sticky (position sticky, top 0).
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { getFeed } from '$lib/api/feed';
  import type { ContentListResponse } from '$lib/api/types';
  import TopicGrid from '$lib/components/TopicGrid.svelte';
  import PersonalisedFeed from '$lib/components/PersonalisedFeed.svelte';
  import ContinueReading from '$lib/components/ContinueReading.svelte';
  import { allTopics } from '$lib/stores/topics';
  import { continueReading } from '$lib/stores/progress';

  let feedItems: ContentListResponse[] = [];

  onMount(async () => {
    // TODO: feedItems = await getFeed();
  });
</script>

<svelte:head><title>Dashboard — AWS Academy</title></svelte:head>

<!-- TODO: Implement two-column layout with TopicGrid, ContinueReading, PersonalisedFeed. -->
```

- [ ] **Step 7: Create `frontend/src/routes/(app)/topics/[slug]/+page.svelte`**

```svelte
<!--
  Topic Page — /topics/[slug]
  Protected.
  Purpose: Show topic description (right), T-level list (left), and topic content (below).
  Data fetching (on mount):
    - GET /topics/{slug} → topic (TopicDetailResponse — includes t_levels list)
    - GET /content?topic={slug} → topicContent (ContentListResponse[])
    - GET /content/{id} for each item clicked (lazy — fetch detail on T-level selection)
  Layout:
    - Breadcrumb at top: [{ label: 'Topics', href: '/dashboard' }, { label: topic.name, href: '' }]
    - Two-column below breadcrumb:
        Left (260px): TLevelList with topic.t_levels
        Right (flex: 1):
          - Topic description (render topic.description as Markdown using marked)
          - Section heading "Related Content"
          - ContentBlock for each item in topicContent
  Styling: padding 1.5rem, gap 1.5rem between columns.
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { marked } from 'marked';
  import { getTopic } from '$lib/api/topics';
  import { listContent } from '$lib/api/content';
  import type { ContentListResponse, TopicDetailResponse } from '$lib/api/types';
  import TLevelList from '$lib/components/TLevelList.svelte';
  import Breadcrumb from '$lib/components/Breadcrumb.svelte';

  let topic: TopicDetailResponse | null = null;
  let topicContent: ContentListResponse[] = [];

  onMount(async () => {
    const slug = $page.params.slug;
    // TODO: [topic, topicContent] = await Promise.all([getTopic(slug), listContent({ topic: slug })]);
  });
</script>

<svelte:head><title>{topic?.name ?? 'Topic'} — AWS Academy</title></svelte:head>

<!-- TODO: Implement two-column layout with Breadcrumb, TLevelList, description, and content blocks. -->
```

- [ ] **Step 8: Create `frontend/src/routes/(app)/topics/[slug]/t-levels/[id]/+page.svelte`**

```svelte
<!--
  T-Level Detail — /topics/[slug]/t-levels/[id]
  Protected.
  Purpose: Show full T-level detail: entry requirements, how to apply, and related content.
  Data fetching (on mount):
    - GET /topics/{slug}/t-levels/{id} → tLevel (TLevelResponse)
    - GET /content?t_level_id={id} → tLevelContent (ContentListResponse[])
    - For each tLevelContent item: GET /content/{id} when user clicks to expand (lazy)
  Layout:
    - Breadcrumb: [{ label: 'Topics', href: '/dashboard' }, { label: topicName, href: '/topics/{slug}' }, { label: tLevel.name, href: '' }]
    - Main content (single column, max-width 800px):
        h1: tLevel.name
        Section "Entry Requirements": render tLevel.entry_requirements as Markdown
        Section "How to Apply": render tLevel.how_to_apply as Markdown
        Section "Related Content": list of ContentBlock components for tLevelContent
    - Left: TLevelList (same topic's T-levels, activeId = current id) for in-page navigation
  Styling: same two-column pattern as topic page (TLevelList left, content right).
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { marked } from 'marked';
  import { getTLevel, getTopic } from '$lib/api/topics';
  import { listContent } from '$lib/api/content';
  import type { ContentListResponse, TLevelResponse, TopicDetailResponse } from '$lib/api/types';
  import TLevelList from '$lib/components/TLevelList.svelte';
  import Breadcrumb from '$lib/components/Breadcrumb.svelte';

  let tLevel: TLevelResponse | null = null;
  let topic: TopicDetailResponse | null = null;
  let tLevelContent: ContentListResponse[] = [];

  onMount(async () => {
    const { slug, id } = $page.params;
    // TODO: fetch tLevel, topic, and tLevelContent in parallel
  });
</script>

<svelte:head><title>{tLevel?.name ?? 'T-Level'} — AWS Academy</title></svelte:head>

<!-- TODO: Implement two-column layout with Breadcrumb, TLevelList (active), and T-level detail. -->
```

- [ ] **Step 9: Create `frontend/src/routes/(app)/settings/+page.svelte`**

```svelte
<!--
  Settings — /settings
  Protected.
  Purpose: Allow user to update their name and change topic interests.
  Sections:
    1. "Profile" — first_name and last_name fields (text inputs), save via PATCH /users/me
       (add this endpoint to the backend users router if needed).
    2. "Topic Interests" — TopicGrid in selectable mode, pre-selected with current $userTopics.
       Save via PUT /users/me/topics.
  Behaviour:
    - Pre-populate inputs from $currentUser store.
    - Show success/error feedback after each save.
  Styling: max-width 600px, margin auto, padding 1.5rem. Section headings use h2.
-->
<script lang="ts">
  import TopicGrid from '$lib/components/TopicGrid.svelte';
  import Button from '$lib/components/Button.svelte';
  import { currentUser, userTopics } from '$lib/stores/user';
  import { allTopics } from '$lib/stores/topics';

  let firstName = $currentUser?.first_name ?? '';
  let lastName = $currentUser?.last_name ?? '';
  let selectedTopicIds: number[] = $userTopics.map((t) => t.id);
</script>

<svelte:head><title>Settings — AWS Academy</title></svelte:head>

<!-- TODO: Implement profile form and topic interest selection with save buttons. -->
```

- [ ] **Step 10: Commit**

```bash
git add frontend/src/routes/
git commit -m "feat(frontend): scaffold all routes — landing, callback, dashboard, topics, settings"
```

---

## Task 17: Frontend Verification

**Files:**
- Modify: `frontend/src/lib/placeholder.test.ts` → delete and replace
- Create: `frontend/src/lib/scaffold.test.ts`

- [ ] **Step 1: Delete placeholder test and create scaffold smoke test**

Delete `frontend/src/lib/placeholder.test.ts`, then create `frontend/src/lib/scaffold.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';

describe('API types', () => {
  it('types module exports required interfaces', async () => {
    // Dynamic import verifies the module compiles and exports exist at runtime
    const types = await import('$lib/api/types');
    // If this import fails, there is a TypeScript/syntax error in types.ts
    expect(types).toBeDefined();
  });
});

describe('Stores', () => {
  it('user store initialises to null', async () => {
    const { currentUser } = await import('$lib/stores/user');
    let value: unknown;
    currentUser.subscribe((v) => { value = v; })();
    expect(value).toBeNull();
  });

  it('allTopics store initialises to empty array', async () => {
    const { allTopics } = await import('$lib/stores/topics');
    let value: unknown;
    allTopics.subscribe((v) => { value = v; })();
    expect(Array.isArray(value)).toBe(true);
    expect(value).toHaveLength(0);
  });
});
```

- [ ] **Step 2: Run frontend tests**

```bash
cd frontend
npm run test
```

Expected: all tests PASS.

- [ ] **Step 3: Run type check**

```bash
cd frontend
npm run check
```

Expected: 0 errors. Fix any type errors before proceeding — common issues:
- Missing `$lib` path alias: ensure `tsconfig.json` has `"paths": { "$lib/*": ["src/lib/*"] }` (SvelteKit generates this in `.svelte-kit/tsconfig.json`; run `npx svelte-kit sync` first).
- Svelte component prop type mismatches: ensure parent passes the exact type the child declares.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/scaffold.test.ts
git rm frontend/src/lib/placeholder.test.ts
git commit -m "test(frontend): add scaffold smoke tests; remove placeholder"
```

---

## Self-Review

### Spec Coverage

| Spec requirement | Task |
|---|---|
| User, Topic, TLevel, Tag, Content, ContentTag, UserTopicInterest, UserContentProgress models | Task 3 |
| All Pydantic schemas with correct field types | Task 4 |
| JWKS-based Cognito auth dependency | Task 5 |
| `sync_user`, `get_me`, `set_topics`, `get_topics` service stubs | Task 6 |
| `list_topics`, `get_topic_by_slug`, `get_t_level` service stubs | Task 6 |
| `list_content`, `get_content`, `get_presigned_url` service stubs | Task 6 |
| `get_feed`, `get_progress`, `upsert_progress` service stubs | Task 6 |
| All 5 routers with correct decorators and dependency injection | Task 7 |
| main.py with all routers registered | Task 8 |
| seed.py stub with hardcoded topic data | Task 8 |
| Backend route-existence tests (401 not 404) | Task 9 |
| Shared TypeScript types | Task 10 |
| `apiFetch` client with JWT from localStorage | Task 10 |
| `exchangeCode`, `syncUser`, `signOut` in auth.ts | Task 10 |
| All API modules (topics, content, feed, progress) | Task 10 |
| `currentUser`, `userTopics`, `allTopics`, `continueReading` stores | Task 11 |
| Button, Card, Badge, ProgressBar stubs | Task 12 |
| AppShell, Sidebar, Breadcrumb stubs | Task 13 |
| TopicGrid (selectable), TopicCard, PersonalisedFeed, FeedItem, ContinueReading stubs | Task 14 |
| TLevelList, TLevelListItem, ContentBlock, AudioPlayer, VideoPlayer stubs | Task 15 |
| All 7 routes + (app) layout auth guard | Task 16 |
| `ssr = false` / SPA mode | Task 16 |
| Cognito login URL construction on landing page | Task 16 |
| Frontend type check passes | Task 17 |
| Aesthetic guidelines in component comment blocks | Tasks 12–15 |
| `.env.example` with all required vars | Task 1 |
| `svelte.config.js` SPA fallback | Task 1 |

No gaps found.
