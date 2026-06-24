# Frontend implementation masterplan

Date: 2026-06-24

## Context

The frontend (`frontend/src/`) is fully scaffolded with documented stub components
(every file in CLAUDE.md's component reference table exists with a doc-comment header
describing purpose/props/layout, and a `<!-- TODO -->` marker where the markup goes)
and seven flat placeholder routes (`/`, `/dashboard`, `/learn`, `/topics`, `/forum`,
`/help`, `/library`, `/settings`), each just a "Coming soon" heading. The
[2026-06-17 frontend skeleton chapter](2026-06-17-frontend-skeleton-design.md)
deliberately built only the public root layout (`Navbar` + `slot` + `Footer`) and left
`AppShell.svelte` untouched for "a later feature."

The team is splitting frontend work by ownership: other team members are filling in
individual leaf components (the stub files), while the interface/shell — how those
components compose into actual pages, routing, and the authenticated-vs-public layout
split — is being built separately. This document sequences that shell/composition work
into six chapters, mirroring the
[backend masterplan](2026-06-24-backend-masterplan.md)'s process: each chapter gets its
own brainstorming → design spec → implementation plan → subagent-driven-implementation
cycle when its turn comes.

A [Histoire](https://histoire.dev) component explorer was set up alongside this
masterplan (`npm run story:dev`) so the team filling in leaf components can preview
them in isolation with mock props — no Docker, backend, or DB required. Each leaf
component should get a `.story.svelte` file (see `Button.story.svelte` and
`SnippetCard.story.svelte` for the pattern) as it's implemented; that's the leaf-component
owners' responsibility, not part of these six chapters.

## Chapters

### 1. Shell & Layout Architecture

Builds `AppShell.svelte` (two-column grid: `NavSidebar` + scrolling content) and
introduces SvelteKit route groups to split public pages (current root layout: `Navbar`
+ `slot` + `Footer`) from authenticated pages (`AppShell`-wrapped). Per CLAUDE.md,
Snippets/Albums/Topics stay publicly browsable without login, so the split is not
simply "logged in vs not" — `/learn` and `/topics` stay in the public group even
though they show extra state (enrolment, progress) when a session exists; `/dashboard`,
`/library`, `/forum`, and `/settings` move to the authenticated group.

Also wires up: `CTASidebar` (used within `AppShell` per CLAUDE.md's reference table),
`AgeGateNotice` (blocks/limits Forum access per tier — needs the shell to know where
to render it), and `HelpPanel` as shell-level chrome triggered from `NavBarAvatar`'s
dropdown (CLAUDE.md: "dropdown (account, settings, dashboard, help)") rather than a
standalone `/help` page — the existing `/help` route stub is likely redundant once this
lands and should be resolved (removed or redirected) during this chapter's design.

**Depends on:** nothing — foundational, same role as Auth & Identity in the backend
masterplan.

### 2. Public Browsing — Topics & Learn

Composes the actual Topic and Learn (Album/Snippet) browsing experience:
Topic index/detail pages, Album browsing (`AlbumGrid`, `AlbumCard`), Album detail
(`AlbumSidebar` listing Sides/Snippets, `AlbumProgressWidget`, `EnrolButton` calling
the `/albums/{id}/enrol` endpoint), and Snippet detail (`SnippetTitleBar`,
`AudioPlayer`/`VideoPlayer`, body rendering). Introduces the nested dynamic routes
needed for this (e.g. Album detail, Snippet detail) that don't exist yet — only flat
`/learn` and `/topics` index pages are currently scaffolded.

**Depends on:** Shell & Layout (needs the public route group decided). Backend-side,
this calls already-built (Album/Side) and in-progress (Content Browsing) APIs — no new
backend work required to start, though Topic Browsing needs backend Content Browsing
to land for topic-filtered Album listing to return real data end-to-end.

### 3. The Library

Composes `/library`: `EnrolledAlbumsList`, `LibraryShelf` (continue-reading/saved
Snippets), and the `AgentChat` integration — CLAUDE.md's "personal learning
dashboard." `AgentChat`/`AgentChatWindow` render here but don't need a real Bedrock
backend to build the UI shell against — that's the backend Dynamic Mentor component's
job; this chapter can stub the chat responses initially if Dynamic Mentor isn't ready
yet (to be confirmed during this chapter's own design).

**Depends on:** Shell & Layout (authenticated route group), backend Auth and Feed &
Progress (enrolled Albums + progress data).

### 4. Dashboard

Composes `/dashboard`: XP-over-time, Albums-enrolled count, Snippets-read count —
using `XPBadge`, `MentorBadge`, `ProgressBar`. This is a distinct page from The
Library (confirmed during this masterplan's brainstorming): Dashboard is a stats/
gamification overview, Library is the enrolled-Albums/progress/AgentChat hub.

**Depends on:** Shell & Layout, backend Gamification/XP (component 5 in the backend
masterplan — added specifically because this chapter needed it).

### 5. Settings & Profile

Composes `/settings`: `SettingsNav`, plus profile editing using `UserProfileHeader`
and `UserProfileBio` (max 500 chars, per CLAUDE.md's component reference table) and
topic-interest management (already has a backend endpoint:
`PUT/GET /users/me/topics`).

**Depends on:** Shell & Layout, backend User Profiles (avatar/header/bio columns
don't exist yet — this chapter is blocked on that migration landing).

### 6. The Forum

Composes `/forum`: `ForumFeed`, `PostCard`, `PostComposer`, `LikeButton`/`SaveButton`,
with `AgeGateNotice` enforcing the tiered access CLAUDE.md mandates (no access under
14, read-only 14–16, full read/write 16+). Sequenced last to match its backend
counterpart, both explicitly nice-to-have.

**Depends on:** Shell & Layout, backend Auth (age tier) and backend Forum (component 6
in the backend masterplan) — this chapter cannot ship real functionality until that
backend work exists, though the visual composition could be built against mocked
posts if the team wants to start early (to be decided when this chapter comes up).

## Sequencing rationale

Shell & Layout is first for the same reason Auth is first on the backend: every other
chapter needs the public/authenticated route split decided before it can place its
pages anywhere. Public Browsing comes next because it has no backend blocker — Album/
Side is already done and Content Browsing is in progress — making it the best
low-risk second chapter, the same role Content Browsing plays in the backend
masterplan. Library and Dashboard follow because they're core MVP scope (CLAUDE.md
item 2's "track progress" and the gamification framing), gated only on Auth/Feed-
Progress/Gamification landing backend-side. Settings comes after because User
Profiles is backend chapter 2 but has no frontend urgency until Library/Dashboard are
done. The Forum is last, paired with its backend counterpart, since both are
explicitly nice-to-have.

## Cross-cutting process notes

- Each chapter repeats the brainstorming → spec → plan → subagent-driven-development
  cycle used for Album/Side and described in the backend masterplan.
- Frontend and backend chapters are loosely paired (Shell↔Auth, Public Browsing↔
  Content Browsing, Library/Dashboard↔Feed-Progress/Gamification, Settings↔User
  Profiles, Forum↔Forum) but don't have to be implemented in lockstep — a frontend
  chapter can start once its backend counterpart's *API shape* is stable, even before
  the backend logic is fully real, the same way frontend work today already calls
  `get_current_user`-gated routes that are still `NotImplementedError` stubs.
- Leaf component implementation (filling in the `<!-- TODO -->` stubs) is explicitly
  out of scope for these six chapters — that's the rest of the team's work, previewed
  via Histoire. These chapters are about composition: routing, layout, data wiring,
  and assembling already-built (or concurrently-built) leaf components into working
  pages.

## Out of scope (for this masterplan and, by default, for every chapter's spec)

- Leaf component internals (see above) — tracked by whoever owns each component, not
  by these chapters.
- Real Cognito auth UI (login/signup/callback flows) — depends on backend Auth &
  Identity; if needed before that lands, a chapter may stub it, to be decided when
  relevant.
- Mobile-specific layouts/hamburger nav — the 2026-06-17 skeleton chapter deferred
  this for the public nav, and it stays deferred here for the authenticated shell too,
  unless a chapter's own design pulls it in.
- Visual design exploration (colours, spacing, animation polish) beyond what's already
  specified in CLAUDE.md's component reference table and existing component doc-
  comments — this masterplan plans composition and data flow, not visual design.
