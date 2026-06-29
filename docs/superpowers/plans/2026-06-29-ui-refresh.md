# UI Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compact the Navbar, move the Footer below the viewport, fix spurious PageCard scrolling, right-size CTASidebar album cards, and eliminate backdrop animation GPU cost on all pages except the unauthenticated home.

**Architecture:** All changes are in the SvelteKit frontend. The shell layout in `+layout.svelte` is restructured (Footer moves outside the 100dvh shell; backdrop CSS is rewritten). Individual components (`Navbar`, `CTASidebar`, `Footer`) receive targeted prop/style changes. No backend changes.

**Tech Stack:** SvelteKit 2 / Svelte 4 + TypeScript. Typecheck: `cd frontend && npm run check`. Tests: `cd frontend && npx vitest run`. Lint: `cd frontend && npm run lint`.

**Spec:** `docs/superpowers/specs/2026-06-29-ui-refresh-design.md`

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `frontend/src/routes/+layout.svelte` | Shell height, Footer position, body height, backdrop CSS |
| Modify | `frontend/src/lib/components/Navbar.svelte` | Height 64→48px, logo 40→28px |
| Modify | `frontend/src/lib/components/CTASidebar.svelte` | Sidebar width 320→280px, album-slot max-height 90px |
| Modify | `frontend/src/lib/components/Footer.svelte` | Add overflowY="hidden", fix stale NavLinks |
| Modify | `frontend/src/routes/learn/+page.svelte` | Add overflowY="hidden" to section heading PageCards |
| Modify | `frontend/src/routes/t-levels/[slug]/+page.svelte` | Add overflowY="hidden" to section heading PageCards |

---

## Task 1: Compact Navbar

**Files:**
- Modify: `frontend/src/lib/components/Navbar.svelte`

Read the file first.

- [ ] **Step 1: Reduce nav-inner height and logo size**

In `frontend/src/lib/components/Navbar.svelte`, find:

```css
  .nav-inner {
    display: flex;
    align-items: center;
    height: 64px;
    width: 100%;
  }
```

Replace with:

```css
  .nav-inner {
    display: flex;
    align-items: center;
    height: 48px;
    width: 100%;
  }
```

Then find:

```css
  .logo {
    height: 40px;
  }
```

Replace with:

```css
  .logo {
    height: 28px;
  }
```

- [ ] **Step 2: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: Run tests**

```bash
cd frontend && npx vitest run
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/components/Navbar.svelte
git commit -m "style: compact Navbar height 64→48px"
```

---

## Task 2: Fix overflowY on short PageCards + Footer NavLinks

Short fixed-height cards must not show scroll affordances. The Footer also has stale nav links.

**Files:**
- Modify: `frontend/src/lib/components/Footer.svelte`
- Modify: `frontend/src/routes/learn/+page.svelte`
- Modify: `frontend/src/routes/t-levels/[slug]/+page.svelte`

- [ ] **Step 1: Fix Footer**

In `frontend/src/lib/components/Footer.svelte`, find:

```svelte
<PageCard as="footer" padding="2rem 1.5rem 0">
```

Replace with:

```svelte
<PageCard as="footer" padding="2rem 1.5rem 0" overflowY="hidden">
```

While in the file, fix the stale NavLinks. Find:

```svelte
        <NavLink href="/topics" label="Topics" />
        <NavLink href="/dashboard" label="Dashboard" />
```

Replace with:

```svelte
        <NavLink href="/t-levels" label="T-Levels" />
        <NavLink href="/" label="Home" />
```

- [ ] **Step 2: Fix section heading PageCards in /learn**

In `frontend/src/routes/learn/+page.svelte`, find (there may be one or more instances):

```svelte
            <PageCard padding="0.875rem 1.25rem">
              <h2 class="section-heading">{section.heading}</h2>
            </PageCard>
```

Replace with:

```svelte
            <PageCard padding="0.875rem 1.25rem" overflowY="hidden">
              <h2 class="section-heading">{section.heading}</h2>
            </PageCard>
```

- [ ] **Step 3: Fix section heading PageCards in /t-levels/[slug]**

In `frontend/src/routes/t-levels/[slug]/+page.svelte`, find:

```svelte
            <PageCard padding="0.875rem 1.25rem">
              <h2 class="section-heading">{section.heading}</h2>
            </PageCard>
```

Replace with:

```svelte
            <PageCard padding="0.875rem 1.25rem" overflowY="hidden">
              <h2 class="section-heading">{section.heading}</h2>
            </PageCard>
```

- [ ] **Step 4: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 5: Run tests**

```bash
cd frontend && npx vitest run
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/components/Footer.svelte frontend/src/routes/learn/+page.svelte "frontend/src/routes/t-levels/[slug]/+page.svelte"
git commit -m "fix: overflowY=hidden on short PageCards, fix stale Footer nav links"
```

---

## Task 3: CTASidebar AlbumCard sizing

**Files:**
- Modify: `frontend/src/lib/components/CTASidebar.svelte`

- [ ] **Step 1: Reduce sidebar width**

In `frontend/src/lib/components/CTASidebar.svelte`, find:

```svelte
<PageCard as="aside" width="320px" padding="1.5rem" overflowY="visible">
```

Replace with:

```svelte
<PageCard as="aside" width="280px" padding="1.5rem" overflowY="visible">
```

- [ ] **Step 2: Cap album-slot height**

In the same file, find:

```css
  .album-slot {
    flex: 1;
    min-width: 0;
    aspect-ratio: 1;
  }
```

Replace with:

```css
  .album-slot {
    flex: 1;
    min-width: 0;
    aspect-ratio: 1;
    max-height: 90px;
  }
```

- [ ] **Step 3: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 4: Run tests**

```bash
cd frontend && npx vitest run
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/components/CTASidebar.svelte
git commit -m "style: reduce CTASidebar width to 280px, cap album cards at 90px"
```

---

## Task 4: Backdrop animation performance

This task rewrites the CSS-only section of `+layout.svelte`. The Svelte template is unchanged.

**Files:**
- Modify: `frontend/src/routes/+layout.svelte`

- [ ] **Step 1: Update blob base styles**

In `frontend/src/routes/+layout.svelte`, find:

```css
  .blob {
    position: absolute;
    width: 70vmax;
    height: 70vmax;
    border-radius: 50%;
    filter: blur(40px);
    opacity: 0.6;
    will-change: transform;
  }
```

Replace with:

```css
  .blob {
    position: absolute;
    width: 85vmax;
    height: 85vmax;
    border-radius: 50%;
    filter: blur(20px);
    opacity: 0.6;
  }
```

- [ ] **Step 2: Remove drift animations from blob-a/b/c**

Find:

```css
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
```

Replace with (positions unchanged, animations removed):

```css
  .blob-a {
    top: -15%;
    left: -15%;
  }

  .blob-b {
    top: -10%;
    right: -20%;
  }

  .blob-c {
    bottom: -20%;
    left: 15%;
  }
```

- [ ] **Step 3: Add morphing-scoped drift (home unauthenticated only)**

After the `.blob-c` rule, add:

```css
  .layer.morphing .blob {
    will-change: transform;
  }

  .layer.morphing .blob-a {
    animation: drift-a 28s ease-in-out infinite;
  }

  .layer.morphing .blob-b {
    animation: drift-b 34s ease-in-out infinite;
  }

  .layer.morphing .blob-c {
    animation: drift-c 40s ease-in-out infinite;
  }
```

- [ ] **Step 4: Remove morph-hue from .layer.morphing**

Find:

```css
  .layer.morphing {
    animation: morph-hue 8s linear infinite;
  }
```

Replace with (remove the animation, keep the class selector in case other rules reference it — but there are none so delete the rule entirely):

Delete this entire rule block.

- [ ] **Step 5: Remove the @keyframes morph-hue block**

Find and delete:

```css
  @keyframes morph-hue {
    from {
      filter: hue-rotate(0deg);
    }
    to {
      filter: hue-rotate(360deg);
    }
  }
```

- [ ] **Step 6: Remove the HiDPI media query**

Find and delete the entire block:

```css
  /* Reduce blur on HiDPI displays — physical pixels are smaller so 40px GPU blur
     covers a proportionally huge area at 4K, hammering the compositor. */
  @media (min-resolution: 2dppx) {
    .blob {
      filter: blur(20px);
    }

    .layer.morphing {
      animation: none;
    }
  }
```

This block is no longer needed: blur is universally 20px and `morph-hue` is gone.

- [ ] **Step 7: Verify prefers-reduced-motion still covers morphing blobs**

Find the existing `prefers-reduced-motion` block and confirm it reads:

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

The `.blob { animation: none }` rule already covers the `.layer.morphing .blob-a/b/c` animations we added in Step 3 (CSS specificity: `.blob` selector inside a media query overrides `.layer.morphing .blob-a` outside it — but to be safe, add an explicit rule). Replace with:

```css
  @media (prefers-reduced-motion: reduce) {
    .blob,
    .layer.morphing .blob-a,
    .layer.morphing .blob-b,
    .layer.morphing .blob-c {
      animation: none;
    }

    .layer {
      transition: none;
    }
  }
```

- [ ] **Step 8: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 9: Run tests**

```bash
cd frontend && npx vitest run
```

Expected: all tests pass.

- [ ] **Step 10: Commit**

```bash
git add frontend/src/routes/+layout.svelte
git commit -m "perf: static blobs on all pages, drift scoped to home unauthenticated only"
```

---

## Task 5: Footer below viewport — layout restructure

**Files:**
- Modify: `frontend/src/routes/+layout.svelte`

- [ ] **Step 1: Move Footer outside the shell**

In `frontend/src/routes/+layout.svelte`, find the template section:

```svelte
<div
  class="shell"
  style="--page-p0: {layers[activeIndex].palette[0]}; --page-p1: {layers[activeIndex].palette[1]};"
>
  <Navbar />
  <div class="content">
    <slot />
  </div>
  <Footer />
</div>
```

Replace with:

```svelte
<div
  class="shell"
  style="--page-p0: {layers[activeIndex].palette[0]}; --page-p1: {layers[activeIndex].palette[1]};"
>
  <Navbar />
  <div class="content">
    <slot />
  </div>
</div>
<Footer />
```

- [ ] **Step 2: Switch shell to 100dvh**

In the CSS, find:

```css
  .shell {
    position: relative;
    display: flex;
    flex-direction: column;
    height: 100vh;
    box-sizing: border-box;
    padding: var(--gap-outer);
    gap: var(--gap-inner);
  }
```

Replace with:

```css
  .shell {
    position: relative;
    display: flex;
    flex-direction: column;
    height: 100dvh;
    box-sizing: border-box;
    padding: var(--gap-outer);
    gap: var(--gap-inner);
  }
```

- [ ] **Step 3: Unclamp body height**

Find:

```css
  :global(html, body) {
    height: 100%;
  }
```

Replace with:

```css
  :global(html) {
    min-height: 100%;
  }
```

Removing `height: 100%` from `body` allows the body to grow beyond the viewport when the footer is present, enabling the browser's native scroll to reveal it.

- [ ] **Step 4: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 5: Run tests**

```bash
cd frontend && npx vitest run
```

Expected: all tests pass.

- [ ] **Step 6: Run lint**

```bash
cd frontend && npm run lint
```

Expected: 0 errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/routes/+layout.svelte
git commit -m "feat: move Footer below viewport, switch shell to 100dvh"
```

---

## Task 6: Final verification

- [ ] **Step 1: Full typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 2: Full test suite**

```bash
cd frontend && npx vitest run
```

Expected: all tests pass.

- [ ] **Step 3: Manual browser check**

Start the app:

```bash
docker compose up --build -d
```

Open http://localhost:3000 and verify:

- Navbar height is noticeably shorter than before (~48px)
- On any page: the footer is not visible on load; scrolling the body reveals it
- The bottom of the last content card ends with correct outer gap before the viewport edge
- On `/` logged out: backdrop blobs drift gently
- On `/learn` or `/t-levels`: backdrop blobs are static (no drift)
- On a mid-range device or with browser throttling (Chrome DevTools → Performance → CPU 4× slowdown): animation is smooth on home; no jank on other pages
- CTASidebar (logged in, on `/`): two album cards side-by-side, visibly smaller than before (~90px tall)
- Section heading cards on `/learn` and `/t-levels/[slug]`: no scroll indicator on hover
