# Home / Dashboard Merge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the "Coming soon" stubs at `/` and `/dashboard` with a real unauthenticated marketing/browsing page and a real authenticated personalised home (CTASidebar + stats + forum feed), deleting `/dashboard` entirely.

**Architecture:** A single `+page.svelte` branches on `$currentUser` — guest branch renders a hero + album grid, auth branch renders `CTASidebar` alongside a stats row and forum feed. `CTASidebar` is implemented as a pure presentational component (all data passed as props). A new `agentDraft` Svelte store carries a typed message from the AgentChat teaser to `/library`. Two small shell changes: the layout exposes the active palette as CSS custom properties on `.shell`, and the `AgentChat` border-image consumes them.

**Tech Stack:** SvelteKit 2 / Svelte 4, TypeScript, `svelte-check`, Vitest.

**Spec:** `docs/superpowers/specs/2026-06-26-home-dashboard-design.md`

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `frontend/src/lib/stores/agentDraft.ts` | Ephemeral store carrying AgentChat draft to `/library` |
| Create | `frontend/src/lib/stores/agentDraft.test.ts` | Smoke + behaviour tests for the store |
| Modify | `frontend/src/lib/components/AgentChatWindow.svelte` | Add `initialDraft` prop |
| Modify | `frontend/src/lib/components/AgentChat.svelte` | Palette-aware border accent |
| Modify | `frontend/src/routes/+layout.svelte` | Expose `--page-p0`/`--page-p1` CSS vars; morphing class for unauth home |
| Modify | `frontend/src/lib/components/AlbumCard.svelte` | Add optional `size` prop for CTASidebar use |
| Modify | `frontend/src/lib/components/CTASidebar.svelte` | Full implementation |
| Modify | `frontend/src/lib/components/Navbar.svelte` | Remove Dashboard NavLink |
| Delete | `frontend/src/routes/dashboard/+page.svelte` | Route no longer needed |
| Rewrite | `frontend/src/routes/+page.svelte` | Guest + auth home branches |

---

### Task 1: Create `agentDraft` store

**Files:**
- Create: `frontend/src/lib/stores/agentDraft.ts`
- Create: `frontend/src/lib/stores/agentDraft.test.ts`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/lib/stores/agentDraft.test.ts`:

```ts
import { describe, it, expect, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { agentDraft } from './agentDraft';

describe('agentDraft', () => {
  beforeEach(() => agentDraft.set(null));

  it('initialises to null', () => {
    expect(get(agentDraft)).toBeNull();
  });

  it('stores a draft message', () => {
    agentDraft.set('What is cloud computing?');
    expect(get(agentDraft)).toBe('What is cloud computing?');
  });

  it('clears back to null', () => {
    agentDraft.set('hello');
    agentDraft.set(null);
    expect(get(agentDraft)).toBeNull();
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd frontend && npx vitest run src/lib/stores/agentDraft.test.ts
```

Expected: FAIL — `agentDraft` module not found.

- [ ] **Step 3: Create the store**

Create `frontend/src/lib/stores/agentDraft.ts`:

```ts
import { writable } from 'svelte/store';

export const agentDraft = writable<string | null>(null);
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd frontend && npx vitest run src/lib/stores/agentDraft.test.ts
```

Expected: PASS — all 3 tests green.

- [ ] **Step 5: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/stores/agentDraft.ts frontend/src/lib/stores/agentDraft.test.ts
git commit -m "feat: add agentDraft store for AgentChat → /library handoff"
```

---

### Task 2: Add `initialDraft` prop to `AgentChatWindow`

**Files:**
- Modify: `frontend/src/lib/components/AgentChatWindow.svelte`

`AgentChatWindow` currently initialises its `draft` variable to `''`. Adding an `initialDraft` prop lets `/library` pre-fill it from the `agentDraft` store.

- [ ] **Step 1: Update the script block**

In `frontend/src/lib/components/AgentChatWindow.svelte`, replace:

```ts
  export let messages: ChatMessage[];
  export let onSend: (text: string) => void;

  let draft = '';
```

With:

```ts
  export let messages: ChatMessage[];
  export let onSend: (text: string) => void;
  export let initialDraft: string = '';

  let draft = initialDraft;
```

- [ ] **Step 2: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: Run the full test suite to confirm nothing broke**

```bash
cd frontend && npx vitest run
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/components/AgentChatWindow.svelte
git commit -m "feat: add initialDraft prop to AgentChatWindow"
```

---

### Task 3: Update `AgentChat` accent border to use palette CSS variables

**Files:**
- Modify: `frontend/src/lib/components/AgentChat.svelte`

The layout will expose `--page-p0` and `--page-p1` CSS custom properties on `.shell` (Task 4). This task makes `AgentChat` consume them, falling back to the existing orange-yellow if they aren't set.

- [ ] **Step 1: Update the border-image declaration**

In `frontend/src/lib/components/AgentChat.svelte`, in the `<style>` block, find:

```css
		border-image: linear-gradient(to right, #ff9900, #ffd700) 1;
```

Replace with:

```css
		border-image: linear-gradient(to right, var(--page-p0, #ff9900), var(--page-p1, #ffd700)) 1;
```

- [ ] **Step 2: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/components/AgentChat.svelte
git commit -m "feat: AgentChat accent border inherits page palette CSS variables"
```

---

### Task 4: Update `+layout.svelte` — palette CSS vars and morphing backdrop

**Files:**
- Modify: `frontend/src/routes/+layout.svelte`

Two additions:
1. Expose the active palette's first two colours as `--page-p0` / `--page-p1` on `.shell` so child components (AgentChat) can consume them.
2. Add a `morphing` class to the active backdrop layer when on the unauthenticated home page, which applies a continuous `hue-rotate` animation for visual interest.

- [ ] **Step 1: Add the `morphingBackdrop` reactive variable**

In `frontend/src/routes/+layout.svelte`, in the `<script>` block, add this line after the existing reactive block (after the closing `}`):

```svelte
  $: morphingBackdrop = $page.url.pathname === '/' && !$currentUser;
```

The full script block should now end with:

```svelte
  $: {
    const next = getPagePalette($page.url.pathname);
    if (next.join('|') !== layers[activeIndex].palette.join('|')) {
      const inactiveIndex = activeIndex === 0 ? 1 : 0;
      layers[inactiveIndex] = { palette: next, visible: true };
      layers[activeIndex] = { ...layers[activeIndex], visible: false };
      activeIndex = inactiveIndex;
      layers = layers;
    }
  }

  $: morphingBackdrop = $page.url.pathname === '/' && !$currentUser;
</script>
```

- [ ] **Step 2: Add `class:morphing` to the layer div**

Find:

```svelte
    <div class="layer" class:visible={layer.visible}>
```

Replace with:

```svelte
    <div class="layer" class:visible={layer.visible} class:morphing={morphingBackdrop && i === activeIndex}>
```

- [ ] **Step 3: Expose palette CSS vars on `.shell`**

Find:

```svelte
<div class="shell">
```

Replace with:

```svelte
<div class="shell" style="--page-p0: {layers[activeIndex].palette[0]}; --page-p1: {layers[activeIndex].palette[1]};">
```

- [ ] **Step 4: Add `.layer.morphing` CSS**

In the `<style>` block, add after the existing `.layer.visible` rule:

```css
  .layer.morphing {
    animation: morph-hue 20s linear infinite;
  }

  @keyframes morph-hue {
    from {
      filter: hue-rotate(0deg);
    }
    to {
      filter: hue-rotate(360deg);
    }
  }
```

- [ ] **Step 5: Extend the `prefers-reduced-motion` block**

Find the existing reduced-motion block:

```css
  @media (prefers-reduced-motion: reduce) {
    .blob {
      animation: none;
    }

    .layer {
      transition: none;
    }
  }
```

Replace with:

```css
  @media (prefers-reduced-motion: reduce) {
    .blob {
      animation: none;
    }

    .layer {
      transition: none;
    }

    .layer.morphing {
      animation: none;
    }
  }
```

- [ ] **Step 6: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 7: Run the full test suite**

```bash
cd frontend && npx vitest run
```

Expected: all tests PASS.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/routes/+layout.svelte
git commit -m "feat: expose page palette as CSS vars; add morphing backdrop for unauth home"
```

---

### Task 5: Add `size` prop to `AlbumCard`

**Files:**
- Modify: `frontend/src/lib/components/AlbumCard.svelte`

`AlbumCard` currently has a fixed `width: 190px; height: 190px`. Inside `CTASidebar` two cards must sit side-by-side in a 320px container. Adding an optional `size` prop (applied as an inline style, which overrides the CSS class) lets callers override the dimensions without touching the default.

- [ ] **Step 1: Add the `size` prop and apply it inline**

In `frontend/src/lib/components/AlbumCard.svelte`, replace:

```svelte
<script lang="ts">
  import type { AlbumListResponse } from '$lib/api/types';

  export let album: AlbumListResponse;
```

With:

```svelte
<script lang="ts">
  import type { AlbumListResponse } from '$lib/api/types';

  export let album: AlbumListResponse;
  export let size: string | undefined = undefined;
```

Then find:

```svelte
<a class="album-card" href={`/learn/${album.id}`}>
```

Replace with:

```svelte
<a class="album-card" href={`/learn/${album.id}`} style={size ? `width: ${size}; height: ${size};` : undefined}>
```

- [ ] **Step 2: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: Run the full test suite**

```bash
cd frontend && npx vitest run
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/components/AlbumCard.svelte
git commit -m "feat: add optional size prop to AlbumCard for CTASidebar use"
```

---

### Task 6: Implement `CTASidebar`

**Files:**
- Modify: `frontend/src/lib/components/CTASidebar.svelte`

Replace the stub with a full implementation. Props are unchanged (`user`, `albums`, `snippets`). The component is purely presentational — all data comes from props, no internal fetching.

- [ ] **Step 1: Replace the full file contents**

Write `frontend/src/lib/components/CTASidebar.svelte`:

```svelte
<!--
  CTASidebar
  Purpose: Wide left sidebar on the home page for authenticated users. Personalised greeting,
    up to 2 enrolled AlbumCards, up to 3 recommended SnippetCards, and an AgentChat teaser
    pinned to the bottom. Navigates to /library on AgentChat submit, carrying the typed message
    via the agentDraft store.
  Used in: / (authenticated branch)
  Props:
    - user (UserResponse): current user — provides first_name for the greeting
    - albums (AlbumListResponse[]): all albums; first 2 shown. Empty state shown if empty.
    - snippets (ContentListResponse[]): recommended snippets; first 3 shown. Section omitted if empty.
-->
<script lang="ts">
  import { goto } from '$app/navigation';
  import type { AlbumListResponse, ContentListResponse, UserResponse } from '$lib/api/types';
  import { agentDraft } from '$lib/stores/agentDraft';
  import AgentChat from '$lib/components/AgentChat.svelte';
  import AlbumCard from '$lib/components/AlbumCard.svelte';
  import NavLink from '$lib/components/NavLink.svelte';
  import PageCard from '$lib/components/PageCard.svelte';
  import SnippetCard from '$lib/components/SnippetCard.svelte';

  export let user: UserResponse;
  export let albums: AlbumListResponse[];
  export let snippets: ContentListResponse[];

  $: hour = new Date().getHours();
  $: timeOfDay = hour < 12 ? 'morning' : hour < 18 ? 'afternoon' : 'evening';
  $: displayedAlbums = albums.slice(0, 2);
  $: displayedSnippets = snippets.slice(0, 3);

  function handleAgentSubmit(event: CustomEvent<string>) {
    agentDraft.set(event.detail);
    goto('/library');
  }
</script>

<PageCard as="aside" width="320px" padding="1.5rem" overflowY="visible">
  <div class="sidebar-inner">

    <p class="greeting">Good {timeOfDay}, {user.first_name} 👋</p>

    <div class="section">
      <span class="section-label">Your Albums</span>
      {#if displayedAlbums.length > 0}
        <div class="album-row">
          {#each displayedAlbums as album}
            <div class="album-slot">
              <AlbumCard {album} size="100%" />
            </div>
          {/each}
        </div>
      {:else}
        <p class="empty-text">Browse Albums to get started</p>
        <NavLink href="/learn" label="Browse Albums" />
      {/if}
    </div>

    {#if displayedSnippets.length > 0}
      <div class="section">
        <span class="section-label">Recommended Snippets</span>
        <div class="snippet-list">
          {#each displayedSnippets as snippet}
            <SnippetCard content={snippet} />
          {/each}
        </div>
      </div>
    {/if}

    <div class="spacer"></div>

    <AgentChat on:submit={handleAgentSubmit} />

  </div>
</PageCard>

<style>
  .sidebar-inner {
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
    height: 100%;
  }

  .greeting {
    font-size: 1rem;
    font-weight: 700;
    color: #232f3e;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #5a6472;
  }

  /* Two AlbumCards side by side, each a square filling its flex slot */
  .album-row {
    display: flex;
    flex-direction: row;
    gap: var(--gap-inner);
  }

  .album-slot {
    flex: 1;
    min-width: 0;
    aspect-ratio: 1;
  }

  .snippet-list {
    display: flex;
    flex-direction: column;
    gap: calc(var(--gap-inner) * 0.5);
  }

  .empty-text {
    font-size: 0.875rem;
    color: #5a6472;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  /* Pushes AgentChat to the bottom of the sidebar */
  .spacer {
    flex: 1;
  }
</style>
```

- [ ] **Step 2: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors. (`snippets` prop may show an "unused export property" warning — this is pre-existing on stubs and is not an error.)

- [ ] **Step 3: Run the full test suite**

```bash
cd frontend && npx vitest run
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/components/CTASidebar.svelte
git commit -m "feat: implement CTASidebar — greeting, AlbumCards, SnippetCards, AgentChat"
```

---

### Task 7: Remove Dashboard NavLink from Navbar

**Files:**
- Modify: `frontend/src/lib/components/Navbar.svelte`

The Dashboard route is being deleted. The Home NavLink (`href="/"`) already serves authenticated users.

- [ ] **Step 1: Remove the Dashboard NavLink line**

In `frontend/src/lib/components/Navbar.svelte`, find and remove this line:

```svelte
      <NavLink href={$currentUser ? '/dashboard' : '/login'} label="Dashboard" />
```

The `<div class="links">` block should now read:

```svelte
    <div class="links">
      <NavLink href="/" label="Home" />
      <NavLink href="/learn" label="Learn" />
      <NavLink href="/topics" label="Topics" />
      <NavLink href={$currentUser ? '/library' : '/login'} label="Library" />
      {#if $currentUser}
        <NavBarAvatar user={$currentUser} />
      {:else}
        <a href="/login" class="login-link" on:click={handleLoginClick}>Log in</a>
      {/if}
    </div>
```

- [ ] **Step 2: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/components/Navbar.svelte
git commit -m "fix: remove Dashboard NavLink from Navbar — merged into Home"
```

---

### Task 8: Delete `/dashboard` route

**Files:**
- Delete: `frontend/src/routes/dashboard/+page.svelte`

- [ ] **Step 1: Delete the route**

```bash
git rm frontend/src/routes/dashboard/+page.svelte
```

- [ ] **Step 2: Confirm directory is gone**

```bash
ls frontend/src/routes/dashboard/ 2>&1
```

Expected: `ls: cannot access 'frontend/src/routes/dashboard/': No such file or directory`

- [ ] **Step 3: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
git commit -m "refactor: delete /dashboard route — content merged into /"
```

---

### Task 9: Rewrite `+page.svelte`

**Files:**
- Rewrite: `frontend/src/routes/+page.svelte`

The guest branch renders: hero (on gradient) + "Explore Albums" header card + album grid card. The auth branch renders: `CTASidebar` + right column (stats row + forum header card + forum posts or empty state).

- [ ] **Step 1: Replace the full file contents**

Write `frontend/src/routes/+page.svelte`:

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { getCognitoLoginUrl } from '$lib/api/auth';
  import { listAlbums } from '$lib/api/albums';
  import { apiFetch } from '$lib/api/client';
  import type { AlbumListResponse } from '$lib/api/types';
  import { currentUser } from '$lib/stores/user';
  import AlbumGrid from '$lib/components/AlbumGrid.svelte';
  import CTASidebar from '$lib/components/CTASidebar.svelte';
  import NavLink from '$lib/components/NavLink.svelte';
  import PageCard from '$lib/components/PageCard.svelte';

  let albums: AlbumListResponse[] = [];
  let feedPosts: unknown[] = [];
  let loading = true;
  let albumError: string | null = null;

  onMount(async () => {
    try {
      albums = await listAlbums();
    } catch {
      albumError = 'Could not load Albums right now. Please try again later.';
    } finally {
      loading = false;
    }

    if ($currentUser) {
      try {
        feedPosts = await apiFetch<unknown[]>('/feed/');
      } catch {
        feedPosts = [];
      }
    }
  });

  async function handleGetStarted() {
    try {
      window.location.href = await getCognitoLoginUrl();
    } catch (err) {
      console.error('Could not build Cognito login URL:', err);
    }
  }
</script>

{#if $currentUser}
  <!-- Authenticated view -->
  <div class="home-auth">
    <CTASidebar user={$currentUser} {albums} snippets={[]} />

    <div class="right-col">

      <!-- Stats row -->
      <div class="stats-row">
        <PageCard padding="0.875rem 1.25rem">
          <div class="stat">
            <span class="stat-label">⭐ XP Earned</span>
            <span class="stat-value">0</span>
            <span class="stat-sub">Keep learning to earn XP</span>
          </div>
        </PageCard>
        <PageCard padding="0.875rem 1.25rem">
          <div class="stat">
            <span class="stat-label">📚 Albums Enrolled</span>
            <span class="stat-value">{albums.length}</span>
            <span class="stat-sub">{albums.length === 1 ? '1 album' : `${albums.length} albums`}</span>
          </div>
        </PageCard>
        <PageCard padding="0.875rem 1.25rem">
          <div class="stat">
            <span class="stat-label">✅ Snippets Read</span>
            <span class="stat-value">0</span>
            <span class="stat-sub">Complete Snippets to track progress</span>
          </div>
        </PageCard>
      </div>

      <!-- Forum header card -->
      <PageCard padding="0.875rem 1.25rem">
        <div class="forum-header">
          <div class="forum-header-left">
            <h2>The Forum</h2>
            <span class="gate-note">Hidden for under-14s · read-only for 14–16</span>
          </div>
          <NavLink href="/forum" label="View all posts →" />
        </div>
      </PageCard>

      <!-- Forum posts or empty state -->
      {#if feedPosts.length === 0}
        <PageCard padding="1.25rem">
          <p class="forum-empty">No posts yet — check back soon.</p>
        </PageCard>
      {:else}
        <div class="forum-grid">
          {#each feedPosts as _post}
            <!-- PostCard rendered here once /feed returns real Post data -->
          {/each}
        </div>
      {/if}

    </div>
  </div>

{:else}
  <!-- Guest view -->
  <div class="hero">
    <h1>Discover your future with Amazon T-Levels</h1>
    <p>Explore short-form content, enrol in curated learning Albums, and connect with Amazon mentors — all in one place.</p>
    <button class="cta" on:click={handleGetStarted}>Get started</button>
  </div>

  <PageCard padding="0.875rem 1.25rem">
    <div class="section-header">
      <h2>Explore Albums</h2>
      <NavLink href="/learn" label="View all →" />
    </div>
  </PageCard>

  <PageCard as="main" padding="1.5rem">
    {#if loading}
      <p class="loading">Loading...</p>
    {:else if albumError}
      <p class="error">{albumError}</p>
    {:else}
      <AlbumGrid {albums} />
    {/if}
  </PageCard>
{/if}

<style>
  /* ── Authenticated layout ── */
  .home-auth {
    display: flex;
    gap: var(--gap-inner);
    min-height: 100%;
    align-items: stretch;
  }

  .right-col {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
  }

  .stats-row {
    display: flex;
    gap: var(--gap-inner);
  }

  /* Make each PageCard stat tile share the row equally */
  .stats-row :global(.page-card) {
    flex: 1;
  }

  .stat {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .stat-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #5a6472;
    font-weight: 700;
    font-family: 'Ubuntu', sans-serif;
  }

  .stat-value {
    font-size: 1.5rem;
    font-weight: 800;
    color: #232f3e;
    font-family: 'Ubuntu', sans-serif;
  }

  .stat-sub {
    font-size: 0.72rem;
    color: #5a6472;
    font-family: 'Ubuntu', sans-serif;
  }

  .forum-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .forum-header-left {
    display: flex;
    align-items: baseline;
    gap: 0.75rem;
  }

  .forum-header-left h2 {
    font-size: 0.95rem;
    font-weight: 700;
    color: #232f3e;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .gate-note {
    font-size: 0.75rem;
    color: #5a6472;
    font-family: 'Ubuntu', sans-serif;
  }

  .forum-grid {
    columns: 3;
    column-gap: var(--gap-inner);
  }

  .forum-empty {
    font-size: 0.875rem;
    color: #5a6472;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  /* ── Guest layout ── */
  .hero {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
    padding: 2.5rem 0;
  }

  .hero h1 {
    font-size: 2.25rem;
    font-weight: 800;
    color: #232f3e;
    line-height: 1.2;
    max-width: 620px;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .hero p {
    font-size: 1rem;
    color: #5a6472;
    max-width: 520px;
    line-height: 1.6;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .cta {
    background: #ffffff;
    color: #232f3e;
    border: none;
    border-radius: 0;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    padding: 0.7rem 1.75rem;
    font-size: 0.9rem;
    font-weight: 700;
    cursor: pointer;
    font-family: 'Ubuntu', sans-serif;
    transition: opacity 0.15s;
    margin-top: 0.25rem;
  }

  .cta:hover {
    opacity: 0.88;
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .section-header h2 {
    font-size: 0.95rem;
    font-weight: 700;
    color: #232f3e;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }

  .loading,
  .error {
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

- [ ] **Step 3: Run the full test suite**

```bash
cd frontend && npx vitest run
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/+page.svelte
git commit -m "feat: implement home page — guest hero+albums and auth CTASidebar+stats+forum"
```

---

### Task 10: Full verification

**Files:** None — verification and browser testing only.

- [ ] **Step 1: Run the full test suite**

```bash
cd frontend && npx vitest run
```

Expected: all tests PASS (the new `agentDraft` tests from Task 1 plus all pre-existing tests).

- [ ] **Step 2: Run typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: Run lint**

```bash
cd frontend && npm run lint
```

Expected: 0 errors (pre-existing warnings on unrelated stubs are fine).

- [ ] **Step 4: Start the dev server**

```bash
cd frontend && npm run dev
```

Open the URL printed by Vite (typically `http://localhost:5173`).

- [ ] **Step 5: Verify guest view**

Without being logged in, visit `/`:
- Hero text "Discover your future with Amazon T-Levels" and subtitle render directly on the animated pastel gradient (no white card behind them)
- Backdrop colours cycle continuously (morphing hue animation active)
- "Get started" button is white with drop shadow, dark text — clicking initiates Cognito login flow
- "Explore Albums" header card renders with "View all →" NavLink on the right
- Album grid card renders below it with the seeded Albums as square icon tiles
- Loading state shows "Loading..." briefly; error state shows message if API is unreachable
- Navbar shows no "Dashboard" link

- [ ] **Step 6: Verify the morphing backdrop stops on other pages**

Navigate to `/learn` — backdrop should return to the normal static pastel gradient, no continuous hue rotation.

- [ ] **Step 7: Verify authenticated view**

Log in via the Cognito Hosted UI, then visit `/`:
- CTASidebar (320px) on the left: greeting updates based on current time of day ("Good morning/afternoon/evening, {first_name} 👋"), two AlbumCard squares side-by-side (enrolled albums), snippets section omitted (empty — no recommendations endpoint yet), AgentChat teaser pinned to the bottom with palette-coloured accent line
- Right column: three stat cards in a row (XP=0, Albums Enrolled=real count, Snippets Read=0), "The Forum" header card with gate note and "View all posts →" NavLink, forum empty state card "No posts yet — check back soon."
- Both columns stretch to the same height between Navbar and Footer

- [ ] **Step 8: Verify AgentChat handoff**

Type a message in the AgentChat teaser and submit — should navigate to `/library`. (The draft store is set; full pre-fill in `/library` is deferred until the Library page is implemented.)

- [ ] **Step 9: Verify `/dashboard` is gone**

Visit `/dashboard` — should return a SvelteKit 404 page.

- [ ] **Step 10: Final commit if any formatting fixes were needed**

If Prettier auto-fixed any formatting:

```bash
cd frontend && npx prettier --write src/routes/+page.svelte src/lib/components/CTASidebar.svelte
git add -p
git commit -m "style: prettier formatting"
```

Otherwise no commit needed.
