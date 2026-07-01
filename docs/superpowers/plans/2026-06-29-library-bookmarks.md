# Library Bookmarks + Semantic Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add album/snippet bookmarking to The Library with pgvector semantic search and a wired-up Dynamic Mentor RAG endpoint.

**Architecture:** pgvector columns on `Content` and `Album` are populated at seed time via Amazon Bedrock Titan Embeddings. A new `UserSnippetSave` table tracks saved snippets (album saves reuse `AlbumEnrolment`). Three new backend services (`embedding_service`, `snippet_service`, `library_service`) expose `/snippets` and `/library` routers. The frontend replaces the `/library` stub with a full page (search bar, enrolled albums, saved snippets, Mentor chat).

**Tech Stack:** FastAPI + SQLAlchemy async + pgvector + boto3 (Bedrock). SvelteKit 2 / Svelte 4 + TypeScript frontend. Typecheck: `cd frontend && npm run check`. Tests: `cd frontend && npx vitest run` / `cd backend && poetry run pytest`. Lint: `cd frontend && npm run lint` / `cd backend && poetry run ruff check .`.

**Spec:** `docs/superpowers/specs/2026-06-29-library-bookmarks-design.md`

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `backend/pyproject.toml` | Add pgvector dep |
| Modify | `docker-compose.yml` | Use pgvector-enabled Postgres image |
| Modify | `backend/app/config.py` | Add Bedrock model IDs + SKIP_EMBEDDINGS flag |
| Create | `backend/alembic/versions/<rev>_add_pgvector.py` | Extension, embedding cols, user_snippet_saves |
| Modify | `backend/app/models/content.py` | Add embedding + embedding_generated_at |
| Modify | `backend/app/models/album.py` | Add embedding + embedding_generated_at |
| Create | `backend/app/models/library.py` | UserSnippetSave |
| Modify | `backend/app/models/__init__.py` | Import UserSnippetSave |
| Modify | `backend/app/models/user.py` | Add saved_snippets relationship |
| Modify | `backend/tests/conftest.py` | CREATE EXTENSION vector before create_all |
| Create | `backend/app/services/embedding_service.py` | embed_text() Bedrock wrapper |
| Create | `backend/tests/test_embedding_service.py` | Tests for embed_text |
| Modify | `backend/seed.py` | Add embed_content() phase |
| Create | `backend/app/schemas/library.py` | LibraryResponse, ContentSearchResult, MentorRequest/Response |
| Create | `backend/app/services/snippet_service.py` | save/unsave/get snippet |
| Create | `backend/tests/test_snippet_service.py` | Tests for snippet_service |
| Create | `backend/app/routers/snippets.py` | /snippets router |
| Create | `backend/app/services/library_service.py` | get_library, semantic_search, mentor_query |
| Create | `backend/tests/test_library_service.py` | Tests for library_service |
| Create | `backend/app/routers/library.py` | /library router |
| Modify | `backend/app/main.py` | Register snippets + library routers |
| Create | `frontend/src/lib/api/library.ts` | getLibrary, searchLibrary, mentorQuery |
| Modify | `frontend/src/lib/components/SnippetCard.svelte` | Full implementation + save toggle |
| Modify | `frontend/src/lib/components/CTASidebar.svelte` | AgentChat navigates to /library?q= |
| Modify | `frontend/src/routes/library/+page.ts` | Auth guard + data load |
| Modify | `frontend/src/routes/library/+page.svelte` | Full library page |

---

## Task 1: Add pgvector dependency + update docker-compose

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add pgvector to Poetry deps**

In `backend/pyproject.toml`, in `[tool.poetry.dependencies]`, add after `boto3 = "^1.35.0"`:

```toml
pgvector = "^0.3.0"
```

- [ ] **Step 2: Install**

```bash
cd backend && poetry add pgvector
```

Expected: lock file updated, `pgvector` package installed.

- [ ] **Step 3: Update docker-compose to use pgvector Postgres image**

In `docker-compose.yml`, find the `db` service image line. It will look like:

```yaml
    image: postgres:16
```

Replace with:

```yaml
    image: ankane/pgvector:latest
```

`ankane/pgvector` is the standard pgvector-enabled Postgres image. It includes the `vector` extension.

- [ ] **Step 4: Rebuild the DB container**

```bash
docker compose down db && docker compose up db -d
```

Expected: DB container restarts with pgvector-capable image.

- [ ] **Step 5: Verify extension is available**

```bash
docker compose exec db psql -U postgres -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"
```

Expected: one row with `name = vector`.

- [ ] **Step 6: Commit**

```bash
git add backend/pyproject.toml backend/poetry.lock docker-compose.yml
git commit -m "feat: add pgvector dependency, switch to ankane/pgvector DB image"
```

---

## Task 2: Config additions

**Files:**
- Modify: `backend/app/config.py`

- [ ] **Step 1: Add Bedrock + embedding settings to Settings**

In `backend/app/config.py`, find the `class Settings` body and add after `AWS_REGION: str = "eu-west-2"`:

```python
    BEDROCK_EMBEDDING_MODEL_ID: str = "amazon.titan-embed-text-v1"
    BEDROCK_GENERATION_MODEL_ID: str = "amazon.titan-text-express-v1"
    SKIP_EMBEDDINGS: bool = False
```

The full class should now end:

```python
    AWS_REGION: str = "eu-west-2"
    BEDROCK_EMBEDDING_MODEL_ID: str = "amazon.titan-embed-text-v1"
    BEDROCK_GENERATION_MODEL_ID: str = "amazon.titan-text-express-v1"
    SKIP_EMBEDDINGS: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
```

- [ ] **Step 2: Typecheck**

```bash
cd backend && poetry run python -c "from app.config import get_settings; s = get_settings(); print(s.BEDROCK_EMBEDDING_MODEL_ID)"
```

Expected: `amazon.titan-embed-text-v1`

- [ ] **Step 3: Commit**

```bash
git add backend/app/config.py
git commit -m "feat: add Bedrock model ID and SKIP_EMBEDDINGS settings"
```

---

## Task 3: Alembic migration — pgvector extension, embedding columns, UserSnippetSave

**Files:**
- Create: `backend/alembic/versions/<rev>_add_pgvector.py` (generated)

- [ ] **Step 1: Generate a blank migration**

```bash
cd backend && poetry run alembic revision -m "add pgvector embeddings and user_snippet_saves"
```

Expected: new file created in `backend/alembic/versions/` with a timestamp prefix.

- [ ] **Step 2: Write the migration**

Open the generated file and replace the `upgrade()` and `downgrade()` functions with:

```python
import sqlalchemy as sa
from alembic import op


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column("content", sa.Column("embedding", sa.Text, nullable=True))
    op.add_column("content", sa.Column("embedding_generated_at", sa.DateTime, nullable=True))

    op.add_column("albums", sa.Column("embedding", sa.Text, nullable=True))
    op.add_column("albums", sa.Column("embedding_generated_at", sa.DateTime, nullable=True))

    op.create_table(
        "user_snippet_saves",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("content_id", sa.Integer, sa.ForeignKey("content.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("saved_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_snippet_saves")
    op.drop_column("albums", "embedding_generated_at")
    op.drop_column("albums", "embedding")
    op.drop_column("content", "embedding_generated_at")
    op.drop_column("content", "embedding")
```

Note: we store embedding as `Text` in the migration and cast to `vector(1536)` via a separate `ALTER COLUMN` so Alembic doesn't need special vector type awareness. Add this after the `add_column` calls for both tables:

```python
    op.execute("ALTER TABLE content ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector")
    op.execute("ALTER TABLE albums ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector")
```

The full `upgrade()`:

```python
def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column("content", sa.Column("embedding", sa.Text, nullable=True))
    op.add_column("content", sa.Column("embedding_generated_at", sa.DateTime, nullable=True))
    op.execute("ALTER TABLE content ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector")

    op.add_column("albums", sa.Column("embedding", sa.Text, nullable=True))
    op.add_column("albums", sa.Column("embedding_generated_at", sa.DateTime, nullable=True))
    op.execute("ALTER TABLE albums ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector")

    op.create_table(
        "user_snippet_saves",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("content_id", sa.Integer, sa.ForeignKey("content.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("saved_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
```

- [ ] **Step 3: Apply migration**

```bash
cd backend && poetry run alembic upgrade head
```

Expected: migration applies without error.

- [ ] **Step 4: Verify**

```bash
docker compose exec db psql -U postgres -d amazon_tlevel -c "\d content" | grep embedding
```

Expected: `embedding` column of type `vector`.

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/versions/
git commit -m "feat: migration — pgvector extension, embedding columns, user_snippet_saves"
```

---

## Task 4: Model updates — embedding columns, UserSnippetSave, User relationships

**Files:**
- Modify: `backend/app/models/content.py`
- Modify: `backend/app/models/album.py`
- Create: `backend/app/models/library.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/user.py`

- [ ] **Step 1: Add embedding fields to Content**

In `backend/app/models/content.py`, add the import at the top:

```python
from pgvector.sqlalchemy import Vector
```

In the `Content` class, add after `created_at`:

```python
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    embedding_generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

- [ ] **Step 2: Add embedding fields to Album**

In `backend/app/models/album.py`, add:

```python
from pgvector.sqlalchemy import Vector
```

In the `Album` class, add after `created_at`:

```python
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    embedding_generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

- [ ] **Step 3: Create UserSnippetSave model**

Create `backend/app/models/library.py`:

```python
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class UserSnippetSave(Base):
    __tablename__ = "user_snippet_saves"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("content.id", ondelete="CASCADE"), primary_key=True)
    saved_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship()
    content: Mapped["Content"] = relationship()
```

- [ ] **Step 4: Import UserSnippetSave in models/__init__.py**

In `backend/app/models/__init__.py`, add:

```python
from app.models.library import UserSnippetSave  # noqa: F401
```

- [ ] **Step 5: Add saved_snippets relationship to User**

In `backend/app/models/user.py`, add the import:

```python
from app.models.library import UserSnippetSave  # noqa: F401 (TYPE_CHECKING not needed — already imported)
```

Add to the `User` class after `progress`:

```python
    saved_snippets: Mapped[list["UserSnippetSave"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
```

Fix `UserSnippetSave.user` to use `back_populates`. In `backend/app/models/library.py`, update:

```python
    user: Mapped["User"] = relationship(back_populates="saved_snippets")
```

- [ ] **Step 6: Typecheck**

```bash
cd backend && poetry run python -c "from app.models.library import UserSnippetSave; print('ok')"
```

Expected: `ok`

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add embedding columns to Content/Album, add UserSnippetSave model"
```

---

## Task 5: Update conftest.py — pgvector extension in test DB

**Files:**
- Modify: `backend/tests/conftest.py`

The test DB uses `Base.metadata.create_all`. The pgvector extension must exist before that runs, otherwise the `vector` column type registration fails.

- [ ] **Step 1: Add extension creation to db_session fixture**

In `backend/tests/conftest.py`, find the `db_session` fixture. Update the `async with engine.begin() as conn:` block to create the extension first:

```python
@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine(get_settings().DATABASE_URL)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with session_factory() as session:
                yield session
        finally:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
    finally:
        await engine.dispose()
```

`text` is already imported from `sqlalchemy` in conftest (it's used in many tests). Verify the import is there; if not, add `from sqlalchemy import text`.

- [ ] **Step 2: Run existing tests to confirm nothing broke**

```bash
cd backend && poetry run pytest tests/ -x -q
```

Expected: all existing tests pass.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/conftest.py
git commit -m "test: create pgvector extension in test DB before create_all"
```

---

## Task 6: embedding_service.py (TDD)

**Files:**
- Create: `backend/app/services/embedding_service.py`
- Create: `backend/tests/test_embedding_service.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_embedding_service.py`:

```python
import json
from unittest.mock import MagicMock, patch

import pytest


def _make_bedrock_response(embedding: list[float]) -> dict:
    body_bytes = json.dumps({"embedding": embedding}).encode()
    mock_body = MagicMock()
    mock_body.read.return_value = body_bytes
    return {"body": mock_body}


def test_embed_text_returns_1536_floats():
    fake_vec = [0.1] * 1536
    with patch("app.services.embedding_service.boto3.client") as mock_client:
        mock_client.return_value.invoke_model.return_value = _make_bedrock_response(fake_vec)
        from app.services.embedding_service import embed_text
        result = embed_text("hello world")
    assert len(result) == 1536
    assert result[0] == pytest.approx(0.1)


def test_embed_text_truncates_to_8000_chars():
    long_text = "x" * 10_000
    fake_vec = [0.0] * 1536
    with patch("app.services.embedding_service.boto3.client") as mock_client:
        mock_client.return_value.invoke_model.return_value = _make_bedrock_response(fake_vec)
        import importlib
        import app.services.embedding_service as mod
        importlib.reload(mod)
        mod.embed_text(long_text)
        call_args = mock_client.return_value.invoke_model.call_args
        body = json.loads(call_args.kwargs["body"])
        assert len(body["inputText"]) == 8000


def test_embed_text_returns_zeros_when_skip_embeddings(monkeypatch):
    monkeypatch.setenv("SKIP_EMBEDDINGS", "true")
    import importlib
    import app.config as cfg_mod
    import app.services.embedding_service as mod
    cfg_mod.get_settings.cache_clear()
    importlib.reload(mod)
    result = mod.embed_text("anything")
    assert result == [0.0] * 1536
    cfg_mod.get_settings.cache_clear()
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
cd backend && poetry run pytest tests/test_embedding_service.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `embedding_service` does not exist yet.

- [ ] **Step 3: Implement embedding_service.py**

Create `backend/app/services/embedding_service.py`:

```python
import json

import boto3

from app.config import get_settings


def embed_text(text: str) -> list[float]:
    settings = get_settings()
    if settings.SKIP_EMBEDDINGS:
        return [0.0] * 1536
    client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
    response = client.invoke_model(
        modelId=settings.BEDROCK_EMBEDDING_MODEL_ID,
        body=json.dumps({"inputText": text[:8000]}),
    )
    return json.loads(response["body"].read())["embedding"]
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
cd backend && poetry run pytest tests/test_embedding_service.py -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/embedding_service.py backend/tests/test_embedding_service.py
git commit -m "feat: add embedding_service.py with Bedrock Titan wrapper"
```

---

## Task 7: seed.py — embed_content() phase

**Files:**
- Modify: `backend/seed.py`

- [ ] **Step 1: Add embed_content() to seed.py**

In `backend/seed.py`, add the following imports at the top (after existing imports):

```python
import json
import os
import sys
```

Then add the `embed_content` async function before `if __name__ == "__main__":`:

```python
async def embed_content() -> None:
    settings = get_settings()
    if settings.SKIP_EMBEDDINGS:
        print("SKIP_EMBEDDINGS=true, skipping embedding phase.")
        return

    from app.services.embedding_service import embed_text
    from app.models.content import Content
    from app.models.album import Album
    from datetime import datetime, timezone

    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        # Embed unembedded Content rows
        result = await session.execute(
            text("SELECT id, title, body FROM content WHERE embedding_generated_at IS NULL")
        )
        rows = result.fetchall()
        print(f"Embedding {len(rows)} snippet(s)...")
        for row in rows:
            input_text = f"{row.title}\n\n{row.body or ''}"
            vec = embed_text(input_text)
            await session.execute(
                text(
                    "UPDATE content SET embedding = :vec, embedding_generated_at = :now "
                    "WHERE id = :id"
                ),
                {"vec": str(vec), "now": datetime.now(timezone.utc), "id": row.id},
            )
        await session.commit()
        print("Snippets embedded.")

        # Embed unembedded Album rows
        result = await session.execute(
            text("SELECT id, title, description FROM albums WHERE embedding_generated_at IS NULL")
        )
        rows = result.fetchall()
        print(f"Embedding {len(rows)} album(s)...")
        for row in rows:
            input_text = f"{row.title}\n\n{row.description}"
            vec = embed_text(input_text)
            await session.execute(
                text(
                    "UPDATE albums SET embedding = :vec, embedding_generated_at = :now "
                    "WHERE id = :id"
                ),
                {"vec": str(vec), "now": datetime.now(timezone.utc), "id": row.id},
            )
        await session.commit()
        print("Albums embedded.")

    await engine.dispose()
```

Update `if __name__ == "__main__":` to support `--embed-only` flag:

```python
if __name__ == "__main__":
    if "--embed-only" in sys.argv:
        asyncio.run(embed_content())
    else:
        asyncio.run(seed())
        asyncio.run(embed_content())
```

Note: `get_settings` is already imported at top of seed.py via `from app.config import get_settings`. If not, add it.

- [ ] **Step 2: Verify seed.py syntax**

```bash
cd backend && poetry run python -c "import seed; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add backend/seed.py
git commit -m "feat: add embed_content() phase to seed.py"
```

---

## Task 8: Library Pydantic schemas

**Files:**
- Create: `backend/app/schemas/library.py`

- [ ] **Step 1: Create library schemas**

Create `backend/app/schemas/library.py`:

```python
from pydantic import BaseModel

from app.models.content import ContentType
from app.schemas.album import AlbumListResponse
from app.schemas.content import ContentResponse


class LibraryResponse(BaseModel):
    enrolled_albums: list[AlbumListResponse]
    saved_snippets: list[ContentResponse]


class ContentSearchResult(BaseModel):
    content_id: int
    title: str
    content_type: ContentType
    album_title: str | None
    similarity_score: float
    is_saved: bool


class MentorRequest(BaseModel):
    message: str


class MentorSource(BaseModel):
    content_id: int
    title: str


class MentorResponse(BaseModel):
    reply: str
    sources: list[MentorSource]
```

- [ ] **Step 2: Check what ContentResponse looks like**

Run:
```bash
cd backend && grep -n "class ContentResponse" app/schemas/*.py
```

If `ContentResponse` doesn't exist in `app/schemas/content.py`, create `backend/app/schemas/content.py`:

```python
from pydantic import BaseModel

from app.models.content import ContentType


class ContentResponse(BaseModel):
    id: int
    title: str
    content_type: ContentType
    media_url: str | None = None
    topic_id: int
    t_level_id: int | None = None

    model_config = {"from_attributes": True}
```

If it already exists, use it as-is. Adjust the import in `library.py` accordingly.

- [ ] **Step 3: Typecheck**

```bash
cd backend && poetry run python -c "from app.schemas.library import LibraryResponse, ContentSearchResult, MentorRequest, MentorResponse; print('ok')"
```

Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas/
git commit -m "feat: add library, search, and mentor Pydantic schemas"
```

---

## Task 9: snippet_service.py + /snippets router (TDD)

**Files:**
- Create: `backend/app/services/snippet_service.py`
- Create: `backend/tests/test_snippet_service.py`
- Create: `backend/app/routers/snippets.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_snippet_service.py`:

```python
import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentType
from app.models.library import UserSnippetSave
from app.models.topic import Topic
from app.models.user import User


async def _make_topic(db: AsyncSession) -> Topic:
    topic = Topic(slug="digital", name="Digital", description="D", accent_colour="#000")
    db.add(topic)
    await db.flush()
    return topic


async def _make_snippet(db: AsyncSession, topic_id: int, title: str = "Intro") -> Content:
    snippet = Content(
        title=title,
        content_type=ContentType.article,
        topic_id=topic_id,
        body="Body text",
    )
    db.add(snippet)
    await db.flush()
    return snippet


async def test_save_snippet_creates_save_row(db_session: AsyncSession, current_user: User) -> None:
    topic = await _make_topic(db_session)
    snippet = await _make_snippet(db_session, topic.id)
    await db_session.commit()

    from app.services.snippet_service import save_snippet
    await save_snippet(db_session, snippet.id, current_user)

    saved = await db_session.get(UserSnippetSave, (current_user.id, snippet.id))
    assert saved is not None


async def test_save_snippet_is_idempotent(db_session: AsyncSession, current_user: User) -> None:
    topic = await _make_topic(db_session)
    snippet = await _make_snippet(db_session, topic.id)
    await db_session.commit()

    from app.services.snippet_service import save_snippet
    await save_snippet(db_session, snippet.id, current_user)
    await save_snippet(db_session, snippet.id, current_user)  # second call must not raise

    from sqlalchemy import select, func
    count = (
        await db_session.execute(
            select(func.count()).where(
                UserSnippetSave.user_id == current_user.id,
                UserSnippetSave.content_id == snippet.id,
            )
        )
    ).scalar_one()
    assert count == 1


async def test_unsave_snippet_removes_save_row(db_session: AsyncSession, current_user: User) -> None:
    topic = await _make_topic(db_session)
    snippet = await _make_snippet(db_session, topic.id)
    db_session.add(UserSnippetSave(user_id=current_user.id, content_id=snippet.id))
    await db_session.commit()

    from app.services.snippet_service import unsave_snippet
    await unsave_snippet(db_session, snippet.id, current_user)

    saved = await db_session.get(UserSnippetSave, (current_user.id, snippet.id))
    assert saved is None


async def test_unsave_snippet_is_no_op_when_not_saved(db_session: AsyncSession, current_user: User) -> None:
    topic = await _make_topic(db_session)
    snippet = await _make_snippet(db_session, topic.id)
    await db_session.commit()

    from app.services.snippet_service import unsave_snippet
    await unsave_snippet(db_session, snippet.id, current_user)  # should not raise


async def test_get_snippet_raises_404_for_unknown_id(db_session: AsyncSession) -> None:
    from app.services.snippet_service import get_snippet
    with pytest.raises(HTTPException) as exc_info:
        await get_snippet(db_session, 9999, user=None)
    assert exc_info.value.status_code == 404


async def test_get_snippet_returns_is_saved_false_for_unauthenticated(
    db_session: AsyncSession,
) -> None:
    topic = await _make_topic(db_session)
    snippet = await _make_snippet(db_session, topic.id)
    await db_session.commit()

    from app.services.snippet_service import get_snippet
    result = await get_snippet(db_session, snippet.id, user=None)
    assert result.is_saved is False


async def test_get_snippet_returns_is_saved_true_when_saved(
    db_session: AsyncSession, current_user: User
) -> None:
    topic = await _make_topic(db_session)
    snippet = await _make_snippet(db_session, topic.id)
    db_session.add(UserSnippetSave(user_id=current_user.id, content_id=snippet.id))
    await db_session.commit()

    from app.services.snippet_service import get_snippet
    result = await get_snippet(db_session, snippet.id, user=current_user)
    assert result.is_saved is True
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
cd backend && poetry run pytest tests/test_snippet_service.py -v
```

Expected: `ImportError` — `snippet_service` does not exist.

- [ ] **Step 3: Create ContentDetailResponse schema**

In `backend/app/schemas/content.py` (create if not there, or add to existing), add:

```python
class ContentDetailResponse(BaseModel):
    id: int
    title: str
    content_type: ContentType
    body: str | None = None
    media_url: str | None = None
    topic_id: int
    t_level_id: int | None = None
    is_saved: bool = False

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Implement snippet_service.py**

Create `backend/app/services/snippet_service.py`:

```python
from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content
from app.models.library import UserSnippetSave
from app.models.user import User
from app.schemas.content import ContentDetailResponse


async def save_snippet(db: AsyncSession, content_id: int, user: User) -> None:
    existing = await db.get(UserSnippetSave, (user.id, content_id))
    if existing is not None:
        return
    db.add(UserSnippetSave(user_id=user.id, content_id=content_id))
    await db.commit()


async def unsave_snippet(db: AsyncSession, content_id: int, user: User) -> None:
    await db.execute(
        delete(UserSnippetSave).where(
            UserSnippetSave.user_id == user.id,
            UserSnippetSave.content_id == content_id,
        )
    )
    await db.commit()


async def get_snippet(
    db: AsyncSession,
    content_id: int,
    user: User | None,
) -> ContentDetailResponse:
    snippet = (
        await db.execute(select(Content).where(Content.id == content_id))
    ).scalar_one_or_none()
    if snippet is None:
        raise HTTPException(status_code=404, detail="Snippet not found")

    is_saved = False
    if user is not None:
        save_row = await db.get(UserSnippetSave, (user.id, content_id))
        is_saved = save_row is not None

    return ContentDetailResponse(
        id=snippet.id,
        title=snippet.title,
        content_type=snippet.content_type,
        body=snippet.body,
        media_url=snippet.media_url,
        topic_id=snippet.topic_id,
        t_level_id=snippet.t_level_id,
        is_saved=is_saved,
    )
```

- [ ] **Step 5: Run tests — confirm they pass**

```bash
cd backend && poetry run pytest tests/test_snippet_service.py -v
```

Expected: 7 tests pass.

- [ ] **Step 6: Create /snippets router**

Create `backend/app/routers/snippets.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.content import ContentDetailResponse
from app.services import snippet_service

router = APIRouter(prefix="/snippets", tags=["snippets"])


@router.get("/{content_id}", response_model=ContentDetailResponse, summary="Get snippet detail")
async def get_snippet(
    content_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> ContentDetailResponse:
    return await snippet_service.get_snippet(db, content_id, current_user)


@router.post("/{content_id}/save", status_code=204, summary="Save snippet to library")
async def save_snippet(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await snippet_service.save_snippet(db, content_id, current_user)


@router.delete("/{content_id}/save", status_code=204, summary="Remove snippet from library")
async def unsave_snippet(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await snippet_service.unsave_snippet(db, content_id, current_user)
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/snippet_service.py backend/tests/test_snippet_service.py backend/app/routers/snippets.py backend/app/schemas/
git commit -m "feat: add snippet_service, ContentDetailResponse, and /snippets router"
```

---

## Task 10: library_service.get_library() (TDD)

**Files:**
- Create: `backend/app/services/library_service.py` (partial)
- Create: `backend/tests/test_library_service.py` (partial)

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_library_service.py`:

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.album import Album, AlbumEnrolment
from app.models.content import Content, ContentType
from app.models.library import UserSnippetSave
from app.models.t_level import TLevel
from app.models.topic import Topic
from app.models.user import User


async def _make_topic(db: AsyncSession) -> Topic:
    topic = Topic(slug="digital", name="Digital", description="D", accent_colour="#000")
    db.add(topic)
    await db.flush()
    return topic


async def _make_t_level(db: AsyncSession, topic_id: int) -> TLevel:
    t_level = TLevel(
        topic_id=topic_id,
        name="Cloud T-Level",
        entry_requirements="5 GCSEs",
        how_to_apply="Apply online",
    )
    db.add(t_level)
    await db.flush()
    return t_level


async def _make_album(db: AsyncSession, t_level_id: int, title: str = "Cloud Album") -> Album:
    album = Album(t_level_id=t_level_id, title=title, description="Desc", icon="cloud")
    db.add(album)
    await db.flush()
    return album


async def _make_snippet(db: AsyncSession, topic_id: int, title: str = "Intro") -> Content:
    snippet = Content(title=title, content_type=ContentType.article, topic_id=topic_id, body="B")
    db.add(snippet)
    await db.flush()
    return snippet


async def test_get_library_returns_enrolled_albums(
    db_session: AsyncSession, current_user: User
) -> None:
    topic = await _make_topic(db_session)
    t_level = await _make_t_level(db_session, topic.id)
    album = await _make_album(db_session, t_level.id)
    db_session.add(AlbumEnrolment(user_id=current_user.id, album_id=album.id))
    await db_session.commit()

    from app.services.library_service import get_library
    result = await get_library(db_session, current_user)

    assert len(result.enrolled_albums) == 1
    assert result.enrolled_albums[0].id == album.id


async def test_get_library_returns_saved_snippets(
    db_session: AsyncSession, current_user: User
) -> None:
    topic = await _make_topic(db_session)
    snippet = await _make_snippet(db_session, topic.id)
    db_session.add(UserSnippetSave(user_id=current_user.id, content_id=snippet.id))
    await db_session.commit()

    from app.services.library_service import get_library
    result = await get_library(db_session, current_user)

    assert len(result.saved_snippets) == 1
    assert result.saved_snippets[0].id == snippet.id


async def test_get_library_returns_empty_when_nothing_saved(
    db_session: AsyncSession, current_user: User
) -> None:
    from app.services.library_service import get_library
    result = await get_library(db_session, current_user)

    assert result.enrolled_albums == []
    assert result.saved_snippets == []
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
cd backend && poetry run pytest tests/test_library_service.py -v
```

Expected: `ImportError` — `library_service` does not exist.

- [ ] **Step 3: Implement get_library()**

Create `backend/app/services/library_service.py`:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.album import Album, AlbumEnrolment
from app.models.content import Content
from app.models.library import UserSnippetSave
from app.models.user import User
from app.schemas.album import AlbumListResponse
from app.schemas.content import ContentResponse
from app.schemas.library import (
    ContentSearchResult,
    LibraryResponse,
    MentorResponse,
    MentorSource,
)

LIBRARY_SEARCH_BOOST = 1.4


async def get_library(db: AsyncSession, user: User) -> LibraryResponse:
    enrolled_stmt = (
        select(Album)
        .join(AlbumEnrolment, AlbumEnrolment.album_id == Album.id)
        .where(AlbumEnrolment.user_id == user.id)
        .options(selectinload(Album.t_level))
    )
    albums = (await db.execute(enrolled_stmt)).scalars().all()
    enrolled_albums = [
        AlbumListResponse(
            id=a.id,
            t_level_id=a.t_level_id,
            topic_id=a.t_level.topic_id,
            title=a.title,
            description=a.description,
            icon=a.icon,
        )
        for a in albums
    ]

    saved_stmt = (
        select(Content)
        .join(UserSnippetSave, UserSnippetSave.content_id == Content.id)
        .where(UserSnippetSave.user_id == user.id)
    )
    snippets = (await db.execute(saved_stmt)).scalars().all()
    saved_snippets = [ContentResponse.model_validate(s) for s in snippets]

    return LibraryResponse(enrolled_albums=enrolled_albums, saved_snippets=saved_snippets)
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
cd backend && poetry run pytest tests/test_library_service.py::test_get_library_returns_enrolled_albums tests/test_library_service.py::test_get_library_returns_saved_snippets tests/test_library_service.py::test_get_library_returns_empty_when_nothing_saved -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/library_service.py backend/tests/test_library_service.py
git commit -m "feat: add library_service.get_library()"
```

---

## Task 11: library_service.semantic_search() (TDD)

**Files:**
- Modify: `backend/app/services/library_service.py`
- Modify: `backend/tests/test_library_service.py`

The boost logic is a pure function; test it without a DB. The full `semantic_search` function is tested by mocking `embed_text` and the DB query.

- [ ] **Step 1: Add boost logic tests to test_library_service.py**

Append to `backend/tests/test_library_service.py`:

```python
def test_apply_boost_elevates_saved_content():
    from unittest.mock import MagicMock
    from app.services.library_service import _apply_boost

    row_saved = MagicMock()
    row_saved.id = 1
    row_saved.title = "Cloud Basics"
    row_saved.content_type = ContentType.article
    row_saved.album_title = "Cloud T-Level"
    row_saved.distance = 0.2  # similarity = 0.8, boosted = 0.8 * 1.4 = 1.12

    row_unsaved = MagicMock()
    row_unsaved.id = 2
    row_unsaved.title = "Networking"
    row_unsaved.content_type = ContentType.article
    row_unsaved.album_title = None
    row_unsaved.distance = 0.15  # similarity = 0.85 (higher raw, but not boosted)

    results = _apply_boost([row_saved, row_unsaved], boosted_ids={1}, saved_ids={1})

    assert results[0].content_id == 1
    assert results[0].is_saved is True
    assert results[1].content_id == 2
    assert results[1].is_saved is False


def test_apply_boost_deduplicates_by_content_id():
    from unittest.mock import MagicMock
    from app.services.library_service import _apply_boost

    row1 = MagicMock()
    row1.id = 1
    row1.title = "A"
    row1.content_type = ContentType.article
    row1.album_title = "Album A"
    row1.distance = 0.1

    row1_dup = MagicMock()
    row1_dup.id = 1  # duplicate
    row1_dup.title = "A"
    row1_dup.content_type = ContentType.article
    row1_dup.album_title = "Album B"
    row1_dup.distance = 0.2

    results = _apply_boost([row1, row1_dup], boosted_ids=set(), saved_ids=set())
    assert len(results) == 1
    assert results[0].content_id == 1


def test_apply_boost_limits_to_10_results():
    from unittest.mock import MagicMock
    from app.services.library_service import _apply_boost

    rows = []
    for i in range(15):
        row = MagicMock()
        row.id = i
        row.title = f"Snippet {i}"
        row.content_type = ContentType.article
        row.album_title = None
        row.distance = i * 0.05
        rows.append(row)

    results = _apply_boost(rows, boosted_ids=set(), saved_ids=set())
    assert len(results) == 10
```

- [ ] **Step 2: Run new tests — confirm they fail**

```bash
cd backend && poetry run pytest tests/test_library_service.py::test_apply_boost_elevates_saved_content tests/test_library_service.py::test_apply_boost_deduplicates_by_content_id tests/test_library_service.py::test_apply_boost_limits_to_10_results -v
```

Expected: `ImportError` — `_apply_boost` does not exist yet.

- [ ] **Step 3: Add _apply_boost and semantic_search to library_service.py**

Append to `backend/app/services/library_service.py`:

```python
from app.services.embedding_service import embed_text


def _apply_boost(
    rows: list,
    boosted_ids: set[int],
    saved_ids: set[int],
) -> list[ContentSearchResult]:
    results = []
    seen: set[int] = set()
    for row in rows:
        if row.id in seen:
            continue
        seen.add(row.id)
        similarity = 1.0 - float(row.distance)
        if row.id in boosted_ids:
            similarity *= LIBRARY_SEARCH_BOOST
        results.append(
            ContentSearchResult(
                content_id=row.id,
                title=row.title,
                content_type=row.content_type,
                album_title=row.album_title,
                similarity_score=round(similarity, 4),
                is_saved=row.id in saved_ids,
            )
        )
    results.sort(key=lambda r: r.similarity_score, reverse=True)
    return results[:10]


async def semantic_search(
    db: AsyncSession, query: str, user: User
) -> list[ContentSearchResult]:
    from sqlalchemy import text as sa_text
    from app.models.album import Side, SideContent

    # Collect IDs that deserve a boost
    saved_ids_stmt = select(UserSnippetSave.content_id).where(
        UserSnippetSave.user_id == user.id
    )
    saved_ids: set[int] = set((await db.execute(saved_ids_stmt)).scalars().all())

    enrolled_album_ids_stmt = select(AlbumEnrolment.album_id).where(
        AlbumEnrolment.user_id == user.id
    )
    enrolled_album_ids: set[int] = set(
        (await db.execute(enrolled_album_ids_stmt)).scalars().all()
    )

    enrolled_content_ids: set[int] = set()
    if enrolled_album_ids:
        enrolled_content_stmt = (
            select(SideContent.content_id)
            .join(Side, Side.id == SideContent.side_id)
            .where(Side.album_id.in_(enrolled_album_ids))
        )
        enrolled_content_ids = set(
            (await db.execute(enrolled_content_stmt)).scalars().all()
        )

    boosted_ids = saved_ids | enrolled_content_ids

    # Vector similarity search
    query_vec = embed_text(query)
    query_vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

    rows = (
        await db.execute(
            sa_text(
                """
                SELECT
                    c.id,
                    c.title,
                    c.content_type,
                    a.title AS album_title,
                    (c.embedding <=> :vec::vector) AS distance
                FROM content c
                LEFT JOIN side_content sc ON sc.content_id = c.id
                LEFT JOIN sides s ON s.id = sc.side_id
                LEFT JOIN albums a ON a.id = s.album_id
                WHERE c.embedding IS NOT NULL
                ORDER BY distance
                LIMIT 20
                """
            ),
            {"vec": query_vec_str},
        )
    ).fetchall()

    return _apply_boost(rows, boosted_ids=boosted_ids, saved_ids=saved_ids)
```

- [ ] **Step 4: Run all library service tests**

```bash
cd backend && poetry run pytest tests/test_library_service.py -v
```

Expected: all 6 tests pass (the `_apply_boost` tests run without DB; `get_library` tests use real DB).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/library_service.py backend/tests/test_library_service.py
git commit -m "feat: add _apply_boost and semantic_search to library_service"
```

---

## Task 12: library_service.mentor_query() (TDD)

**Files:**
- Modify: `backend/app/services/library_service.py`
- Modify: `backend/tests/test_library_service.py`

- [ ] **Step 1: Add mentor_query test**

Append to `backend/tests/test_library_service.py`:

```python
async def test_mentor_query_returns_reply_and_sources(
    db_session: AsyncSession, current_user: User
) -> None:
    import json
    from unittest.mock import MagicMock, patch

    topic = await _make_topic(db_session)
    snippet = await _make_snippet(db_session, topic.id, title="Cloud Networking")
    await db_session.commit()

    fake_embed = [0.1] * 1536
    fake_gen_body = json.dumps({
        "results": [{"outputText": "Networking connects computers.", "completionReason": "FINISH"}]
    }).encode()
    mock_gen_response = {"body": MagicMock(read=MagicMock(return_value=fake_gen_body))}

    with (
        patch("app.services.library_service.embed_text", return_value=fake_embed),
        patch("app.services.library_service._fetch_mentor_context") as mock_ctx,
        patch("app.services.library_service.boto3.client") as mock_bedrock,
    ):
        mock_ctx.return_value = [
            {"content_id": snippet.id, "title": snippet.title, "body": snippet.body or ""}
        ]
        mock_bedrock.return_value.invoke_model.return_value = mock_gen_response

        from app.services.library_service import mentor_query
        result = await mentor_query(db_session, "What is networking?", current_user)

    assert "Networking" in result.reply
    assert len(result.sources) >= 1
    assert result.sources[0].title == "Cloud Networking"
```

- [ ] **Step 2: Run test — confirm it fails**

```bash
cd backend && poetry run pytest tests/test_library_service.py::test_mentor_query_returns_reply_and_sources -v
```

Expected: `ImportError` — `mentor_query` / `_fetch_mentor_context` not yet defined.

- [ ] **Step 3: Implement mentor_query() in library_service.py**

Append to `backend/app/services/library_service.py`:

```python
import json

import boto3

from app.config import get_settings
from app.schemas.library import MentorResponse, MentorSource

MENTOR_CONTEXT_CHUNKS = 6
MENTOR_PERSONAL_LIMIT = 5
MENTOR_GLOBAL_LIMIT = 10


async def _fetch_mentor_context(
    db: AsyncSession, query_vec: list[float], user: User
) -> list[dict]:
    from sqlalchemy import text as sa_text

    vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

    # Personal: saved + enrolled content
    saved_ids_stmt = select(UserSnippetSave.content_id).where(
        UserSnippetSave.user_id == user.id
    )
    saved_ids = set((await db.execute(saved_ids_stmt)).scalars().all())

    enrolled_album_ids_stmt = select(AlbumEnrolment.album_id).where(
        AlbumEnrolment.user_id == user.id
    )
    enrolled_album_ids = set((await db.execute(enrolled_album_ids_stmt)).scalars().all())

    from app.models.album import Side, SideContent

    enrolled_content_ids: set[int] = set()
    if enrolled_album_ids:
        enrolled_content_stmt = (
            select(SideContent.content_id)
            .join(Side, Side.id == SideContent.side_id)
            .where(Side.album_id.in_(enrolled_album_ids))
        )
        enrolled_content_ids = set(
            (await db.execute(enrolled_content_stmt)).scalars().all()
        )

    personal_ids = saved_ids | enrolled_content_ids

    personal_rows = []
    if personal_ids:
        personal_rows = (
            await db.execute(
                sa_text(
                    """
                    SELECT id, title, body,
                           (embedding <=> :vec::vector) AS distance
                    FROM content
                    WHERE id = ANY(:ids) AND embedding IS NOT NULL
                    ORDER BY distance
                    LIMIT :lim
                    """
                ),
                {"vec": vec_str, "ids": list(personal_ids), "lim": MENTOR_PERSONAL_LIMIT},
            )
        ).fetchall()

    global_rows = (
        await db.execute(
            sa_text(
                """
                SELECT id, title, body,
                       (embedding <=> :vec::vector) AS distance
                FROM content
                WHERE embedding IS NOT NULL
                ORDER BY distance
                LIMIT :lim
                """
            ),
            {"vec": vec_str, "lim": MENTOR_GLOBAL_LIMIT},
        )
    ).fetchall()

    # Merge: personal rows boosted, global rows at base weight
    merged: dict[int, dict] = {}
    for row in global_rows:
        merged[row.id] = {
            "content_id": row.id,
            "title": row.title,
            "body": row.body or "",
            "score": 1.0 - float(row.distance),
        }
    for row in personal_rows:
        score = (1.0 - float(row.distance)) * LIBRARY_SEARCH_BOOST
        if row.id not in merged or score > merged[row.id]["score"]:
            merged[row.id] = {
                "content_id": row.id,
                "title": row.title,
                "body": row.body or "",
                "score": score,
            }

    ranked = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
    return ranked[:MENTOR_CONTEXT_CHUNKS]


async def mentor_query(db: AsyncSession, message: str, user: User) -> MentorResponse:
    settings = get_settings()
    query_vec = embed_text(message)
    chunks = await _fetch_mentor_context(db, query_vec, user)

    context_text = "\n\n".join(
        f"{c['title']}: {c['body'][:500]}" for c in chunks
    )

    prompt = (
        "You are the Dynamic Mentor for Living Campus, an Amazon T-Level education platform.\n"
        "Answer the student's question using the provided context from their learning materials.\n"
        "If the context doesn't cover the question, say so and answer from general knowledge.\n\n"
        f"Context:\n{context_text}\n\n"
        f"Student question: {message}\n\nMentor:"
    )

    client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
    response = client.invoke_model(
        modelId=settings.BEDROCK_GENERATION_MODEL_ID,
        body=json.dumps({
            "inputText": prompt,
            "textGenerationConfig": {"maxTokenCount": 512, "temperature": 0.7, "topP": 0.9},
        }),
    )
    body = json.loads(response["body"].read())
    reply_text = body["results"][0]["outputText"].strip()

    sources = [MentorSource(content_id=c["content_id"], title=c["title"]) for c in chunks]
    return MentorResponse(reply=reply_text, sources=sources)
```

- [ ] **Step 4: Run all library service tests**

```bash
cd backend && poetry run pytest tests/test_library_service.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/library_service.py backend/tests/test_library_service.py
git commit -m "feat: add mentor_query() to library_service"
```

---

## Task 13: /library router + register routers in main.py

**Files:**
- Create: `backend/app/routers/library.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create /library router**

Create `backend/app/routers/library.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.library import ContentSearchResult, LibraryResponse, MentorRequest, MentorResponse
from app.services import library_service

router = APIRouter(prefix="/library", tags=["library"])


@router.get("/", response_model=LibraryResponse, summary="Get user's library")
async def get_library(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LibraryResponse:
    return await library_service.get_library(db, current_user)


@router.get(
    "/search",
    response_model=list[ContentSearchResult],
    summary="Semantic search across catalogue",
)
async def search(
    q: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ContentSearchResult]:
    return await library_service.semantic_search(db, q, current_user)


@router.post("/mentor", response_model=MentorResponse, summary="Ask the Dynamic Mentor")
async def mentor(
    body: MentorRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MentorResponse:
    return await library_service.mentor_query(db, body.message, current_user)
```

- [ ] **Step 2: Register new routers in main.py**

In `backend/app/main.py`, add the imports:

```python
from app.routers import albums, auth, content, feed, library, snippets, topics, users
```

Then add after `app.include_router(albums.router)`:

```python
app.include_router(snippets.router)
app.include_router(library.router)
```

- [ ] **Step 3: Run full backend test suite**

```bash
cd backend && poetry run pytest -x -q
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/library.py backend/app/main.py
git commit -m "feat: add /library router and register /snippets and /library in main.py"
```

---

## Task 14: Frontend — library.ts API client

**Files:**
- Create: `frontend/src/lib/api/library.ts`

- [ ] **Step 1: Check existing API client pattern**

Read `frontend/src/lib/api/albums.ts` to understand the fetch pattern used in this project (base URL, error handling, auth headers).

- [ ] **Step 2: Create library.ts**

Create `frontend/src/lib/api/library.ts`:

```typescript
import { ApiError } from '$lib/api/types';

const BASE = '/api';

export interface LibraryAlbum {
  id: number;
  t_level_id: number;
  topic_id: number;
  title: string;
  description: string;
  icon: string;
}

export interface LibrarySnippet {
  id: number;
  title: string;
  content_type: 'article' | 'audio' | 'video';
  media_url: string | null;
  topic_id: number;
  t_level_id: number | null;
}

export interface LibraryResponse {
  enrolled_albums: LibraryAlbum[];
  saved_snippets: LibrarySnippet[];
}

export interface ContentSearchResult {
  content_id: number;
  title: string;
  content_type: 'article' | 'audio' | 'video';
  album_title: string | null;
  similarity_score: number;
  is_saved: boolean;
}

export interface MentorSource {
  content_id: number;
  title: string;
}

export interface MentorResponse {
  reply: string;
  sources: MentorSource[];
}

async function fetchWithAuth(path: string, options: RequestInit = {}): Promise<Response> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(options.headers ?? {}) },
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, detail.detail ?? res.statusText);
  }
  return res;
}

export async function getLibrary(): Promise<LibraryResponse> {
  const res = await fetchWithAuth('/library/');
  return res.json();
}

export async function searchLibrary(query: string): Promise<ContentSearchResult[]> {
  const res = await fetchWithAuth(`/library/search?q=${encodeURIComponent(query)}`);
  return res.json();
}

export async function mentorQuery(message: string): Promise<MentorResponse> {
  const res = await fetchWithAuth('/library/mentor', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
  return res.json();
}

export async function saveSnippet(contentId: number): Promise<void> {
  await fetchWithAuth(`/snippets/${contentId}/save`, { method: 'POST' });
}

export async function unsaveSnippet(contentId: number): Promise<void> {
  await fetchWithAuth(`/snippets/${contentId}/save`, { method: 'DELETE' });
}
```

- [ ] **Step 3: Verify ApiError import works**

```bash
grep -n "export class ApiError\|export.*ApiError" frontend/src/lib/api/types.ts
```

If `ApiError` is not exported from `types.ts`, add it there:

```typescript
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}
```

- [ ] **Step 4: Typecheck**

```bash
cd frontend && npm run check 2>&1 | grep -E "error|Error" | head -10
```

Expected: 0 new errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/api/library.ts frontend/src/lib/api/types.ts
git commit -m "feat: add library.ts API client (getLibrary, searchLibrary, mentorQuery, save/unsave)"
```

---

## Task 15: SnippetCard.svelte — full implementation + save toggle

**Files:**
- Modify: `frontend/src/lib/components/SnippetCard.svelte`

The file is currently a stub (template comment + empty script). Read it first.

- [ ] **Step 1: Read SnippetCard.svelte**

Read `frontend/src/lib/components/SnippetCard.svelte` to see the current stub and prop definitions.

- [ ] **Step 2: Implement SnippetCard.svelte**

Replace the entire file content with:

```svelte
<!--
  SnippetCard
  Purpose: Square card to open a Snippet (article / audio / video).
  Props:
    - content (ContentListResponse): the Snippet to display
    - xp (number | undefined): XP available — shown via XPBadge if set
    - saved (boolean | undefined): whether the user has saved this snippet
    - onSaveToggle (() => void | undefined): called when save button clicked (auth-gated by parent)
-->
<script lang="ts">
  import type { ContentListResponse } from '$lib/api/types';

  export let content: ContentListResponse;
  export let xp: number | undefined = undefined;
  export let saved: boolean | undefined = undefined;
  export let onSaveToggle: (() => void) | undefined = undefined;

  const ICONS: Record<string, string> = {
    article: '📄',
    audio: '🎧',
    video: '🎬',
  };

  $: icon = ICONS[content.content_type] ?? '📄';
</script>

<div class="snippet-card">
  {#if xp !== undefined}
    <span class="xp-badge">+{xp} XP</span>
  {/if}
  {#if onSaveToggle !== undefined}
    <button
      class="save-btn"
      class:saved
      on:click|stopPropagation={onSaveToggle}
      aria-label={saved ? 'Remove from library' : 'Save to library'}
      title={saved ? 'Remove from library' : 'Save to library'}
    >
      {saved ? '🔖' : '🏷️'}
    </button>
  {/if}
  <span class="icon" aria-hidden="true">{icon}</span>
  <span class="title">{content.title}</span>
</div>

<style>
  .snippet-card {
    position: relative;
    aspect-ratio: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.85);
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(35, 47, 62, 0.12);
    cursor: pointer;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }

  .snippet-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(35, 47, 62, 0.18);
  }

  .icon {
    font-size: 2rem;
  }

  .title {
    font-size: 0.85rem;
    font-weight: 600;
    text-align: center;
    color: #232f3e;
    line-height: 1.3;
  }

  .xp-badge {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    font-size: 0.7rem;
    font-weight: 700;
    background: linear-gradient(to right, #f97316, #facc15);
    color: white;
    border-radius: 99px;
    padding: 0.15rem 0.45rem;
  }

  .save-btn {
    position: absolute;
    top: 0.5rem;
    left: 0.5rem;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1rem;
    padding: 0;
    line-height: 1;
    opacity: 0.6;
    transition: opacity 0.15s;
  }

  .save-btn:hover,
  .save-btn.saved {
    opacity: 1;
  }
</style>
```

- [ ] **Step 3: Typecheck**

```bash
cd frontend && npm run check 2>&1 | grep -E "^.*error" | head -10
```

Expected: 0 new errors.

- [ ] **Step 4: Run tests**

```bash
cd frontend && npx vitest run
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/components/SnippetCard.svelte
git commit -m "feat: implement SnippetCard with save toggle"
```

---

## Task 16: CTASidebar — AgentChat navigates to /library

**Files:**
- Modify: `frontend/src/lib/components/CTASidebar.svelte`

The AgentChat in the sidebar is a teaser: on submit, it navigates to `/library?q={message}` so the Library page picks up the query. Read the file first.

- [ ] **Step 1: Read CTASidebar.svelte**

Read `frontend/src/lib/components/CTASidebar.svelte` to find the `<AgentChat>` usage and current submit handler.

- [ ] **Step 2: Add goto import and handle AgentChat submit**

In `CTASidebar.svelte`, in the `<script>` block, add the import:

```typescript
import { goto } from '$app/navigation';
```

Find the `<AgentChat>` element. Add an `on:submit` handler:

```svelte
<AgentChat
  placeholder="Ask your mentor anything..."
  on:submit={(e) => goto(`/library?q=${encodeURIComponent(e.detail)}`)}
/>
```

If the `<AgentChat>` element already has `on:submit`, replace its handler with the `goto` call above.

- [ ] **Step 3: Typecheck**

```bash
cd frontend && npm run check 2>&1 | grep -E "^.*error" | head -10
```

Expected: 0 new errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/components/CTASidebar.svelte
git commit -m "feat: CTASidebar AgentChat navigates to /library?q= on submit"
```

---

## Task 17: /library page — auth guard, data load, full UI

**Files:**
- Modify: `frontend/src/routes/library/+page.ts`
- Modify: `frontend/src/routes/library/+page.svelte`

- [ ] **Step 1: Write +page.ts with auth guard and data load**

Replace `frontend/src/routes/library/+page.ts` content. If the file doesn't exist, create it.

Check how other authenticated pages do redirects (e.g. `frontend/src/routes/settings/+page.ts`) and follow the same pattern. Typical SvelteKit pattern:

```typescript
import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';
import { getLibrary } from '$lib/api/library';

export const load: PageLoad = async ({ url, parent }) => {
  const { user } = await parent();
  if (!user) {
    throw redirect(302, `/login?next=${encodeURIComponent(url.pathname)}`);
  }
  const library = await getLibrary();
  const q = url.searchParams.get('q') ?? '';
  return { library, initialQuery: q };
};
```

Read `frontend/src/routes/+layout.ts` to confirm what `parent()` returns (specifically whether it exposes a `user` field). Adjust the guard accordingly if the field name differs.

- [ ] **Step 2: Implement /library page**

Replace `frontend/src/routes/library/+page.svelte` with:

```svelte
<script lang="ts">
  import type { PageData } from './$types';
  import PageCard from '$lib/components/PageCard.svelte';
  import AlbumCard from '$lib/components/AlbumCard.svelte';
  import SnippetCard from '$lib/components/SnippetCard.svelte';
  import AgentChat from '$lib/components/AgentChat.svelte';
  import { searchLibrary, mentorQuery, saveSnippet, unsaveSnippet } from '$lib/api/library';
  import type { ContentSearchResult, MentorResponse } from '$lib/api/library';

  export let data: PageData;

  let query = data.initialQuery;
  let searchResults: ContentSearchResult[] | null = null;
  let searching = false;
  let searchError = '';

  let mentorReply: MentorResponse | null = null;
  let mentorLoading = false;
  let mentorError = '';

  // Optimistic save state: track which saved snippets are saved
  let savedIds = new Set(data.library.saved_snippets.map((s) => s.id));

  async function handleSearch() {
    if (!query.trim()) return;
    searching = true;
    searchError = '';
    try {
      searchResults = await searchLibrary(query);
    } catch {
      searchError = 'Search failed. Please try again.';
    } finally {
      searching = false;
    }
  }

  async function handleMentor(event: CustomEvent<string>) {
    mentorLoading = true;
    mentorError = '';
    try {
      mentorReply = await mentorQuery(event.detail);
    } catch {
      mentorError = 'The mentor is unavailable right now. Please try again.';
    } finally {
      mentorLoading = false;
    }
  }

  async function toggleSave(contentId: number, currentlySaved: boolean) {
    if (currentlySaved) {
      savedIds.delete(contentId);
      savedIds = new Set(savedIds);
      await unsaveSnippet(contentId);
    } else {
      savedIds.add(contentId);
      savedIds = new Set(savedIds);
      await saveSnippet(contentId);
    }
  }
</script>

<div class="library-layout">
  <!-- Search bar -->
  <PageCard padding="1rem 1.5rem">
    <form class="search-bar" on:submit|preventDefault={handleSearch}>
      <input
        bind:value={query}
        type="search"
        placeholder="Search your learning materials..."
        class="search-input"
      />
      <button type="submit" class="search-btn" disabled={searching}>
        {searching ? 'Searching…' : 'Search'}
      </button>
    </form>
    {#if searchError}
      <p class="error">{searchError}</p>
    {/if}
  </PageCard>

  {#if searchResults !== null}
    <!-- Search results view -->
    <PageCard padding="1.5rem">
      <h2 class="section-heading">Search Results</h2>
      {#if searchResults.length === 0}
        <p class="empty">No results found for "{query}".</p>
      {:else}
        <div class="snippet-grid">
          {#each searchResults as result (result.content_id)}
            <SnippetCard
              content={{ id: result.content_id, title: result.title, content_type: result.content_type }}
              saved={savedIds.has(result.content_id)}
              onSaveToggle={() => toggleSave(result.content_id, savedIds.has(result.content_id))}
            />
          {/each}
        </div>
      {/if}
      <button class="clear-btn" on:click={() => { searchResults = null; query = ''; }}>
        ← Back to library
      </button>
    </PageCard>
  {:else}
    <!-- Default library view: two columns -->
    <div class="library-columns">
      <!-- Enrolled albums -->
      <div class="column">
        <PageCard padding="1.5rem" overflowY="hidden">
          <h2 class="section-heading">Enrolled Albums</h2>
        </PageCard>
        {#if data.library.enrolled_albums.length === 0}
          <PageCard padding="1.5rem">
            <p class="empty">You haven't enrolled in any albums yet.</p>
          </PageCard>
        {:else}
          {#each data.library.enrolled_albums as album (album.id)}
            <AlbumCard {album} />
          {/each}
        {/if}
      </div>

      <!-- Saved snippets -->
      <div class="column">
        <PageCard padding="1.5rem" overflowY="hidden">
          <h2 class="section-heading">Saved Snippets</h2>
        </PageCard>
        {#if data.library.saved_snippets.length === 0}
          <PageCard padding="1.5rem">
            <p class="empty">You haven't saved any snippets yet.</p>
          </PageCard>
        {:else}
          <div class="snippet-grid">
            {#each data.library.saved_snippets as snippet (snippet.id)}
              <SnippetCard
                content={snippet}
                saved={savedIds.has(snippet.id)}
                onSaveToggle={() => toggleSave(snippet.id, savedIds.has(snippet.id))}
              />
            {/each}
          </div>
        {/if}
      </div>
    </div>
  {/if}

  <!-- Dynamic Mentor -->
  <PageCard padding="1.5rem">
    <h2 class="section-heading">Dynamic Mentor</h2>
    <AgentChat
      placeholder="Ask your mentor anything about your saved content..."
      on:submit={handleMentor}
    />
    {#if mentorLoading}
      <p class="mentor-loading">Thinking…</p>
    {/if}
    {#if mentorError}
      <p class="error">{mentorError}</p>
    {/if}
    {#if mentorReply}
      <div class="mentor-reply">
        <p>{mentorReply.reply}</p>
        {#if mentorReply.sources.length > 0}
          <div class="sources">
            <span class="sources-label">Sources:</span>
            {#each mentorReply.sources as source (source.content_id)}
              <span class="source-chip">{source.title}</span>
            {/each}
          </div>
        {/if}
      </div>
    {/if}
  </PageCard>
</div>

<style>
  .library-layout {
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner, 0.75rem);
    max-width: 1100px;
    margin: 0 auto;
    width: 100%;
  }

  .search-bar {
    display: flex;
    gap: 0.75rem;
  }

  .search-input {
    flex: 1;
    padding: 0.65rem 1rem;
    border: 1px solid rgba(35, 47, 62, 0.2);
    border-radius: 8px;
    font-size: 0.95rem;
    outline: none;
  }

  .search-input:focus {
    border-color: #f97316;
  }

  .search-btn {
    padding: 0.65rem 1.25rem;
    background: linear-gradient(to right, #f97316, #facc15);
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    color: white;
  }

  .search-btn:disabled {
    opacity: 0.6;
    cursor: default;
  }

  .library-columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--gap-inner, 0.75rem);
  }

  .column {
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner, 0.75rem);
  }

  .snippet-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 0.75rem;
  }

  .section-heading {
    margin: 0;
    font-size: 1rem;
    font-weight: 700;
    color: #232f3e;
  }

  .empty {
    color: #5a6472;
    font-size: 0.9rem;
    margin: 0;
  }

  .error {
    color: #dc2626;
    font-size: 0.875rem;
    margin: 0.5rem 0 0;
  }

  .clear-btn {
    margin-top: 1rem;
    background: none;
    border: none;
    color: #f97316;
    cursor: pointer;
    font-size: 0.9rem;
    padding: 0;
  }

  .mentor-loading {
    color: #5a6472;
    font-size: 0.9rem;
    margin: 0.75rem 0 0;
  }

  .mentor-reply {
    margin-top: 1rem;
    background: rgba(249, 115, 22, 0.06);
    border-radius: 8px;
    padding: 1rem;
  }

  .mentor-reply p {
    margin: 0 0 0.75rem;
    font-size: 0.95rem;
    line-height: 1.6;
    color: #232f3e;
  }

  .sources {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    align-items: center;
  }

  .sources-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: #5a6472;
  }

  .source-chip {
    font-size: 0.75rem;
    background: rgba(249, 115, 22, 0.12);
    color: #c2410c;
    border-radius: 99px;
    padding: 0.2rem 0.6rem;
    font-weight: 500;
  }
</style>
```

- [ ] **Step 3: Typecheck**

```bash
cd frontend && npm run check 2>&1 | tail -5
```

Expected: 0 errors.

- [ ] **Step 4: Run full test suite**

```bash
cd frontend && npx vitest run
```

Expected: all tests pass.

- [ ] **Step 5: Run lint**

```bash
cd frontend && npm run lint
```

Expected: 0 errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/routes/library/
git commit -m "feat: implement /library page — search, enrolled albums, saved snippets, Dynamic Mentor"
```

---

## Task 18: Final verification

- [ ] **Step 1: Run full backend test suite**

```bash
cd backend && poetry run pytest -q
```

Expected: all tests pass, 0 failures.

- [ ] **Step 2: Run full frontend test suite**

```bash
cd frontend && npx vitest run
```

Expected: all tests pass.

- [ ] **Step 3: Run seed with embeddings (local only)**

```bash
cd backend && SKIP_EMBEDDINGS=false poetry run python seed.py
```

Expected: seeds content, then embeds all snippets and albums via Bedrock.

- [ ] **Step 4: Smoke test the API**

Start the stack:
```bash
docker compose up --build -d
```

Test the health check:
```bash
curl http://localhost:8000/health
```

Expected: `{"status": "ok"}`

Test that the library endpoint requires auth:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/library/
```

Expected: `401`

- [ ] **Step 5: Commit any final fixes, then push**

```bash
git add -A
git status  # confirm nothing stale
git push origin dev
```
