# Frontend Skeleton Design

> **Status:** Approved

## Goal

Implement an initial skeleton frontend shell — navbar, footer, and blank placeholder pages — in Amazon's brand style, with no real application content yet.

## Architecture

Root `+layout.svelte` wraps every page with `<Navbar />`, a `<slot />` for page content, and `<Footer />`. A shared `NavLink.svelte` component is used by both navbar and footer so hover animations and styling stay consistent. No authenticated shell (`AppShell.svelte`) is touched — that is reserved for a later feature.

## Tech Stack

- SvelteKit + TypeScript
- CSS (scoped `<style>` blocks, no external CSS framework)
- Google Fonts — Ubuntu (400, 700)

---

## File Structure

```
frontend/src/
├── app.html                          — add Google Fonts <link>
├── routes/
│   ├── +layout.svelte                — root layout: Navbar + slot + Footer + global styles
│   ├── +page.svelte                  — Home placeholder
│   ├── learn/+page.svelte            — Learn placeholder
│   ├── topics/+page.svelte           — Topics placeholder
│   └── dashboard/+page.svelte        — Dashboard placeholder
└── lib/
    └── components/
        ├── NavLink.svelte            — shared animated link component
        ├── Navbar.svelte             — logo left, links right
        └── Footer.svelte             — three-column footer
```

Static asset: `frontend/static/assets/logo.png` — copy from repo root `assets/logo.png`.

Existing stubs (`AppShell.svelte`, `Sidebar.svelte`, all `lib/api/*`, `lib/stores/*`) are left untouched.

---

## Section 1 — NavLink Component

**File:** `src/lib/components/NavLink.svelte`

**Props:**
- `href: string` — link destination
- `label: string` — visible text

**Behaviour:** Renders an `<a>` tag. On hover, an animated gradient underline grows in from the left with ease-in-out timing.

**Animation spec:**
- `::after` pseudo-element, `position: absolute`
- `bottom: -0.3em` — gap between text baseline and underline top
- `height: 0.15em` — scales with font size
- `border-radius: 9999px` — rounded/pill ends
- `background: linear-gradient(to right, #ff9900, #ffd700)` — orange to yellow
- `transform: scaleX(0)` → `scaleX(1)` on hover
- `transform-origin: left`
- `transition: transform 0.3s ease-in-out`
- Parent `<a>`: `position: relative; display: inline-block`

---

## Section 2 — Navbar

**File:** `src/lib/components/Navbar.svelte`

**Layout:** Fixed-height (`64px`), full width, `display: flex; align-items: center`. Logo pinned left, nav links right-aligned via `margin-left: auto` on the link group.

**Colours:** Background `#232f3e`, text `#ffffff`.

**Logo:** `<img src="/assets/logo.png" alt="T Level Placements at Amazon" />` wrapped in an `<a href="/">`. Image height constrained to ~40px.

**Links (in order):** Home (`/`), Learn (`/learn`), Topics (`/topics`), Dashboard (`/dashboard`) — each rendered as `<NavLink />`.

**Spacing:** `1.5rem` horizontal padding on the navbar container; `1.5rem` gap between nav links.

---

## Section 3 — Footer

**File:** `src/lib/components/Footer.svelte`

**Layout:** Same `#232f3e` background. Three equal columns via CSS Grid (`grid-template-columns: repeat(3, 1fr)`). `2rem` padding top/bottom, `1.5rem` horizontal padding.

**Columns:**

| Column | Heading | Links |
|--------|---------|-------|
| Navigation | Navigation | Home, Learn, Topics, Dashboard — each a `<NavLink />` |
| About | About | About This Project, T-Level Programme |
| Support | Support | Help, Contact Us |

Column headings: uppercase, `0.75rem` letter-spacing, `0.85rem` font size, `#ff9900` colour.

**About/Support links:** Plain `<NavLink />` — no real destinations yet, `href="#"` as placeholder.

**Bottom bar:** A thin `1px` `rgba(255,255,255,0.15)` border-top below the columns, with a centred copyright line: `© 2026 Amazon T-Level Project`.

---

## Section 4 — Root Layout & Global Styles

**File:** `src/routes/+layout.svelte`

Renders: `<Navbar /> <slot /> <Footer />`.

Global `<style>` block (`:global`):
- `font-family: 'Ubuntu', sans-serif`
- `body`: `margin: 0; background: #f5f5f0; color: #232f3e`
- Box-sizing reset

**File:** `src/app.html`

Add inside `<head>`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;700&display=swap" rel="stylesheet" />
```

---

## Section 5 — Placeholder Pages

Each page renders a `<main>` with a heading and a short "coming soon" paragraph. No real content.

| Route | Heading |
|-------|---------|
| `/` | Home |
| `/learn` | Learn |
| `/topics` | Topics |
| `/dashboard` | Dashboard |

**Shared page style:** `max-width: 900px; margin: 4rem auto; padding: 0 1.5rem`.

---

## What Is NOT in Scope

- Authentication or protected routes
- Any real data or API calls
- Mobile hamburger menu (deferred — navbar links wrap gracefully at narrow widths for now)
- `AppShell.svelte` or `Sidebar.svelte` changes
