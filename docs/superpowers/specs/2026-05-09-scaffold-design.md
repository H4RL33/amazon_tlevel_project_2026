# Scaffold Design — T-Level AWS Academy Platform

**Date:** 2026-05-09
**Status:** Approved
**Author:** Harley (via brainstorming session)

---

## Purpose

Define the frontend components, backend routes, and database models to scaffold as stubs. Junior developers (Bobby Daunton, Ahad Afzaal) will implement the logic. Each file is a skeleton only — typed signatures, docstrings/comment blocks, and `raise NotImplementedError` or empty templates. No business logic is written by the scaffolder.

---

## Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Navigation | Persistent sidebar | Matches AWS Academy aesthetic; topic areas always accessible |
| Dashboard layout | Topic grid top-left, continue reading bottom-left, feed right column | Faithful to design brief |
| Auth | Cognito Hosted UI → `/auth/callback` → `/auth/sync` → onboarding | Removes password UI complexity; juniors build the interesting parts |
| Content storage | Markdown in Postgres `TEXT`; media (audio/video) in S3 | Simple to seed and render; AI-synthesised audio via Polly stored as S3 objects |
| Data | Fully relational (all domain concepts as DB tables); seeded, not admin-managed | Teaches real DB modelling without admin CRUD scope |
| Scaffold style | Stubs only: typed props, docstrings, `NotImplementedError`, empty templates | Juniors focus on logic, not boilerplate |

---

## Aesthetic Guidelines

All components reference these styling constants:

- **Sidebar background:** `#0a2540` (dark navy)
- **Page background:** `#0d1117`
- **Card/surface background:** `#161b22`
- **Primary accent:** `#1f6feb` (AWS blue)
- **Text primary:** `#c9d1d9`
- **Text muted:** `#8b949e`
- **Border radius:** `8px` cards, `4px` inputs/badges
- **Drop shadows:** `0 1px 4px rgba(0,0,0,0.3)`
- **Topic accent colours** (one per topic, used as left border bars on cards):
  - Digital: `#3b82f6`
  - Business: `#10b981`
  - Media: `#f59e0b`
  - Finance: `#6366f1`
  - Engineering: `#ef4444`
- **Font:** system sans-serif stack; headings semi-bold
- **Breadcrumbs:** appear on `/topics/[slug]` and `/topics/[slug]/t-levels/[id]`

---

## Database Models

Five routers; eight tables. Topics, T-Levels, Tags, and Content are seeded once and not admin-editable. User-linked tables are written at runtime.

### `Topic`
| Column | Type | Notes |
|---|---|---|
| `id` | `int` PK | |
| `slug` | `varchar(50)` unique | e.g. `digital`, `business` |
| `name` | `varchar(100)` | Display name |
| `description` | `text` | Markdown — topic overview |
| `accent_colour` | `varchar(7)` | Hex, e.g. `#3b82f6` |

### `TLevel`
| Column | Type | Notes |
|---|---|---|
| `id` | `int` PK | |
| `topic_id` | `int` FK → `topics.id` | |
| `name` | `varchar(200)` | |
| `entry_requirements` | `text` | Markdown |
| `how_to_apply` | `text` | Markdown |

### `Tag`
| Column | Type | Notes |
|---|---|---|
| `id` | `int` PK | |
| `name` | `varchar(100)` unique | e.g. `cloud`, `networking` |

### `Content`
| Column | Type | Notes |
|---|---|---|
| `id` | `int` PK | |
| `title` | `varchar(255)` | |
| `body` | `text` | Markdown (articles); null for audio/video |
| `content_type` | `enum` | `article`, `audio`, `video` |
| `media_url` | `varchar(500)` | S3 key (not full URL — backend generates pre-signed URLs) |
| `topic_id` | `int` FK → `topics.id` | Always set |
| `t_level_id` | `int` FK → `t_levels.id` nullable | Set for T-level-specific content |
| `created_at` | `datetime` | |

### `ContentTag` (junction)
| Column | Type |
|---|---|
| `content_id` | `int` FK |
| `tag_id` | `int` FK |

### `User`
| Column | Type | Notes |
|---|---|---|
| `id` | `int` PK | |
| `cognito_sub` | `varchar(100)` unique | Cognito user ID |
| `email` | `varchar(255)` unique | |
| `first_name` | `varchar(100)` | |
| `last_name` | `varchar(100)` | |
| `created_at` | `datetime` | |

### `UserTopicInterest` (junction)
| Column | Type |
|---|---|
| `user_id` | `int` FK |
| `topic_id` | `int` FK |

### `UserContentProgress`
| Column | Type | Notes |
|---|---|---|
| `user_id` | `int` FK | |
| `content_id` | `int` FK | |
| `last_viewed_at` | `datetime` | |
| `progress_pct` | `int` | 0–100; < 100 = "continue reading" |

---

## Backend — Routers & Services

### Router structure

```
backend/app/
├── routers/
│   ├── auth.py         ← POST /auth/sync
│   ├── users.py        ← GET/PUT /users/me, /users/me/topics
│   ├── topics.py       ← GET /topics, /topics/{slug}, /topics/{slug}/t-levels/{id}
│   ├── content.py      ← GET /content, /content/{id}, /content/{id}/audio-url
│   └── feed.py         ← GET /feed, GET/POST /progress
├── services/
│   ├── auth_service.py
│   ├── user_service.py
│   ├── topic_service.py
│   ├── content_service.py
│   └── feed_service.py
├── models/
│   ├── user.py
│   ├── topic.py
│   ├── t_level.py
│   ├── tag.py
│   ├── content.py
│   └── progress.py
└── schemas/
    ├── user.py
    ├── topic.py
    ├── content.py
    └── feed.py
```

### Auth dependency

All protected routes use a `get_current_user` FastAPI dependency that:
1. Reads `Authorization: Bearer <token>` header
2. Fetches Cognito JWKS from `https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json`
3. Validates and decodes the JWT
4. Returns the Cognito `sub` claim

### Endpoints

**`POST /auth/sync`** — Protected  
Body: `{ first_name, last_name }` (Cognito already holds email)  
Creates User row if none exists for this `cognito_sub`; returns `UserResponse`.  
Called by frontend immediately after token exchange.

---

**`GET /users/me`** — Protected  
Returns `UserResponse` for the current user including their topic interests.

**`PUT /users/me/topics`** — Protected  
Body: `{ topic_ids: list[int] }`  
Replaces all `UserTopicInterest` rows for this user. Used on onboarding and settings.

**`GET /users/me/topics`** — Protected  
Returns list of `TopicResponse` for the user's chosen topics.

---

**`GET /topics`** — Protected  
Returns all 5 topics.

**`GET /topics/{slug}`** — Protected  
Returns `TopicDetailResponse` including its list of T-levels.

**`GET /topics/{slug}/t-levels/{id}`** — Protected  
Returns `TLevelResponse` with `entry_requirements` and `how_to_apply` (rendered Markdown).

---

**`GET /content`** — Protected  
Query params: `?topic=<slug>`, `?t_level_id=<int>`, `?type=<article|audio|video>`, `?tag=<name>`  
Returns paginated list of `ContentResponse`. Does not include `body` (use detail endpoint for full content).

**`GET /content/{id}`** — Protected  
Returns full `ContentResponse` including `body` (Markdown). For audio/video, includes a short-lived pre-signed S3 URL in `media_url`.

**`GET /content/{id}/audio-url`** — Protected  
Returns a fresh pre-signed S3 URL for audio streaming. Separate endpoint so the player can refresh the URL without re-fetching the full content item.

---

**`GET /feed`** — Protected  
Returns personalised list of `ContentResponse` based on the user's topic interests and tag engagement history. Service stub must document the intended ranking logic.

**`GET /progress`** — Protected  
Returns `UserContentProgress` rows where `progress_pct < 100`, ordered by `last_viewed_at` desc. Powers "continue reading".

**`POST /progress/{content_id}`** — Protected  
Body: `{ progress_pct: int }`  
Upserts `UserContentProgress`. Called by `AudioPlayer` and `VideoPlayer` components as the user progresses.

---

## Frontend — Routes

Protected routes live inside a SvelteKit route group `src/routes/(app)/` with a shared `+layout.svelte` that renders `AppShell`. Public routes sit at `src/routes/` root level.

| Route | File | Auth | Purpose |
|---|---|---|---|
| `/` | `src/routes/+page.svelte` | Public | Landing/hero, "Get Started" CTA → Cognito Hosted UI |
| `/auth/callback` | `src/routes/auth/callback/+page.svelte` | Public | Exchanges Cognito `?code=` for tokens via PKCE (no client secret), calls `/auth/sync`, redirects to `/onboarding` or `/dashboard` |
| `/onboarding` | `src/routes/(app)/onboarding/+page.svelte` | Protected | Topic area selection on first login; calls `PUT /users/me/topics` then redirects to `/dashboard` |
| `/dashboard` | `src/routes/(app)/dashboard/+page.svelte` | Protected | Topic grid + personalised feed + continue reading |
| `/topics/[slug]` | `src/routes/(app)/topics/[slug]/+page.svelte` | Protected | Topic description, T-level list (left), topic content (below) |
| `/topics/[slug]/t-levels/[id]` | `src/routes/(app)/topics/[slug]/t-levels/[id]/+page.svelte` | Protected | T-level detail: entry requirements, how to apply, related content |
| `/settings` | `src/routes/(app)/settings/+page.svelte` | Protected | Update name; change topic interests |

**Auth guard:** `src/hooks.server.ts` intercepts all `/(app)/*` routes. If no valid Cognito JWT is present in the session, redirects to `/`. The `(app)` group layout (`src/routes/(app)/+layout.svelte`) mounts `AppShell` and populates the `allTopics` and `currentUser` stores on load.

---

## Frontend — Components

### Layout

**`AppShell.svelte`**
- Purpose: root layout wrapper for all authenticated pages
- Used in: `src/routes/(app)/+layout.svelte`
- Props: none (uses `<slot />`)
- Styling: CSS grid — fixed-width sidebar column (`240px`) + `1fr` content area; full viewport height

**`Sidebar.svelte`**
- Purpose: persistent left navigation with topic links, user avatar, settings link
- Used in: `AppShell`
- Props: `user: UserResponse`, `topics: TopicResponse[]`, `activePath: string`
- Styling: background `#0a2540`, full height, topic items with coloured left-border accent on hover/active, user avatar at bottom above settings link

**`Breadcrumb.svelte`**
- Purpose: shows page hierarchy on deep routes
- Used in: topic page, T-level page
- Props: `crumbs: Array<{ label: string; href: string }>`
- Styling: muted text, `/` separator, last item non-linked

### Dashboard

**`TopicGrid.svelte`**
- Purpose: 2×3 grid (5 topics + 1 "explore all" card) of topic area cards
- Used in: `/dashboard` top-left, `/onboarding` (multi-select variant)
- Props: `topics: TopicResponse[]`, `selectable: boolean` (onboarding mode)
- Styling: CSS grid, each card has coloured left accent bar matching topic colour

**`TopicCard.svelte`**
- Purpose: single topic area card with name, short description, accent colour
- Used in: `TopicGrid`
- Props: `topic: TopicResponse`, `selected: boolean`, `selectable: boolean`
- Styling: `Card` base + left accent bar; selected state adds blue ring; hover lifts with shadow

**`PersonalisedFeed.svelte`**
- Purpose: right-column container for the personalised content feed
- Used in: `/dashboard`
- Props: `items: ContentResponse[]`
- Styling: scrollable column, gap between `FeedItem`s

**`FeedItem.svelte`**
- Purpose: single content item in the feed — title, content type badge, topic tag, progress indicator if in progress
- Used in: `PersonalisedFeed`
- Props: `item: ContentResponse`, `progress: number | null`
- Styling: surface card with hover state; `Badge` for type; topic accent dot

**`ContinueReading.svelte`**
- Purpose: bottom-left dashboard section showing in-progress content items
- Used in: `/dashboard`
- Props: `items: UserContentProgress[]`
- Styling: horizontal scroll row of compact cards with `ProgressBar`

### Topic & T-Level pages

**`TLevelList.svelte`**
- Purpose: left-column list of T-levels for a topic
- Used in: `/topics/[slug]`
- Props: `tLevels: TLevelResponse[]`, `activeId: number | null`
- Styling: vertical list, active item highlighted with primary accent; hover state

**`TLevelListItem.svelte`**
- Purpose: single row in the T-level list
- Used in: `TLevelList`
- Props: `tLevel: TLevelResponse`, `active: boolean`
- Styling: padding, chevron right icon, active = bold + accent left border

**`ContentBlock.svelte`**
- Purpose: renders a single `Content` item — Markdown article via `svelte-markdown`, or delegates to `AudioPlayer`/`VideoPlayer` for media
- Used in: topic page (topic-level content), T-level page (T-level-specific content)
- Props: `content: ContentResponse`
- Styling: `Card` wrapper; Markdown gets prose typography styles; media players sit inside the card

### Media

**`AudioPlayer.svelte`**
- Purpose: streams audio from a pre-signed S3 URL; calls `POST /progress/{id}` as the user listens to update `progress_pct`
- Used in: `ContentBlock`
- Props: `contentId: number`, `src: string`
- Styling: custom controls (play/pause, scrubber, time display) matching platform dark theme; `ProgressBar` below scrubber

**`VideoPlayer.svelte`**
- Purpose: embeds and plays video from a pre-signed S3 URL; same progress reporting pattern as `AudioPlayer`
- Used in: `ContentBlock`
- Props: `contentId: number`, `src: string`
- Styling: 16:9 aspect ratio container, dark controls overlay

### UI Primitives

**`Button.svelte`**
- Purpose: standard interactive button
- Props: `variant: 'primary' | 'secondary' | 'danger'`, `disabled: boolean`, `type`
- Styling: primary = `#1f6feb` fill; secondary = muted surface; danger = `#ef4444`

**`Card.svelte`**
- Purpose: surface container with optional title and actions slot
- Props: `title?: string`
- Styling: background `#161b22`, `8px` radius, soft drop shadow, `1.5rem` padding

**`Badge.svelte`**
- Purpose: small label for content type or topic name
- Props: `label: string`, `colour?: string`
- Styling: pill shape, `0.25rem 0.6rem` padding, small caps, coloured background at 20% opacity with matching text

**`ProgressBar.svelte`**
- Purpose: horizontal progress indicator for reading/listening progress
- Props: `pct: number` (0–100)
- Styling: thin bar (`4px`), background `#21262d`, fill `#1f6feb`, rounded ends

---

## Frontend — Stores

**`src/lib/stores/user.ts`**
- `currentUser`: `Writable<UserResponse | null>` — authenticated user; null when logged out
- `userTopics`: `Writable<TopicResponse[]>` — user's chosen topic interests

**`src/lib/stores/topics.ts`**
- `allTopics`: `Writable<TopicResponse[]>` — all 5 topics; loaded once on first authenticated page load

**`src/lib/stores/progress.ts`**
- `continueReading`: `Writable<UserContentProgress[]>` — in-progress content for the dashboard

---

## Frontend — API Modules

All under `src/lib/api/`. All call `apiFetch` from `client.ts` with the Cognito JWT attached.

**`client.ts`** — base fetch wrapper; reads JWT from store; throws `ApiError` on non-2xx

**`auth.ts`** — `exchangeCode(code: string)`, `syncUser(firstName, lastName)`, `signOut()`

**`topics.ts`** — `listTopics()`, `getTopic(slug)`, `getTLevel(slug, id)`

**`content.ts`** — `listContent(filters)`, `getContent(id)`, `getAudioUrl(id)`

**`feed.ts`** — `getFeed()`

**`progress.ts`** — `getProgress()`, `updateProgress(contentId, pct)`

---

## Scaffold Conventions for Juniors

1. **Backend services:** every function has a docstring stating what it must do, any constraints (e.g. "never return `hashed_password`", "must upsert, not insert"), and ends with `raise NotImplementedError`.
2. **Backend routers:** correct decorator, dependency injection (`Depends(get_current_user)`, `Depends(get_db)`), response model, and summary string. No body logic — delegates directly to service.
3. **Svelte components:** opening comment block with purpose, props, usage, and styling notes. `export let` declarations with types. Empty `<script>`, empty template. No logic.
4. **API modules:** typed function signatures calling `apiFetch` with correct path and method. No extra logic.
5. **Stores:** declared and typed but not populated — components call API modules and write to stores.

---

## Additional Files to Scaffold

| File | Purpose |
|---|---|
| `src/hooks.server.ts` | Auth guard — intercept protected routes, validate JWT, redirect if absent |
| `src/routes/(app)/+layout.svelte` | Mounts `AppShell`, loads `currentUser` + `allTopics` stores |
| `backend/app/dependencies/auth.py` | `get_current_user` dependency — JWKS validation of Cognito JWT |
| `backend/seed.py` | Script to seed Topics, TLevels, Tags, and Content from JSON/Markdown files |

## Environment Variables to Add to `.env.example`

```dotenv
# Cognito (frontend)
VITE_COGNITO_DOMAIN=https://your-pool.auth.eu-west-2.amazoncognito.com
VITE_COGNITO_CLIENT_ID=your-app-client-id
VITE_COGNITO_REDIRECT_URI=http://localhost:5173/auth/callback

# Cognito (backend — for JWKS validation)
COGNITO_REGION=eu-west-2
COGNITO_USER_POOL_ID=eu-west-2_xxxxxxx

# AWS S3 (backend — for pre-signed media URLs)
S3_BUCKET_NAME=exeaws26-content
AWS_REGION=eu-west-2

# Existing
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/appdb
SECRET_KEY=change-me-in-production
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:5173
```

## Frontend — Additional Dependencies

Add to `frontend/package.json` devDependencies:

- `svelte-markdown` — renders Markdown body in `ContentBlock`

---

## Out of Scope

- Admin panel / content management UI
- Alembic migrations (add separately once models are finalised)
- Email notifications
- Search
- Social features (comments, likes)
