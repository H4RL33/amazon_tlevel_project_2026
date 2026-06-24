# Floating-card visual polish — design spec

**Date:** 2026-06-24
**Status:** Approved, ready for planning

## Why

The current UI is flat: a single cream background (`#f5f5f0`) behind plain content, a dark navy Navbar/Footer, and dark-navy sidebars (`AlbumSidebar`, `NavSidebar`). The team wants an AWS-console-style "floating card" visual language — content sits on white cards with soft shadows, floating over a colourful per-page pastel gradient backdrop — to give the prototype a more polished, distinctive feel ahead of the showcase demo. A mockup (`screencaps/polish_mockup.jpg`) anchors the intended look.

## Scope

This is a visual redesign touching shared layout primitives and every page, but it is one cohesive design language change, not several independent subsystems. It's planned and implemented as a single spec with a sequenced multi-task implementation plan.

**In scope:** global gutter/gap system, gradient backdrop, `PageCard` primitive, AlbumCard redesign, AlbumSidebar/NavSidebar/CTASidebar restyle, Navbar/Footer restyle, rollout to every existing page.

**Out of scope (explicitly deferred):**
- Full responsive/breakpoint design. This pass should avoid unnecessarily brittle fixed-pixel layouts where it's easy not to, so a future responsive refactor is easier — but no breakpoints or mobile layouts are implemented now.
- A new/transparent logo asset (current navy-background PNG logo is kept as-is; it will render as a navy badge on the new white Navbar, which is acceptable for now).
- Real enrolment/progress data on AlbumCard (it never had it — `progress` prop was always `null` from any real caller).

## Global spacing tokens

Two CSS custom properties drive every gap/inset in the new layout, so all panel-alignment constraints fall out of construction rather than needing hand-tuned per-component values:

- `--gap-inner: 1.5rem` — gap between vertically stacked sections (Navbar → content row → Footer), and gap between a sidebar card and its sibling content card within a row.
- `--gap-outer: 2.25rem` (1.5× `--gap-inner`) — outer page padding on all four viewport edges (top, bottom, left, right).

Because `--gap-outer` is applied uniformly on all four sides, and `--gap-inner` is applied uniformly to all internal gaps, the following all hold automatically:
- Left edges of Navbar, any sidebar card, and Footer are flush (same left gutter).
- Right edges of Navbar, content card, and Footer are flush (same right gutter).
- The gap above the Navbar (viewport top) equals the gap below the Footer (viewport bottom).
- A sidebar card's top edge aligns exactly with its sibling content card's top edge (both start after the same Navbar→row gap).

Define these as `:global` custom properties on `:root` (or `body`) in the root layout, so every component can reference them via `var(--gap-inner)` / `var(--gap-outer)`.

## `PageCard` component

New shared primitive: `frontend/src/lib/components/PageCard.svelte`.

- White (`#ffffff`) background, square corners (no `border-radius`), soft directional-blur drop shadow: `box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);` (the shadow style validated via mockup as "option C").
- Generous internal padding (e.g. `2rem`) between the card's content and its own border — distinct from the external `--gap-inner`/`--gap-outer` spacing between cards.
- Renders its content via a default slot. Accepts an optional prop to render as a different root element (`<main>` vs `<aside>` vs plain `<div>`) since both semantic content areas and sidebar panels reuse this component, but each page must end up with exactly one semantic `<main>` — see "Root layout" below.
- No fixed width by default — width is controlled by the parent flex/grid context (page-level layout decides single-card vs sidebar+content row).

This is also how sidebars get their styling: `AlbumSidebar`/`NavSidebar`/`CTASidebar` render inside (or are restyled as) a `PageCard`-equivalent surface — same white background, same omnidirectional shadow, same square corners — not a directional shadow. (Earlier in discussion a directional right-shadow was floated for sidebars; this was superseded — sidebars are fully floating with gaps on all sides, so they use the *same* omnidirectional shadow as content cards.)

## Root layout (`routes/+layout.svelte`)

Current bug to fix: the root layout wraps `<slot />` in its own `<main>`, and several pages (e.g. `/learn/[id]`) render *another* `<main>` inside that — nested `<main>` elements are invalid semantic HTML, a CLAUDE.md hard requirement. Fix: the root layout's wrapper becomes a plain non-semantic element (it exists only for the sticky-footer flex trick from the prior session's change), and each page keeps exactly one `<main>`, now styled via `PageCard`.

New responsibilities for the root layout:
1. Render the gradient backdrop layer (see below) as a `position: fixed`, full-viewport, lowest-`z-index` background.
2. Apply `--gap-outer` as padding on the outermost wrapper, and `--gap-inner` as the `gap` in a `flex-direction: column` stack containing Navbar, the routed page content (`<slot />`), and Footer.
3. Keep the existing sticky-footer behaviour (content area `flex: 1 0 auto`) from the prior session's change — still required so short pages don't leave the Footer floating mid-viewport.
4. Navbar and Footer become `PageCard`-styled (white, same omnidirectional shadow) full-width-within-gutter panels.

Each page's own markup is responsible for whether it renders one `PageCard` (single-column pages: Home, Topics list, Help, Library, Settings, Login, Forum) or two `PageCard`s as flex row siblings with `--gap-inner` between them (sidebar pages: Learn/[id] with `AlbumSidebar`, Topics with `NavSidebar`, Dashboard with `CTASidebar`).

## Gradient backdrop

New module: `frontend/src/lib/gradient.ts`.

- Pure function `getPagePalette(pathname: string): [string, string, string]` — deterministic per route (same path always yields the same palette, satisfying "stable per page, not jarring on refresh").
- Algorithm: hash `pathname` with a simple string hash (no crypto) to derive a base hue (0-360°). Derive two more hues via fixed offsets tuned for pleasant non-clashing combinations (roughly triadic, e.g. +110°/+220°, adjusted to avoid muddy combinations). Fix saturation (~55-65%) and lightness (~85-90%) identically across all three colours — this is the "soft pastel, AWS-console" mood validated in brainstorming, and keeps all three colours visually consistent in weight (no single blob reads darker/muddier than the others).
- Rendering: three large soft-edged `radial-gradient(circle at <x>% <y>%, <color>, transparent 60%)` layers stacked on the fixed backdrop `<div>`, positioned behind Navbar/content/Footer (lowest `z-index`).
- Animation: each blob's centre position (`cx`/`cy`, as CSS custom properties) drifts via independent `@keyframes` loops with different durations per blob (e.g. 28s/34s/40s) and `ease-in-out` timing, so the three blobs desync and never look mechanically synchronized. Pure CSS — no JS animation-frame loop, GPU/compositor-friendly.
- Respects `prefers-reduced-motion: reduce` (CLAUDE.md accessibility mandate): animation is disabled via a media query, falling back to the static (non-animated) gradient — the palette itself is unaffected, only the motion.
- Because cards are opaque white surfaces, the backdrop is purely decorative behind them — no WCAG contrast concern for card content. Navbar/Footer text contrast is evaluated against their own white surface, not the backdrop.

## `AlbumCard` redesign

- Square tile, ~190px, using the shared `PageCard` shadow style (white background, square corners, `box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35)`).
- Content: a centred 60px simple black-outline (`stroke="#232f3e"`, no fill) SVG cloud icon, with the Album title beneath it (bold, ~0.95rem, centred, wraps to 2 lines if needed).
- Description and the `progress` prop/`ProgressBar` usage are removed entirely from the card face — description still appears on the Album detail page (`/learn/[id]`); `progress` was always `null` from every real caller today, so removing it is not a behaviour regression.
- Icon sourcing: inline SVG via an `ICONS: Record<string, string>`-style map keyed by `album.icon` (replacing the current emoji `ICONS` map) — no new icon-library dependency, since only one real icon ("cloud") exists today and inline SVG keeps this simple to extend later.

`AlbumGrid` changes its CSS grid from wide-row columns (`minmax(280px, 1fr)`) to fixed tile sizing (`repeat(auto-fill, minmax(190px, 190px))` or equivalent), so it reads as a row of tiles rather than a stretched list, with `--gap-inner` (or a similarly-scaled grid gap) between tiles.

## Sidebars (`AlbumSidebar`, `NavSidebar`, `CTASidebar`)

All three:
- Switch from dark navy (`#0a2540`) to the white `PageCard` surface, same omnidirectional shadow, square corners.
- Recolour text/links from light-on-dark to dark-on-light (`#232f3e` primary, a muted grey for secondary text) — verify WCAG AA contrast ratios for both default and active/hover link states against the new white background (this is a real accessibility-relevant change, not just a re-skin).
- Height: the sidebar's container spans the full height of its row (i.e. matches its sibling content `PageCard`'s height via flex `align-items: stretch` / equal-height row), which in turn spans from the Navbar→row gap down to the row→Footer gap — so its rendered top edge aligns with the content card's top edge, and its bottom edge sits at the same `--gap-inner` distance above the Footer as the content card's bottom edge.
- Sticky content: the sidebar's inner nav-list content uses `position: sticky` (with an appropriate `top` offset) within that full-height container, so it stays in view while a taller sibling content card scrolls, but never overlaps the Footer (bounded by its own container's height).

`AlbumSidebar`/`NavSidebar` width increases ~20%: `240px → 288px`. `CTASidebar` keeps its existing wider sizing (~320px, since it holds more content per product direction) and gets the colour/shadow/height/sticky treatment but not the nav-sidebar-specific +20% width bump.

## Navbar / Footer

- Both switch from dark navy full-bleed bars to white `PageCard`-styled floating panels: same background, same square corners, same omnidirectional shadow as content cards, inset by `--gap-outer` from the viewport edges (left/right) and separated from the content row by `--gap-inner` (top/bottom respectively).
- `NavLink` text colour changes from white to dark (`#232f3e`) for contrast against the new white background; the existing orange-yellow gradient underline accent is unaffected.
- Footer's column headings/links and `bottom-bar` copyright text get the equivalent dark-on-light recolour.
- The existing navy `#232f3e` logo PNG (`static/assets/logo.png`) is kept unchanged — it has an opaque navy background baked into the image itself, so on the new white Navbar it will render as a small navy "badge" rather than blending in. This is accepted as-is for this pass (no new transparent/light logo asset is being created now).

## Responsive note (non-binding for this pass)

No breakpoints or mobile layout are implemented in this pass. Where it doesn't conflict with the design above, prefer relative units (`rem`, `%`, `fr`, flexible `minmax()` tracks) over hard-coded pixel values, and avoid layout decisions that would be unnecessarily awkward to make responsive later (e.g. avoid baking in assumptions that exactly two `PageCard`s always fit side-by-side at any viewport width). This is a soft guideline for this pass, not a requirement to build responsive behaviour now.

## Testing approach

- Unit tests for `lib/gradient.ts`: same pathname → same palette across repeated calls; different pathnames → (almost certainly) different palettes; derived hue/saturation/lightness values stay within the defined pastel band.
- `npm run check` continues to report 0 type errors; existing component smoke tests (`shell.test.ts` etc.) continue passing, updated where component props/markup change (e.g. `AlbumCard` losing its `progress` prop).
- Manual WCAG AA contrast verification for the new dark-on-white Navbar/Footer/sidebar text and link states — calculated, not eyeballed.
- Manual visual verification via the dev server across a representative sample of page types (a single-`PageCard` page, e.g. `/`, and a sidebar+content page, e.g. `/learn/[id]`), since this is a primarily visual change that automated tests can't meaningfully assert on.

## Implementation sequencing (for the planning phase)

Recommended task order for the implementation plan (each independently committable and reviewable):
1. Global spacing tokens + `PageCard` component (no rollout yet).
2. `lib/gradient.ts` + backdrop layer, wired into the root layout (fixes the nested-`<main>` bug at the same time).
3. Navbar / Footer restyle.
4. `AlbumCard` + `AlbumGrid` redesign.
5. `AlbumSidebar` restyle (white surface, sticky content, +20% width).
6. `NavSidebar` restyle (same treatment).
7. `CTASidebar` restyle (same treatment, existing wider sizing kept).
8. Per-page rollout: convert every remaining page's bare `<main>` to `PageCard` usage (Home, Topics, Help, Library, Settings, Login, Forum, Dashboard, Learn list, Learn detail).
9. Full local verification (tests, lint, type-check, contrast check, manual browser pass).
