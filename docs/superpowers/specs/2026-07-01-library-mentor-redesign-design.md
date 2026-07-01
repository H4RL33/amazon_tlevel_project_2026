# Library Three-Column Redesign + Dynamic Mentor Streaming Design

**Date:** 2026-07-01
**Status:** Approved

## Overview

Redesign `/library` from its current single-sidebar-plus-grid layout into a three-column layout: chat session history on the left, the Dynamic Mentor conversation centered, and a stacked pair of panels (Enrolled Albums, Saved Snippets) on the right. This requires giving the Dynamic Mentor real persistence for the first time — today `POST /library/mentor` is entirely stateless, one message in, one reply out, nothing saved. It also adds real token streaming (Bedrock's Nova Lite model, already configured, supports `invoke_model_with_response_stream`), a redesigned message UI (Discord-style single column with avatars, replacing the current two-sided bubble stub), and a rebuilt Dynamic Mentor avatar and colour treatment pulled from the app's existing per-route gradient system (`$lib/gradient.ts`) instead of hardcoded orange.

The existing semantic search box on `/library` is dropped in this redesign — the Mentor's own RAG retrieval already does semantic search over the catalogue, making a separate search box redundant.

---

## Data Model

Two new tables, following the existing `UserSnippetSave` pattern in `backend/app/models/library.py`:

```python
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str]  # first ~60 chars of the first user message, truncated, set once
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship()
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    role: Mapped[str]  # "user" | "mentor"
    text: Mapped[str]
    sources: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)  # mentor messages only
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session: Mapped["ChatSession"] = relationship(back_populates="messages")
```

Both tables cascade-delete with the user (via `ChatSession`'s FK) and with the session (via `ChatMessage`'s FK), consistent with existing models. `title` is derived once from the first user message and never regenerated — no extra LLM call spent just to title a chat. All of this data lives in the private-VPC Postgres instance, satisfying CLAUDE.md's "no external data retention" constraint for student telemetry.

Migration: standard `alembic revision --autogenerate -m "add chat_sessions and chat_messages"` + `upgrade head`.

---

## Backend API

New routes added to the existing `library` router (`backend/app/routers/library.py`), backed by a new `chat_service.py` (mirrors `library_service.py`'s structure):

- `GET /library/chats` — list current user's sessions (`id`, `title`, `updated_at`), newest first.
- `GET /library/chats/{id}` — full message history for one session. 404 (not 403, to avoid leaking session-id existence) if it doesn't belong to the requesting user.
- `POST /library/chats` — create a new empty session (backs the "New chat" button). Returns the new session's `id`.
- `POST /library/chats/{id}/messages` — send a message, get back a `text/event-stream` response streaming the mentor's reply token-by-token.

### Streaming mechanism

Reuses `_fetch_mentor_context`'s existing RAG retrieval from `library_service.mentor_query`, but swaps the model call from `invoke_model` to `invoke_model_with_response_stream`. The FastAPI endpoint returns a `StreamingResponse` that yields each chunk as an SSE `data: ...` line as it arrives from Bedrock. Once the stream completes, the backend persists both the user's message and the fully-assembled mentor reply (with `sources`) to `chat_messages` in one transaction, and bumps `ChatSession.updated_at`.

The frontend does **not** use the native `EventSource` API (it can't send an `Authorization: Bearer` header). Instead it uses `fetch()` with a `ReadableStream` reader — the same authenticated-request pattern already used everywhere else in this app — decoding SSE chunks manually as they arrive.

### Error handling

If the Bedrock stream errors or the client disconnects mid-stream, the backend still persists whatever text was assembled so far as the mentor message, rather than losing the exchange. The frontend shows a small "message may be incomplete — try asking again" note under a reply that stopped short, rather than silently treating a truncated reply as complete.

### Retired endpoint

`POST /library/mentor` (the old stateless endpoint) is removed outright. Its only two consumers — the Library page and the CTASidebar teaser hand-off — are both being replaced by the session-based flow, so there's no reason to keep two parallel "ask the mentor" code paths.

### CTASidebar hand-off

`AgentChat.svelte`'s `submit` event, currently wired to call `mentorQuery` directly from the home page, changes to: `POST /library/chats` → navigate to `/library?session={id}&draft={message}` → the Library page auto-sends `draft` into the new session on mount. This finally closes the component's long-standing "TODO: decide exact hand-off mechanism" comment.

---

## Frontend Layout

`/library/+page.svelte` becomes a three-`PageCard` row (`display: flex`, `gap: var(--gap-inner)`, `height: 100%`), matching the floating-card visual language used everywhere else (square corners, standard `0 10px 18px -4px` shadow):

```
.library-layout
├── PageCard as="aside"  — chat session history (left)
│     flex: 0 0 var(--rail-width)
├── PageCard as="main"   — Dynamic Mentor chat window (center)
│     flex: 1 1 auto; min-width: 0
└── .right-stack (flex column, gap: var(--gap-inner))
      flex: 0 0 var(--rail-width)
      ├── PageCard — "Enrolled Albums", 2-col grid, own overflow-y: auto
      └── PageCard — "Saved Snippets", list, own overflow-y: auto
```

Both flanking columns share one derived width so they can't drift apart:

```css
--rail-width: calc(2 * 220px + var(--gap-inner) + 3rem);
/* 2 AlbumCards at the existing AlbumGrid max track width (220px, see
   AlbumGrid.svelte's minmax(190px, 220px)) + one --gap-inner between them
   + 1.5rem padding on each side of the PageCard (2 * 1.5rem = 3rem) */
```

The right stack's two panels split the column's height evenly (`flex: 1 1 0` each), each with its own independent scrollbar — not one merged panel — per the Option A wireframe direction. Empty states ("No albums enrolled yet — browse Albums to get started" / equivalent for snippets) match the current Library page's empty-state copy style.

### Left rail: chat session history

"+ New chat" button pinned at the top, then a scrollable list of session titles + relative timestamps below, ordered newest-first. Active session gets the same active-state visual treatment as `NavLink`. Empty state (no chats yet): just the "New chat" button and a short empty-state line.

### Center: Dynamic Mentor chat window

Full rebuild of `AgentChatWindow.svelte`, which today is a rough stub (hardcoded dark bubbles, plain `<input>`/`<button>` instead of the shared `TextInput`/`Button` components, no streaming, no real API wiring, an unused local `ChatMessage` interface with a "replace with real API type" TODO).

**Message layout:** single column, Discord-style — no left/right split between user and mentor. Each message: avatar (top-left) + username + relative timestamp on one line, message text below, full width.

**Dynamic Mentor avatar:** small (38px in-chat) circle:
- Base: `radial-gradient(circle at 35% 30%, ...)` using hues from `getShadowHues('/library')` (the saturated variant from `gradient.ts`) rather than hardcoded colours, so it still ties into the app's per-route palette system even though `/library` only ever resolves to one fixed palette.
- Two soft radial "sheen" highlights layered on top for depth: bright hotspot top-left, soft dark falloff bottom-right.
- `breathe` animation: `filter: hue-rotate(0deg → 70deg) brightness(1 → 1.18)`, 5s ease-in-out infinite alternate. No dot-matrix pattern, no lens-warp filter, no chromatic glow, and no scale pulse — all explored during brainstorming and explicitly dropped in favour of the simpler gradient + breathe treatment.

**Streaming-in text:** each SSE chunk renders as its own `<span>` starting at `filter: blur(6px); opacity: 0`, transitioning to `blur(0); opacity: 1` over 0.7s ease-out as it arrives — text visibly "resolves into focus" rather than popping in instantly.

**Send flourish:** on submit, the input row's bottom accent line and box-shadow run a one-shot `animation` (not `transition`, matching the existing `chroma-spin` pattern in `TopicBanner.svelte`/`AlbumCard.svelte`) — roughly 0.55–0.6s, sweeping through a desaturated (~55%) multi-hue gradient with a soft colour-matched glow pulse, then settling back to the resting two-tone accent line.

**Source chips / active-session highlight:** use the saturated `shadowHsl()` variant of the route palette from `gradient.ts`, replacing the two hardcoded `rgba(249, 115, 22, ...)` orange literals currently in `AgentChatWindow.svelte`.

`AgentChat.svelte` (the CTASidebar teaser) keeps its current `--page-p0`/`--page-p1`-driven accent line as-is — it's meant to feel like part of whatever page it's currently shown on, not locked to the Library page's palette.

### Chat card streaming glow

While a reply is streaming in, the entire center `PageCard` (the chat window) gets a large inner chromatic glow around its perimeter, layered on top of (not replacing) the card's normal outer drop-shadow:

- **Colour:** four inset `box-shadow` layers, each offset toward a different corner (top-left/top-right/bottom-right/bottom-left) via `inset <x> <y> <blur> <spread> <colour>`, so four distinct hues stay visible around the edges simultaneously rather than blending into one colour toward the centre. Hues cycle continuously via a `linear infinite` keyframe animation on the shadow colours (~6s loop, four ~90°-spaced steps) while streaming is active — colours use the same route-palette derivation as the rest of the Mentor's chromatic accents (`getShadowHues`/`shadowHsl` from `gradient.ts`), not fixed literals.
- **Fog creep-in/dissipate:** the glow layer additionally carries a `filter: blur()` that eases from a heavy blur (invisible/hazy at rest) to fully sharp as the glow appears, and back to hazy as it leaves — not a plain opacity fade. Appearing: `opacity 0→1` + `blur 22px→0`, 0.9s ease-out (glow "condenses into focus" as streaming starts). Leaving: reverse, 1.1s ease-in (slightly slower/softer, reads as dispersing rather than switching off). The colour-cycle animation and the appear/leave blur+opacity transition are independent (different CSS properties/mechanisms), so the cycle keeps running underneath regardless of transition state — it's always mid-cycle and ready the instant a new stream starts.
- **Trigger:** a `streaming` class (or equivalent state-driven class binding) toggled on the chat window's root `PageCard` for the duration of an active SSE stream — added when the first chunk of a reply starts arriving, removed when the stream closes (whether it completed normally or was cut short per the error-handling behaviour above).

### Right stack

Reuses the existing `AlbumCard`/`SnippetCard` components unchanged (both already have the tilt + chromatic hover-glow treatment from prior work) — no new card variants needed.

---

## Testing

- **Backend:** pytest coverage for the new `chat_service` — create session, list sessions (ownership-scoped), post message with a mocked Bedrock streaming client (no real AWS calls in tests), 404-on-wrong-owner case. Follows the existing `library_service` test conventions.
- **Frontend:** `vitest` coverage for any pure logic extracted from the streaming/session code (e.g. an SSE-chunk parser, if pulled out as a standalone function) and continued coverage of palette lookups via the existing `gradient.test.ts`.
- **Animation/visual correctness** (breathing avatar, blur-in text, send flourish): not unit-testable. Verified via Playwright measurement/screenshot passes before considering the work done, matching how the rest of this session's visual fixes (sticky sidebar, shadow clipping) were verified.
- **Migration:** run against local Docker Postgres (`docker compose exec backend poetry run alembic upgrade head`) and checked into the migration chain.

---

## Out of Scope

- Rate limiting / abuse prevention on the mentor endpoint.
- Session renaming/deletion UI (sessions accumulate; deletion can be a follow-up if it turns out to matter).
- Regenerating a session's title after the first message.
- Any change to `AgentChat.svelte`'s own visual styling beyond the hand-off mechanism.
