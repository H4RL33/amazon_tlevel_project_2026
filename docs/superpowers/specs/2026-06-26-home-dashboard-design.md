# Home / Dashboard Merge — Design Spec

Date: 2026-06-26

## Context

The platform previously had a "Coming soon" stub at `/` and a separate `/dashboard` route (also a stub). During showcase planning the team decided to merge them: `/` becomes the single entry point for both guests and authenticated users. `/dashboard` is deleted entirely. This spec covers the full implementation of `/` and the supporting changes needed across the shell.

**Decisions already made (do not re-brainstorm):**
- Unauthenticated `/` → marketing hero + Album browsing
- Authenticated `/` → personalised CTASidebar + stats + forum feed
- `/dashboard` route deleted (not redirected)
- Data loading: reactive branch in `+page.svelte` with `onMount` (Approach A)
- AgentChat handoff: Svelte store → `/library` reads on mount

---

## File Map

| Action | Path |
|--------|------|
| Rewrite | `frontend/src/routes/+page.svelte` |
| Implement | `frontend/src/lib/components/CTASidebar.svelte` |
| Create | `frontend/src/lib/stores/agentDraft.ts` |
| Modify | `frontend/src/routes/+layout.svelte` |
| Modify | `frontend/src/lib/components/AgentChat.svelte` |
| Modify | `frontend/src/lib/components/Navbar.svelte` |
| Delete | `frontend/src/routes/dashboard/` |

---

## 1. Unauthenticated home (`+page.svelte` — guest branch)

`+page.svelte` opens with `{#if $currentUser}` / `{:else}` / `{/if}`. The guest branch renders three stacked elements inside the `.content` scroll area (no outer wrapper card):

### Hero (on gradient — no card)
A plain `<div class="hero">` with no background, sitting directly on the animated gradient backdrop:
- `<h1>` — "Discover your future with Amazon T-Levels"
- `<p>` — short subtitle (1–2 sentences)
- `<button>` CTA — "Get started", styled as a white `PageCard` surface (background `#fff`, `border-radius: 0`, `box-shadow: var(--shadow)`, dark text `#232f3e`, `font-weight: 700`). Calls `getCognitoLoginUrl()` on click — same function the Navbar "Log in" link uses.

### "Explore Albums" header card
`<PageCard>` with `padding="0.875rem 1.25rem"`:
- Left: `<h2>` "Explore Albums"
- Right: `<NavLink href="/learn" label="View all →" />`

### Album grid card
`<PageCard as="main">` with `padding="1.5rem"` containing `<AlbumGrid albums={albums} />`.

**Data:** `listAlbums()` called in `onMount`. Loading state: a brief "Loading..." text inside the grid card. Error state: "Could not load Albums right now. Please try again later." Matches the existing `/learn/+page.svelte` pattern.

### Morphing backdrop
When `$page.url.pathname === '/'` and `$currentUser` is `null`, `+layout.svelte` adds a `morphing` class to the active backdrop layer. This class applies `animation: morph-hue 20s linear infinite` with `@keyframes morph-hue { from { filter: hue-rotate(0deg); } to { filter: hue-rotate(360deg); } }` at the layer level, cycling the pastel blob colours continuously for visual interest. The existing `prefers-reduced-motion` rule covers this automatically (all animations disabled).

---

## 2. Authenticated home (`+page.svelte` — auth branch)

The auth branch renders a `<div class="home-page">` flex row (same `display: flex; gap: var(--gap-inner);` pattern as `/learn/[id]`):

```
<CTASidebar {user} {albums} {snippets} />
<div class="right-col">   ← no PageCard wrapper
  stats row
  forum header card
  forum masonry grid
</div>
```

**Data fetched in `onMount`:**
- `albums` — `listAlbums()` (public, same call as guest branch — reused)
- `feedPosts` — `apiFetch('/feed/')` wrapped in try/catch; on error `feedPosts = []`

`snippets` passed to `CTASidebar` is always `[]` for now — no recommendations endpoint exists yet. CTASidebar omits the Snippets section entirely when the array is empty, so this is graceful.

### Right column layout

No wrapper card. Three elements stacked with `gap: var(--gap-inner)`:

**Stats row** — `display: flex; gap: var(--gap-inner)`:
- *XP Earned* — stubs to `0`, subtext "Keep learning to earn XP" (XP backend not yet implemented; render as plain styled text — `XPBadge` is a pill label for SnippetCard, not a stat display)
- *Albums Enrolled* — `albums.length` (real data)
- *Snippets Read* — stubs to `0`, subtext "Complete Snippets to track progress" (progress API stub)

Each stat is a `<PageCard>` with `padding="0.875rem 1.25rem"`, a muted uppercase label, a large bold value, and a small subtext line.

**Forum header card** — `<PageCard padding="0.875rem 1.25rem">`:
- Left: `<h2>` "The Forum" + muted span "Hidden for under-14s · read-only for 14–16"
- Right: `<NavLink href="/forum" label="View all posts →" />`

Age gating is enforced server-side. The client renders whatever the feed API returns; if the user is ineligible the API returns no posts (or will once implemented).

**Forum masonry grid** — CSS `columns: 3; column-gap: var(--gap-inner)`:
- Each post rendered as `<PostCard>` with `break-inside: avoid; margin-bottom: var(--gap-inner)`
- If `feedPosts.length === 0` (API stub or genuinely empty): render a single muted paragraph "No posts yet — check back soon." inside a `<PageCard>` instead of the grid

---

## 3. CTASidebar implementation

The existing stub (`PageCard as="aside" width="320px" padding="1.5rem"`) gets its content filled in. Props are unchanged: `user: UserResponse`, `albums: AlbumListResponse[]`, `snippets: ContentListResponse[]`.

**Layout (top to bottom, `display: flex; flex-direction: column; gap: var(--gap-inner)`):**

1. **Greeting** — derives time-of-day from `new Date().getHours()`: `< 12` → "morning", `< 18` → "afternoon", else "evening". Renders `"Good {greeting}, {user.first_name} 👋"` as a bold `<p>`.

2. **Albums section**
   - Section label: small uppercase "Your Albums" in muted text
   - `albums.slice(0, 2)` in `display: flex; flex-direction: row; gap: var(--gap-inner)` — each rendered as `<AlbumCard album={...} />` (the existing square icon tile component; it scales to fill the flex track)
   - Empty state (no enrolled albums): muted paragraph "Browse Albums to get started" with a `<NavLink href="/learn" label="Browse Albums" />`

3. **Snippets section**
   - Section label: small uppercase "Recommended Snippets" in muted text
   - `snippets.slice(0, 3)` as `<SnippetCard content={...} />` stacked vertically (`display: flex; flex-direction: column; gap: calc(var(--gap-inner) * 0.5)`)
   - If `snippets` is empty: section omitted entirely (no empty state needed — sidebar doesn't feel broken without it)

4. **Flex spacer** — `<div style="flex: 1" />` pushes AgentChat to the bottom

5. **AgentChat** — `<AgentChat>` component at the bottom. On the `submit` event: import `agentDraft` store, call `agentDraft.set(message)`, then `goto('/library')`.

---

## 4. AgentChat store

**`frontend/src/lib/stores/agentDraft.ts`** (new file):
```ts
import { writable } from 'svelte/store';
export const agentDraft = writable<string | null>(null);
```

`CTASidebar` sets it on AgentChat submit. `AgentChatWindow.svelte` gains an `initialDraft: string = ''` prop; its internal `let draft` is initialised from it (`let draft = initialDraft`). `/library/+page.svelte` reads `$agentDraft` on `onMount`, passes it as `initialDraft` to `AgentChatWindow`, then calls `agentDraft.set(null)` to clear the store. The store is ephemeral — not persisted to `localStorage`.

---

## 5. Palette accent wiring (`+layout.svelte` + `AgentChat.svelte`)

**`+layout.svelte`:** Add an inline `style` attribute to `.shell` exposing the active palette as CSS custom properties:
```svelte
<div class="shell" style="--page-p0: {layers[activeIndex].palette[0]}; --page-p1: {layers[activeIndex].palette[1]};">
```

**`AgentChat.svelte`:** Change the `border-image` CSS declaration to:
```css
border-image: linear-gradient(to right, var(--page-p0, #ff9900), var(--page-p1, #ffd700)) 1;
```
The fallback values (`#ff9900`, `#ffd700`) preserve the existing orange-yellow on any page where the variables aren't set.

---

## 6. `/dashboard` deletion + Navbar cleanup

**Delete** `frontend/src/routes/dashboard/` with `git rm -r`.

**`Navbar.svelte`:** Remove the line:
```svelte
<NavLink href={$currentUser ? '/dashboard' : '/login'} label="Dashboard" />
```
The Home NavLink (`href="/"`) already serves as the dashboard entry point for authenticated users.

---

## Data flow summary

```
+page.svelte onMount
  ├── listAlbums()          → albums (used by both branches)
  └── apiFetch('/feed/')    → feedPosts (auth branch only, try/catch)

CTASidebar (props, no internal fetching)
  ├── albums.slice(0, 2)   → AlbumCard × 2
  ├── snippets.slice(0, 3) → SnippetCard × 3
  └── AgentChat submit     → agentDraft store → goto('/library')

Right col
  ├── albums.length        → Albums Enrolled stat
  ├── 0 (stub)             → XP Earned stat
  ├── 0 (stub)             → Snippets Read stat
  └── feedPosts            → PostCard masonry grid (or empty state)
```

---

## Testing

- **Vitest:** No new unit tests beyond the existing smoke tests (no new pure logic to unit-test — `getPagePalette` is already tested, `agentDraft` is a trivial writable)
- **`svelte-check`:** Run after every file change; 0 errors required before commit
- **Manual browser verification:**
  - Guest view: hero on gradient, "Get started" white card button, Albums grid loads
  - Morphing backdrop: pastel colours cycle continuously on unauth home; stop on other pages
  - Auth view: greeting updates by time of day, 2 AlbumCards side by side, 3 Snippets stacked, AgentChat accent matches page gradient, stats render (0s acceptable), forum shows empty state (API stub)
  - AgentChat submit: navigates to `/library`, message pre-filled
  - `/dashboard` → 404 (route deleted)
  - Navbar: no Dashboard link visible

---

## Known gaps (out of scope, not blocking)

- `snippets` passed to CTASidebar stubs to `[]` — a recommendations endpoint doesn't exist yet; the empty state handles this gracefully
- XP and Snippets Read stats stub to `0` — XP backend (gamification) and progress API are not yet implemented
- Forum feed stubs to empty state — `getFeed()` throws; empty state shown
- Age-tier enforcement client-side — `UserResponse` does not include DOB or age tier; full client-side gating deferred until that field is added. Server-side enforcement is the primary control.
