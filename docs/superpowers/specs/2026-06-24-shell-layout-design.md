# Shell & Layout Architecture — design spec

Date: 2026-06-24

## Context

This is chapter 1 of the
[frontend masterplan](2026-06-24-frontend-masterplan.md) — foundational, since
every later chapter needs the public/authenticated layout question settled before
it can place its pages anywhere.

The masterplan's original framing assumed a two-layout split: a public layout
(`Navbar` + `slot` + `Footer`, already built in the
[2026-06-17 skeleton chapter](2026-06-17-frontend-skeleton-design.md)) and a
separate authenticated layout wrapping pages in `AppShell.svelte` (a two-column grid
with a persistent `NavSidebar`). Reviewing the actual component stubs while
designing this chapter surfaced a conflict with that assumption:

- `NavSidebar.svelte` is already implemented (not a stub) — but as a *global* app
  sidebar (topic links, a Dashboard link, user info, a Settings link), not the
  contextual "section nav for a long page" role `AlbumSidebar` and `SettingsNav`
  already occupy.
- `NavBarAvatar.svelte`'s doc comment describes a dropdown (Dashboard/Settings/Help)
  meant to live in the top `Navbar` — overlapping with what `NavSidebar` already
  does.

Resolved during brainstorming: sidebars in this app are for in-page section nav
(Settings sections, an Album's Sides, a Topic list), not global app navigation.
Global navigation belongs to one `Navbar`, present on every page, public and
authenticated alike. This eliminates the need for `AppShell` and any route-group
split entirely — there is one layout for the whole app.

## Architecture

**One root layout, no route groups.** Every route continues to use the existing
`src/routes/+layout.svelte` (`Navbar` + `slot` + `Footer`) — nothing changes here
structurally. `AppShell.svelte` is deleted; it's fully superseded by this decision
and was never wired into any route.

**`Navbar`** gains two things:

1. A `Library` link, added to the existing `Home`/`Learn`/`Topics`/`Dashboard` set
   (order: Home, Learn, Topics, Library, Dashboard). All links are always visible
   regardless of auth state — Library and Dashboard require an account, but rather
   than hiding the links for anonymous visitors, their `href` is computed reactively:
   `$currentUser ? '/library' : '/login'` (same pattern for Dashboard). This needs no
   changes to `NavLink` itself — `Navbar` just passes a different `href`.
2. An auth slot at the **end** of the existing `.links` flex group (which already has
   `margin-left: auto`, pushing the whole group — and now this slot too — to the far
   right of the header, after the nav links, not mixed in with the logo on the left).
   Renders `<NavBarAvatar user={$currentUser} />` when `$currentUser` is non-null,
   otherwise a "Log in" link/button to `/login`.

**Contextual section-nav sidebars** (`NavSidebar`, `SettingsNav`, `AlbumSidebar`) are
composed inline by whichever page needs them — not by a wrapping layout. This
chapter narrows `NavSidebar`'s contract (see below) since it's the component that
surfaced the issue, but does **not** wire it into `/topics` or `/learn` — that's
Chapter 2 (Public Browsing)'s job, once those pages actually exist.

## Component changes

### `Navbar.svelte`

Add `Library` to the link list. Add the conditional avatar/login slot as the last
child of `.links`, so it inherits the existing right-alignment.

### `NavBarAvatar.svelte`

Implement fully: avatar circle (image if available, else initials on a coloured
circle, per its existing doc comment), click toggles a dropdown, outside-click or
Escape closes it. Dropdown items: **Dashboard** (`/dashboard`), **Settings**
(`/settings`), **Help** (`/help`) — three items, not four. The original doc comment
listed "Account Settings" and "App Settings" as separate entries both pointing at
`/settings`; collapsed into one `Settings` link since the underlying destination is
identical (any internal section distinction is `/settings`'s own concern, via
`SettingsNav`, not a nav-dropdown concern).

### Login link (new, inline in `Navbar`, no new component)

When `$currentUser` is `null`, render `<NavLink href="/login" label="Log in" />` in
the auth slot instead of `NavBarAvatar` — reuses the existing, already-implemented
`NavLink` (same hover-underline treatment as the other nav links) rather than
introducing a dependency on `Button.svelte`, which is still an unimplemented stub.

### New route: `/login`

A minimal placeholder page (e.g. "Sign in coming soon"). Exists purely so the
Library/Dashboard/avatar-slot redirect logic has a real destination to navigate to.
The actual Cognito login flow is out of scope here — it belongs to the backend and
frontend Auth & Identity chapters, which will replace this page's contents later
without needing to change anything that links to `/login`.

### `NavSidebar.svelte` (narrowed contract, not wired up yet)

Trim props to `topics: TopicResponse[]` and `activePath: string` — remove the `user`
prop entirely. Trim markup to just: the topic links list with active-state
highlighting (keep the existing `accent_colour`-on-hover/active styling). Remove the
Dashboard link, the user-info block, and the Settings link — those are now owned by
`Navbar`/`NavBarAvatar`. The component is not composed into any route by this
chapter; it's left ready for Chapter 2 to actually use on `/topics` and `/learn`.

### `HelpPanel.svelte`

Implement its existing doc comment as specified: a static, hardcoded FAQ list,
card-style layout (question as heading, answer as body text below it). No API/CMS
integration — that's an explicit "TODO: decide" in the original stub, and a static
list is sufficient for now.

### `/help/+page.svelte`

Render `<HelpPanel />`. This route already exists as a placeholder; this chapter
fills it in.

### `AppShell.svelte`

Deleted. It was never imported by any route, so removing it has no callers to
update.

## Data flow

Auth state comes from the existing `currentUser` writable store
(`$lib/stores/user.ts`), already defined, currently always `null` since nothing
sets it yet (real Cognito sync is a later backend/frontend Auth chapter). Every
component in this chapter just reacts to whatever's in that store — testing sets the
store directly to simulate logged-in vs logged-out, the same pattern the store's own
doc comment already implies ("Set after `/auth/sync` succeeds").

## Testing

Per the earlier decision in this project to skip adding a DOM-rendering test layer
(`@testing-library/svelte`/jsdom) for now, this chapter follows the existing
"does it compile and export a default" pattern in `src/lib/scaffold.test.ts` for the
new/changed pieces (`Navbar`, `NavBarAvatar`, `HelpPanel`, the `/login` page) — not
real rendering/interaction tests. Real visual/behavioural verification happens via
Histoire (a `.story.svelte` for each finished component, covering the logged-in,
logged-out, and dropdown-open states where relevant) and manual checking in the
running app.

A plain test confirms `AppShell.svelte` no longer exists at its old path, as a
regression guard against it being silently reintroduced.

## Out of scope (deferred to later chapters)

- Wiring `NavSidebar` into actual `/topics` or `/learn` pages — Chapter 2 (Public
  Browsing).
- `SettingsNav` and `AlbumSidebar` implementation/wiring — Chapters 2 and 5.
- `AgeGateNotice` integration — moved to Chapter 6 (The Forum), since there's no
  shell-level hook for it anymore now that `AppShell` is gone; it's naturally a
  `/forum` page-level concern.
- The real Cognito login flow — `/login` stays a static placeholder until the
  backend and frontend Auth & Identity chapters land.
- `CTASidebar` — Chapter 4 (Dashboard) owns it.
