# Topics → T-Levels Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Topics stub with a T-Levels two-level experience (index → topic detail) and implement the /learn page (albums grouped by topic), both using a shared NavSidebar + scroll-to-section pattern.

**Architecture:** `Topic → TLevel → Album` FK chain already in DB. Backend implements topic_service stubs and exposes `topic_id` in album responses. Frontend adds `/t-levels` and `/t-levels/[slug]` routes, rewrites `/learn`, and generalises `NavSidebar` and `AlbumCard` to be data-agnostic.

**Tech Stack:** FastAPI + SQLAlchemy async (backend), SvelteKit 2 / Svelte 4 + TypeScript (frontend). Backend tests use pytest-asyncio + real Postgres via conftest fixtures. Frontend uses `npm run check` (svelte-check) for typecheck and `npx vitest run` for unit tests.

**Spec:** `docs/superpowers/specs/2026-06-29-topics-refactor-design.md`

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Modify | `backend/app/models/topic.py` | Add `t_levels` relationship |
| Modify | `backend/app/models/t_level.py` | Add `albums` relationship, update `back_populates` on `topic` |
| Modify | `backend/app/models/album.py` | Add `back_populates="albums"` to `t_level` relationship |
| Modify | `backend/app/routers/topics.py` | Remove router-level auth dependency |
| Modify | `backend/app/schemas/topic.py` | Add `TLevelWithAlbumsResponse`, update `TopicDetailResponse` |
| Modify | `backend/app/schemas/album.py` | Add `topic_id: int` to `AlbumListResponse` |
| Modify | `backend/app/services/topic_service.py` | Implement all three stubs |
| Modify | `backend/app/services/album_service.py` | Eager-load `t_level`, manual response construction in `list_albums` and `get_album_detail` |
| Create | `backend/tests/test_topic_service.py` | Service-level tests for all three topic functions |
| Modify | `frontend/src/lib/api/types.ts` | Add `topic_id` to `AlbumListResponse`, add `TLevelWithAlbumsResponse`, update `TopicDetailResponse` |
| Modify | `frontend/src/lib/api/topics.ts` | Implement `listTopics` and `getTopic` against real API |
| Modify | `frontend/src/lib/components/Navbar.svelte` | Rename "Topics" → "T-Levels", change href |
| Modify | `frontend/src/lib/components/NavSidebar.svelte` | Generic `links` + `activeHref` props |
| Modify | `frontend/src/lib/components/AlbumCard.svelte` | Optional `href`, `label`, make `album` optional |
| Modify | `frontend/src/routes/learn/+page.svelte` | Full implementation: fetch topics + albums, group, NavSidebar |
| Create | `frontend/src/routes/t-levels/+page.svelte` | Topic index: 2×2 AlbumCard grid |
| Create | `frontend/src/routes/t-levels/[slug]/+page.svelte` | Topic detail: NavSidebar + t_level sections |
| Delete | `frontend/src/routes/topics/+page.svelte` | Remove old stub |

---

## Task 1: Add SQLAlchemy back_populates relationships

No migration needed — these are Python-only relationship descriptors, no new columns.

**Files:**
- Modify: `backend/app/models/topic.py`
- Modify: `backend/app/models/t_level.py`
- Modify: `backend/app/models/album.py`

- [ ] **Step 1: Update `topic.py`**

Replace the full file contents of `backend/app/models/topic.py`:

```python
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    accent_colour: Mapped[str] = mapped_column(String(7))

    t_levels: Mapped[list["TLevel"]] = relationship(
        back_populates="topic", order_by="TLevel.id"
    )
```

- [ ] **Step 2: Update `t_level.py`**

Replace the full file contents of `backend/app/models/t_level.py`:

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

    topic: Mapped["Topic"] = relationship(back_populates="t_levels")
    albums: Mapped[list["Album"]] = relationship(
        back_populates="t_level", order_by="Album.id"
    )
```

- [ ] **Step 3: Update `album.py` — add `back_populates` to existing `t_level` relationship**

In `backend/app/models/album.py`, find:

```python
    t_level: Mapped["TLevel"] = relationship()
```

Replace with:

```python
    t_level: Mapped["TLevel"] = relationship(back_populates="albums")
```

- [ ] **Step 4: Run the existing test suite to confirm nothing broke**

```bash
docker compose exec backend poetry run pytest tests/ -x -q
```

Expected: all existing tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/topic.py backend/app/models/t_level.py backend/app/models/album.py
git commit -m "refactor: add back_populates relationships Topic.t_levels, TLevel.albums"
```

---

## Task 2: Fix topics.py router auth + implement `list_topics`

**Files:**
- Modify: `backend/app/routers/topics.py`
- Modify: `backend/app/services/topic_service.py`
- Create: `backend/tests/test_topic_service.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_topic_service.py`:

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.topic import Topic
from app.models.t_level import TLevel
from app.services import topic_service


async def _make_topic(db: AsyncSession, slug: str = "digital", name: str = "Digital") -> Topic:
    topic = Topic(slug=slug, name=name, description="Desc", accent_colour="#0066CC")
    db.add(topic)
    await db.flush()
    return topic


async def _make_t_level(db: AsyncSession, topic_id: int, name: str = "Cloud Computing") -> TLevel:
    t_level = TLevel(
        topic_id=topic_id,
        name=name,
        entry_requirements="5 GCSEs",
        how_to_apply="Apply online",
    )
    db.add(t_level)
    await db.flush()
    return t_level


async def test_list_topics_returns_all_topics_ordered_by_name(db_session: AsyncSession) -> None:
    await _make_topic(db_session, slug="digital", name="Digital")
    await _make_topic(db_session, slug="business", name="Business")
    await db_session.commit()

    result = await topic_service.list_topics(db_session)

    assert len(result) == 2
    assert result[0].name == "Business"
    assert result[1].name == "Digital"


async def test_list_topics_returns_empty_list_when_no_topics(db_session: AsyncSession) -> None:
    result = await topic_service.list_topics(db_session)
    assert result == []
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
docker compose exec backend poetry run pytest tests/test_topic_service.py -v
```

Expected: FAIL — `NotImplementedError`.

- [ ] **Step 3: Fix the router-level auth dependency**

In `backend/app/routers/topics.py`, change line 9 from:

```python
router = APIRouter(prefix="/topics", tags=["topics"], dependencies=[Depends(get_current_user)])
```

To:

```python
router = APIRouter(prefix="/topics", tags=["topics"])
```

Also remove the now-unused import at the top of the file. The full updated `topics.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.topic import TLevelResponse, TopicDetailResponse, TopicResponse
from app.services import topic_service

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("/", response_model=list[TopicResponse], summary="List all topic areas")
async def list_topics(
    db: AsyncSession = Depends(get_db),
) -> list[TopicResponse]:
    return await topic_service.list_topics(db)


@router.get("/{slug}", response_model=TopicDetailResponse, summary="Get topic with T-levels")
async def get_topic(
    slug: str,
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
    db: AsyncSession = Depends(get_db),
) -> TLevelResponse:
    return await topic_service.get_t_level(db, slug, t_level_id)
```

- [ ] **Step 4: Implement `list_topics`**

Replace the full contents of `backend/app/services/topic_service.py`:

```python
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.t_level import TLevel
from app.models.topic import Topic
from app.schemas.topic import TLevelResponse, TopicDetailResponse, TopicResponse


async def list_topics(db: AsyncSession) -> list[TopicResponse]:
    result = await db.execute(select(Topic).order_by(Topic.name))
    return [TopicResponse.model_validate(t) for t in result.scalars().all()]


async def get_topic_by_slug(db: AsyncSession, slug: str) -> TopicDetailResponse:
    raise NotImplementedError


async def get_t_level(db: AsyncSession, topic_slug: str, t_level_id: int) -> TLevelResponse:
    raise NotImplementedError
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
docker compose exec backend poetry run pytest tests/test_topic_service.py -v
```

Expected: both `list_topics` tests pass; other tests still `NotImplementedError` (none written for them yet).

- [ ] **Step 6: Verify the router is now anonymous-accessible**

```bash
docker compose exec backend poetry run pytest tests/ -x -q
```

Expected: all existing tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/app/routers/topics.py backend/app/services/topic_service.py backend/tests/test_topic_service.py
git commit -m "feat: fix topics router auth + implement list_topics"
```

---

## Task 3: Add `topic_id` to `AlbumListResponse` + update `list_albums` and `get_album_detail`

**Files:**
- Modify: `backend/app/schemas/album.py`
- Modify: `backend/app/services/album_service.py`

- [ ] **Step 1: Add `topic_id` to `AlbumListResponse` in `backend/app/schemas/album.py`**

Find:

```python
class AlbumListResponse(BaseModel):
    id: int
    t_level_id: int
    title: str
    description: str
    icon: str

    model_config = {"from_attributes": True}
```

Replace with:

```python
class AlbumListResponse(BaseModel):
    id: int
    t_level_id: int
    topic_id: int
    title: str
    description: str
    icon: str

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Update `list_albums` in `backend/app/services/album_service.py`**

Find the `list_albums` function and replace it:

```python
async def list_albums(
    db: AsyncSession,
    t_level_id: int | None = None,
    topic: str | None = None,
) -> list[AlbumListResponse]:
    stmt = select(Album).options(selectinload(Album.t_level))
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
    return [
        AlbumListResponse(
            id=album.id,
            t_level_id=album.t_level_id,
            topic_id=album.t_level.topic_id,
            title=album.title,
            description=album.description,
            icon=album.icon,
        )
        for album in albums
    ]
```

- [ ] **Step 3: Update `get_album_detail` to also load `t_level` and include `topic_id`**

In `get_album_detail`, find:

```python
    stmt = (
        select(Album)
        .where(Album.id == album_id)
        .options(
            selectinload(Album.sides)
            .selectinload(Side.side_contents)
            .selectinload(SideContent.content)
        )
    )
```

Replace with:

```python
    stmt = (
        select(Album)
        .where(Album.id == album_id)
        .options(
            selectinload(Album.t_level),
            selectinload(Album.sides)
            .selectinload(Side.side_contents)
            .selectinload(SideContent.content),
        )
    )
```

Then find the `AlbumDetailResponse(...)` construction:

```python
    detail = AlbumDetailResponse(
        id=album.id,
        t_level_id=album.t_level_id,
        title=album.title,
        description=album.description,
        icon=album.icon,
        sides=sides,
    )
```

Replace with:

```python
    detail = AlbumDetailResponse(
        id=album.id,
        t_level_id=album.t_level_id,
        topic_id=album.t_level.topic_id,
        title=album.title,
        description=album.description,
        icon=album.icon,
        sides=sides,
    )
```

- [ ] **Step 4: Run the full test suite**

```bash
docker compose exec backend poetry run pytest tests/ -x -q
```

Expected: all tests pass. The existing album service tests create a Topic and TLevel via `_make_topic_and_t_level`, so `album.t_level.topic_id` will be populated correctly.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/album.py backend/app/services/album_service.py
git commit -m "feat: add topic_id to AlbumListResponse, eager-load t_level in album_service"
```

---

## Task 4: Add `TLevelWithAlbumsResponse` + implement `get_topic_by_slug`

**Files:**
- Modify: `backend/app/schemas/topic.py`
- Modify: `backend/app/services/topic_service.py`
- Modify: `backend/tests/test_topic_service.py`

- [ ] **Step 1: Add `TLevelWithAlbumsResponse` and update `TopicDetailResponse` in `backend/app/schemas/topic.py`**

Replace the full file:

```python
from pydantic import BaseModel

from app.schemas.album import AlbumListResponse


class TLevelResponse(BaseModel):
    id: int
    topic_id: int
    name: str
    entry_requirements: str
    how_to_apply: str

    model_config = {"from_attributes": True}


class TLevelWithAlbumsResponse(TLevelResponse):
    albums: list[AlbumListResponse]


class TopicResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    accent_colour: str

    model_config = {"from_attributes": True}


class TopicDetailResponse(TopicResponse):
    t_levels: list[TLevelWithAlbumsResponse]
```

- [ ] **Step 2: Write the failing test for `get_topic_by_slug`**

Append to `backend/tests/test_topic_service.py`:

```python
from app.models.album import Album


async def test_get_topic_by_slug_returns_topic_with_t_levels_and_albums(
    db_session: AsyncSession,
) -> None:
    topic = await _make_topic(db_session, slug="digital", name="Digital")
    t_level = await _make_t_level(db_session, topic.id, name="Cloud Computing")
    album = Album(
        t_level_id=t_level.id,
        title="Intro to Cloud",
        description="An intro album",
        icon="cloud",
    )
    db_session.add(album)
    await db_session.commit()

    result = await topic_service.get_topic_by_slug(db_session, "digital")

    assert result.slug == "digital"
    assert result.name == "Digital"
    assert len(result.t_levels) == 1
    assert result.t_levels[0].name == "Cloud Computing"
    assert len(result.t_levels[0].albums) == 1
    assert result.t_levels[0].albums[0].title == "Intro to Cloud"
    assert result.t_levels[0].albums[0].topic_id == topic.id


async def test_get_topic_by_slug_raises_404_for_unknown_slug(db_session: AsyncSession) -> None:
    from fastapi import HTTPException
    import pytest

    with pytest.raises(HTTPException) as exc_info:
        await topic_service.get_topic_by_slug(db_session, "nonexistent")

    assert exc_info.value.status_code == 404


async def test_get_topic_by_slug_returns_empty_t_levels_when_none(
    db_session: AsyncSession,
) -> None:
    await _make_topic(db_session, slug="finance", name="Finance")
    await db_session.commit()

    result = await topic_service.get_topic_by_slug(db_session, "finance")

    assert result.slug == "finance"
    assert result.t_levels == []
```

- [ ] **Step 3: Run the tests to verify they fail**

```bash
docker compose exec backend poetry run pytest tests/test_topic_service.py::test_get_topic_by_slug_returns_topic_with_t_levels_and_albums -v
```

Expected: FAIL — `NotImplementedError`.

- [ ] **Step 4: Implement `get_topic_by_slug`**

In `backend/app/services/topic_service.py`, replace the `get_topic_by_slug` stub:

```python
async def get_topic_by_slug(db: AsyncSession, slug: str) -> TopicDetailResponse:
    stmt = (
        select(Topic)
        .where(Topic.slug == slug)
        .options(selectinload(Topic.t_levels).selectinload(TLevel.albums))
    )
    result = await db.execute(stmt)
    topic = result.scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    return TopicDetailResponse(
        id=topic.id,
        slug=topic.slug,
        name=topic.name,
        description=topic.description,
        accent_colour=topic.accent_colour,
        t_levels=[
            TLevelWithAlbumsResponse(
                id=t.id,
                topic_id=t.topic_id,
                name=t.name,
                entry_requirements=t.entry_requirements,
                how_to_apply=t.how_to_apply,
                albums=[
                    AlbumListResponse(
                        id=a.id,
                        t_level_id=a.t_level_id,
                        topic_id=topic.id,
                        title=a.title,
                        description=a.description,
                        icon=a.icon,
                    )
                    for a in t.albums
                ],
            )
            for t in topic.t_levels
        ],
    )
```

Also add the missing import at the top of `topic_service.py`. The full import block should be:

```python
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.t_level import TLevel
from app.models.topic import Topic
from app.schemas.album import AlbumListResponse
from app.schemas.topic import TLevelResponse, TLevelWithAlbumsResponse, TopicDetailResponse, TopicResponse
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
docker compose exec backend poetry run pytest tests/test_topic_service.py -v
```

Expected: all topic service tests pass.

- [ ] **Step 6: Run full suite**

```bash
docker compose exec backend poetry run pytest tests/ -x -q
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/topic.py backend/app/services/topic_service.py backend/tests/test_topic_service.py
git commit -m "feat: add TLevelWithAlbumsResponse, implement get_topic_by_slug"
```

---

## Task 5: Implement `get_t_level`

**Files:**
- Modify: `backend/app/services/topic_service.py`
- Modify: `backend/tests/test_topic_service.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_topic_service.py`:

```python
async def test_get_t_level_returns_t_level_scoped_to_topic(db_session: AsyncSession) -> None:
    topic = await _make_topic(db_session, slug="digital", name="Digital")
    t_level = await _make_t_level(db_session, topic.id, name="Cloud Computing")
    await db_session.commit()

    result = await topic_service.get_t_level(db_session, "digital", t_level.id)

    assert result.id == t_level.id
    assert result.name == "Cloud Computing"
    assert result.topic_id == topic.id


async def test_get_t_level_raises_404_for_wrong_topic_slug(db_session: AsyncSession) -> None:
    from fastapi import HTTPException
    import pytest

    topic = await _make_topic(db_session, slug="digital", name="Digital")
    t_level = await _make_t_level(db_session, topic.id)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await topic_service.get_t_level(db_session, "business", t_level.id)

    assert exc_info.value.status_code == 404


async def test_get_t_level_raises_404_for_nonexistent_id(db_session: AsyncSession) -> None:
    from fastapi import HTTPException
    import pytest

    await _make_topic(db_session, slug="digital", name="Digital")
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await topic_service.get_t_level(db_session, "digital", 9999)

    assert exc_info.value.status_code == 404
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
docker compose exec backend poetry run pytest tests/test_topic_service.py::test_get_t_level_returns_t_level_scoped_to_topic -v
```

Expected: FAIL — `NotImplementedError`.

- [ ] **Step 3: Implement `get_t_level`**

In `backend/app/services/topic_service.py`, replace the `get_t_level` stub:

```python
async def get_t_level(db: AsyncSession, topic_slug: str, t_level_id: int) -> TLevelResponse:
    stmt = (
        select(TLevel)
        .join(Topic, TLevel.topic_id == Topic.id)
        .where(TLevel.id == t_level_id, Topic.slug == topic_slug)
    )
    result = await db.execute(stmt)
    t_level = result.scalar_one_or_none()
    if t_level is None:
        raise HTTPException(status_code=404, detail="T-Level not found")
    return TLevelResponse.model_validate(t_level)
```

- [ ] **Step 4: Run all topic service tests**

```bash
docker compose exec backend poetry run pytest tests/test_topic_service.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Run full suite**

```bash
docker compose exec backend poetry run pytest tests/ -x -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/topic_service.py backend/tests/test_topic_service.py
git commit -m "feat: implement get_t_level with topic slug scoping"
```

---

## Task 6: Update frontend API types + implement `topics.ts`

**Files:**
- Modify: `frontend/src/lib/api/types.ts`
- Modify: `frontend/src/lib/api/topics.ts`

- [ ] **Step 1: Update `frontend/src/lib/api/types.ts`**

Make two changes:

**a)** Add `topic_id` to `AlbumListResponse`. Find:

```typescript
export interface AlbumListResponse {
  id: number;
  t_level_id: number;
  title: string;
  description: string;
  icon: string;
}
```

Replace with:

```typescript
export interface AlbumListResponse {
  id: number;
  t_level_id: number;
  topic_id: number;
  title: string;
  description: string;
  icon: string;
}
```

**b)** Add `TLevelWithAlbumsResponse` and update `TopicDetailResponse`. Find:

```typescript
export interface TopicDetailResponse extends TopicResponse {
  t_levels: TLevelResponse[];
}
```

Replace with:

```typescript
export interface TLevelWithAlbumsResponse extends TLevelResponse {
  albums: AlbumListResponse[];
}

export interface TopicDetailResponse extends TopicResponse {
  t_levels: TLevelWithAlbumsResponse[];
}
```

- [ ] **Step 2: Implement `listTopics` and `getTopic` in `frontend/src/lib/api/topics.ts`**

Replace the full file:

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

export async function getUserTopics(): Promise<TopicResponse[]> {
  return apiFetch<TopicResponse[]>('/users/me/topics');
}
```

- [ ] **Step 3: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 4: Run frontend tests**

```bash
cd frontend && npx vitest run
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/api/types.ts frontend/src/lib/api/topics.ts
git commit -m "feat: add topic_id to AlbumListResponse type, implement listTopics/getTopic"
```

---

## Task 7: Update Navbar

**Files:**
- Modify: `frontend/src/lib/components/Navbar.svelte`

- [ ] **Step 1: Rename "Topics" to "T-Levels" and update the href**

In `frontend/src/lib/components/Navbar.svelte`, find:

```svelte
      <NavLink href="/topics" label="Topics" />
```

Replace with:

```svelte
      <NavLink href="/t-levels" label="T-Levels" />
```

- [ ] **Step 2: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/components/Navbar.svelte
git commit -m "feat: rename Topics nav link to T-Levels"
```

---

## Task 8: Refactor `NavSidebar.svelte`

**Files:**
- Modify: `frontend/src/lib/components/NavSidebar.svelte`

- [ ] **Step 1: Replace NavSidebar with generic links + activeHref**

Replace the full file contents of `frontend/src/lib/components/NavSidebar.svelte`:

```svelte
<!--
  NavSidebar
  Purpose: Section-navigation sidebar used on /learn and /t-levels/[slug]. Renders a
    vertical list of anchor links that scroll to named sections on the same page. The
    active link is highlighted based on the activeHref prop, which the parent page
    updates via IntersectionObserver as the user scrolls.
  Used in: /learn, /t-levels/[slug]
  Props:
    - links ({ label: string; href: string }[]): ordered list of anchor links
    - activeHref (string): href of the currently-visible section, e.g. "#digital"
-->
<script lang="ts">
  import PageCard from '$lib/components/PageCard.svelte';

  export let links: { label: string; href: string }[];
  export let activeHref: string = '';
</script>

<PageCard as="aside" width="288px" padding="1.5rem 1rem">
  <nav class="sidebar">
    {#each links as link}
      <a href={link.href} class:active={link.href === activeHref}>
        {link.label}
      </a>
    {/each}
  </nav>
</PageCard>

<style>
  .sidebar {
    position: sticky;
    top: var(--gap-inner);
  }

  a {
    color: #232f3e;
    text-decoration: none;
    font-size: 0.875rem;
    padding: 0.5rem 0;
    display: block;
  }

  a:hover,
  a.active {
    background-color: rgba(31, 111, 235, 0.08);
    border-left: 3px solid #1f6ffb;
    font-weight: bold;
    padding-left: 0.5rem;
  }
</style>
```

- [ ] **Step 2: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors (any existing callers of the old `topics`/`activePath` props will
show type errors — those will be fixed when the pages are implemented in Tasks 10–12).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/components/NavSidebar.svelte
git commit -m "refactor: NavSidebar accepts generic links[] + activeHref prop"
```

---

## Task 9: Refactor `AlbumCard.svelte`

**Files:**
- Modify: `frontend/src/lib/components/AlbumCard.svelte`

- [ ] **Step 1: Add optional `href`, `label` props; make `album` optional**

Replace the full file contents of `frontend/src/lib/components/AlbumCard.svelte`:

```svelte
<!--
  AlbumCard
  Purpose: Square icon-tile for Albums or Topics. In album mode (album prop set), links to
    /learn/[id] and shows album title. In topic mode (href + label set, no album), links to
    the provided href with the provided label. Used in AlbumGrid, CTASidebar, and the
    /t-levels index page.
  Props:
    - album (AlbumListResponse | undefined): the Album to display. Optional.
    - href (string | undefined): overrides the link destination when set.
    - label (string | undefined): overrides the displayed title when set.
    - size (string | undefined): CSS size override (width and height), e.g. "100%".
-->
<script lang="ts">
  import type { AlbumListResponse } from '$lib/api/types';

  export let album: AlbumListResponse | undefined = undefined;
  export let href: string | undefined = undefined;
  export let label: string | undefined = undefined;
  export let size: string | undefined = undefined;

  const ICON_PATHS: Record<string, string[]> = {
    cloud: ['M6 18a4 4 0 0 1-.6-7.96A5 5 0 0 1 15 8a4.5 4.5 0 0 1 1 8.9', 'M6 18h10'],
  };
  const DEFAULT_ICON_PATHS = ['M4 4h16v16H4z'];

  $: resolvedHref = href ?? (album ? `/learn/${album.id}` : '/');
  $: resolvedLabel = label ?? album?.title ?? '';
  $: iconPaths = album ? (ICON_PATHS[album.icon] ?? DEFAULT_ICON_PATHS) : DEFAULT_ICON_PATHS;
</script>

<a
  class="album-card"
  href={resolvedHref}
  style={size ? `width: ${size}; height: ${size};` : undefined}
>
  <svg
    class="icon"
    aria-hidden="true"
    viewBox="0 0 24 24"
    width="60"
    height="60"
    fill="none"
    stroke="#232f3e"
    stroke-width="1.3"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    {#each iconPaths as d}
      <path {d} />
    {/each}
  </svg>
  <h3>{resolvedLabel}</h3>
</a>

<style>
  .album-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    width: 190px;
    height: 190px;
    box-sizing: border-box;
    padding: 1rem;
    background: #ffffff;
    border-radius: 0;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    text-decoration: none;
    color: inherit;
  }

  .icon {
    flex-shrink: 0;
  }

  h3 {
    margin: 0;
    color: #232f3e;
    font-size: 0.95rem;
    font-weight: 700;
    text-align: center;
  }
</style>
```

- [ ] **Step 2: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: Run frontend tests**

```bash
cd frontend && npx vitest run
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/components/AlbumCard.svelte
git commit -m "refactor: AlbumCard accepts optional href/label for topic-card use"
```

---

## Task 10: Implement `/learn/+page.svelte`

**Files:**
- Modify: `frontend/src/routes/learn/+page.svelte`

- [ ] **Step 1: Replace the stub with the full implementation**

Replace the full contents of `frontend/src/routes/learn/+page.svelte`:

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { listAlbums } from '$lib/api/albums';
  import { listTopics } from '$lib/api/topics';
  import type { AlbumListResponse, TopicResponse } from '$lib/api/types';
  import AlbumGrid from '$lib/components/AlbumGrid.svelte';
  import NavSidebar from '$lib/components/NavSidebar.svelte';
  import PageCard from '$lib/components/PageCard.svelte';

  interface Section {
    id: string;
    heading: string;
    albums: AlbumListResponse[];
  }

  let sections: Section[] = [];
  let loading = true;
  let error: string | null = null;
  let activeHref = '';
  let observer: IntersectionObserver | null = null;

  $: links = sections.map((s) => ({ label: s.heading, href: '#' + s.id }));

  onMount(async () => {
    try {
      const [topics, albums] = await Promise.all([listTopics(), listAlbums()]);

      const albumsByTopic = new Map<number, AlbumListResponse[]>();
      for (const album of albums) {
        const list = albumsByTopic.get(album.topic_id) ?? [];
        list.push(album);
        albumsByTopic.set(album.topic_id, list);
      }

      sections = topics
        .filter((t: TopicResponse) => albumsByTopic.has(t.id))
        .map((t: TopicResponse) => ({
          id: t.slug,
          heading: t.name,
          albums: albumsByTopic.get(t.id) ?? [],
        }));
    } catch {
      error = 'Could not load content right now. Please try again later.';
    } finally {
      loading = false;
    }

    observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            activeHref = '#' + entry.target.id;
            break;
          }
        }
      },
      { rootMargin: '0px 0px -75% 0px', threshold: 0 },
    );

    const sectionEls = document.querySelectorAll('.sections section[id]');
    sectionEls.forEach((el) => observer?.observe(el));

    return () => observer?.disconnect();
  });
</script>

<div class="page-layout">
  {#if !loading && !error && sections.length > 0}
    <NavSidebar {links} {activeHref} />
  {/if}

  <div class="main">
    {#if loading}
      <PageCard as="main" padding="1.5rem">
        <p class="status">Loading...</p>
      </PageCard>
    {:else if error}
      <PageCard as="main" padding="1.5rem">
        <p class="status">{error}</p>
      </PageCard>
    {:else if sections.length === 0}
      <PageCard as="main" padding="1.5rem">
        <p class="status">No albums available yet.</p>
      </PageCard>
    {:else}
      <div class="sections">
        {#each sections as section}
          <section id={section.id}>
            <PageCard padding="0.875rem 1.25rem">
              <h2 class="section-heading">{section.heading}</h2>
            </PageCard>
            <PageCard as="div" padding="1.5rem">
              <AlbumGrid albums={section.albums} />
            </PageCard>
          </section>
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  .page-layout {
    display: flex;
    gap: var(--gap-inner);
    align-items: flex-start;
    min-height: 100%;
  }

  .main {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
  }

  .sections {
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
  }

  section {
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
  }

  .section-heading {
    font-size: 0.95rem;
    font-weight: 700;
    color: #232f3e;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .status {
    font-size: 0.875rem;
    color: #5a6472;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }
</style>
```

- [ ] **Step 2: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: Run frontend tests**

```bash
cd frontend && npx vitest run
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/learn/+page.svelte
git commit -m "feat: implement /learn — albums grouped by topic with NavSidebar scroll-spy"
```

---

## Task 11: Create `/t-levels/+page.svelte`

**Files:**
- Create: `frontend/src/routes/t-levels/+page.svelte`

- [ ] **Step 1: Create the t-levels directory and index page**

Create `frontend/src/routes/t-levels/+page.svelte`:

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { listTopics } from '$lib/api/topics';
  import type { TopicResponse } from '$lib/api/types';
  import AlbumCard from '$lib/components/AlbumCard.svelte';
  import PageCard from '$lib/components/PageCard.svelte';

  let topics: TopicResponse[] = [];
  let loading = true;
  let error: string | null = null;

  onMount(async () => {
    try {
      topics = await listTopics();
    } catch {
      error = 'Could not load T-Levels right now. Please try again later.';
    } finally {
      loading = false;
    }
  });
</script>

<PageCard as="main" padding="1.5rem">
  {#if loading}
    <p class="status">Loading...</p>
  {:else if error}
    <p class="status">{error}</p>
  {:else}
    <div class="topic-grid">
      {#each topics as topic}
        <AlbumCard label={topic.name} href="/t-levels/{topic.slug}" />
      {/each}
    </div>
  {/if}
</PageCard>

<style>
  .topic-grid {
    display: grid;
    grid-template-columns: repeat(2, 190px);
    gap: 1.5rem;
  }

  .status {
    font-size: 0.875rem;
    color: #5a6472;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }
</style>
```

- [ ] **Step 2: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes/t-levels/+page.svelte
git commit -m "feat: implement /t-levels index — 2x2 topic card grid"
```

---

## Task 12: Create `/t-levels/[slug]/+page.svelte`

**Files:**
- Create: `frontend/src/routes/t-levels/[slug]/+page.svelte`

- [ ] **Step 1: Create the slug directory and detail page**

Create `frontend/src/routes/t-levels/[slug]/+page.svelte`:

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { getTopic } from '$lib/api/topics';
  import type { TLevelWithAlbumsResponse, AlbumListResponse } from '$lib/api/types';
  import AlbumGrid from '$lib/components/AlbumGrid.svelte';
  import NavSidebar from '$lib/components/NavSidebar.svelte';
  import PageCard from '$lib/components/PageCard.svelte';

  interface Section {
    id: string;
    heading: string;
    albums: AlbumListResponse[];
  }

  let sections: Section[] = [];
  let topicName = '';
  let loading = true;
  let error: string | null = null;
  let activeHref = '';
  let observer: IntersectionObserver | null = null;

  $: links = sections.map((s) => ({ label: s.heading, href: '#' + s.id }));

  onMount(async () => {
    const slug = $page.params.slug;

    try {
      const topic = await getTopic(slug);
      topicName = topic.name;

      sections = topic.t_levels
        .filter((t: TLevelWithAlbumsResponse) => t.albums.length > 0)
        .map((t: TLevelWithAlbumsResponse) => ({
          id: `t-level-${t.id}`,
          heading: t.name,
          albums: t.albums,
        }));
    } catch (err: unknown) {
      const status = (err as { status?: number })?.status;
      if (status === 404) {
        goto('/t-levels');
        return;
      }
      error = 'Could not load this T-Level area. Please try again later.';
    } finally {
      loading = false;
    }

    observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            activeHref = '#' + entry.target.id;
            break;
          }
        }
      },
      { rootMargin: '0px 0px -75% 0px', threshold: 0 },
    );

    const sectionEls = document.querySelectorAll('.sections section[id]');
    sectionEls.forEach((el) => observer?.observe(el));

    return () => observer?.disconnect();
  });
</script>

<div class="page-layout">
  {#if !loading && !error && sections.length > 0}
    <NavSidebar {links} {activeHref} />
  {/if}

  <div class="main">
    {#if loading}
      <PageCard as="main" padding="1.5rem">
        <p class="status">Loading...</p>
      </PageCard>
    {:else if error}
      <PageCard as="main" padding="1.5rem">
        <p class="status">{error}</p>
      </PageCard>
    {:else if sections.length === 0}
      <PageCard as="main" padding="1.5rem">
        <p class="status">No albums available in {topicName} yet.</p>
      </PageCard>
    {:else}
      <div class="sections">
        {#each sections as section}
          <section id={section.id}>
            <PageCard padding="0.875rem 1.25rem">
              <h2 class="section-heading">{section.heading}</h2>
            </PageCard>
            <PageCard as="div" padding="1.5rem">
              <AlbumGrid albums={section.albums} />
            </PageCard>
          </section>
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  .page-layout {
    display: flex;
    gap: var(--gap-inner);
    align-items: flex-start;
    min-height: 100%;
  }

  .main {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
  }

  .sections {
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
  }

  section {
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
  }

  .section-heading {
    font-size: 0.95rem;
    font-weight: 700;
    color: #232f3e;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .status {
    font-size: 0.875rem;
    color: #5a6472;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }
</style>
```

- [ ] **Step 2: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes/t-levels/[slug]/+page.svelte
git commit -m "feat: implement /t-levels/[slug] — albums grouped by T-Level with NavSidebar"
```

---

## Task 13: Delete `/topics` route + final verification

**Files:**
- Delete: `frontend/src/routes/topics/+page.svelte`

- [ ] **Step 1: Delete the old topics route**

```bash
git rm frontend/src/routes/topics/+page.svelte
rmdir frontend/src/routes/topics/ 2>/dev/null || true
```

- [ ] **Step 2: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: Run full frontend test suite**

```bash
cd frontend && npx vitest run
```

Expected: all tests pass.

- [ ] **Step 4: Run full backend test suite**

```bash
docker compose exec backend poetry run pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 5: Run frontend lint**

```bash
cd frontend && npm run lint
```

Expected: 0 errors.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: delete /topics stub — replaced by /t-levels"
```

- [ ] **Step 7: Start the app and verify in browser**

```bash
docker compose up --build -d
docker compose exec backend poetry run alembic upgrade head
```

Open http://localhost:3000 and verify:

- Navbar shows "T-Levels" (not "Topics"), links to `/t-levels`
- `/learn` shows albums grouped under topic headings; NavSidebar highlights active section on scroll
- `/t-levels` shows a 2×2 grid of topic cards (one per Topic in the DB)
- `/t-levels/digital` (or whichever slug is seeded) shows T-levels as section headings with albums beneath each; NavSidebar highlights active section on scroll
- `/topics` returns a SvelteKit 404
- Guest (logged-out) users can access all three pages without a 401
