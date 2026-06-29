# Topics → T-Levels Refactor Design

Date: 2026-06-29

## Context

The existing `/topics` route is a "Coming soon" stub. The `NavSidebar` component is
partially wired (accepts `topics` and `activePath` but hardcodes links to `/topics/[slug]`).
The `/learn` route is also a stub. The backend `topic_service` is entirely
`NotImplementedError` stubs, and `topics.py` has a router-level auth dependency that
incorrectly blocks anonymous access.

This spec replaces the Topics module with a two-surface T-levels experience and
implements the `/learn` page simultaneously, since both surfaces share the same
NavSidebar + scroll-to-section pattern and draw from the same data chain
(`Topic → TLevel → Album`).

---

## Routes

| Before | After | Purpose |
|--------|-------|---------|
| `/topics` (stub) | `/t-levels` | Topic index — 2×2 Topic cards |
| `/topics/[slug]` (none) | `/t-levels/[slug]` | Topic detail — Albums grouped by T-level |
| `/learn` (stub) | `/learn` | Albums grouped by Topic |

The SvelteKit route directory `frontend/src/routes/topics/` is deleted entirely.
`frontend/src/routes/t-levels/` is created with `+page.svelte` and `[slug]/+page.svelte`.

### Navbar

The "Topics" `NavLink` is renamed to "T-Levels" and its `href` changes to `/t-levels`.

---

## Backend

### 1. Fix `topics.py` router auth

Remove `dependencies=[Depends(get_current_user)]` from the `APIRouter(...)` call in
`backend/app/routers/topics.py`. Topics, T-Levels, and Albums are publicly accessible
without login per CLAUDE.md. Real Cognito auth is now active so this actively returns
401 for anonymous requests.

### 2. Extend `AlbumListResponse` with `topic_id`

Add `topic_id: int` to `AlbumListResponse` in `backend/app/schemas/album.py`. The
`album_service.list_albums` query must eager-load the `Album.t_level` relationship so
`album.t_level.topic_id` is available without an extra query. This lets the `/learn`
frontend group albums by topic client-side without a new endpoint.

### 3. New schema: `TLevelWithAlbumsResponse`

Add to `backend/app/schemas/topic.py`:

```python
class TLevelWithAlbumsResponse(TLevelResponse):
    albums: list[AlbumListResponse]
```

Update `TopicDetailResponse` to use `TLevelWithAlbumsResponse` instead of
`TLevelResponse`:

```python
class TopicDetailResponse(TopicResponse):
    t_levels: list[TLevelWithAlbumsResponse]
```

### 4. Implement `topic_service` stubs

**`list_topics(db)`**
`SELECT * FROM topics ORDER BY name`. Returns `list[TopicResponse]`.

**`get_topic_by_slug(db, slug)`**
Select the `Topic` where `slug` matches, eager-loading its `t_levels` and each t_level's
`albums`. Raise HTTP 404 if not found. Returns `TopicDetailResponse` (with
`TLevelWithAlbumsResponse` per t_level). Albums within each t_level are ordered by
`album.id` (creation order).

**`get_t_level(db, topic_slug, t_level_id)`**
Select the `TLevel` by `id`, join to its `Topic` and assert `topic.slug == topic_slug`.
Raise HTTP 404 if not found or slug mismatched. Returns `TLevelResponse`.

---

## Frontend

### 1. `NavSidebar.svelte` — generic links prop

Replace the current `topics: TopicResponse[]` + `activePath: string` props with:

```ts
export let links: { label: string; href: string }[];
export let activeHref: string = '';
```

Each link renders as an `<a>` tag. `activeHref` is set by the parent page via an
`IntersectionObserver` (see section layout below) and passed down as a plain prop —
no two-way binding. A link is active when `link.href === activeHref`. This also fixes
the known prefix-collision bug (previously `activePath.startsWith('/topics/digital')`
would incorrectly match `/topics/digital-something`).

Styling: keep the existing left-border active treatment. The active class is toggled by
comparing `link.href === activeHref` rather than computed from URL.

### 2. `AlbumCard.svelte` — optional override props

Add two optional props:

```ts
export let href: string | undefined = undefined;
export let label: string | undefined = undefined;
```

When `href` is set it overrides the album-derived link (`/learn/${album.id}`). When
`label` is set it overrides `album.title` in the `<h3>`. The `album` prop becomes
`AlbumListResponse | undefined = undefined`. The icon slot falls back to a generic
placeholder SVG when no `album` is provided (or when `album.icon` has no match in
`ICON_PATHS`; the default path already handles this).

The component remains a single file. No new component is created for topic cards.

### 3. Shared scroll-section layout pattern

Both `/learn` and `/t-levels/[slug]` use the same layout:

```svelte
<script>
  let activeHref = '';
  // IntersectionObserver set up in onMount, updates activeHref when sections scroll into view
</script>

<div class="page-layout">
  <NavSidebar {links} {activeHref} />
  <div class="sections">
    {#each sections as section}
      <section id={section.id}>
        <h2>{section.heading}</h2>
        <AlbumGrid albums={section.albums} />
      </section>
    {/each}
  </div>
</div>
```

The page creates an `IntersectionObserver` in `onMount` that watches each `<section>`
element. When a section's top edge crosses the viewport threshold, `activeHref` is set
to `'#' + section.id`. The observer is disconnected on component destroy. `NavSidebar`
receives `activeHref` as a plain prop and applies the active class to the link whose
`href` matches.

Sections with zero albums are omitted from both the sidebar and the main content.

### 4. `/learn/+page.svelte`

On mount, fetches `GET /topics/` and `GET /albums/` in parallel. Groups albums by
`topic_id` client-side. Builds `sections` array in topic-name order (matching the order
returned by `list_topics`). Passes topic slugs as anchor ids (`id="digital"`). Sidebar
links: `{ label: topic.name, href: '#' + topic.slug }`.

### 5. `/t-levels/+page.svelte`

On mount, fetches `GET /topics/`. Renders a 2×2 grid of `AlbumCard` in topic mode:

```svelte
<AlbumCard label={topic.name} href="/t-levels/{topic.slug}" />
```

No NavSidebar on this page — it is a simple index, not a scroll-to-section layout.

### 6. `/t-levels/[slug]/+page.svelte`

On mount, fetches `GET /topics/{slug}`. If the response is 404, redirects to `/t-levels`.
Builds `sections` from `topic.t_levels` (each with its `albums`). Anchor ids are
`id="t-level-{t_level.id}"`. Sidebar links: `{ label: t_level.name, href: '#t-level-' + t_level.id }`.

### 7. Delete `frontend/src/routes/topics/`

The `+page.svelte` stub is deleted. The directory is removed.

---

## API types (`frontend/src/lib/api/types.ts`)

Add `topic_id: number` to `AlbumListResponse`.

Add:

```ts
export interface TLevelWithAlbumsResponse {
  id: number;
  topic_id: number;
  name: string;
  entry_requirements: string;
  how_to_apply: string;
  albums: AlbumListResponse[];
}

export interface TopicDetailResponse extends TopicResponse {
  t_levels: TLevelWithAlbumsResponse[];
}
```

Add a new API call in `frontend/src/lib/api/topics.ts`:

```ts
export async function getTopic(slug: string): Promise<TopicDetailResponse>
export async function listTopics(): Promise<TopicResponse[]>
```

---

## Out of scope

- `/t-levels/[slug]/[t_level_id]` T-level detail page — not requested.
- `entry_requirements` and `how_to_apply` T-level fields are fetched but not rendered
  in this spec. They are available for a future T-level detail page.
- `accent_colour` from `TopicResponse` is available but not used for section styling in
  this spec. Can be wired to section heading colour in a future polish pass.
- Mobile/responsive layout for the NavSidebar + sections pattern.
- Tests — backend service tests follow the existing `conftest.py` fixture pattern and
  are included in the implementation plan as a task per service function.
