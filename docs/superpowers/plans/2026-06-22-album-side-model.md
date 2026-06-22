# Album / Side Data Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Model Albums and Sides, link them to existing Snippets (`Content`) via a many-to-many `SideContent` join table, add enrolment, and expose it all through a public `/albums` API — per `docs/superpowers/specs/2026-06-22-album-side-model-design.md`.

**Architecture:** Four new SQLAlchemy models (`Album`, `Side`, `SideContent`, `AlbumEnrolment`), one Alembic migration, a real (non-stub) `album_service.py`, a public `albums.py` router, an `get_current_user_optional` auth dependency stub, a fix to `content.py`'s incorrect router-level auth, and a Postgres service container added to CI so the new DB-backed tests actually run there.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async ORM, Alembic, pytest + pytest-asyncio + httpx, Poetry.

---

## Before you start

All commands below assume `cd backend` first. You need a local Postgres reachable
at `postgresql+asyncpg://test:test@localhost:5432/test` for the test suite (matches
`tests/conftest.py`). The easiest way:

```bash
docker run -d --name tlevel-test-db -p 5432:5432 \
  -e POSTGRES_USER=test -e POSTGRES_PASSWORD=test -e POSTGRES_DB=test \
  postgres:17-alpine
```

(This is separate from the `docker-compose.yml` `db` service, which uses different
credentials for local app development — the test suite needs its own.)

---

### Task 1: Add DB-backed test fixtures to `conftest.py`

Right now `tests/conftest.py` only sets env vars; there's no way to get a real DB
session or an authenticated/anonymous HTTP client into a test. Every later task
depends on this.

**Files:**
- Modify: `backend/tests/conftest.py`
- Test: `backend/tests/test_health.py` (existing — must still pass after this change)

- [ ] **Step 1: Rewrite `conftest.py`**

```python
import os

# Set env vars before any app module is imported, because get_settings() is
# called at module-level in database.py and cached via lru_cache.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.database import get_db  # noqa: E402
from app.dependencies.auth import get_current_user, get_current_user_optional  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.models.user import User  # noqa: E402

_engine = create_async_engine(get_settings().DATABASE_URL)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


@pytest.fixture
async def db_session() -> AsyncSession:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with _session_factory() as session:
        yield session

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def current_user(db_session: AsyncSession) -> User:
    user = User(
        cognito_sub="test-sub",
        email="test@example.com",
        first_name="Test",
        last_name="User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def client(db_session: AsyncSession, current_user: User) -> AsyncClient:
    """
    Anonymous-by-default test client: get_db is overridden with the test session,
    get_current_user (required-auth routes) returns the fixture user, and
    get_current_user_optional returns None — i.e. requests look anonymous to any
    route using optional auth, unless you use `authenticated_client` instead.
    """

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return current_user

    async def override_get_current_user_optional():
        return None

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_user_optional] = override_get_current_user_optional

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(client: AsyncClient, current_user: User) -> AsyncClient:
    """Same as `client`, but get_current_user_optional also returns the fixture user."""

    async def override_get_current_user_optional():
        return current_user

    app.dependency_overrides[get_current_user_optional] = override_get_current_user_optional
    yield client
```

- [ ] **Step 2: Run the existing health test to confirm fixtures didn't break it**

Run: `poetry run pytest tests/test_health.py -v`
Expected: `PASSED` (requires the local test Postgres from "Before you start" to be running, even though this particular test doesn't touch the DB — `client` now always sets up `db_session`).

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add DB session and auth-override fixtures to conftest"
```

---

### Task 2: Add `Album`, `Side`, `SideContent`, `AlbumEnrolment` models

**Files:**
- Create: `backend/app/models/album.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Write `app/models/album.py`**

```python
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class Album(Base):
    __tablename__ = "albums"

    id: Mapped[int] = mapped_column(primary_key=True)
    t_level_id: Mapped[int] = mapped_column(ForeignKey("t_levels.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    icon: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    t_level: Mapped["TLevel"] = relationship()
    sides: Mapped[list["Side"]] = relationship(
        back_populates="album",
        order_by="Side.position",
        cascade="all, delete-orphan",
    )


class Side(Base):
    __tablename__ = "sides"

    id: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int] = mapped_column(ForeignKey("albums.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    position: Mapped[int] = mapped_column(Integer)

    album: Mapped["Album"] = relationship(back_populates="sides")
    side_contents: Mapped[list["SideContent"]] = relationship(
        back_populates="side",
        order_by="SideContent.position",
        cascade="all, delete-orphan",
    )


class SideContent(Base):
    __tablename__ = "side_content"

    side_id: Mapped[int] = mapped_column(ForeignKey("sides.id"), primary_key=True)
    content_id: Mapped[int] = mapped_column(
        ForeignKey("content.id"), primary_key=True, index=True
    )
    position: Mapped[int] = mapped_column(Integer)

    side: Mapped["Side"] = relationship(back_populates="side_contents")
    content: Mapped["Content"] = relationship()


class AlbumEnrolment(Base):
    __tablename__ = "album_enrolments"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    album_id: Mapped[int] = mapped_column(ForeignKey("albums.id"), primary_key=True)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship()
    album: Mapped["Album"] = relationship()
```

- [ ] **Step 2: Register the new models in `app/models/__init__.py`**

The file currently ends with:

```python
from app.models.content import Content, ContentTag, ContentType, Tag  # noqa: E402, F401
from app.models.progress import UserContentProgress  # noqa: E402, F401
from app.models.t_level import TLevel  # noqa: E402, F401
from app.models.topic import Topic  # noqa: E402, F401
from app.models.user import User, UserTopicInterest  # noqa: E402, F401
```

Add one line, keeping alphabetical order:

```python
from app.models.album import Album, AlbumEnrolment, Side, SideContent  # noqa: E402, F401
from app.models.content import Content, ContentTag, ContentType, Tag  # noqa: E402, F401
from app.models.progress import UserContentProgress  # noqa: E402, F401
from app.models.t_level import TLevel  # noqa: E402, F401
from app.models.topic import Topic  # noqa: E402, F401
from app.models.user import User, UserTopicInterest  # noqa: E402, F401
```

- [ ] **Step 3: Verify the models import cleanly**

Run: `poetry run python -c "from app.models import Album, Side, SideContent, AlbumEnrolment; print('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add app/models/album.py app/models/__init__.py
git commit -m "feat: add Album, Side, SideContent, AlbumEnrolment models"
```

---

### Task 3: Migration for the new tables

**Files:**
- Create: `backend/migrations/versions/<autogenerated>_add_album_side_models.py`

- [ ] **Step 1: Generate the migration skeleton**

Run: `poetry run alembic revision --autogenerate -m "add album, side, side_content, album_enrolments"`
Expected: a new file at `migrations/versions/<hash>_add_album_side_models.py` is created. Note the `<hash>` for the next step — it'll differ each run.

- [ ] **Step 2: Replace the file's `upgrade()`/`downgrade()` bodies**

Open the generated file. Keep its existing `revision = "..."` and `down_revision = "0893638fd517"` lines exactly as autogenerated. Replace the `upgrade()` and `downgrade()` function bodies with:

```python
def upgrade() -> None:
    op.create_table(
        "albums",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("t_level_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("icon", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["t_level_id"], ["t_levels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_albums_t_level_id"), "albums", ["t_level_id"], unique=False)

    op.create_table(
        "sides",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("album_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["album_id"], ["albums.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sides_album_id"), "sides", ["album_id"], unique=False)

    op.create_table(
        "side_content",
        sa.Column("side_id", sa.Integer(), nullable=False),
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["side_id"], ["sides.id"]),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"]),
        sa.PrimaryKeyConstraint("side_id", "content_id"),
    )
    op.create_index(
        op.f("ix_side_content_content_id"), "side_content", ["content_id"], unique=False
    )

    op.create_table(
        "album_enrolments",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("album_id", sa.Integer(), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["album_id"], ["albums.id"]),
        sa.PrimaryKeyConstraint("user_id", "album_id"),
    )


def downgrade() -> None:
    op.drop_table("album_enrolments")
    op.drop_index(op.f("ix_side_content_content_id"), table_name="side_content")
    op.drop_table("side_content")
    op.drop_index(op.f("ix_sides_album_id"), table_name="sides")
    op.drop_table("sides")
    op.drop_index(op.f("ix_albums_t_level_id"), table_name="albums")
    op.drop_table("albums")
```

- [ ] **Step 3: Apply the migration against your local dev DB**

Run: `poetry run alembic upgrade head` (requires the `docker-compose.yml` `db` service running, or whatever DB your `.env`'s `DATABASE_URL` points at)
Expected: no errors; ends with output mentioning the new revision hash.

- [ ] **Step 4: Roll it back and re-apply, to prove `downgrade()` is correct too**

Run: `poetry run alembic downgrade -1 && poetry run alembic upgrade head`
Expected: both commands succeed with no errors.

- [ ] **Step 5: Commit**

```bash
git add migrations/versions/
git commit -m "feat: add migration for album, side, side_content, album_enrolments"
```

---

### Task 4: Fix `content.py` — Snippets must be public

`app/routers/content.py` currently requires auth on every route via a router-level
dependency. CLAUDE.md requires Snippet routes to be public. This is unrelated to the
Album feature itself but was found while designing it, and the new `albums.py` router
needs to follow the *correct* pattern, not copy the bug.

**Files:**
- Modify: `backend/app/routers/content.py`
- Test: `backend/tests/test_content.py` (new)

- [ ] **Step 1: Write the failing test**

```python
from httpx import AsyncClient


async def test_list_content_does_not_require_auth(client: AsyncClient) -> None:
    response = await client.get("/content/")
    assert response.status_code != 401
```

Note: `client` overrides `get_current_user` to always succeed, so this test alone
wouldn't currently fail — the point isn't that it 401s today, it's that the route
*shouldn't depend on auth succeeding at all*. Step 2 makes that explicit by checking
the dependency is gone from the router declaration itself, which is the actual bug.
Replace the test above with this instead:

```python
from httpx import AsyncClient

from app.routers.content import router


def test_content_router_has_no_router_level_auth_dependency() -> None:
    assert router.dependencies == []
```

- [ ] **Step 2: Run it to verify it fails**

Run: `poetry run pytest tests/test_content.py -v`
Expected: `FAIL` — `router.dependencies` currently contains the `get_current_user` dependency, not `[]`.

- [ ] **Step 3: Remove the router-level auth dependency**

In `app/routers/content.py`, change:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.content import ContentDetailResponse, ContentListResponse
from app.services import content_service

router = APIRouter(prefix="/content", tags=["content"], dependencies=[Depends(get_current_user)])
```

to:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.content import ContentDetailResponse, ContentListResponse
from app.services import content_service

router = APIRouter(prefix="/content", tags=["content"])
```

(`get_current_user` and its `Depends` import are no longer used anywhere else in this
file — the rest of the file only uses `Depends(get_db)`.)

- [ ] **Step 4: Run the test again to verify it passes**

Run: `poetry run pytest tests/test_content.py -v`
Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/routers/content.py tests/test_content.py
git commit -m "fix: make content (Snippet) routes public, not auth-gated"
```

---

### Task 5: Add `get_current_user_optional` dependency

**Files:**
- Modify: `backend/app/dependencies/auth.py`

- [ ] **Step 1: Add the optional-auth dependency**

```python
from app.models.user import User


async def get_current_user() -> User:
    # Replace this with a real implementation (local JWT or Cognito) when auth is decided.
    raise NotImplementedError


async def get_current_user_optional() -> User | None:
    # Replace this with a real implementation (local JWT or Cognito) when auth is decided.
    # Must return None when no Authorization header is present, rather than raising —
    # used by routes that behave differently for logged-in vs anonymous requests
    # (e.g. GET /albums/{id}) without requiring auth to succeed.
    raise NotImplementedError
```

- [ ] **Step 2: Verify it imports cleanly**

Run: `poetry run python -c "from app.dependencies.auth import get_current_user_optional; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add app/dependencies/auth.py
git commit -m "feat: add get_current_user_optional auth dependency stub"
```

---

### Task 6: Album schemas

**Files:**
- Create: `backend/app/schemas/album.py`

- [ ] **Step 1: Write the schemas**

```python
from pydantic import BaseModel

from app.models.content import ContentType

__all__ = [
    "AlbumListResponse",
    "SnippetSummaryResponse",
    "SideResponse",
    "AlbumDetailResponse",
]


class AlbumListResponse(BaseModel):
    id: int
    t_level_id: int
    title: str
    description: str
    icon: str

    model_config = {"from_attributes": True}


class SnippetSummaryResponse(BaseModel):
    id: int
    title: str
    content_type: ContentType

    model_config = {"from_attributes": True}


class SideResponse(BaseModel):
    id: int
    title: str
    position: int
    snippets: list[SnippetSummaryResponse]


class AlbumDetailResponse(AlbumListResponse):
    sides: list[SideResponse]
    enrolled: bool | None = None
    completed_count: int | None = None
    total_count: int | None = None
    progress_pct: int | None = None
```

`enrolled`/`completed_count`/`total_count`/`progress_pct` default to `None` and the
route will use `response_model_exclude_none=True` (Task 9) so anonymous responses
omit them entirely, per the spec.

- [ ] **Step 2: Verify it imports cleanly**

Run: `poetry run python -c "from app.schemas.album import AlbumDetailResponse; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add app/schemas/album.py
git commit -m "feat: add Album/Side response schemas"
```

---

### Task 7: `album_service.list_albums`

**Files:**
- Create: `backend/app/services/album_service.py`
- Test: `backend/tests/test_album_service.py` (new)

- [ ] **Step 1: Write the failing test**

```python
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.album import Album
from app.models.t_level import TLevel
from app.models.topic import Topic
from app.services import album_service


async def _make_topic_and_t_level(db: AsyncSession) -> TLevel:
    topic = Topic(
        slug="digital-production", name="Digital Production", description="...", accent_colour="#0066CC"
    )
    db.add(topic)
    await db.flush()
    t_level = TLevel(
        topic_id=topic.id,
        name="Digital Production, Design and Development",
        entry_requirements="...",
        how_to_apply="...",
    )
    db.add(t_level)
    await db.flush()
    return t_level


async def test_list_albums_returns_all_albums_by_default(db_session: AsyncSession) -> None:
    t_level = await _make_topic_and_t_level(db_session)
    db_session.add(
        Album(t_level_id=t_level.id, title="Cloud Computing", description="...", icon="cloud")
    )
    await db_session.commit()

    result = await album_service.list_albums(db_session)

    assert len(result) == 1
    assert result[0].title == "Cloud Computing"


async def test_list_albums_filters_by_t_level_id(db_session: AsyncSession) -> None:
    t_level = await _make_topic_and_t_level(db_session)
    db_session.add(
        Album(t_level_id=t_level.id, title="Cloud Computing", description="...", icon="cloud")
    )
    await db_session.commit()

    result = await album_service.list_albums(db_session, t_level_id=t_level.id + 1)

    assert result == []
```

- [ ] **Step 2: Run to verify it fails**

Run: `poetry run pytest tests/test_album_service.py -v`
Expected: `FAIL` — `album_service` module doesn't exist yet.

- [ ] **Step 3: Implement `album_service.list_albums`**

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.album import Album
from app.models.t_level import TLevel
from app.models.topic import Topic
from app.schemas.album import AlbumListResponse


async def list_albums(
    db: AsyncSession,
    t_level_id: int | None = None,
    topic: str | None = None,
) -> list[AlbumListResponse]:
    stmt = select(Album)
    if t_level_id is not None:
        stmt = stmt.where(Album.t_level_id == t_level_id)
    if topic is not None:
        stmt = (
            stmt.join(TLevel, Album.t_level_id == TLevel.id)
            .join(Topic, TLevel.topic_id == Topic.id)
            .where(Topic.slug == topic)
        )

    result = await db.execute(stmt)
    albums = result.scalars().all()
    return [AlbumListResponse.model_validate(album) for album in albums]
```

- [ ] **Step 4: Run to verify it passes**

Run: `poetry run pytest tests/test_album_service.py -v`
Expected: both tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/services/album_service.py tests/test_album_service.py
git commit -m "feat: implement album_service.list_albums"
```

---

### Task 8: `album_service.get_album_detail` — anonymous path

**Files:**
- Modify: `backend/app/services/album_service.py`
- Modify: `backend/tests/test_album_service.py`

- [ ] **Step 1: Write the failing tests**

Add `import pytest`, `from app.models.album import Side, SideContent`, and
`from app.models.content import Content, ContentType` to the **top** of
`tests/test_album_service.py`, alongside the existing imports — not inline with the
new code below. Then append the following to the bottom of the file:

```python
async def _make_album_with_side_and_snippet(db: AsyncSession) -> Album:
    t_level = await _make_topic_and_t_level(db)
    album = Album(t_level_id=t_level.id, title="Cloud Computing", description="...", icon="cloud")
    db.add(album)
    await db.flush()

    side = Side(album_id=album.id, title="Side A", position=0)
    db.add(side)
    await db.flush()

    content = Content(
        title="What is the cloud?",
        content_type=ContentType.article,
        topic_id=t_level.topic_id,
    )
    db.add(content)
    await db.flush()

    db.add(SideContent(side_id=side.id, content_id=content.id, position=0))
    await db.commit()
    return album


async def test_get_album_detail_returns_404_for_missing_album(db_session: AsyncSession) -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await album_service.get_album_detail(db_session, album_id=999, current_user=None)
    assert exc_info.value.status_code == 404


async def test_get_album_detail_anonymous_includes_sides_but_no_progress(
    db_session: AsyncSession,
) -> None:
    album = await _make_album_with_side_and_snippet(db_session)

    detail = await album_service.get_album_detail(db_session, album.id, current_user=None)

    assert detail.title == "Cloud Computing"
    assert len(detail.sides) == 1
    assert detail.sides[0].snippets[0].title == "What is the cloud?"
    assert detail.enrolled is None
    assert detail.progress_pct is None
```

- [ ] **Step 2: Run to verify it fails**

Run: `poetry run pytest tests/test_album_service.py -v`
Expected: `FAIL` — `get_album_detail` doesn't exist yet (`AttributeError`).

- [ ] **Step 3: Implement the anonymous path**

At the top of `app/services/album_service.py`, alongside the existing imports from
Task 7, add:

```python
from fastapi import HTTPException
from sqlalchemy.orm import selectinload

from app.models.album import AlbumEnrolment, Side, SideContent
from app.models.progress import UserContentProgress
from app.models.user import User
from app.schemas.album import AlbumDetailResponse, SideResponse, SnippetSummaryResponse
```

Then append the following to the bottom of the file:

```python
async def get_album_detail(
    db: AsyncSession,
    album_id: int,
    current_user: User | None,
) -> AlbumDetailResponse:
    stmt = (
        select(Album)
        .where(Album.id == album_id)
        .options(
            selectinload(Album.sides)
            .selectinload(Side.side_contents)
            .selectinload(SideContent.content)
        )
    )
    album = (await db.execute(stmt)).scalar_one_or_none()
    if album is None:
        raise HTTPException(status_code=404, detail="Album not found")

    sides = [
        SideResponse(
            id=side.id,
            title=side.title,
            position=side.position,
            snippets=[
                SnippetSummaryResponse.model_validate(sc.content)
                for sc in sorted(side.side_contents, key=lambda sc: sc.position)
            ],
        )
        for side in sorted(album.sides, key=lambda s: s.position)
    ]

    detail = AlbumDetailResponse(
        id=album.id,
        t_level_id=album.t_level_id,
        title=album.title,
        description=album.description,
        icon=album.icon,
        sides=sides,
    )

    if current_user is None:
        return detail

    return await _add_progress_fields(db, detail, album, current_user)


async def _add_progress_fields(
    db: AsyncSession,
    detail: AlbumDetailResponse,
    album: Album,
    current_user: User,
) -> AlbumDetailResponse:
    raise NotImplementedError
```

(`_add_progress_fields` is a deliberate stub here — Task 9 implements it. This step
should make the two new tests pass without needing it, since both use
`current_user=None`.)

- [ ] **Step 4: Run to verify it passes**

Run: `poetry run pytest tests/test_album_service.py -v`
Expected: all tests so far `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/services/album_service.py tests/test_album_service.py
git commit -m "feat: implement album_service.get_album_detail (anonymous path)"
```

---

### Task 9: `album_service.get_album_detail` — authenticated/progress path

**Files:**
- Modify: `backend/app/services/album_service.py`
- Modify: `backend/tests/test_album_service.py`

- [ ] **Step 1: Write the failing tests**

Add `from app.models.album import AlbumEnrolment`,
`from app.models.progress import UserContentProgress`, and
`from app.models.user import User` to the **top** of `tests/test_album_service.py`.
Then append the following to the bottom of the file:

```python
async def _make_user(db: AsyncSession) -> User:
    user = User(cognito_sub="sub-1", email="a@example.com", first_name="A", last_name="B")
    db.add(user)
    await db.flush()
    return user


async def test_get_album_detail_authenticated_not_enrolled(db_session: AsyncSession) -> None:
    album = await _make_album_with_side_and_snippet(db_session)
    user = await _make_user(db_session)
    await db_session.commit()

    detail = await album_service.get_album_detail(db_session, album.id, current_user=user)

    assert detail.enrolled is False
    assert detail.progress_pct is None


async def test_get_album_detail_authenticated_enrolled_partial_progress(
    db_session: AsyncSession,
) -> None:
    album = await _make_album_with_side_and_snippet(db_session)
    user = await _make_user(db_session)
    db_session.add(AlbumEnrolment(user_id=user.id, album_id=album.id))
    await db_session.commit()

    detail = await album_service.get_album_detail(db_session, album.id, current_user=user)

    assert detail.enrolled is True
    assert detail.total_count == 1
    assert detail.completed_count == 0
    assert detail.progress_pct == 0


async def test_get_album_detail_authenticated_enrolled_full_progress(
    db_session: AsyncSession,
) -> None:
    album = await _make_album_with_side_and_snippet(db_session)
    user = await _make_user(db_session)
    db_session.add(AlbumEnrolment(user_id=user.id, album_id=album.id))

    content_id = album.sides[0].side_contents[0].content_id
    db_session.add(
        UserContentProgress(user_id=user.id, content_id=content_id, progress_pct=100)
    )
    await db_session.commit()

    detail = await album_service.get_album_detail(db_session, album.id, current_user=user)

    assert detail.completed_count == 1
    assert detail.total_count == 1
    assert detail.progress_pct == 100
```

- [ ] **Step 2: Run to verify it fails**

Run: `poetry run pytest tests/test_album_service.py -v`
Expected: `FAIL` — `_add_progress_fields` raises `NotImplementedError`.

- [ ] **Step 3: Implement `_add_progress_fields`**

Replace the stub in `app/services/album_service.py`:

```python
async def _add_progress_fields(
    db: AsyncSession,
    detail: AlbumDetailResponse,
    album: Album,
    current_user: User,
) -> AlbumDetailResponse:
    enrolment_stmt = select(AlbumEnrolment).where(
        AlbumEnrolment.user_id == current_user.id,
        AlbumEnrolment.album_id == album.id,
    )
    enrolment = (await db.execute(enrolment_stmt)).scalar_one_or_none()
    detail.enrolled = enrolment is not None

    if enrolment is None:
        return detail

    content_ids = [sc.content_id for side in album.sides for sc in side.side_contents]
    total_count = len(content_ids)
    detail.total_count = total_count

    if total_count == 0:
        detail.completed_count = 0
        detail.progress_pct = 0
        return detail

    completed_stmt = select(func.count()).where(
        UserContentProgress.user_id == current_user.id,
        UserContentProgress.content_id.in_(content_ids),
        UserContentProgress.progress_pct == 100,
    )
    completed_count = (await db.execute(completed_stmt)).scalar_one()
    detail.completed_count = completed_count
    detail.progress_pct = round(completed_count / total_count * 100)
    return detail
```

In `app/services/album_service.py`, change the existing `from sqlalchemy import select`
line (added in Task 7) to `from sqlalchemy import func, select` — `func` is newly
needed for `func.count()` above.

- [ ] **Step 4: Run to verify it passes**

Run: `poetry run pytest tests/test_album_service.py -v`
Expected: all tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/services/album_service.py tests/test_album_service.py
git commit -m "feat: implement album progress computation for authenticated users"
```

---

### Task 10: `album_service.enrol` / `unenrol`

**Files:**
- Modify: `backend/app/services/album_service.py`
- Modify: `backend/tests/test_album_service.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_album_service.py`:

```python
async def test_enrol_creates_enrolment(db_session: AsyncSession) -> None:
    album = await _make_album_with_side_and_snippet(db_session)
    user = await _make_user(db_session)
    await db_session.commit()

    await album_service.enrol(db_session, album.id, user)

    enrolment = (
        await db_session.execute(
            select(AlbumEnrolment).where(
                AlbumEnrolment.user_id == user.id, AlbumEnrolment.album_id == album.id
            )
        )
    ).scalar_one_or_none()
    assert enrolment is not None


async def test_enrol_twice_is_idempotent(db_session: AsyncSession) -> None:
    album = await _make_album_with_side_and_snippet(db_session)
    user = await _make_user(db_session)
    await db_session.commit()

    await album_service.enrol(db_session, album.id, user)
    await album_service.enrol(db_session, album.id, user)

    count = (
        await db_session.execute(
            select(func.count()).where(
                AlbumEnrolment.user_id == user.id, AlbumEnrolment.album_id == album.id
            )
        )
    ).scalar_one()
    assert count == 1


async def test_enrol_raises_404_for_missing_album(db_session: AsyncSession) -> None:
    from fastapi import HTTPException

    user = await _make_user(db_session)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await album_service.enrol(db_session, album_id=999, user=user)
    assert exc_info.value.status_code == 404


async def test_unenrol_removes_enrolment(db_session: AsyncSession) -> None:
    album = await _make_album_with_side_and_snippet(db_session)
    user = await _make_user(db_session)
    db_session.add(AlbumEnrolment(user_id=user.id, album_id=album.id))
    await db_session.commit()

    await album_service.unenrol(db_session, album.id, user)

    enrolment = (
        await db_session.execute(
            select(AlbumEnrolment).where(
                AlbumEnrolment.user_id == user.id, AlbumEnrolment.album_id == album.id
            )
        )
    ).scalar_one_or_none()
    assert enrolment is None


async def test_unenrol_when_not_enrolled_is_idempotent(db_session: AsyncSession) -> None:
    album = await _make_album_with_side_and_snippet(db_session)
    user = await _make_user(db_session)
    await db_session.commit()

    await album_service.unenrol(db_session, album.id, user)  # should not raise
```

- [ ] **Step 2: Run to verify it fails**

Run: `poetry run pytest tests/test_album_service.py -v`
Expected: `FAIL` — `enrol`/`unenrol` don't exist yet.

- [ ] **Step 3: Implement `enrol` and `unenrol`**

In `app/services/album_service.py`, change the `from sqlalchemy import func, select`
line (from Task 9) to `from sqlalchemy import delete, func, select`. Then append:

```python
async def enrol(db: AsyncSession, album_id: int, user: User) -> None:
    album = (await db.execute(select(Album).where(Album.id == album_id))).scalar_one_or_none()
    if album is None:
        raise HTTPException(status_code=404, detail="Album not found")

    existing = (
        await db.execute(
            select(AlbumEnrolment).where(
                AlbumEnrolment.user_id == user.id, AlbumEnrolment.album_id == album_id
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return

    db.add(AlbumEnrolment(user_id=user.id, album_id=album_id))
    await db.commit()


async def unenrol(db: AsyncSession, album_id: int, user: User) -> None:
    await db.execute(
        delete(AlbumEnrolment).where(
            AlbumEnrolment.user_id == user.id, AlbumEnrolment.album_id == album_id
        )
    )
    await db.commit()
```

- [ ] **Step 4: Run to verify it passes**

Run: `poetry run pytest tests/test_album_service.py -v`
Expected: all tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/services/album_service.py tests/test_album_service.py
git commit -m "feat: implement album_service.enrol and unenrol"
```

---

### Task 11: `album_service.add_content_to_side` — one-Side-per-Album enforcement

This is the helper that enforces the rule from the spec: a Snippet can be in Sides of
different Albums, but only one Side within the same Album. It's not exposed via the
API in this plan (no content-authoring endpoints exist yet) — it exists so seed
scripts/future admin tooling have a correct way to assign Snippets to Sides, and so
the rule is tested now while the model is fresh.

**Files:**
- Modify: `backend/app/services/album_service.py`
- Modify: `backend/tests/test_album_service.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_album_service.py`:

```python
async def test_add_content_to_side_creates_membership(db_session: AsyncSession) -> None:
    t_level = await _make_topic_and_t_level(db_session)
    album = Album(t_level_id=t_level.id, title="Cloud Computing", description="...", icon="cloud")
    db_session.add(album)
    await db_session.flush()
    side = Side(album_id=album.id, title="Side A", position=0)
    db_session.add(side)
    await db_session.flush()
    content = Content(title="Intro", content_type=ContentType.article, topic_id=t_level.topic_id)
    db_session.add(content)
    await db_session.commit()

    await album_service.add_content_to_side(db_session, side.id, content.id, position=0)

    membership = (
        await db_session.execute(
            select(SideContent).where(
                SideContent.side_id == side.id, SideContent.content_id == content.id
            )
        )
    ).scalar_one_or_none()
    assert membership is not None


async def test_add_content_to_side_can_reuse_snippet_across_albums(
    db_session: AsyncSession,
) -> None:
    t_level = await _make_topic_and_t_level(db_session)
    content = Content(title="Shared intro", content_type=ContentType.video, topic_id=t_level.topic_id)
    db_session.add(content)
    await db_session.flush()

    album_1 = Album(t_level_id=t_level.id, title="Album 1", description="...", icon="a")
    album_2 = Album(t_level_id=t_level.id, title="Album 2", description="...", icon="b")
    db_session.add_all([album_1, album_2])
    await db_session.flush()
    side_1 = Side(album_id=album_1.id, title="Side A", position=0)
    side_2 = Side(album_id=album_2.id, title="Side A", position=0)
    db_session.add_all([side_1, side_2])
    await db_session.commit()

    await album_service.add_content_to_side(db_session, side_1.id, content.id, position=0)
    await album_service.add_content_to_side(db_session, side_2.id, content.id, position=0)

    count = (
        await db_session.execute(
            select(func.count()).where(SideContent.content_id == content.id)
        )
    ).scalar_one()
    assert count == 2


async def test_add_content_to_side_moves_within_same_album(db_session: AsyncSession) -> None:
    t_level = await _make_topic_and_t_level(db_session)
    album = Album(t_level_id=t_level.id, title="Cloud Computing", description="...", icon="cloud")
    db_session.add(album)
    await db_session.flush()
    side_a = Side(album_id=album.id, title="Side A", position=0)
    side_b = Side(album_id=album.id, title="Side B", position=1)
    db_session.add_all([side_a, side_b])
    await db_session.flush()
    content = Content(title="Intro", content_type=ContentType.article, topic_id=t_level.topic_id)
    db_session.add(content)
    await db_session.commit()

    await album_service.add_content_to_side(db_session, side_a.id, content.id, position=0)
    await album_service.add_content_to_side(db_session, side_b.id, content.id, position=0)

    count = (
        await db_session.execute(
            select(func.count()).where(SideContent.content_id == content.id)
        )
    ).scalar_one()
    assert count == 1
    membership = (
        await db_session.execute(
            select(SideContent).where(SideContent.content_id == content.id)
        )
    ).scalar_one()
    assert membership.side_id == side_b.id
```

- [ ] **Step 2: Run to verify it fails**

Run: `poetry run pytest tests/test_album_service.py -v`
Expected: `FAIL` — `add_content_to_side` doesn't exist yet.

- [ ] **Step 3: Implement `add_content_to_side`**

Add to `app/services/album_service.py`:

```python
async def add_content_to_side(
    db: AsyncSession,
    side_id: int,
    content_id: int,
    position: int,
) -> None:
    side = (await db.execute(select(Side).where(Side.id == side_id))).scalar_one_or_none()
    if side is None:
        raise HTTPException(status_code=404, detail="Side not found")

    sibling_side_ids = (
        (await db.execute(select(Side.id).where(Side.album_id == side.album_id)))
        .scalars()
        .all()
    )

    await db.execute(
        delete(SideContent).where(
            SideContent.content_id == content_id,
            SideContent.side_id.in_(sibling_side_ids),
        )
    )
    db.add(SideContent(side_id=side_id, content_id=content_id, position=position))
    await db.commit()
```

- [ ] **Step 4: Run to verify it passes**

Run: `poetry run pytest tests/test_album_service.py -v`
Expected: all tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/services/album_service.py tests/test_album_service.py
git commit -m "feat: implement add_content_to_side with one-side-per-album enforcement"
```

---

### Task 12: `albums` router + register in `main.py`

**Files:**
- Create: `backend/app/routers/albums.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_albums_router.py` (new)

- [ ] **Step 1: Write the failing tests**

```python
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.album import Album, AlbumEnrolment, Side, SideContent
from app.models.content import Content, ContentType
from app.models.t_level import TLevel
from app.models.topic import Topic
from app.models.user import User


async def _make_album_with_side_and_snippet(db: AsyncSession) -> Album:
    topic = Topic(slug="digital-production", name="Digital Production", description="...", accent_colour="#0066CC")
    db.add(topic)
    await db.flush()
    t_level = TLevel(topic_id=topic.id, name="Digital Production", entry_requirements="...", how_to_apply="...")
    db.add(t_level)
    await db.flush()
    album = Album(t_level_id=t_level.id, title="Cloud Computing", description="...", icon="cloud")
    db.add(album)
    await db.flush()
    side = Side(album_id=album.id, title="Side A", position=0)
    db.add(side)
    await db.flush()
    content = Content(title="What is the cloud?", content_type=ContentType.article, topic_id=topic.id)
    db.add(content)
    await db.flush()
    db.add(SideContent(side_id=side.id, content_id=content.id, position=0))
    await db.commit()
    return album


async def test_list_albums(client: AsyncClient, db_session: AsyncSession) -> None:
    await _make_album_with_side_and_snippet(db_session)

    response = await client.get("/albums/")

    assert response.status_code == 200
    assert response.json()[0]["title"] == "Cloud Computing"


async def test_get_album_detail_anonymous_omits_progress_fields(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    album = await _make_album_with_side_and_snippet(db_session)

    response = await client.get(f"/albums/{album.id}")

    assert response.status_code == 200
    body = response.json()
    assert "enrolled" not in body
    assert "progress_pct" not in body
    assert body["sides"][0]["snippets"][0]["title"] == "What is the cloud?"


async def test_get_album_detail_authenticated_includes_enrolled_field(
    authenticated_client: AsyncClient, db_session: AsyncSession
) -> None:
    album = await _make_album_with_side_and_snippet(db_session)

    response = await authenticated_client.get(f"/albums/{album.id}")

    assert response.status_code == 200
    assert response.json()["enrolled"] is False


async def test_get_album_detail_404(client: AsyncClient) -> None:
    response = await client.get("/albums/999")
    assert response.status_code == 404


async def test_enrol_then_unenrol(
    client: AsyncClient, db_session: AsyncSession, current_user: User
) -> None:
    album = await _make_album_with_side_and_snippet(db_session)

    enrol_response = await client.post(f"/albums/{album.id}/enrol")
    assert enrol_response.status_code == 204

    detail_response = await client.get(f"/albums/{album.id}")
    assert detail_response.json()["enrolled"] is True

    unenrol_response = await client.delete(f"/albums/{album.id}/enrol")
    assert unenrol_response.status_code == 204

    detail_response_2 = await client.get(f"/albums/{album.id}")
    assert detail_response_2.json()["enrolled"] is False
```

- [ ] **Step 2: Run to verify it fails**

Run: `poetry run pytest tests/test_albums_router.py -v`
Expected: `FAIL` — `404 Not Found` for all routes (router doesn't exist/isn't registered).

- [ ] **Step 3: Write `app/routers/albums.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.album import AlbumDetailResponse, AlbumListResponse
from app.services import album_service

router = APIRouter(prefix="/albums", tags=["albums"])


@router.get("/", response_model=list[AlbumListResponse], summary="List albums")
async def list_albums(
    t_level_id: int | None = None,
    topic: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[AlbumListResponse]:
    return await album_service.list_albums(db, t_level_id, topic)


@router.get(
    "/{album_id}",
    response_model=AlbumDetailResponse,
    response_model_exclude_none=True,
    summary="Get album detail with sides and snippets",
)
async def get_album(
    album_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> AlbumDetailResponse:
    return await album_service.get_album_detail(db, album_id, current_user)


@router.post("/{album_id}/enrol", status_code=204, summary="Enrol in an album")
async def enrol(
    album_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await album_service.enrol(db, album_id, current_user)


@router.delete("/{album_id}/enrol", status_code=204, summary="Un-enrol from an album")
async def unenrol(
    album_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await album_service.unenrol(db, album_id, current_user)
```

- [ ] **Step 4: Register the router in `app/main.py`**

Change:

```python
from app.routers import auth, content, feed, topics, users
```

to:

```python
from app.routers import albums, auth, content, feed, topics, users
```

And add, after the other `app.include_router(...)` calls:

```python
app.include_router(albums.router)
```

- [ ] **Step 5: Run to verify it passes**

Run: `poetry run pytest tests/test_albums_router.py -v`
Expected: all tests `PASSED`

- [ ] **Step 6: Commit**

```bash
git add app/routers/albums.py app/main.py tests/test_albums_router.py
git commit -m "feat: add /albums router and register it in the app"
```

---

### Task 13: Add Postgres service container to CI

**Files:**
- Modify: `.github/workflows/backend.yml`

- [ ] **Step 1: Add the `services:` block to the `test` job**

Change:

```yaml
  test:
    name: Test
    runs-on: ubuntu-latest
    needs: lint-autofix
    steps:
```

to:

```yaml
  test:
    name: Test
    runs-on: ubuntu-latest
    needs: lint-autofix
    services:
      postgres:
        image: postgres:17-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U test"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5
    steps:
```

This matches the `DATABASE_URL` already set in the job's `Run tests` step
(`postgresql+asyncpg://test:test@localhost:5432/test`) and in `tests/conftest.py`.

- [ ] **Step 2: Verify the YAML is well-formed**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/backend.yml'))" ` (from repo root)
Expected: no output, no error.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/backend.yml
git commit -m "ci: add postgres service container so backend DB tests run in CI"
```

- [ ] **Step 4: Push and confirm the workflow run is green**

```bash
git push origin dev
```

Then check the run: `gh run list --workflow=backend.yml --branch=dev --limit 1` and
`gh run view <run-id>` once it completes. Expected: `Test` job passes, including the
new `test_album_service.py`, `test_albums_router.py`, and `test_content.py` files.

---

### Task 14: Full local verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full backend test suite**

Run: `poetry run pytest tests/ -v`
Expected: all tests `PASSED`, including pre-existing `test_health.py`.

- [ ] **Step 2: Run ruff**

Run: `poetry run ruff check app/ tests/`
Expected: no errors (or only auto-fixable ones — run `poetry run ruff check --fix app/ tests/` and re-check).

- [ ] **Step 3: Confirm migration head matches models**

Run: `poetry run alembic check` (Alembic 1.13+: fails if models and the latest migration are out of sync)
Expected: no output / exit code 0.
