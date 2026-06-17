# Skeleton Redesign — Design Spec

**Date:** 2026-06-17  
**Status:** Approved

## Overview

Resets the project to a clean, runnable skeleton ahead of a formal proposal. The platform will be an interactive learning / information platform for students (ages 11+). The exact feature split is undecided; this scaffold gives an inexperienced team a clear structure to build into once the proposal is settled.

The project is renamed from `exe_coll_t_level_aws_2026` to `amazon_tlevel_project_2026` and will be run locally as a prototype (no cloud hosting target at this stage).

---

## 1. Project Rename

- Repository directory renamed to `amazon_tlevel_project_2026`
- Internal name/title fields updated in:
  - `backend/pyproject.toml` — `[tool.poetry] name`
  - `frontend/package.json` — `"name"`
  - `README.md` — title heading
  - `.github/workflows/backend.yml` / `frontend.yml` — `name:` fields
  - `backend/app/main.py` — FastAPI `title=`

---

## 2. Backend Skeleton

### Dependency management

`requirements.txt` removed. Backend managed with Poetry via `pyproject.toml`.

**Core dependencies:** `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]`, `asyncpg`, `pydantic-settings`, `python-jose`, `passlib[bcrypt]`  
**Dev dependencies:** `pytest`, `pytest-asyncio`, `httpx`, `ruff`

### Folder structure

```
backend/
  app/
    config.py             — DATABASE_URL + SECRET_KEY + ENVIRONMENT + ALLOWED_ORIGINS only
    database.py           — SQLAlchemy async engine setup (kept as-is)
    main.py               — FastAPI app, CORS middleware, router includes, /health endpoint
    dependencies/
      auth.py             — get_current_user stub (raises NotImplementedError)
    models/               — all 5 ORM class files kept (User, Topic, TLevel, Content, Progress)
    routers/              — all 5 routers kept; all handlers raise NotImplementedError
    schemas/              — all Pydantic schema files kept as-is (no implementation to strip)
    services/             — all service files kept; all functions raise NotImplementedError
  tests/
    __init__.py
    conftest.py           — minimal async client fixture, no DB dependency
    test_health.py        — GET /health → 200 {"status": "ok"}
  Dockerfile              — Poetry-based build
  .env.example            — DATABASE_URL, SECRET_KEY, ENVIRONMENT, ALLOWED_ORIGINS only
  .dockerignore           — kept as-is
```

**Removed:**
- `backend/main.py` (top-level entry point duplicate)
- `backend/seed.py`
- `backend/requirements.txt`
- All AWS/Cognito/S3 config fields from `config.py` and `.env.example`

### Auth design note

`get_current_user` in `dependencies/auth.py` raises `NotImplementedError`. The signature remains `async def get_current_user(...) -> User` so that a local JWT implementation or AWS Cognito can be dropped in at that single point without touching any router.

---

## 3. Frontend Skeleton

### Tooling

SvelteKit + Vite + TypeScript — no changes. Vitest remains for unit tests. `marked` dependency removed (no content rendering yet).

### Folder structure

```
frontend/
  src/
    app.html
    lib/
      api/
        client.ts         — stub: exports placeholder apiFetch (throws Error("not implemented"))
        auth.ts           — stub: exports placeholder functions
        content.ts        — stub
        topics.ts         — stub
        users.ts          — stub
        types.ts          — kept as-is (TypeScript interfaces, not implementation)
    routes/
      +page.svelte        — single placeholder home page
  tests/
    placeholder.test.ts   — vitest: asserts 1 + 1 === 2 so CI passes
```

**Removed:** All existing route files (auth/callback, feed, etc.) pending proposal decision.

The `lib/api/` stubs preserve function signatures so the team knows the expected contract, but throw `Error("not implemented")` in the body.

---

## 4. Docker Compose

`docker-compose.yml` at repo root. Three services for local development:

| Service | Image / Build | Port | Notes |
|---|---|---|---|
| `db` | `postgres:17-alpine` | 5432 | Named volume; health-checked with `pg_isready` |
| `backend` | `./backend/Dockerfile` | 8000 | Volume-mounts `./backend`; uvicorn `--reload`; reads `backend/.env` |
| `frontend` | `./frontend/Dockerfile` | 5173 | Volume-mounts `./frontend`; `npm run dev -- --host` |

`backend` depends on `db` (healthy). `frontend` depends on `backend`.

A `frontend/Dockerfile` is added (Node dev image, no build step for local dev).

---

## 5. CI/CD Pipelines

Both workflows retain path-filtered triggers and lint-autofix jobs. AWS deploy stages are removed entirely.

### `backend.yml`

1. **lint-autofix** — ruff check + format, commit back on PRs (unchanged)
2. **test** — `poetry install`, `pytest backend/tests/ -v` with dummy env vars

Removed: `build-and-push`, `deploy`

### `frontend.yml`

1. **lint-autofix** — Prettier + ESLint, commit back on PRs (unchanged)
2. **test** — `npm ci`, `npm run test:unit -- --run`

Removed: `build`, `deploy`

---

## Compliance note

The platform may serve users as young as 11. No personal data handling, social features, or age-gating are implemented at skeleton stage, but these concerns should be revisited when the proposal is finalised (data minimisation, parental consent flows, content moderation if social features are added).
