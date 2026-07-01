# Floating-Card Visual Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every page a floating "AWS-console" card look — white `PageCard` panels (Navbar, Footer, sidebars, page content) with a soft omnidirectional drop shadow, floating over a per-route, slowly-animated 3-colour pastel gradient backdrop.

**Architecture:** A new `PageCard.svelte` primitive (white background, square corners, shared shadow, configurable `as`/`padding`/`width`) becomes the single styling source for every floating panel. The root layout grows a fixed-position animated gradient backdrop (palette computed deterministically per route by `lib/gradient.ts`) and a `--gap-inner`/`--gap-outer` spacing system that every panel's margins/gaps reuse, so left/right/top/bottom alignment across Navbar, sidebars, content, and Footer falls out of using the same two tokens everywhere. `AlbumCard` becomes a square icon tile. `AlbumSidebar`/`NavSidebar`/`CTASidebar` switch from dark-navy to white surfaces with sticky inner nav content. Every existing page is rolled over to render its content inside `PageCard`(s).

**Tech Stack:** SvelteKit 2 / Svelte 4, TypeScript, Vitest, `svelte-check`, ESLint/Prettier, Histoire (component stories). Pure CSS animation (no JS animation loop). No new dependencies.

**Spec:** `docs/superpowers/specs/2026-06-24-floating-card-visual-polish-design.md`

**Design note on width/alignment:** Per the approved design, Navbar/Footer/sidebars/content all use `--gap-outer` as their outer-edge inset and stretch to fill the width available within that inset (not a narrower centred card with large visible gradient margins). This is what makes "left edges flush" and "right edges flush" hold automatically across Navbar, any sidebar, content cards, and Footer — see spec's global spacing tokens section.

---

### Task 1: `PageCard` component

**Files:**
- Create: `frontend/src/lib/components/PageCard.svelte`
- Test: `frontend/src/lib/shell.test.ts`

- [ ] **Step 1: Write the failing smoke test**

Append to `frontend/src/lib/shell.test.ts`:

```ts
describe('PageCard', () => {
  it('exports a default Svelte component', async () => {
    const mod = await import('$lib/components/PageCard.svelte');
    expect(mod.default).toBeDefined();
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: FAIL — `frontend/src/lib/components/PageCard.svelte` doesn't exist yet.

- [ ] **Step 3: Create `frontend/src/lib/components/PageCard.svelte`**

```svelte
<!--
  PageCard
  Purpose: Shared "floating panel" surface used by every piece of page chrome (Navbar,
    Footer, sidebars, page content) to get the same white background, square corners,
    and omnidirectional drop shadow over the animated gradient backdrop.
  Used in: Navbar, Footer, AlbumSidebar, NavSidebar, CTASidebar, and every routed page's
    content area.
  Props:
    - as (string): root element tag to render, e.g. 'main' | 'nav' | 'footer' | 'aside' |
      'div'. Defaults to 'div'. Lets each consumer keep correct page semantics (e.g. a
      page's content area renders as <main>, a sidebar as <aside>) while sharing one
      visual implementation.
    - padding (string): CSS padding shorthand for the card's own internal padding,
      between its border and its slotted content. Defaults to '2rem'. Distinct from the
      --gap-inner/--gap-outer spacing between cards, which callers control themselves.
    - width (string): CSS width. Defaults to 'auto' (fills whatever flex/grid track the
      caller places it in) — used by sidebars/CTASidebar to set a fixed width.
  Styling:
    background #ffffff, border-radius 0 (square corners), box-shadow
    0 10px 18px -4px rgba(35, 47, 62, 0.35) (the validated "soft directional blur" shadow).
-->
<script lang="ts">
  export let as: string = 'div';
  export let padding: string = '2rem';
  export let width: string = 'auto';
</script>

<svelte:element this={as} class="page-card" style="padding: {padding}; width: {width};">
  <slot />
</svelte:element>

<style>
  .page-card {
    background: #ffffff;
    border-radius: 0;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    box-sizing: border-box;
  }
</style>
```

- [ ] **Step 4: Run the test again to verify it passes**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — all tests green.

- [ ] **Step 5: Verify it compiles**

Run (from `frontend/`): `npm run check`
Expected: 0 errors.

- [ ] **Step 6: Format and commit**

```bash
cd frontend
npx prettier --write src/lib/components/PageCard.svelte src/lib/shell.test.ts
git add src/lib/components/PageCard.svelte src/lib/shell.test.ts
git commit -m "feat: add PageCard floating-panel primitive"
```

---

### Task 2: `lib/gradient.ts` — per-route pastel palette

**Files:**
- Create: `frontend/src/lib/gradient.ts`
- Test: `frontend/src/lib/gradient.test.ts`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/lib/gradient.test.ts`:

```ts
import { describe, it, expect } from 'vitest';
import { getPagePalette } from './gradient';

describe('getPagePalette', () => {
  it('returns the same palette for the same pathname every time', () => {
    expect(getPagePalette('/learn')).toEqual(getPagePalette('/learn'));
  });

  it('returns a different palette for a different pathname', () => {
    expect(getPagePalette('/learn')).not.toEqual(getPagePalette('/topics'));
  });

  it('returns three distinct hsl colours', () => {
    const [a, b, c] = getPagePalette('/dashboard');
    expect(new Set([a, b, c]).size).toBe(3);
  });

  it('keeps every colour within the fixed pastel saturation/lightness band', () => {
    const palette = getPagePalette('/');
    for (const colour of palette) {
      expect(colour).toMatch(/^hsl\(\d+, 60%, 87%\)$/);
    }
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: FAIL — `frontend/src/lib/gradient.ts` doesn't exist yet.

- [ ] **Step 3: Create `frontend/src/lib/gradient.ts`**

```ts
/**
 * Deterministic per-route pastel palette for the page backdrop. Same pathname always
 * yields the same three colours (stable across visits/refreshes); different pathnames
 * yield visually distinct palettes. Saturation/lightness are fixed so every page's
 * backdrop reads as the same soft "AWS console" pastel mood.
 */

const SATURATION = 60;
const LIGHTNESS = 87;
const HUE_OFFSET_B = 110;
const HUE_OFFSET_C = 220;

function hashString(input: string): number {
  let hash = 0;
  for (let i = 0; i < input.length; i++) {
    hash = (hash << 5) - hash + input.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

function hsl(hue: number): string {
  return `hsl(${hue}, ${SATURATION}%, ${LIGHTNESS}%)`;
}

export function getPagePalette(pathname: string): [string, string, string] {
  const baseHue = hashString(pathname) % 360;
  const hueB = (baseHue + HUE_OFFSET_B) % 360;
  const hueC = (baseHue + HUE_OFFSET_C) % 360;
  return [hsl(baseHue), hsl(hueB), hsl(hueC)];
}
```

- [ ] **Step 4: Run the tests again to verify they pass**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — all tests green.

- [ ] **Step 5: Verify it compiles**

Run (from `frontend/`): `npm run check`
Expected: 0 errors.

- [ ] **Step 6: Format and commit**

```bash
cd frontend
npx prettier --write src/lib/gradient.ts src/lib/gradient.test.ts
git add src/lib/gradient.ts src/lib/gradient.test.ts
git commit -m "feat: add deterministic per-route pastel palette generator"
```

---

### Task 3: Root layout — backdrop, spacing tokens, fix nested-`<main>` bug

**Files:**
- Modify: `frontend/src/routes/+layout.svelte`

**Context:** The current root layout (from a prior chapter) wraps `<slot />` in its own `<main>` purely to get sticky-footer flex behaviour. Several pages (e.g. `/learn/[id]`) render their *own* `<main>` too, so today's markup nests two `<main>` elements — invalid semantic HTML (a CLAUDE.md hard requirement). This task replaces that wrapper with a plain non-semantic `<div>`, adds the two global spacing tokens, and adds the animated gradient backdrop. Navbar/Footer are NOT visually restyled in this task (that's Tasks 4-5) — this task only changes the layout shell structure they sit inside.

- [ ] **Step 1: Replace the root layout**

Read the current file first:

```bash
cat frontend/src/routes/+layout.svelte
```

Replace its entire contents with:

```svelte
<script lang="ts">
  import { page } from '$app/stores';
  import Navbar from '$lib/components/Navbar.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import { getPagePalette } from '$lib/gradient';

  $: palette = getPagePalette($page.url.pathname);
</script>

<div class="backdrop" aria-hidden="true">
  <div class="blob blob-a" style="background: radial-gradient(circle, {palette[0]}, transparent 70%);"></div>
  <div class="blob blob-b" style="background: radial-gradient(circle, {palette[1]}, transparent 70%);"></div>
  <div class="blob blob-c" style="background: radial-gradient(circle, {palette[2]}, transparent 70%);"></div>
</div>

<div class="shell">
  <Navbar />
  <div class="content">
    <slot />
  </div>
  <Footer />
</div>

<style>
  :global(*, *::before, *::after) {
    box-sizing: border-box;
  }

  :global(html, body) {
    height: 100%;
  }

  :global(body) {
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
    background: #f5f5f0;
    color: #232f3e;
  }

  :global(:root) {
    --gap-inner: 1.5rem;
    --gap-outer: 2.25rem;
  }

  .backdrop {
    position: fixed;
    inset: 0;
    z-index: -1;
    overflow: hidden;
    background: #f5f5f0;
  }

  .blob {
    position: absolute;
    width: 70vmax;
    height: 70vmax;
    border-radius: 50%;
    filter: blur(40px);
    opacity: 0.6;
  }

  .blob-a {
    top: -15%;
    left: -15%;
    animation: drift-a 28s ease-in-out infinite;
  }

  .blob-b {
    top: -10%;
    right: -20%;
    animation: drift-b 34s ease-in-out infinite;
  }

  .blob-c {
    bottom: -20%;
    left: 15%;
    animation: drift-c 40s ease-in-out infinite;
  }

  @keyframes drift-a {
    0%,
    100% {
      transform: translate(0, 0);
    }
    50% {
      transform: translate(8vmax, 6vmax);
    }
  }

  @keyframes drift-b {
    0%,
    100% {
      transform: translate(0, 0);
    }
    50% {
      transform: translate(-6vmax, 8vmax);
    }
  }

  @keyframes drift-c {
    0%,
    100% {
      transform: translate(0, 0);
    }
    50% {
      transform: translate(5vmax, -7vmax);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .blob {
      animation: none;
    }
  }

  .shell {
    position: relative;
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    box-sizing: border-box;
    padding: var(--gap-outer);
    gap: var(--gap-inner);
  }

  .content {
    flex: 1 0 auto;
  }
</style>
```

- [ ] **Step 2: Verify it compiles**

Run (from `frontend/`): `npm run check`
Expected: 0 errors.

- [ ] **Step 3: Run the full test suite to confirm nothing broke**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — all tests green (this task doesn't change any component the existing tests import).

- [ ] **Step 4: Format and commit**

```bash
cd frontend
npx prettier --write src/routes/+layout.svelte
git add src/routes/+layout.svelte
git commit -m "feat: add animated per-route gradient backdrop and spacing tokens to root layout"
```

---

### Task 4: Navbar restyle

**Files:**
- Modify: `frontend/src/lib/components/Navbar.svelte`
- Modify: `frontend/src/lib/components/NavLink.svelte`

**Context:** Navbar switches from a full-bleed dark navy bar to a `PageCard`-styled white floating panel. Because `PageCard` renders its root element dynamically (`<svelte:element this={as}>`), a component that *uses* `PageCard` cannot put plain element-selector CSS like `nav { ... }` in its own `<style>` block and expect it to match — Svelte's scoped-style compiler only scopes elements a component's own template literally contains, and `PageCard`'s internal `<nav>` belongs to `PageCard.svelte`'s scope, not `Navbar.svelte`'s. So Navbar's flex/height layout goes on an inner wrapper `<div>` that `Navbar.svelte` does render literally, inside `PageCard`'s slot.

- [ ] **Step 1: Replace `Navbar.svelte`**

```svelte
<script lang="ts">
  import NavLink from '$lib/components/NavLink.svelte';
  import NavBarAvatar from '$lib/components/NavBarAvatar.svelte';
  import PageCard from '$lib/components/PageCard.svelte';
  import { currentUser } from '$lib/stores/user';
</script>

<PageCard as="nav" padding="0 1.5rem">
  <div class="nav-inner">
    <a href="/" class="logo-link">
      <img src="/assets/logo.png" alt="T Level Placements at Amazon" class="logo" />
    </a>
    <div class="links">
      <NavLink href="/" label="Home" />
      <NavLink href="/learn" label="Learn" />
      <NavLink href="/topics" label="Topics" />
      <NavLink href={$currentUser ? '/library' : '/login'} label="Library" />
      <NavLink href={$currentUser ? '/dashboard' : '/login'} label="Dashboard" />
      {#if $currentUser}
        <NavBarAvatar user={$currentUser} />
      {:else}
        <NavLink href="/login" label="Log in" />
      {/if}
    </div>
  </div>
</PageCard>

<style>
  .nav-inner {
    display: flex;
    align-items: center;
    height: 64px;
    width: 100%;
  }

  .logo-link {
    display: flex;
    align-items: center;
    text-decoration: none;
    flex-shrink: 0;
  }

  .logo {
    height: 40px;
  }

  .links {
    margin-left: auto;
    display: flex;
    gap: 1.5rem;
    align-items: center;
    overflow: visible;
  }
</style>
```

- [ ] **Step 2: Recolour `NavLink.svelte` for the white background**

In `frontend/src/lib/components/NavLink.svelte`, change the link colour from white to dark:

```svelte
<style>
  a {
    position: relative;
    display: inline-block;
    color: #232f3e;
    text-decoration: none;
    font-family: 'Ubuntu', sans-serif;
  }

  a::after {
    content: '';
    position: absolute;
    left: 0;
    bottom: -0.3em;
    width: 100%;
    height: 0.15em;
    border-radius: 9999px;
    background: linear-gradient(to right, #ff9900, #ffd700);
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 0.3s ease-in-out;
  }

  a:hover::after {
    transform: scaleX(1);
  }
</style>
```

(Only the `color` value changes, from `#ffffff` to `#232f3e` — everything else in the file stays the same.)

- [ ] **Step 3: Verify it compiles and tests still pass**

Run (from `frontend/`):
```bash
npm run check
npm run test:unit -- --run
```
Expected: 0 type errors; all tests PASS (`Navbar` and `NavLink` are only smoke-tested for exporting a default component, which is unaffected by styling changes).

- [ ] **Step 4: Format and commit**

```bash
cd frontend
npx prettier --write src/lib/components/Navbar.svelte src/lib/components/NavLink.svelte
git add src/lib/components/Navbar.svelte src/lib/components/NavLink.svelte
git commit -m "feat: restyle Navbar as a floating white PageCard panel"
```

---

### Task 5: Footer restyle

**Files:**
- Modify: `frontend/src/lib/components/Footer.svelte`

**Context:** Footer switches from a full-bleed dark navy bar to a `PageCard`-styled white floating panel. Unlike Navbar, Footer's existing template already renders its content (`.columns`, `.bottom-bar`) as direct children of its root element, so no extra wrapper `<div>` is needed — only the root element changes from `<footer>` to `<PageCard as="footer">`.

The existing heading colour `#ff9900` (orange) was chosen for a dark background and fails WCAG AA contrast on white (~2.1:1, needs 4.5:1) — it must change to a darker amber, `#a35200` (verified ~5.6:1 on white), to stay legible and compliant per CLAUDE.md's accessibility mandate. The `.bottom-bar` copyright text similarly moves from `rgba(255,255,255,0.7)` (light-on-dark) to the muted `#5a6472` used elsewhere in this redesign (verified ~6.0:1 on white).

- [ ] **Step 1: Replace `Footer.svelte`**

```svelte
<script lang="ts">
  import NavLink from '$lib/components/NavLink.svelte';
  import PageCard from '$lib/components/PageCard.svelte';
</script>

<PageCard as="footer" padding="2rem 1.5rem 0">
  <div class="columns">
    <div class="column">
      <h3 class="column-heading">Navigation</h3>
      <div class="column-links">
        <NavLink href="/" label="Home" />
        <NavLink href="/learn" label="Learn" />
        <NavLink href="/topics" label="Topics" />
        <NavLink href="/dashboard" label="Dashboard" />
      </div>
    </div>
    <div class="column">
      <h3 class="column-heading">About</h3>
      <div class="column-links">
        <NavLink href="#" label="About This Project" />
        <NavLink href="#" label="T-Level Programme" />
      </div>
    </div>
    <div class="column">
      <h3 class="column-heading">Support</h3>
      <div class="column-links">
        <NavLink href="#" label="Help" />
        <NavLink href="#" label="Contact Us" />
      </div>
    </div>
  </div>
  <div class="bottom-bar">
    <p>© 2026 Amazon T-Level Project</p>
  </div>
</PageCard>

<style>
  .columns {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
    padding-bottom: 2rem;
  }

  .column {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .column-heading {
    margin: 0 0 0.75rem;
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #a35200;
  }

  .column-links {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    align-items: flex-start;
  }

  .bottom-bar {
    border-top: 1px solid rgba(35, 47, 62, 0.15);
    padding: 1rem 0;
    text-align: center;
    font-size: 0.85rem;
    color: #5a6472;
  }

  .bottom-bar p {
    margin: 0;
  }
</style>
```

- [ ] **Step 2: Verify it compiles and tests still pass**

Run (from `frontend/`):
```bash
npm run check
npm run test:unit -- --run
```
Expected: 0 type errors; all tests PASS.

- [ ] **Step 3: Format and commit**

```bash
cd frontend
npx prettier --write src/lib/components/Footer.svelte
git add src/lib/components/Footer.svelte
git commit -m "feat: restyle Footer as a floating white PageCard panel"
```

---

### Task 6: `AlbumCard` + `AlbumGrid` redesign

**Files:**
- Modify: `frontend/src/lib/components/AlbumCard.svelte`
- Modify: `frontend/src/lib/components/AlbumGrid.svelte`
- Test: `frontend/src/lib/shell.test.ts` (existing smoke tests already cover both — no new test needed since the public API of both components, beyond the removed `progress` prop, is unchanged for the purposes of those tests)

**Context:** `AlbumCard` becomes a square icon tile (white background, square corners, the validated soft directional-blur shadow `0 10px 18px -4px rgba(35, 47, 62, 0.35)`) with a large centred black-outline SVG cloud icon and the title beneath it. Description and the `progress` prop are removed from the card face entirely — `progress` was always `null` from every real caller today (no behaviour regression). Icon paths are stored as plain `d` attribute strings (not `{@html}`) to avoid introducing any HTML-injection-shaped pattern, even though the source is a static developer-controlled map.

- [ ] **Step 1: Replace `AlbumCard.svelte`**

```svelte
<!--
  AlbumCard
  Purpose: Square icon-tile used to open an Album — a curated, course-like set of Snippets
    forming a learning pathway. Requires an account to enrol.
  Used in: AlbumGrid (and later: CTASidebar, EnrolledAlbumsList, once those chapters land)
  Props:
    - album (AlbumListResponse): the Album to display
  Layout:
    A square tile: a large centred line-icon (looked up from album.icon) with the Album's
    title beneath it. No description or progress indicator on the card face — those live
    on the Album detail page.
  Styling:
    White background, square corners, soft directional-blur drop shadow
    (0 10px 18px -4px rgba(35, 47, 62, 0.35)), ~190px square.
-->
<script lang="ts">
  import type { AlbumListResponse } from '$lib/api/types';

  export let album: AlbumListResponse;

  const ICON_PATHS: Record<string, string[]> = {
    cloud: ['M6 18a4 4 0 0 1-.6-7.96A5 5 0 0 1 15 8a4.5 4.5 0 0 1 1 8.9', 'M6 18h10'],
  };
  const DEFAULT_ICON_PATHS = ['M4 4h16v16H4z'];

  $: iconPaths = ICON_PATHS[album.icon] ?? DEFAULT_ICON_PATHS;
</script>

<a class="album-card" href={`/learn/${album.id}`}>
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
  <h3>{album.title}</h3>
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

- [ ] **Step 2: Replace `AlbumGrid.svelte`'s grid styling**

```svelte
<!--
  AlbumGrid
  Purpose: Grid/list of AlbumCards for browsing all available Albums. Publicly viewable without
    an account (enrolling requires one, via EnrolButton on the Album view itself).
  Used in: Album discovery page
  Props:
    - albums (AlbumListResponse[]): same shape AlbumCard expects
  Behaviour:
    If albums is empty, show an empty state: "No Albums available yet."
  Styling:
    Flex-wrap row of square AlbumCard tiles, gap matches the global --gap-inner spacing
    token used everywhere else in this layout.
-->
<script lang="ts">
  import AlbumCard from './AlbumCard.svelte';
  import type { AlbumListResponse } from '$lib/api/types';

  export let albums: AlbumListResponse[];
</script>

{#if albums.length === 0}
  <p>No Albums available yet.</p>
{:else}
  <div class="album-grid">
    {#each albums as album}
      <!-- Code above goes through every item in the albums array, and for each item, calls it album -->
      <AlbumCard {album} />
      <!-- Code above is shorthand for <AlbumCard album={album} /> -->
    {/each}
  </div>
{/if}

<style>
  .album-grid {
    display: flex;
    flex-wrap: wrap;
    gap: var(--gap-inner);
  }
</style>
```

- [ ] **Step 3: Run the full test suite**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — all tests green (existing smoke tests only check the component exports a default, which is unaffected).

- [ ] **Step 4: Verify it compiles**

Run (from `frontend/`): `npm run check`
Expected: 0 errors.

- [ ] **Step 5: Format and commit**

```bash
cd frontend
npx prettier --write src/lib/components/AlbumCard.svelte src/lib/components/AlbumGrid.svelte
git add src/lib/components/AlbumCard.svelte src/lib/components/AlbumGrid.svelte
git commit -m "feat: redesign AlbumCard as a square icon tile"
```

---

### Task 7: `SideHeader` recolour + `AlbumSidebar` restyle

**Files:**
- Modify: `frontend/src/lib/components/SideHeader.svelte`
- Modify: `frontend/src/lib/components/AlbumSidebar.svelte`

**Context:** `AlbumSidebar` switches from a dark-navy fixed-width panel to a white floating `PageCard` (`as="aside"`), 20% wider (`240px → 288px`), whose height stretches to match its sibling content card via the parent flex row's default `align-items: stretch` (no per-component change needed for that — it falls out of how `/learn/[id]`'s page markup arranges the row, handled in Task 11). Its inner nav list becomes `position: sticky` so it stays in view while a taller sibling content card scrolls, bounded by its own container's height (never overlapping the Footer). `SideHeader` (only ever used inside `AlbumSidebar`) gets matching dark-on-light recolouring in the same task since the two are tightly coupled and `SideHeader` has no other consumer.

- [ ] **Step 1: Recolour `SideHeader.svelte`**

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
    colour #5a6472 (muted, AA-compliant on white), followed by the title in a slightly larger
    weight, with a divider line below.
-->
<script lang="ts">
  export let title: string;
  export let index: number;
</script>

<div class="side-header">
  <span class="label">SIDE {index}</span>
  <h4>{title}</h4>
  <div class="divider" aria-hidden="true"></div>
</div>

<style>
  .side-header {
    margin: 1rem 0 0.5rem;
  }

  .label {
    display: block;
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    color: #5a6472;
    text-transform: uppercase;
  }

  h4 {
    margin: 0.25rem 0 0.5rem;
    color: #232f3e;
    font-size: 0.95rem;
    font-weight: 600;
  }

  .divider {
    border-top: 1px solid #e2e2dc;
  }
</style>
```

- [ ] **Step 2: Replace `AlbumSidebar.svelte`**

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
    Floating white PageCard (aside), 288px wide, full height of its row (matches the sibling
    content card via the parent flex row). Inner nav content is sticky so it stays in view
    while a taller sibling content card scrolls.
-->
<script lang="ts">
  import type { SideResponse } from '$lib/api/types';
  import SideHeader from '$lib/components/SideHeader.svelte';
  import PageCard from '$lib/components/PageCard.svelte';

  export let sides: SideResponse[];
  export let activeSnippetId: number | null;
</script>

<PageCard as="aside" width="288px" padding="1.5rem 1rem">
  <nav class="album-sidebar" aria-label="Album sides and snippets">
    {#each sides as side, index}
      <SideHeader title={side.title} index={index + 1} />
      <ul>
        {#each side.snippets as snippet}
          <li
            class:active={snippet.id === activeSnippetId}
            aria-current={snippet.id === activeSnippetId ? 'true' : undefined}
          >
            {snippet.title}
          </li>
        {/each}
      </ul>
    {/each}
  </nav>
</PageCard>

<style>
  .album-sidebar {
    position: sticky;
    top: var(--gap-inner);
  }

  ul {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  li {
    color: #5a6472;
    font-size: 0.875rem;
    padding: 0.4rem 0;
  }

  li.active {
    font-weight: bold;
    color: #232f3e;
  }
</style>
```

- [ ] **Step 3: Run the full test suite**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — all tests green.

- [ ] **Step 4: Verify it compiles**

Run (from `frontend/`): `npm run check`
Expected: 0 errors.

- [ ] **Step 5: Format and commit**

```bash
cd frontend
npx prettier --write src/lib/components/SideHeader.svelte src/lib/components/AlbumSidebar.svelte
git add src/lib/components/SideHeader.svelte src/lib/components/AlbumSidebar.svelte
git commit -m "feat: restyle AlbumSidebar and SideHeader as a floating white panel"
```

---

### Task 8: `NavSidebar` restyle

**Files:**
- Modify: `frontend/src/lib/components/NavSidebar.svelte`

**Context:** Same treatment as `AlbumSidebar` — white floating `PageCard` (`as="aside"`), 20% wider (`240px → 288px`), sticky inner nav content. `NavSidebar` is not currently wired into any route yet (its docstring already notes "wired up in a later chapter"), so this task only updates the component itself; no page changes here.

- [ ] **Step 1: Replace `NavSidebar.svelte`**

```svelte
<!--
  NavSidebar
  Purpose: Topic-list section nav, used inline within pages that need to browse by
    Topic (e.g. /topics, /learn) -- not a persistent global app sidebar. Global nav
    (Library/Dashboard/avatar) lives in Navbar/NavBarAvatar instead.
  Used in: /topics, /learn (wired up in a later chapter)
  Props:
    - topics (TopicResponse[]): list of all 5 topics to render as nav links
    - activePath (string): current URL path -- highlight matching topic link
  Layout:
    Topic links -> /topics/[slug] for each topic.
  Styling:
    Floating white PageCard (aside), 288px wide, full height of its row, sticky inner
    nav content -- same treatment as AlbumSidebar.
-->
<script lang="ts">
  import type { TopicResponse } from '$lib/api/types';
  import PageCard from '$lib/components/PageCard.svelte';

  export let topics: TopicResponse[];
  export let activePath: string;
</script>

<PageCard as="aside" width="288px" padding="1.5rem 1rem">
  <nav class="sidebar">
    {#each topics as topic}
      <a
        href={`/topics/${topic.slug}`}
        class:active={activePath.startsWith(`/topics/${topic.slug}`)}
      >
        {topic.name}
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
  }
</style>
```

- [ ] **Step 2: Run the full test suite**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — all tests green.

- [ ] **Step 3: Verify it compiles**

Run (from `frontend/`): `npm run check`
Expected: 0 errors.

- [ ] **Step 4: Run the Histoire build** (NavSidebar has an existing story)

Run (from `frontend/`): `npm run story:build`
Expected: builds with no errors. Clean up afterward: `rm -rf .histoire/dist`.

- [ ] **Step 5: Format and commit**

```bash
cd frontend
npx prettier --write src/lib/components/NavSidebar.svelte
git add src/lib/components/NavSidebar.svelte
git commit -m "feat: restyle NavSidebar as a floating white panel"
```

---

### Task 9: `CTASidebar` container restyle (stub only)

**Files:**
- Modify: `frontend/src/lib/components/CTASidebar.svelte`

**Context:** `CTASidebar` is currently an unimplemented stub (only a docstring and `// TODO` comments — no markup, and it isn't wired into `/dashboard` or any other route yet). This task does **not** implement its content (greeting, AlbumCards, SnippetCards, AgentChat — that's explicitly future work per its own docstring). It only gives the stub a `PageCard` container shell, matching every other panel's visual language, sized wider than the nav sidebars (~320px) since it will hold more content once implemented.

- [ ] **Step 1: Replace `CTASidebar.svelte`**

```svelte
<!--
  CTASidebar
  Purpose: Wide left sidebar on the dashboard with a personalised, time-of-day-aware welcome
    message, two enrolled AlbumCards, three recommended SnippetCards, and an AgentChat teaser.
  Used in: /dashboard
  Props:
    - user (UserResponse): used to render "Good morning/afternoon/evening, {first_name}"
    - albums (Album[] — TODO: replace with real API type once the Album model exists; for now
      whatever shape AlbumCard expects, max 2 items shown)
    - snippets (ContentListResponse[]): recommended Snippets, max 3 items shown
  Layout (top to bottom):
    1. Welcome message (derive greeting from local time-of-day)
    2. Two AlbumCards, stacked vertically
    3. Three SnippetCards, laid out horizontally
    4. AgentChat teaser at the bottom
  Styling:
    Floating white PageCard (aside), ~320px wide (wider than the nav sidebars since it
    holds more content), full height of its row, same shadow/colour treatment as every
    other panel in this layout.
-->
<script lang="ts">
  import type { ContentListResponse, UserResponse } from '$lib/api/types';
  import PageCard from '$lib/components/PageCard.svelte';

  interface Album {
    id: number;
    title: string;
  }

  export let user: UserResponse;
  export let albums: Album[];
  export let snippets: ContentListResponse[];
</script>

<PageCard as="aside" width="320px" padding="1.5rem">
  <!-- TODO: Implement greeting (time-of-day), then render albums.slice(0, 2) as AlbumCards, -->
  <!-- snippets.slice(0, 3) as SnippetCards, then an AgentChat at the bottom. -->
</PageCard>
```

- [ ] **Step 2: Run the full test suite**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — all tests green (CTASidebar has no existing test importing it; this step confirms nothing else broke).

- [ ] **Step 3: Verify it compiles**

Run (from `frontend/`): `npm run check`
Expected: 0 errors. Note: `user`, `albums`, `snippets` props will still report as "unused export property" warnings — this is pre-existing (the component was already an unimplemented stub before this task) and not a regression.

- [ ] **Step 4: Format and commit**

```bash
cd frontend
npx prettier --write src/lib/components/CTASidebar.svelte
git add src/lib/components/CTASidebar.svelte
git commit -m "feat: give CTASidebar stub a floating PageCard container"
```

---

### Task 10: Per-page rollout — single-`PageCard` pages

**Files:**
- Modify: `frontend/src/routes/+page.svelte` (Home)
- Modify: `frontend/src/routes/topics/+page.svelte`
- Modify: `frontend/src/routes/dashboard/+page.svelte`
- Modify: `frontend/src/routes/forum/+page.svelte`
- Modify: `frontend/src/routes/help/+page.svelte`
- Modify: `frontend/src/routes/library/+page.svelte`
- Modify: `frontend/src/routes/settings/+page.svelte`
- Modify: `frontend/src/routes/login/+page.svelte`
- Modify: `frontend/src/routes/learn/+page.svelte`

**Context:** Every page below renders a single `<main>` styled with the same `max-width: 900px; margin: 4rem auto; padding: 0 1.5rem;` rule today. None of them currently render a sidebar (`/topics` and `/dashboard` are still "Coming soon" stubs — `NavSidebar`/`CTASidebar` aren't wired into any route yet, per their own docstrings). This task converts each to render its `<main>` via `PageCard`, with an inner `.content` wrapper that keeps the original `900px` reading-width constraint (now centred inside the card rather than the old page background). The outer page's own spacing (`4rem auto`) is dropped — vertical separation from Navbar/Footer is now handled by the root layout's `--gap-inner`/`--gap-outer` tokens (Task 3), so keeping the old margin would double up the spacing.

- [ ] **Step 1: Update Home (`frontend/src/routes/+page.svelte`)**

```svelte
<script lang="ts">
  import PageCard from '$lib/components/PageCard.svelte';
</script>

<PageCard as="main">
  <div class="content">
    <h1>Home</h1>
    <p>Coming soon.</p>
  </div>
</PageCard>

<style>
  .content {
    max-width: 900px;
    margin: 0 auto;
  }
</style>
```

- [ ] **Step 2: Update Topics (`frontend/src/routes/topics/+page.svelte`)**

```svelte
<script lang="ts">
  import PageCard from '$lib/components/PageCard.svelte';
</script>

<PageCard as="main">
  <div class="content">
    <h1>Topics</h1>
    <p>Coming soon.</p>
  </div>
</PageCard>

<style>
  .content {
    max-width: 900px;
    margin: 0 auto;
  }
</style>
```

- [ ] **Step 3: Update Dashboard (`frontend/src/routes/dashboard/+page.svelte`)**

```svelte
<script lang="ts">
  import PageCard from '$lib/components/PageCard.svelte';
</script>

<PageCard as="main">
  <div class="content">
    <h1>Dashboard</h1>
    <p>Coming soon.</p>
  </div>
</PageCard>

<style>
  .content {
    max-width: 900px;
    margin: 0 auto;
  }
</style>
```

- [ ] **Step 4: Update Forum (`frontend/src/routes/forum/+page.svelte`)**

```svelte
<script lang="ts">
  import PageCard from '$lib/components/PageCard.svelte';
</script>

<PageCard as="main">
  <div class="content">
    <h1>Forum</h1>
    <p>Coming soon.</p>
  </div>
</PageCard>

<style>
  .content {
    max-width: 900px;
    margin: 0 auto;
  }
</style>
```

- [ ] **Step 5: Update Help (`frontend/src/routes/help/+page.svelte`)**

```svelte
<script lang="ts">
  import HelpPanel from '$lib/components/HelpPanel.svelte';
  import PageCard from '$lib/components/PageCard.svelte';
</script>

<PageCard as="main">
  <div class="content">
    <h1>Help</h1>
    <HelpPanel />
  </div>
</PageCard>

<style>
  .content {
    max-width: 900px;
    margin: 0 auto;
  }
</style>
```

- [ ] **Step 6: Update Library (`frontend/src/routes/library/+page.svelte`)**

```svelte
<script lang="ts">
  import PageCard from '$lib/components/PageCard.svelte';
</script>

<PageCard as="main">
  <div class="content">
    <h1>Library</h1>
    <p>Coming soon.</p>
  </div>
</PageCard>

<style>
  .content {
    max-width: 900px;
    margin: 0 auto;
  }
</style>
```

- [ ] **Step 7: Update Settings (`frontend/src/routes/settings/+page.svelte`)**

```svelte
<script lang="ts">
  import PageCard from '$lib/components/PageCard.svelte';
</script>

<PageCard as="main">
  <div class="content">
    <h1>Settings</h1>
    <p>Coming soon.</p>
  </div>
</PageCard>

<style>
  .content {
    max-width: 900px;
    margin: 0 auto;
  }
</style>
```

- [ ] **Step 8: Update Login (`frontend/src/routes/login/+page.svelte`)**

```svelte
<script lang="ts">
  import PageCard from '$lib/components/PageCard.svelte';
</script>

<PageCard as="main">
  <div class="content">
    <h1>Sign in</h1>
    <p>
      Sign-in is coming soon. In the meantime, you can keep browsing Snippets, Albums, and
      Topics without an account.
    </p>
    <a href="/">Back to Home</a>
  </div>
</PageCard>

<style>
  .content {
    max-width: 900px;
    margin: 0 auto;
  }

  a {
    color: #1f6feb;
  }
</style>
```

- [ ] **Step 9: Update Learn list (`frontend/src/routes/learn/+page.svelte`)**

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import AlbumGrid from '$lib/components/AlbumGrid.svelte';
  import PageCard from '$lib/components/PageCard.svelte';
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

<PageCard as="main">
  <div class="content">
    <h1>Learn</h1>
    {#if loading}
      <p>Loading...</p>
    {:else if error}
      <p>{error}</p>
    {:else}
      <AlbumGrid {albums} />
    {/if}
  </div>
</PageCard>

<style>
  .content {
    max-width: 900px;
    margin: 0 auto;
  }
</style>
```

- [ ] **Step 10: Run the full test suite**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — all tests green (every page above is only smoke-tested for `/login` and `/learn`, which still export a default component).

- [ ] **Step 11: Verify it compiles**

Run (from `frontend/`): `npm run check`
Expected: 0 errors.

- [ ] **Step 12: Format and commit**

```bash
cd frontend
npx prettier --write \
  src/routes/+page.svelte \
  src/routes/topics/+page.svelte \
  src/routes/dashboard/+page.svelte \
  src/routes/forum/+page.svelte \
  src/routes/help/+page.svelte \
  src/routes/library/+page.svelte \
  src/routes/settings/+page.svelte \
  src/routes/login/+page.svelte \
  src/routes/learn/+page.svelte
git add \
  src/routes/+page.svelte \
  src/routes/topics/+page.svelte \
  src/routes/dashboard/+page.svelte \
  src/routes/forum/+page.svelte \
  src/routes/help/+page.svelte \
  src/routes/library/+page.svelte \
  src/routes/settings/+page.svelte \
  src/routes/login/+page.svelte \
  src/routes/learn/+page.svelte
git commit -m "feat: roll PageCard out to every single-column page"
```

---

### Task 11: `/learn/[id]` — sidebar + content row

**Files:**
- Modify: `frontend/src/routes/learn/[id]/+page.svelte`

**Context:** This is the one page that already renders a sidebar (`AlbumSidebar`, restyled in Task 7) alongside its content. It becomes the two-`PageCard`-as-flex-siblings row confirmed during brainstorming (`gap: var(--gap-inner)` between them, default flex `align-items: stretch` makes both cards match the row's height automatically — no extra CSS needed for that). The content side becomes a `PageCard` (`as="main"`) instead of a bare styled `<main>`, which also removes the nested-`<main>` markup this page previously had (its own `<main>` was nested inside the root layout's old `<main>` wrapper — now fixed at the source in Task 3, and this page only ever renders one `<main>` itself regardless).

- [ ] **Step 1: Replace `frontend/src/routes/learn/[id]/+page.svelte`**

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import AlbumSidebar from '$lib/components/AlbumSidebar.svelte';
  import PageCard from '$lib/components/PageCard.svelte';
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

{#if loading}
  <PageCard as="main">
    <p>Loading...</p>
  </PageCard>
{:else if error || !album}
  <PageCard as="main">
    <p>{error ?? 'Album not found.'}</p>
  </PageCard>
{:else}
  <div class="album-page">
    <AlbumSidebar sides={album.sides} activeSnippetId={null} />
    <PageCard as="main">
      <h1>{album.title}</h1>
      <p>{album.description}</p>
    </PageCard>
  </div>
{/if}

<style>
  .album-page {
    display: flex;
    gap: var(--gap-inner);
  }
</style>
```

- [ ] **Step 2: Run the full test suite**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — all tests green (`/learn/[id]` is only smoke-tested for exporting a default component).

- [ ] **Step 3: Verify it compiles**

Run (from `frontend/`): `npm run check`
Expected: 0 errors.

- [ ] **Step 4: Format and commit**

```bash
cd frontend
npx prettier --write "src/routes/learn/[id]/+page.svelte"
git add "src/routes/learn/[id]/+page.svelte"
git commit -m "feat: roll out sidebar+content PageCard row to /learn/[id]"
```

---

### Task 12: Full verification — contrast test + full suite

**Files:**
- Create: `frontend/src/lib/a11y-contrast.test.ts`

**Context:** This redesign moves several pieces of text from light-on-dark to dark-on-light. Per the spec's testing approach, contrast ratios must be calculated, not eyeballed. This task writes a small, dependency-free WCAG contrast-ratio calculator and asserts it against every colour pair this redesign introduced: Navbar/Footer/sidebar primary text (`#232f3e`) on white, the muted/secondary text (`#5a6472`) on white, and Footer's heading colour (`#a35200`) on white. All three were hand-calculated during planning (≈13.6:1, ≈6.0:1, ≈5.6:1 respectively) — this test makes that verification automated and repeatable instead of a one-off calculation.

- [ ] **Step 1: Write the contrast test**

Create `frontend/src/lib/a11y-contrast.test.ts`:

```ts
import { describe, it, expect } from 'vitest';

/** WCAG 2.x relative luminance + contrast ratio, no dependency. */
function hexToRgb(hex: string): [number, number, number] {
  const value = hex.replace('#', '');
  return [
    parseInt(value.slice(0, 2), 16),
    parseInt(value.slice(2, 4), 16),
    parseInt(value.slice(4, 6), 16),
  ];
}

function channelLuminance(value: number): number {
  const srgb = value / 255;
  return srgb <= 0.03928 ? srgb / 12.92 : Math.pow((srgb + 0.055) / 1.055, 2.4);
}

function relativeLuminance(hex: string): number {
  const [r, g, b] = hexToRgb(hex).map(channelLuminance);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrastRatio(hexA: string, hexB: string): number {
  const lighter = Math.max(relativeLuminance(hexA), relativeLuminance(hexB));
  const darker = Math.min(relativeLuminance(hexA), relativeLuminance(hexB));
  return (lighter + 0.05) / (darker + 0.05);
}

const WHITE = '#ffffff';
const AA_NORMAL_TEXT = 4.5;

describe('floating-card redesign text contrast on white panels', () => {
  it('primary text (#232f3e) meets WCAG AA on white', () => {
    expect(contrastRatio('#232f3e', WHITE)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT);
  });

  it('muted/secondary text (#5a6472) meets WCAG AA on white', () => {
    expect(contrastRatio('#5a6472', WHITE)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT);
  });

  it("Footer's heading colour (#a35200) meets WCAG AA on white", () => {
    expect(contrastRatio('#a35200', WHITE)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT);
  });
});
```

- [ ] **Step 2: Run it to verify it passes**

Run (from `frontend/`): `npm run test:unit -- --run`
Expected: PASS — all tests green, including the three new contrast assertions.

- [ ] **Step 3: Run the full verification suite**

Run (from `frontend/`):
```bash
npm run test:unit -- --run
npm run lint
npm run check
npm run story:build
rm -rf .histoire/dist
```
Expected: tests all PASS; lint reports 0 errors (pre-existing warnings in unrelated stub files are fine); `svelte-check` reports 0 errors; Histoire builds with no errors.

- [ ] **Step 4: Manual browser verification**

From `backend/`: ensure Postgres is migrated to head and seeded (`poetry run alembic upgrade head && poetry run python seed.py` if not already done). From `frontend/`: run `npm run dev`, open the reported local URL.

Verify:
- `/` (Home), `/topics`, `/help`, etc.: a single white floating card with square corners and a visible soft shadow, over a softly animated pastel gradient backdrop. Navbar and Footer are also white floating panels with matching shadows, aligned with the content card's left/right edges.
- `/learn`: the same single-card treatment, with a row of square AlbumCard tiles (black-outline cloud icon, title beneath) inside the card.
- `/learn/<id>`: two floating cards side by side — the white AlbumSidebar (with Sides/Snippets) on the left, the Album's title/description card on the right — both starting at the same height, both ending at the same height above the Footer.
- Refreshing the same page shows the same gradient colours each time; navigating to a different page shows a different (but still pastel) palette.
- No console errors in the browser. Reduced-motion: enabling "prefers reduced motion" in OS/browser settings stops the backdrop's drift animation.

- [ ] **Step 5: Format and commit**

```bash
cd frontend
npx prettier --write src/lib/a11y-contrast.test.ts
git add src/lib/a11y-contrast.test.ts
git commit -m "test: add WCAG contrast verification for the floating-card redesign's text colours"
```
