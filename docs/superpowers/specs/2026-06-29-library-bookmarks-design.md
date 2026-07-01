# Library Bookmarks + Semantic Search Design

**Date:** 2026-06-29
**Status:** Approved

## Overview

Add bookmarking/saving of albums and snippets to The Library, with semantic indexing via pgvector and Amazon Bedrock Titan Embeddings. The embedding store serves two purposes: semantic search inside The Library, and retrieval-augmented generation (RAG) for the Dynamic Mentor (AgentChat).

Albums are saved via the existing `AlbumEnrolment` mechanism. Snippets get a new `UserSnippetSave` table. The full catalogue is embedded at seed time; saved/enrolled content receives a score boost at query time (hybrid weighting).

---

## Data Model

### pgvector extension

Enable `pgvector` in PostgreSQL via Alembic migration:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Embedding columns on existing models

**`Content` (snippets):**
- `embedding: vector(1536)` — nullable, populated by seed
- `embedding_generated_at: DateTime` — nullable; non-null rows are skipped on re-seed

**`Album`:**
- `embedding: vector(1536)` — nullable, populated by seed
- `embedding_generated_at: DateTime` — nullable; non-null rows skipped on re-seed

Both columns get an `ivfflat` index for approximate nearest-neighbour queries.

Embedding dimensions: 1536 — matches `amazon.titan-embed-text-v1`.

### New table: `UserSnippetSave`

```python
class UserSnippetSave(Base):
    __tablename__ = "user_snippet_saves"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("content.id"), primary_key=True)
    saved_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship()
    content: Mapped["Content"] = relationship()
```

Mirrors `AlbumEnrolment`. Album saves continue to use `AlbumEnrolment` unchanged.

### User model additions

`User` gains two new relationships:
- `saved_snippets` via `UserSnippetSave`
- `enrolled_albums` via `AlbumEnrolment` (already exists, relationship formalised)

---

## Embedding Pipeline

### Trigger

`seed.py` gains an `embed_content()` phase that runs after content seeding. Invoke with:

```bash
poetry run python seed.py --embed   # embed only
poetry run python seed.py           # seed + embed (default)
```

A `SKIP_EMBEDDINGS=true` env var skips Bedrock calls in CI.

### What gets embedded

| Model | Input text |
|-------|-----------|
| `Content` | `f"{title}\n\n{body[:8000]}"` |
| `Album` | `f"{title}\n\n{description}"` |

### Bedrock call

```python
client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
response = client.invoke_model(
    modelId=settings.BEDROCK_EMBEDDING_MODEL_ID,
    body=json.dumps({"inputText": text}),
)
embedding = json.loads(response["body"].read())["embedding"]
```

Sequential loop over all un-embedded rows. For the prototype corpus this is acceptable. At scale, parallelise with `asyncio.gather`.

### Config additions

```python
BEDROCK_EMBEDDING_MODEL_ID: str = "amazon.titan-embed-text-v1"
BEDROCK_GENERATION_MODEL_ID: str = "amazon.titan-text-express-v1"
SKIP_EMBEDDINGS: bool = False
```

---

## Backend API

### New router: `/library`

**`GET /library/`** (auth required)
Returns the user's enrolled albums and saved snippets.

Response:
```json
{
  "enrolled_albums": [AlbumListResponse + is_enrolled: true],
  "saved_snippets": [ContentResponse + is_saved: true]
}
```

**`GET /library/search?q=<query>`** (auth required)
1. Embed `q` via Bedrock Titan
2. Cosine similarity query (`<=>`) against `Content.embedding` — top-20 candidates
3. Apply boost: items whose `content_id` is in the user's saved set, or whose album the user is enrolled in, get score multiplied by `LIBRARY_SEARCH_BOOST = 1.4`
4. Re-rank and return top-10

Response: `list[ContentSearchResult]`
```json
{
  "content_id": int,
  "title": str,
  "content_type": str,
  "album_title": str | null,
  "similarity_score": float,
  "is_saved": bool
}
```

**`POST /library/mentor`** (auth required)
Dynamic Mentor RAG endpoint.

Request: `{ "message": str }`

Steps:
1. Embed `message` via Bedrock Titan
2. **Personal query**: cosine similarity on user's saved/enrolled content — top-5, boost `×1.4`
3. **Global query**: cosine similarity on full catalogue — top-10, base weight `×1.0`
4. Merge, deduplicate by `content_id`, re-rank by weighted score, take top-6
5. Build RAG prompt with context chunks + user message
6. Call `BEDROCK_GENERATION_MODEL_ID` (Titan Text Express)
7. Return `{ "reply": str, "sources": [{ "content_id": int, "title": str }] }`

### New router: `/snippets`

**`POST /snippets/{content_id}/save`** (auth required, 204)
Upsert row in `UserSnippetSave`. Idempotent.

**`DELETE /snippets/{content_id}/save`** (auth required, 204)
Delete row from `UserSnippetSave`. No-op if not saved.

**`GET /snippets/{content_id}`** (public)
Snippet detail. For authenticated users, include `is_saved: bool` derived from `UserSnippetSave`.

### Modified: `/albums/{album_id}`

Add `is_enrolled: bool` to `AlbumDetailResponse`. Derived from `AlbumEnrolment` for authenticated users; `false` for guests.

### Service layer

| File | Responsibility |
|------|---------------|
| `backend/app/services/library_service.py` | `get_library()`, `semantic_search()`, `mentor_query()` |
| `backend/app/services/snippet_service.py` | `save_snippet()`, `unsave_snippet()`, `get_snippet()` |
| `backend/app/services/embedding_service.py` | `embed_text()` wrapper around Bedrock; used by seed.py and library_service |

The score boost constant (`LIBRARY_SEARCH_BOOST = 1.4`) lives in `library_service.py` as a module-level constant.

---

## RAG Prompt

```
You are the Dynamic Mentor for Living Campus, an Amazon T-Level education platform.
Answer the student's question using the provided context from their saved learning materials.
If the context doesn't cover the question, say so clearly and answer from general knowledge.

Context:
{chunk_1_title}: {chunk_1_text}
...

Student question: {message}
```

Sources returned in the response allow the frontend to render citation chips.

---

## Frontend

### `/library` page

**Layout:** Two-column below a search bar.
- Left column: enrolled albums as `AlbumCard` components (title, progress bar, unenrol button)
- Right column: saved snippets as `SnippetCard` grid (with unsave button)
- Search bar at top: on submit calls `GET /library/search?q=`; results replace the default two-column view with ranked `ContentSearchResult` cards

**Auth guard:** `/library/+page.ts` redirects unauthenticated users to `/login` using the existing SvelteKit load guard pattern.

### `SnippetCard` additions

A bookmark icon toggle (saved ↔ unsaved). On click:
- If unsaved: `POST /snippets/{id}/save` → optimistic UI update
- If saved: `DELETE /snippets/{id}/save` → optimistic UI update

Initial state comes from `is_saved` on the snippet response. Shown only when authenticated.

### `AgentChat` wire-up

On form submit: `POST /library/mentor` with `{ message }`. Response `reply` renders as Markdown in the chat. Response `sources` render as small citation chips below the reply. Simple request/response (no streaming in this iteration).

### New/modified files

| File | Change |
|------|--------|
| `frontend/src/routes/library/+page.svelte` | Full implementation (replaces stub) |
| `frontend/src/routes/library/+page.ts` | Auth guard + `GET /library/` data load |
| `frontend/src/lib/api/library.ts` | `getLibrary()`, `searchLibrary()`, `mentorQuery()` |
| `frontend/src/lib/components/SnippetCard.svelte` | Add save toggle (auth-gated) |
| `frontend/src/lib/components/AgentChat.svelte` | Wire to `POST /library/mentor` |

---

## Migration Plan

1. Alembic migration: `pgvector` extension, embedding columns + indexes on `content` and `albums`, `user_snippet_saves` table
2. Update `seed.py` with `embed_content()` phase
3. Backend: `embedding_service.py`, `snippet_service.py`, `library_service.py`, two new routers
4. Frontend: library page, SnippetCard save toggle, AgentChat wire-up

---

## Out of Scope

- Recommendations ("you might also like")
- Streaming Mentor responses
- Per-user embedding namespaces (hybrid global+personal weighting covers this at query time)
- Admin CMS for content management
- Comment threading on saved items
