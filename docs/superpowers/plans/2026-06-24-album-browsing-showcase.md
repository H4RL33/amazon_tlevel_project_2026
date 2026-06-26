# Album Browsing Showcase Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Album browsing work end-to-end for a showcase demo — seed real Album/Side/Snippet data on the backend, implement the frontend's real API client, and build `/learn` (Album list) and `/learn/[id]` (Album detail) pages — per `docs/superpowers/specs/2026-06-24-album-browsing-showcase-design.md`.

**Architecture:** Backend: extend `seed.py`'s existing idempotent pattern with `Content`/`Album`/`Side`/`SideContent` rows — no route/service changes, the Album/Side chapter's endpoints already work. Frontend: implement the previously-stubbed `apiFetch`, add a real `albums.ts` API client and matching types, fix `AlbumCard`/`AlbumGrid`'s prop shape to match the real backend response, implement `AlbumSidebar`/`SideHeader`, and build the two new pages.

**Tech Stack:** FastAPI + SQLAlchemy (backend, unchanged); SvelteKit + TypeScript + Vitest (frontend).

---

### Task 1: Seed Content, Album, Side, and SideContent rows

**Files:**
- Modify: `backend/seed.py`

- [ ] **Step 1: Add the seed data constants**

Add near the top of `backend/seed.py`, after the existing `TOPICS` list:

```python
SNIPPETS = [
    {
        "title": "What is Cloud Computing?",
        "body": "Cloud computing means renting computing power, storage, and "
        "services over the internet instead of buying and running your own "
        "physical servers. Providers like AWS offer this on demand, billed by "
        "usage, so you can scale up or down as your needs change.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    {
        "title": "Virtual Private Servers Explained",
        "body": "A Virtual Private Server (VPS) is a virtual machine sold as a "
        "service by a hosting provider. It behaves like a dedicated physical "
        "server but is actually a partitioned slice of a larger physical "
        "machine, shared with other VPS instances.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    {
        "title": "Intro to Virtual Private Networks",
        "body": "A Virtual Private Network (VLAN) logically separates devices "
        "on the same physical network into distinct broadcast domains, "
        "improving security and organisation without needing separate "
        "physical switches for each group.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    {
        "title": "Servers vs Serverless",
        "body": "Traditional servers run continuously and you pay for them "
        "whether or not they're handling requests. Serverless computing runs "
        "your code only when triggered, and you pay only for the compute time "
        "actually used.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
]

ALBUM = {
    "title": "Cloud Computing Fundamentals",
    "description": "An introduction to cloud computing, virtualisation, and "
    "the infrastructure that powers modern digital services.",
    "icon": "cloud",
    "t_level_topic_slug": "digital-infrastructure",
    "sides": [
        {
            "title": "Getting Started",
            "snippet_titles": ["What is Cloud Computing?", "Servers vs Serverless"],
        },
        {
            "title": "Networking Basics",
            "snippet_titles": [
                "Virtual Private Servers Explained",
                "Intro to Virtual Private Networks",
            ],
        },
    ],
}
```

- [ ] **Step 2: Add the seeding function**

Add this function after `_seed_topics` in `backend/seed.py`:

```python
async def _seed_album(session: AsyncSession) -> None:
    result = await session.execute(
        text("SELECT id FROM t_levels WHERE topic_id = (SELECT id FROM topics WHERE slug = :slug) LIMIT 1"),
        {"slug": ALBUM["t_level_topic_slug"]},
    )
    t_level_id = result.scalar_one()

    content_ids: dict[str, int] = {}
    for snippet in SNIPPETS:
        result = await session.execute(
            text("SELECT id FROM topics WHERE slug = :slug"),
            {"slug": snippet["topic_slug"]},
        )
        topic_id = result.scalar_one()

        await session.execute(
            text("""
                INSERT INTO content (title, body, content_type, topic_id)
                SELECT :title, :body, :content_type, :topic_id
                WHERE NOT EXISTS (
                    SELECT 1 FROM content WHERE title = :title
                )
            """),
            {
                "title": snippet["title"],
                "body": snippet["body"],
                "content_type": snippet["content_type"],
                "topic_id": topic_id,
            },
        )
        await session.flush()

        result = await session.execute(
            text("SELECT id FROM content WHERE title = :title"),
            {"title": snippet["title"]},
        )
        content_ids[snippet["title"]] = result.scalar_one()

    result = await session.execute(
        text("SELECT id FROM albums WHERE title = :title"),
        {"title": ALBUM["title"]},
    )
    album_id = result.scalar_one_or_none()

    if album_id is None:
        await session.execute(
            text("""
                INSERT INTO albums (title, description, icon, t_level_id)
                VALUES (:title, :description, :icon, :t_level_id)
            """),
            {
                "title": ALBUM["title"],
                "description": ALBUM["description"],
                "icon": ALBUM["icon"],
                "t_level_id": t_level_id,
            },
        )
        await session.flush()

        result = await session.execute(
            text("SELECT id FROM albums WHERE title = :title"),
            {"title": ALBUM["title"]},
        )
        album_id = result.scalar_one()

        for position, side in enumerate(ALBUM["sides"]):
            await session.execute(
                text("""
                    INSERT INTO sides (album_id, title, position)
                    VALUES (:album_id, :title, :position)
                """),
                {"album_id": album_id, "title": side["title"], "position": position},
            )
            await session.flush()

            result = await session.execute(
                text("""
                    SELECT id FROM sides
                    WHERE album_id = :album_id AND title = :title AND position = :position
                """),
                {"album_id": album_id, "title": side["title"], "position": position},
            )
            side_id = result.scalar_one()

            for snippet_position, title in enumerate(side["snippet_titles"]):
                await session.execute(
                    text("""
                        INSERT INTO side_content (side_id, content_id, position)
                        VALUES (:side_id, :content_id, :position)
                    """),
                    {
                        "side_id": side_id,
                        "content_id": content_ids[title],
                        "position": snippet_position,
                    },
                )

    await session.commit()
```

- [ ] **Step 3: Call it from `seed()`**

Change the existing `seed()` function from:

```python
async def seed() -> None:
    engine = create_async_engine(get_settings().DATABASE_URL, echo=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        await _seed_topics(session)
    await engine.dispose()
    print("Seed complete.")
```

to:

```python
async def seed() -> None:
    engine = create_async_engine(get_settings().DATABASE_URL, echo=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        await _seed_topics(session)
        await _seed_album(session)
    await engine.dispose()
    print("Seed complete.")
```

- [ ] **Step 4: Run it against a local Postgres to verify**

Ensure a Postgres matching `backend/.env`'s `DATABASE_URL` is running and migrated to
head (`poetry run alembic upgrade head` from `backend/`), then run:
`poetry run python seed.py`
Expected: no errors, ends with "Seed complete." Run it a **second time** immediately
after to confirm idempotency — expected: no errors, no duplicate rows (the `WHERE
NOT EXISTS`/`scalar_one_or_none()` guards should make the second run a no-op for
`content`/`albums`/`sides`/`side_content`).

Verify the data landed correctly:
```bash
poetry run python -c "
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import get_settings

async def check():
    engine = create_async_engine(get_settings().DATABASE_URL)
    async with engine.connect() as conn:
        result = await conn.execute(text('SELECT COUNT(*) FROM albums'))
        print('albums:', result.scalar_one())
        result = await conn.execute(text('SELECT COUNT(*) FROM sides'))
        print('sides:', result.scalar_one())
        result = await conn.execute(text('SELECT COUNT(*) FROM side_content'))
        print('side_content:', result.scalar_one())
    await engine.dispose()

asyncio.run(check())
"
```
Expected: `albums: 1`, `sides: 2`, `side_content: 4` (after either the first or
second run — counts must be identical both times).

- [ ] **Step 5: Commit**

```bash
git add backend/seed.py
git commit -m "feat: seed a real Album with Sides and Snippets for demo data"
```

---

### Task 2: Implement `apiFetch` for real

**Files:**
- Modify: `frontend/src/lib/api/client.ts`
- Test: `frontend/src/lib/api/client.test.ts` (new)

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/lib/api/client.test.ts`:

```ts
import { afterEach, describe, expect, it, vi } from 'vitest';
import { apiFetch, ApiError } from './client';

describe('apiFetch', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns parsed JSON on a successful response', async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ hello: 'world' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );
    vi.stubGlobal('fetch', mockFetch);

    const result = await apiFetch<{ hello: string }>('/topics/');

    expect(result).toEqual({ hello: 'world' });
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/topics/'),
      expect.any(Object)
    );
  });

  it('throws ApiError with the response status on a non-2xx response', async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Not found' }), { status: 404 })
    );
    vi.stubGlobal('fetch', mockFetch);

    await expect(apiFetch('/albums/999')).rejects.toMatchObject({
      status: 404,
      message: expect.stringContaining('404'),
    });
  });

  it('ApiError is an instance of Error with the correct name', () => {
    const err = new ApiError(500, 'boom');
    expect(err).toBeInstanceOf(Error);
    expect(err.name).toBe('ApiError');
    expect(err.status).toBe(500);
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: the two `apiFetch` tests FAIL — `apiFetch` currently just throws "not
implemented" unconditionally, so the success-case test fails and the error-case
test's status/message won't match. The `ApiError` instantiation test passes already
(that class is already implemented correctly).

- [ ] **Step 3: Replace `client.ts`'s `apiFetch` implementation**

Replace the existing stub:

```ts
export async function apiFetch<T>(_path: string, _init: RequestInit = {}): Promise<T> {
  throw new Error('not implemented');
}
```

with:

```ts
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '';
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init.headers,
    },
  });

  if (!response.ok) {
    throw new ApiError(response.status, `Request to ${path} failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}
```

(Keep the existing `TOKEN_KEY` constant and `ApiError` class above this function
unchanged — they're correct already and not part of this task.)

- [ ] **Step 4: Run the tests again to verify they pass**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — all `apiFetch` tests green, plus the full existing suite still
green.

- [ ] **Step 5: Format and commit**

```bash
cd frontend
npx prettier --write src/lib/api/client.ts src/lib/api/client.test.ts
git add src/lib/api/client.ts src/lib/api/client.test.ts
git commit -m "feat: implement apiFetch for real"
```

---

### Task 3: Add Album/Side response types

**Files:**
- Modify: `frontend/src/lib/api/types.ts`

- [ ] **Step 1: Append the new types**

Add to the end of `frontend/src/lib/api/types.ts`:

```ts
export interface AlbumListResponse {
  id: number;
  t_level_id: number;
  title: string;
  description: string;
  icon: string;
}

export interface SnippetSummaryResponse {
  id: number;
  title: string;
  content_type: ContentType;
}

export interface SideResponse {
  id: number;
  title: string;
  position: number;
  snippets: SnippetSummaryResponse[];
}

export interface AlbumDetailResponse extends AlbumListResponse {
  sides: SideResponse[];
  enrolled?: boolean;
  completed_count?: number;
  total_count?: number;
  progress_pct?: number;
}
```

These match the backend's `app/schemas/album.py` exactly (verified against the
Album/Side chapter's implementation) — `enrolled`/`completed_count`/`total_count`/
`progress_pct` are optional because the backend omits them entirely for anonymous
requests (`response_model_exclude_none=True`), which is exactly the case this slice
exercises (no auth yet).

- [ ] **Step 2: Verify it compiles**

Run (from `frontend/`): `npm run check`
Expected: 0 errors (same pre-existing warning count as before this change — this
step only adds new exported interfaces, nothing that should introduce new errors
elsewhere).

- [ ] **Step 3: Commit**

```bash
cd frontend
git add src/lib/api/types.ts
git commit -m "feat: add Album/Side response types"
```

---

### Task 4: Add the `albums.ts` API client

**Files:**
- Create: `frontend/src/lib/api/albums.ts`
- Test: `frontend/src/lib/api/albums.test.ts`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/lib/api/albums.test.ts`:

```ts
import { afterEach, describe, expect, it, vi } from 'vitest';
import { getAlbumDetail, listAlbums } from './albums';
import type { AlbumDetailResponse, AlbumListResponse } from './types';

describe('listAlbums', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('calls GET /albums/ and returns the parsed list', async () => {
    const albums: AlbumListResponse[] = [
      { id: 1, t_level_id: 1, title: 'Cloud Computing Fundamentals', description: '...', icon: 'cloud' },
    ];
    const mockFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(albums), { status: 200 }));
    vi.stubGlobal('fetch', mockFetch);

    const result = await listAlbums();

    expect(result).toEqual(albums);
    expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/albums/'), expect.any(Object));
  });
});

describe('getAlbumDetail', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('calls GET /albums/{id} and returns the parsed detail', async () => {
    const album: AlbumDetailResponse = {
      id: 1,
      t_level_id: 1,
      title: 'Cloud Computing Fundamentals',
      description: '...',
      icon: 'cloud',
      sides: [],
    };
    const mockFetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(album), { status: 200 }));
    vi.stubGlobal('fetch', mockFetch);

    const result = await getAlbumDetail(1);

    expect(result).toEqual(album);
    expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/albums/1'), expect.any(Object));
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: FAIL — `frontend/src/lib/api/albums.ts` doesn't exist yet (import error).

- [ ] **Step 3: Create `albums.ts`**

```ts
import { apiFetch } from './client';
import type { AlbumDetailResponse, AlbumListResponse } from './types';

export async function listAlbums(): Promise<AlbumListResponse[]> {
  return apiFetch<AlbumListResponse[]>('/albums/');
}

export async function getAlbumDetail(id: number): Promise<AlbumDetailResponse> {
  return apiFetch<AlbumDetailResponse>(`/albums/${id}`);
}
```

- [ ] **Step 4: Run the tests again to verify they pass**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — all tests green.

- [ ] **Step 5: Format and commit**

```bash
cd frontend
npx prettier --write src/lib/api/albums.ts src/lib/api/albums.test.ts
git add src/lib/api/albums.ts src/lib/api/albums.test.ts
git commit -m "feat: add albums.ts API client"
```

---

### Task 5: Fix `AlbumCard` to use the real `AlbumListResponse` shape

**Files:**
- Modify: `frontend/src/lib/components/AlbumCard.svelte`
- Test: `frontend/src/lib/shell.test.ts` (reuse the existing shared smoke-test file)

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/lib/shell.test.ts` (this file already exists from the Shell
& Layout chapter and holds this project's "compiles and exports a default" smoke
tests — keep using it rather than creating a new file, since it's the established
home for this test style):

```ts
describe('AlbumCard', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('$lib/components/AlbumCard.svelte');
    expect(mod.default).toBeDefined();
  });
});
```

- [ ] **Step 2: Run it to verify it currently passes (sanity check)**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — `AlbumCard.svelte` already exports a default component (the stub);
this is the baseline before the rewrite.

- [ ] **Step 3: Replace `AlbumCard.svelte`'s contents**

```svelte
<!--
  AlbumCard
  Purpose: Wide card used to open an Album — a curated, course-like set of Snippets forming a
    learning pathway. Requires an account to enrol.
  Used in: AlbumGrid (and later: CTASidebar, EnrolledAlbumsList, once those chapters land)
  Props:
    - album (AlbumListResponse): the Album to display
    - progress (number | null): Snippets read out of the Album's total. null if not enrolled
      or not logged in -- always null until auth/enrolment exist.
  Layout:
    Left: square icon portion (decorative emoji, looked up from album.icon).
    Right: album.title, album.description as subtitle, and a ProgressBar only when progress
      is not null.
  Styling:
    Card base, flex row, left square ~80px, right column flex-grow.
-->
<script lang="ts">
  import ProgressBar from '$lib/components/ProgressBar.svelte';
  import type { AlbumListResponse } from '$lib/api/types';

  export let album: AlbumListResponse;
  export let progress: number | null = null;

  const ICONS: Record<string, string> = {
    cloud: '☁️',
  };
  const DEFAULT_ICON = '📦';

  $: icon = ICONS[album.icon] ?? DEFAULT_ICON;
</script>

<a class="album-card" href={`/learn/${album.id}`}>
  <div class="icon">{icon}</div>
  <div class="info">
    <h3>{album.title}</h3>
    <p>{album.description}</p>
    {#if progress !== null}
      <ProgressBar pct={progress} />
    {/if}
  </div>
</a>

<style>
  .album-card {
    display: flex;
    gap: 1rem;
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 1rem;
    text-decoration: none;
    color: inherit;
  }

  .icon {
    flex-shrink: 0;
    width: 80px;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.5rem;
    background: #0d1117;
    border-radius: 6px;
  }

  .info {
    flex-grow: 1;
    min-width: 0;
  }

  .info h3 {
    margin: 0 0 0.25rem;
    color: #c9d1d9;
    font-size: 1rem;
  }

  .info p {
    margin: 0;
    color: #8b949e;
    font-size: 0.875rem;
    line-height: 1.5;
  }
</style>
```

Note: this drops the old made-up `Album` interface (`tagline`/`iconUrl`/
`snippetCount`) entirely in favor of the real `AlbumListResponse` type.
`ProgressBar.svelte`'s prop is `pct` (verified against its current source) — it's
still an unimplemented stub itself, but that doesn't matter here since `progress`
is always `null` in this slice, so the `{#if progress !== null}` branch never
actually renders it.

- [ ] **Step 4: Run the test to verify it still passes**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS.

- [ ] **Step 5: Verify it compiles**

Run (from `frontend/`): `npm run check`
Expected: 0 errors.

- [ ] **Step 6: Format and commit**

```bash
cd frontend
npx prettier --write src/lib/components/AlbumCard.svelte src/lib/shell.test.ts
git add src/lib/components/AlbumCard.svelte src/lib/shell.test.ts
git commit -m "fix: AlbumCard uses the real AlbumListResponse shape"
```

---

### Task 6: Fix `AlbumGrid`'s prop type

**Files:**
- Modify: `frontend/src/lib/components/AlbumGrid.svelte`
- Test: `frontend/src/lib/shell.test.ts`

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/lib/shell.test.ts`:

```ts
describe('AlbumGrid', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('$lib/components/AlbumGrid.svelte');
    expect(mod.default).toBeDefined();
  });
});
```

- [ ] **Step 2: Run it to verify it currently passes (sanity check)**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — baseline before the prop-type fix.

- [ ] **Step 3: Update `AlbumGrid.svelte`'s prop type**

Read the current file first (`frontend/src/lib/components/AlbumGrid.svelte`). It has
its own made-up local `Album` interface. Replace just the type-related parts —
change:

```svelte
<script lang="ts">
  /* Changes */
  import AlbumCard from './AlbumCard.svelte';
  // Album card data 
  interface Album {
    id: number;
    title: string;
    tagline: string;
    iconUrl: string;
    snippetCount: number;
  }
 // Album card data 
  export let albums: Album[];
</script>
```

to:

```svelte
<script lang="ts">
  import AlbumCard from './AlbumCard.svelte';
  import type { AlbumListResponse } from '$lib/api/types';

  export let albums: AlbumListResponse[];
</script>
```

Leave the rest of the file (the `{#if albums.length === 0}` block, the
`{#each albums as album}<AlbumCard {album} />{/each}` loop, and the `<style>`
block) exactly as they are — they don't reference the old `Album` interface's
specific fields directly, so they keep working unchanged once `AlbumCard` (fixed in
Task 5) accepts the real type.

- [ ] **Step 4: Run the test to verify it still passes**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS.

- [ ] **Step 5: Verify it compiles**

Run (from `frontend/`): `npm run check`
Expected: 0 errors.

- [ ] **Step 6: Format and commit**

```bash
cd frontend
npx prettier --write src/lib/components/AlbumGrid.svelte src/lib/shell.test.ts
git add src/lib/components/AlbumGrid.svelte src/lib/shell.test.ts
git commit -m "fix: AlbumGrid uses the real AlbumListResponse type"
```

---

### Task 7: Implement `SideHeader`

**Files:**
- Modify: `frontend/src/lib/components/SideHeader.svelte`
- Test: `frontend/src/lib/shell.test.ts`

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/lib/shell.test.ts`:

```ts
describe('SideHeader', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('$lib/components/SideHeader.svelte');
    expect(mod.default).toBeDefined();
  });
});
```

- [ ] **Step 2: Run it to verify it currently passes (sanity check)**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — baseline before the rewrite.

- [ ] **Step 3: Replace `SideHeader.svelte`'s contents**

```svelte
<!--
  SideHeader
  Purpose: Divider/header inside AlbumSidebar marking the start of a Side (chapter) and grouping
    its constituent Snippets underneath it.
  Used in: AlbumSidebar
  Props:
    - title (string): the Side's title
    - index (number): the Side's position within the Album (e.g. for "Side 1", "Side 2" labels)
  Styling:
    Small uppercase label (e.g. "SIDE {index}"), font-size 0.7rem, letter-spacing 0.08em,
    color #8b949e, followed by the title in a slightly larger weight, with a divider line below.
-->
<script lang="ts">
  export let title: string;
  export let index: number;
</script>

<div class="side-header">
  <span class="label">SIDE {index}</span>
  <h4>{title}</h4>
  <hr />
</div>

<style>
  .side-header {
    margin: 1rem 0 0.5rem;
  }

  .label {
    display: block;
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    color: #8b949e;
    text-transform: uppercase;
  }

  h4 {
    margin: 0.25rem 0 0.5rem;
    color: #c9d1d9;
    font-size: 0.95rem;
    font-weight: 600;
  }

  hr {
    border: none;
    border-top: 1px solid #21262d;
    margin: 0;
  }
</style>
```

- [ ] **Step 4: Run the test to verify it still passes**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS.

- [ ] **Step 5: Format and commit**

```bash
cd frontend
npx prettier --write src/lib/components/SideHeader.svelte src/lib/shell.test.ts
git add src/lib/components/SideHeader.svelte src/lib/shell.test.ts
git commit -m "feat: implement SideHeader"
```

---

### Task 8: Implement `AlbumSidebar`

**Files:**
- Modify: `frontend/src/lib/components/AlbumSidebar.svelte`
- Test: `frontend/src/lib/shell.test.ts`

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/lib/shell.test.ts`:

```ts
describe('AlbumSidebar', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('$lib/components/AlbumSidebar.svelte');
    expect(mod.default).toBeDefined();
  });
});
```

- [ ] **Step 2: Run it to verify it currently passes (sanity check)**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — baseline before the rewrite.

- [ ] **Step 3: Replace `AlbumSidebar.svelte`'s contents**

```svelte
<!--
  AlbumSidebar
  Purpose: Adapted version of NavSidebar shown within an Album view. Displays the Album's Sides
    (chapters) vertically, each with its constituent Snippets listed underneath via SideHeader.
  Used in: /learn/[id]
  Props:
    - sides (SideResponse[]): the Album's Sides, each with its Snippets
    - activeSnippetId (number | null): id of the Snippet currently being read, for highlighting.
      Always null for now -- there's no Snippet detail page yet, so nothing can be "active."
      Kept as a prop so a future chapter can wire it up without changing this component's
      interface.
  Layout:
    For each side: a SideHeader, followed by its snippets as a vertical list. Snippets render
    as plain text (not links) for now, since there's no Snippet detail page to navigate to yet.
  Styling:
    Same visual language as NavSidebar (background #0a2540, width 240px).
-->
<script lang="ts">
  import type { SideResponse } from '$lib/api/types';
  import SideHeader from '$lib/components/SideHeader.svelte';

  export let sides: SideResponse[];
  export let activeSnippetId: number | null;
</script>

<nav class="album-sidebar">
  {#each sides as side, index}
    <SideHeader title={side.title} index={index + 1} />
    <ul>
      {#each side.snippets as snippet}
        <li class:active={snippet.id === activeSnippetId}>{snippet.title}</li>
      {/each}
    </ul>
  {/each}
</nav>

<style>
  .album-sidebar {
    background: #0a2540;
    height: 100%;
    width: 240px;
    padding: 1rem 0.75rem;
    box-sizing: border-box;
  }

  ul {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  li {
    color: #c9d1d9;
    font-size: 0.875rem;
    padding: 0.4rem 0;
  }

  li.active {
    font-weight: bold;
    color: #ffffff;
  }
</style>
```

- [ ] **Step 4: Run the test to verify it still passes**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS.

- [ ] **Step 5: Verify it compiles**

Run (from `frontend/`): `npm run check`
Expected: 0 errors.

- [ ] **Step 6: Format and commit**

```bash
cd frontend
npx prettier --write src/lib/components/AlbumSidebar.svelte src/lib/shell.test.ts
git add src/lib/components/AlbumSidebar.svelte src/lib/shell.test.ts
git commit -m "feat: implement AlbumSidebar"
```

---

### Task 9: Build the `/learn` Album list page

**Files:**
- Modify: `frontend/src/routes/learn/+page.svelte`
- Test: `frontend/src/lib/shell.test.ts`

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/lib/shell.test.ts`:

```ts
describe('/learn page', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('../routes/learn/+page.svelte');
    expect(mod.default).toBeDefined();
  });
});
```

- [ ] **Step 2: Run it to verify it currently passes (sanity check)**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — the placeholder page already exports a default component; this is
the baseline before the rewrite.

- [ ] **Step 3: Replace `/learn/+page.svelte`'s contents**

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import AlbumGrid from '$lib/components/AlbumGrid.svelte';
  import { listAlbums } from '$lib/api/albums';
  import type { AlbumListResponse } from '$lib/api/types';

  let albums: AlbumListResponse[] = [];
  let loading = true;
  let error: string | null = null;

  onMount(async () => {
    try {
      albums = await listAlbums();
    } catch {
      error = 'Could not load Albums right now. Please try again later.';
    } finally {
      loading = false;
    }
  });
</script>

<main>
  <h1>Learn</h1>
  {#if loading}
    <p>Loading...</p>
  {:else if error}
    <p>{error}</p>
  {:else}
    <AlbumGrid {albums} />
  {/if}
</main>

<style>
  main {
    max-width: 900px;
    margin: 4rem auto;
    padding: 0 1.5rem;
  }
</style>
```

- [ ] **Step 4: Run the test to verify it still passes**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS.

- [ ] **Step 5: Verify it compiles**

Run (from `frontend/`): `npm run check`
Expected: 0 errors.

- [ ] **Step 6: Format and commit**

```bash
cd frontend
npx prettier --write src/routes/learn/+page.svelte src/lib/shell.test.ts
git add src/routes/learn/+page.svelte src/lib/shell.test.ts
git commit -m "feat: build /learn Album list page"
```

---

### Task 10: Build the `/learn/[id]` Album detail page

**Files:**
- Create: `frontend/src/routes/learn/[id]/+page.svelte`
- Test: `frontend/src/lib/shell.test.ts`

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/lib/shell.test.ts`:

```ts
describe('/learn/[id] page', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('../routes/learn/[id]/+page.svelte');
    expect(mod.default).toBeDefined();
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: FAIL — `frontend/src/routes/learn/[id]/+page.svelte` doesn't exist yet.

- [ ] **Step 3: Create `frontend/src/routes/learn/[id]/+page.svelte`**

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import AlbumSidebar from '$lib/components/AlbumSidebar.svelte';
  import { getAlbumDetail } from '$lib/api/albums';
  import type { AlbumDetailResponse } from '$lib/api/types';

  let album: AlbumDetailResponse | null = null;
  let loading = true;
  let error: string | null = null;

  onMount(async () => {
    const id = Number($page.params.id);
    try {
      album = await getAlbumDetail(id);
    } catch {
      error = 'Could not load this Album right now. Please try again later.';
    } finally {
      loading = false;
    }
  });
</script>

<div class="album-page">
  {#if loading}
    <main><p>Loading...</p></main>
  {:else if error || !album}
    <main><p>{error ?? 'Album not found.'}</p></main>
  {:else}
    <AlbumSidebar sides={album.sides} activeSnippetId={null} />
    <main>
      <h1>{album.title}</h1>
      <p>{album.description}</p>
    </main>
  {/if}
</div>

<style>
  .album-page {
    display: flex;
  }

  main {
    flex-grow: 1;
    max-width: 700px;
    margin: 4rem auto;
    padding: 0 1.5rem;
  }
</style>
```

`$app/stores`'s `page` store gives access to the dynamic route's `[id]` param via
`$page.params.id` — this is SvelteKit's standard way to read a route param in a
`+page.svelte` (as opposed to a `+page.ts` `load` function, which the design spec
left as an implementer's choice; this plan uses the in-component approach since
it's simpler to test with this project's current "exports a default" smoke-test
style and doesn't require a separate `+page.ts` file).

- [ ] **Step 4: Run the test again to verify it passes**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — all tests green.

- [ ] **Step 5: Verify it compiles**

Run (from `frontend/`): `npm run check`
Expected: 0 errors.

- [ ] **Step 6: Format and commit**

```bash
cd frontend
npx prettier --write src/routes/learn/[id]/+page.svelte src/lib/shell.test.ts
git add src/routes/learn/[id]/+page.svelte src/lib/shell.test.ts
git commit -m "feat: build /learn/[id] Album detail page"
```

---

### Task 11: Full local verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full frontend test suite**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: all tests PASS.

- [ ] **Step 2: Run lint**

Run (from `frontend/`): `npm run lint`
Expected: 0 errors (pre-existing warnings in unrelated stub files are fine — do not
fix unrelated files' formatting as part of this plan).

- [ ] **Step 3: Run the type checker**

Run (from `frontend/`): `npm run check`
Expected: 0 errors.

- [ ] **Step 4: Run the Histoire build**

Run (from `frontend/`): `npm run story:build`
Expected: all existing stories still build with no errors (this plan doesn't add
new `.story.svelte` files, but confirms nothing broke any existing one — e.g.
`AlbumCard`/`AlbumGrid`'s type changes could theoretically affect a story that
references them, though none currently do). Clean up afterward:
`rm -rf .histoire/dist`.

- [ ] **Step 5: Seed and manually verify against the running app**

From `backend/`: ensure Postgres is migrated to head and run `poetry run python
seed.py`. From `frontend/`: run `npm run dev`, open the reported local URL.

Verify:
- `/learn` shows one Album card: "Cloud Computing Fundamentals" with a ☁️ icon.
- Clicking it navigates to `/learn/<id>` and shows the title, description, and a
  left sidebar with two Sides ("Getting Started", "Networking Basics"), each
  listing its Snippet titles underneath.
- No console errors in the browser.
