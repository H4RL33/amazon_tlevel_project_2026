# UI Refresh — Layout, Performance & Consistency Design Spec

**Date:** 2026-06-29  
**Scope:** Layout restructure, backdrop animation performance, navbar compaction, CTASidebar card sizing, PageCard scroll consistency

---

## Goals

1. **Fit the initial viewport** — remove the Footer from the 100dvh shell so the viewport contains only Navbar + content, with the Footer accessible by scrolling the body.
2. **Reduce animation GPU cost** — backdrop blobs are expensive on low/mid-range devices. Remove per-frame compositing on all pages except the unauthenticated home.
3. **Compact the Navbar** — reclaim 16px of vertical space.
4. **Right-size CTASidebar album cards** — two side-by-side cards at 90×90px instead of 124×124px.
5. **Eliminate spurious scroll affordances** — short fixed-height PageCards (section headings, Footer) must not show scroll indicators.

---

## 1. Layout Restructure (Footer below viewport)

### Approach

Keep the current `100dvh` shell with its inner-scrolling `.content` area (Option B). Move `<Footer />` outside the `.shell` div in `+layout.svelte` so it sits below the viewport in the DOM. Body scroll reveals it.

### Changes

**`frontend/src/routes/+layout.svelte`**

- Shell: `height: 100vh` → `height: 100dvh` (accounts for mobile browser chrome bar).
- `:global(html, body) { height: 100% }` → `html` keeps `min-height: 100%`; remove `height: 100%` from `body`. Clamping body to exactly the viewport height clips the footer from being scrollable.
- Move `<Footer />` from inside `.shell` to after it in the template. The shell's existing `padding-bottom: var(--gap-outer)` already provides the correct bottom gap for content before the viewport edge — no change needed there.

**`frontend/src/lib/components/Footer.svelte`**

- Add `overflowY="hidden"` to the `<PageCard>` — the footer never needs internal scrolling.

### Acceptance

- On any page, the footer is not visible on initial load; scrolling the browser window reveals it.
- The bottom edge of the last content card/sidebar ends `var(--gap-outer)` above the viewport bottom.
- Mobile (Safari): no layout shift from the address bar.

---

## 2. Navbar Compact

**`frontend/src/lib/components/Navbar.svelte`**

- `.nav-inner { height: 64px }` → `height: 48px`
- `.logo { height: 40px }` → `height: 28px`

No structural changes. The 16px reduction gives back meaningful vertical real estate on 768–1080px displays.

---

## 3. CTASidebar AlbumCard Sizing

**`frontend/src/lib/components/CTASidebar.svelte`**

The side-by-side layout is already correct (`.album-row` with `flex-direction: row`). Two changes:

- `PageCard width="320px"` → `width="280px"` — reduces the sidebar footprint.
- `.album-slot`: add `max-height: 90px`. This caps each card at 90px tall, overriding the `aspect-ratio: 1` expansion that currently makes slots fill available height.

Effective card size: `(280px − 2×24px padding − 24px gap) / 2 = 104px wide`, `90px tall`.

---

## 4. Fix Spurious Scroll on Short PageCards

PageCard defaults to `overflowY="auto"`. Short fixed-height cards that never need internal scrolling must use `overflowY="hidden"` to suppress the scroll affordance.

**Affected call sites:**

| File | Element | Fix |
|------|---------|-----|
| `frontend/src/routes/learn/+page.svelte` | `<PageCard padding="0.875rem 1.25rem">` wrapping `<h2>` | Add `overflowY="hidden"` |
| `frontend/src/routes/t-levels/[slug]/+page.svelte` | Same pattern | Add `overflowY="hidden"` |
| `frontend/src/lib/components/Footer.svelte` | Root `<PageCard>` | Add `overflowY="hidden"` (also covers item 1 above) |

The Navbar already has `overflowY="visible"` (required for the NavBarAvatar dropdown) — no change.

---

## 5. Backdrop Animation Performance

### Root causes

| Cause | Cost |
|-------|------|
| `morph-hue` keyframe (`filter: hue-rotate`) on home unauthenticated | Forces full layer re-rasterisation every frame — most expensive |
| `filter: blur(40px)` on three 70vmax elements that are also `transform`-animated | Blur must re-run on every frame for each animated blob |
| `will-change: transform` on all 6 blobs (2 layers × 3) at all times | Promotes all blobs to GPU layers even on pages with no animation |

### Changes

**`frontend/src/routes/+layout.svelte`** — CSS section:

**Blob base styles (all pages):**
- Size: `70vmax` → `85vmax` — larger blobs compensate for reduced blur radius, maintaining full backdrop coverage.
- Blur: `filter: blur(40px)` → `filter: blur(20px)` universally.
- Remove `will-change: transform` from `.blob`.
- Remove drift keyframe animations (`drift-a`, `drift-b`, `drift-c`) from `.blob-a`, `.blob-b`, `.blob-c`.

**Home unauthenticated only (`.layer.morphing .blob`):**
- Re-add `will-change: transform` scoped to `.layer.morphing .blob`.
- Re-add drift animations scoped to `.layer.morphing .blob-a/b/c` (same durations: 28s, 34s, 40s).

**Remove entirely:**
- `morph-hue` keyframe and its `animation` on `.layer.morphing` — replaced by the blob drift, which provides sufficient engagement without the hue-rotate cost.
- The `@media (min-resolution: 2dppx)` block that reduced blur and killed `morph-hue` on HiDPI — no longer needed since blur is universally 20px and `morph-hue` is removed.

**`prefers-reduced-motion`** — existing rule already covers both blob animation and layer transition; no change needed.

### Result

| Scenario | Animations running |
|----------|-------------------|
| Any page (authenticated or not) except home-guest | Zero — static blobs, cheap opacity crossfade on navigation |
| Home, unauthenticated | 3 blob drift transforms, GPU-promoted, no blur recompute because blobs aren't transformed on-screen (wait — see note) |

> **Note on blur + transform:** `filter: blur()` on a `will-change: transform` element still means the browser blurs the layer once (at paint time) and then composites it via transform. The blur does not re-run on every frame when only `transform` changes — only the composite step runs. So the drift on home is cheap: one-time blur paint + per-frame compositing.

---

## Footer NavLinks (housekeeping)

The Footer currently links to `/topics` and `/dashboard` — both removed routes. Update to `/t-levels` and `/` respectively while making the other changes.

---

## Non-Goals

- No changes to page-level layout patterns, routing, or data fetching.
- No responsive/mobile breakpoints (out of scope for this pass).
- No changes to colour tokens or the palette system.
