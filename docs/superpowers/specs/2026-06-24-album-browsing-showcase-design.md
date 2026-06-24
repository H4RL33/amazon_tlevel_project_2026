# Album Browsing Showcase — design spec

Date: 2026-06-24

## Context

A showcase with the team's AWS mentor is happening soon, and the goal is a genuine
clickable demo, not just visual polish on already-finished pages. Investigation
found that **Album browsing is the only flow that can work end-to-end today** — the
backend's `album_service` (built in the Album/Side chapter) queries `Content`
directly via SQLAlchemy joins and doesn't depend on any of the still-stubbed
services (`content_service`, `topic_service`, `feed_service`, `user_service`,
`auth_service`). Everything else in the app is blocked on those stubs or on real
auth, neither of which exists yet.

This is **not** the full "Public Browsing — Topics & Learn" frontend masterplan
chapter (see [`2026-06-24-frontend-masterplan.md`](2026-06-24-frontend-masterplan.md))
— it's a tightly-scoped slice of it, sized for a one-evening sprint: enough to
browse a real, seeded Album end-to-end. Topics index/detail pages, standalone
Snippet browsing/detail pages, `EnrolButton`, and `AlbumProgressWidget` (which needs
auth) are explicitly out of scope here and remain for the full chapter later.

Three things currently block this, found during investigation:

1. **`frontend/src/lib/api/client.ts`'s `apiFetch` is a stub** — `throw new
   Error('not implemented')`. Nothing in the frontend can call the backend at all
   today, regardless of which page.
2. **`AlbumCard`/`AlbumGrid` use a made-up `Album` shape** (`tagline`, `iconUrl`,
   `snippetCount`) that doesn't match the real backend `AlbumListResponse`
   (`id`, `t_level_id`, `title`, `description`, `icon`).
3. **No seed data exists for `Content`, `Album`, `Side`, or `SideContent`** —
   `backend/seed.py` only seeds `Topic`/`TLevel` rows. There is nothing to browse
   even once the above two are fixed.

## Architecture

**Backend:** Extend `backend/seed.py` (not a new script — keep the existing
single-entrypoint, idempotent pattern) to also seed a handful of `Content` rows and
one `Album` with two `Side`s, each containing some of those `Content` rows via
`SideContent`. No backend route/service changes — the existing `/albums/` and
`/albums/{id}` endpoints already serve this correctly (confirmed during the
Album/Side chapter's testing).

**Frontend:** Implement `apiFetch` for real (plain `fetch` wrapper using
`import.meta.env.VITE_API_BASE_URL`, matching the env var already wired through
`docker-compose.yml`'s build args — not SvelteKit's `$env/static/public`, since
that's for `PUBLIC_`-prefixed vars and this project already standardised on the
`VITE_` prefix). Add `frontend/src/lib/api/albums.ts` following the exact pattern of
the existing `topics.ts`/`content.ts` files. Add the missing Album/Side response
types to `frontend/src/lib/api/types.ts`, matching the backend's Pydantic schemas
exactly (`AlbumListResponse`, `SnippetSummaryResponse`, `SideResponse`,
`AlbumDetailResponse`). Fix `AlbumCard.svelte` and `AlbumGrid.svelte` to use the real
`AlbumListResponse` shape instead of their invented one. Implement `AlbumSidebar`
and `SideHeader` (currently stubs). Build two new pages: `/learn` (Album list, using
`AlbumGrid`) and `/learn/[id]` (Album detail, using `AlbumSidebar` to show Sides and
Snippets).

## Component-level decisions

**`AlbumCard`'s `icon` field:** the backend stores `icon` as a plain string
identifier (e.g. `"cloud"`), not a URL — per CLAUDE.md's component reference table,
it's "Icon identifier for AlbumCard." For this slice, render it as a decorative
emoji via a small lookup map with a sensible default fallback (e.g. 📦) rather than
building a real icon system — that's a future visual-polish task, not blocking for
a demo.

**Progress indicator:** `AlbumCard` currently takes a `progress: number | null`
prop. Since there's no auth yet, every Album is effectively "not enrolled" — pass
`null` always from the list page. Don't remove the prop (a future chapter wires
real progress through once auth/enrolment exist), just don't try to populate it now.

**Snippet links in `AlbumSidebar`:** per its existing doc comment, each Side lists
its Snippets as a vertical list of links, with `activeSnippetId` highlighting the
current one. Since there's no Snippet detail page yet (that's `content_service`'s
job, still a backend stub), these links render as plain text (not real `<a href>`
navigation) for this slice — clicking a Snippet name does nothing yet. Keep the
`activeSnippetId` prop in the component's contract (always pass `null` for now) so
a future chapter can wire it up without changing the component's interface.

**Routing:** `/learn` becomes the Album list page (replacing today's "Coming soon"
placeholder). `/learn/[id]` is a new dynamic route for Album detail. No nested
Side/Snippet sub-routes in this slice — the whole Album (all Sides, all Snippet
titles) renders on one page.

## Data flow

1. `/learn` calls `listAlbums()` (no filters) on mount, renders `AlbumGrid`.
2. Clicking an `AlbumCard` navigates to `/learn/[id]`.
3. `/learn/[id]` calls `getAlbumDetail(id)` on mount (or via SvelteKit's `load`
   function — implementer's choice, consistent with how other dynamic routes in
   this codebase are expected to work once built), renders the Album's
   title/description plus `AlbumSidebar` with its Sides/Snippets.
4. No enrolment, no progress, no authenticated behaviour anywhere in this slice —
   the `GET /albums/{id}` endpoint's anonymous path (already built and tested)
   is exactly what gets exercised.

## Testing

Per the project's established testing philosophy (see prior chapters), this stays
at the "module compiles and exports a default" smoke-test level for new Svelte
components/pages, consistent with `frontend/src/lib/shell.test.ts`'s existing
pattern — no DOM-rendering test layer. `apiFetch` and the new `albums.ts` functions
get real unit tests (they're plain TypeScript, not Svelte components, and
correctness there matters more than for static markup) using Vitest's `fetch`
mocking (`vi.stubGlobal('fetch', ...)` or equivalent). Backend seed data changes are
verified by running `poetry run python seed.py` against a local Postgres and
confirming the new rows exist (no new pytest tests needed — `seed.py` isn't covered
by the existing pytest suite, consistent with how the `Topic`/`TLevel` seeding isn't
tested either).

## Out of scope (deferred to the full Public Browsing chapter or later)

- Topics index/detail pages (`/topics`, `/topics/[slug]`).
- Standalone Snippet browsing/search and Snippet detail pages.
- `EnrolButton`, `AlbumProgressWidget` — both need real auth/enrolment.
- Making `AlbumSidebar`'s Snippet links real navigation — needs a Snippet detail
  page, which needs `content_service` implemented (backend chapter, not yet done).
- `NavSidebar` (already narrowed in the Shell & Layout chapter) being wired into
  `/topics`/`/learn` — this slice's `/learn` pages don't need topic-list section
  nav since they're not browsing by Topic, just listing/viewing Albums directly.
- Any other `lib/api/*.ts` file's `apiFetch` calls becoming real — `topics.ts` and
  `content.ts` still call the now-real `apiFetch`, but their underlying backend
  endpoints (`topic_service`, `content_service`) are still stubs, so those calls
  will fail until those backend chapters land. That's fine — nothing in this slice
  calls them.
