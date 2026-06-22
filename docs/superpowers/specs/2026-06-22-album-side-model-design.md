# Album / Side data model — design spec

Date: 2026-06-22

## Context

The backend currently models `Content` (Snippet), `Topic`, and `TLevel`, but has no
concept of an Album (a curated learning pathway, per CLAUDE.md's domain terminology)
or its constituent Sides. This blocks "The Library" and learning-pathway browsing —
the second item in the MVP scope.

This is the first subsystem tackled in the backend-focused chapter (auth/age-tier and
the Forum are deferred to later chapters).

## Data model

### `Album` (`app/models/album.py`)

| Column | Type | Notes |
|---|---|---|
| `id` | PK | |
| `t_level_id` | FK → `t_levels.id`, required | Each Album is the pathway for exactly one T-Level offering. |
| `title` | `String(200)` | |
| `description` | `Text` | |
| `icon` | `String(100)` | Icon identifier for `AlbumCard`. |
| `created_at` | `DateTime`, `server_default=func.now()` | |

Relationship: `t_level` (one), `sides` (`list["Side"]`, ordered by `Side.position`,
`cascade="all, delete-orphan"`).

### `Side` (`app/models/album.py`)

| Column | Type | Notes |
|---|---|---|
| `id` | PK | |
| `album_id` | FK → `albums.id` | |
| `title` | `String(200)` | |
| `position` | `Integer` | Ordering within the Album. |

Relationship: `album` (back-populates `sides`), `contents`
(`list["Content"]`, ordered by `Content.position`).

### `Content` changes (`app/models/content.py`)

Add two nullable columns:

- `side_id: Mapped[int | None]` — FK → `sides.id`, indexed. Nullable because existing
  seeded Snippets aren't assigned to a Side yet.
- `position: Mapped[int | None]` — ordering within the Side.

A Snippet belongs to **at most one** Side (no join table — matches how Snippets are
authored today: written for one place).

### `AlbumEnrolment` (`app/models/album.py`)

| Column | Type | Notes |
|---|---|---|
| `user_id` | FK → `users.id`, part of composite PK | |
| `album_id` | FK → `albums.id`, part of composite PK | |
| `enrolled_at` | `DateTime`, `server_default=func.now()` | |

No status or progress columns. Progress and completion are derived at read time by
joining `Side → Content → UserContentProgress` and counting completed vs. total
Snippets in the Album — no denormalised state to keep in sync.

### Migration

One Alembic migration: `add album, side, album_enrolment tables; add content.side_id, content.position`.

## API

New router `app/routers/albums.py`, prefix `/albums`. **No router-level auth
dependency** — Albums are publicly browsable like Snippets, per CLAUDE.md ("Snippets
and Albums publicly accessible without login; authenticated users can enrol... and
track progress").

| Route | Auth | Behaviour |
|---|---|---|
| `GET /albums/` | none | List Albums. Filterable by `t_level_id` and `topic` (via the Album's TLevel's Topic). Returns title/description/icon/t_level_id — not Sides. |
| `GET /albums/{id}` | optional | Detail: title/description/icon + ordered Sides, each with its ordered Snippets (id/title/content_type only — not body/media_url, matching `Content`'s list/detail split). If the requester is authenticated, additionally includes `enrolled: bool` and, when enrolled, `completed_count`/`total_count`/`progress_pct`. Anonymous requests omit these fields entirely (not null — absent). 404 if the Album doesn't exist. |
| `POST /albums/{id}/enrol` | required | Creates the `AlbumEnrolment` row. Idempotent — no error if already enrolled. 404 if the Album doesn't exist. |
| `DELETE /albums/{id}/enrol` | required | Removes the enrolment row if it exists. Idempotent. |

### Auth dependency addition

`app/dependencies/auth.py` needs a second dependency, `get_current_user_optional`,
returning `User | None` instead of raising, for the "optional auth" shape needed by
`GET /albums/{id}`. Both `get_current_user` and `get_current_user_optional` remain
`NotImplementedError` stubs until the auth chapter — only the shape is added now, via
FastAPI dependency overrides in tests until then.

## Existing bug fix: `content.py` auth

`app/routers/content.py` currently has `dependencies=[Depends(get_current_user)]` at
the router level, requiring auth on every Snippet route — contradicting CLAUDE.md's
"Snippets are public" requirement, and inconsistent with the Album router built here.
Fix: remove the router-level dependency.

## Service layer

`app/services/album_service.py` — real SQLAlchemy implementation (not stubs), using
`selectinload` to eager-load `Album.sides` and `Side.contents` for the detail route to
avoid N+1 queries. Progress is computed by a single aggregate query joining
`UserContentProgress` against the Album's Content IDs, rather than per-Snippet
round trips.

## CI fix: Postgres service container

`backend.yml`'s `test` job has no database, so the new DB-backed tests (and any
existing ones added later) cannot run in CI. Add a `postgres:13` service container
with credentials matching `tests/conftest.py`'s `DATABASE_URL`
(`test:test@localhost:5432/test`), and a healthcheck so the test step waits for it to
be ready.

## Testing

`tests/conftest.py` currently only sets env vars — no DB fixtures exist. Add:

- A `db_session` fixture: creates all tables (`Base.metadata.create_all`) against the
  test Postgres before each test, drops them after.
- A `client` fixture override that injects the test session via `get_db` and overrides
  `get_current_user`/`get_current_user_optional` with a fixture `User` row, so
  enrolment endpoints are testable despite real auth not existing yet.

Coverage:
- List Albums, with and without `t_level_id`/`topic` filters.
- Album detail: ordered Sides/Snippets returned correctly.
- Progress computation: 0 of N, partial, and fully-complete cases.
- Enrol/un-enrol: idempotency (enrolling twice doesn't error or duplicate the row).
- Anonymous `GET /albums/{id}` succeeds and omits `enrolled`/progress fields.
- `content.py` Snippet routes are reachable without auth (regression test for the bug fix).

## Out of scope (deferred to later chapters)

- Real Cognito JWT auth / `get_current_user` implementation.
- Age-tier derivation and enforcement.
- The Forum (Post/Like/Save models).
- Dynamic Mentor / Bedrock integration.
- Assigning existing seeded Snippets to Sides (seed data update) — can follow once
  Sides exist, as a separate small task.
