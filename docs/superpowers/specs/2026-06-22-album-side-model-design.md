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

Relationship: `album` (back-populates `sides`), `side_contents`
(`list["SideContent"]`, ordered by `SideContent.position`).

### `SideContent` (`app/models/album.py`)

A Snippet can be reused across multiple Albums (e.g. a shared intro video), but within
any single Album it belongs to exactly one Side. That rules out a direct `side_id`
column on `Content` (which would cap a Snippet at one Side *ever*) — instead, a join
table:

| Column | Type | Notes |
|---|---|---|
| `side_id` | FK → `sides.id`, part of composite PK | |
| `content_id` | FK → `content.id`, part of composite PK | |
| `position` | `Integer` | Ordering within this Side. Belongs to the join row, not to `Content`, since the same Snippet can have a different position in a different Side. |

The "one Side per Album" rule isn't expressible as a simple DB constraint (it spans
the join through `Side.album_id`), so it's enforced in `album_service` at write time:
adding a Snippet to a Side first removes any existing `SideContent` row for that
`content_id` whose `Side.album_id` matches — i.e. moving a Snippet to a different Side
within the same Album is a move, not an addition.

### `Content` changes (`app/models/content.py`)

None. `Content` gains a `side_contents: Mapped[list["SideContent"]]` relationship but
no new columns — Side/position membership lives entirely on `SideContent`.

### `AlbumEnrolment` (`app/models/album.py`)

| Column | Type | Notes |
|---|---|---|
| `user_id` | FK → `users.id`, part of composite PK | |
| `album_id` | FK → `albums.id`, part of composite PK | |
| `enrolled_at` | `DateTime`, `server_default=func.now()` | |

No status or progress columns. Progress and completion are derived at read time by
joining `Side → SideContent → UserContentProgress` and counting completed vs. total
Snippets in the Album — no denormalised state to keep in sync.

### Migration

One Alembic migration: `add album, side, side_content, album_enrolment tables`.

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
`selectinload` to eager-load `Album.sides` and `Side.side_contents` (plus
`SideContent.content`) for the detail route to avoid N+1 queries. Progress is
computed by a single aggregate query joining `UserContentProgress` against the
Album's Content IDs (gathered via `SideContent`), rather than per-Snippet round trips.

`add_content_to_side(db, side_id, content_id, position)` enforces the one-Side-per-
Album rule described above: before inserting, it deletes any existing `SideContent`
row for that `content_id` whose `Side.album_id` matches the target Side's Album.

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
- A Snippet can belong to Sides in two different Albums simultaneously.
- Adding a Snippet already in one Side of an Album to a different Side of the *same*
  Album moves it (one `SideContent` row for that pair afterwards), rather than leaving
  it in both.

## Out of scope (deferred to later chapters)

- Real Cognito JWT auth / `get_current_user` implementation.
- Age-tier derivation and enforcement.
- The Forum (Post/Like/Save models).
- Dynamic Mentor / Bedrock integration.
- Assigning existing seeded Snippets to Sides (seed data update) — can follow once
  Sides exist, as a separate small task.
