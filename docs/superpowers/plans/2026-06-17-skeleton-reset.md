# Skeleton Reset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reset the project to a clean, runnable skeleton with Poetry, Docker Compose, and stripped CI — ready for a team to build into once the proposal is decided.

**Architecture:** Three Docker containers (SvelteKit frontend, FastAPI backend, Postgres DB) orchestrated by Docker Compose for local development. All service and router implementations are stubs (`raise NotImplementedError`). Folder structure is preserved as scaffolding for an inexperienced team. Auth is a typed stub with a clear swap point for future local JWT or Cognito.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy (async), Poetry; SvelteKit, TypeScript, Vitest; PostgreSQL 17; Docker Compose; GitHub Actions.

---

## File Map

| Action | Path |
|---|---|
| Modify | `README.md` |
| Modify | `frontend/package.json` |
| Rewrite | `backend/pyproject.toml` |
| Rewrite | `backend/Dockerfile` |
| Delete | `backend/requirements.txt` |
| Delete | `backend/seed.py` |
| Delete | `backend/main.py` |
| Rewrite | `backend/app/config.py` |
| Rewrite | `backend/app/main.py` |
| Rewrite | `backend/app/dependencies/auth.py` |
| Rewrite | `backend/.env.example` |
| Rewrite | `backend/tests/conftest.py` |
| Create | `backend/tests/test_health.py` |
| Delete | `backend/tests/test_auth.py` |
| Delete | `backend/tests/test_models.py` |
| Delete | `backend/tests/test_schemas.py` |
| Rewrite | `frontend/src/lib/api/client.ts` |
| Rewrite | `frontend/src/lib/api/auth.ts` |
| Rewrite | `frontend/src/lib/api/content.ts` |
| Rewrite | `frontend/src/lib/api/feed.ts` |
| Rewrite | `frontend/src/lib/api/progress.ts` |
| Rewrite | `frontend/src/lib/api/topics.ts` |
| Rewrite | `frontend/src/routes/+page.svelte` |
| Delete | `frontend/src/routes/(app)/` (whole directory) |
| Delete | `frontend/src/routes/auth/` (whole directory) |
| Create | `docker-compose.yml` |
| Create | `frontend/Dockerfile` |
| Modify | `frontend/.env.example` |
| Rewrite | `.github/workflows/backend.yml` |
| Rewrite | `.github/workflows/frontend.yml` |

---

## Task 1: Update project metadata

**Files:**
- Modify: `README.md`
- Modify: `frontend/package.json`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Update README title**

Replace the contents of `README.md` with:

```markdown
# amazon_tlevel_project_2026
Interactive learning / information platform — Amazon T-Level Project 2026.
```

- [ ] **Step 2: Update frontend package name**

In `frontend/package.json`, change line 2:

```json
  "name": "amazon-tlevel-project-2026",
```

- [ ] **Step 3: Update FastAPI app title**

In `backend/app/main.py`, change the `FastAPI(...)` call:

```python
app = FastAPI(title="Amazon T-Level Project 2026 API", version="0.1.0")
```

- [ ] **Step 4: Commit**

```bash
git add README.md frontend/package.json backend/app/main.py
git commit -m "chore: rename project to amazon_tlevel_project_2026"
```

---

## Task 2: Configure Poetry

**Files:**
- Rewrite: `backend/pyproject.toml`
- Rewrite: `backend/Dockerfile`
- Delete: `backend/requirements.txt`

- [ ] **Step 1: Rewrite pyproject.toml with Poetry sections**

Replace the entire contents of `backend/pyproject.toml`:

```toml
[tool.poetry]
name = "amazon-tlevel-project-2026"
version = "0.1.0"
description = "Amazon T-Level Project 2026 — interactive learning platform"
authors = []
packages = [{include = "app"}]

[tool.poetry.dependencies]
python = "^3.12"
fastapi = "^0.115.0"
uvicorn = {extras = ["standard"], version = "^0.32.0"}
sqlalchemy = {extras = ["asyncio"], version = "^2.0.0"}
asyncpg = "^0.30.0"
pydantic-settings = "^2.6.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}

[tool.poetry.group.dev.dependencies]
pytest = "^8.3.0"
pytest-asyncio = "^0.24.0"
httpx = "^0.27.0"
ruff = "^0.8.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP"]
ignore = ["E501"]
fixable = ["ALL"]

[tool.ruff.lint.per-file-ignores]
"app/models/*.py" = ["F821"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
```

- [ ] **Step 2: Generate poetry.lock**

Run from the repo root (Poetry must be installed: `pip install poetry`):

```bash
cd backend && poetry install --no-root
```

Expected: Poetry resolves dependencies and writes `backend/poetry.lock`. You will see output like:

```
Creating virtualenv amazon-tlevel-project-2026 in .../backend/.venv
Installing dependencies from lock file
...
Package operations: N installs, 0 updates, 0 removals
```

- [ ] **Step 3: Rewrite backend Dockerfile**

Replace the entire contents of `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry==1.8.5

ENV POETRY_VENVS_IN_PROJECT=1

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-interaction

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

Note: `POETRY_VENVS_IN_PROJECT=1` places the virtualenv at `/app/.venv`. Docker Compose volume-mounts only `app/` and `tests/` subdirectories, so the `.venv` in the image layer is preserved at runtime.

- [ ] **Step 4: Delete requirements.txt**

```bash
rm backend/requirements.txt
```

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/poetry.lock backend/Dockerfile
git rm backend/requirements.txt
git commit -m "chore: switch backend dependency management to Poetry"
```

---

## Task 3: Strip backend config and auth dependency

**Files:**
- Rewrite: `backend/app/config.py`
- Rewrite: `backend/app/dependencies/auth.py`
- Rewrite: `backend/.env.example`
- Delete: `backend/main.py`
- Delete: `backend/seed.py`

- [ ] **Step 1: Rewrite config.py — remove all AWS fields**

Replace the entire contents of `backend/app/config.py`:

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 2: Stub get_current_user**

Replace the entire contents of `backend/app/dependencies/auth.py`:

```python
from app.models.user import User


async def get_current_user() -> User:
    # Replace this with a real implementation (local JWT or Cognito) when auth is decided.
    raise NotImplementedError
```

- [ ] **Step 3: Update .env.example — remove AWS fields**

Replace the entire contents of `backend/.env.example`:

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/app
SECRET_KEY=change-me-in-production
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:5173
```

- [ ] **Step 4: Delete dead files**

```bash
rm backend/main.py backend/seed.py
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/app/dependencies/auth.py backend/.env.example
git rm backend/main.py backend/seed.py
git commit -m "chore: strip AWS config and stub auth dependency"
```

---

## Task 4: Update backend tests

**Files:**
- Rewrite: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`
- Delete: `backend/tests/test_auth.py`, `backend/tests/test_models.py`, `backend/tests/test_schemas.py`

- [ ] **Step 1: Rewrite conftest.py**

Replace the entire contents of `backend/tests/conftest.py`:

```python
import os

# Set env vars before any app module is imported, because get_settings() is
# called at module-level in database.py and cached via lru_cache.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
```

- [ ] **Step 2: Write the health check test**

Create `backend/tests/test_health.py`:

```python
from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 3: Run the test**

```bash
cd backend && poetry run pytest tests/test_health.py -v
```

Expected output:

```
tests/test_health.py::test_health_returns_ok PASSED
1 passed in ...s
```

If it fails with a settings error, check that env vars in `conftest.py` are set before the `from app.main import app` line.

- [ ] **Step 4: Delete stale test files**

```bash
rm backend/tests/test_auth.py backend/tests/test_models.py backend/tests/test_schemas.py
```

- [ ] **Step 5: Commit**

```bash
git add backend/tests/conftest.py backend/tests/test_health.py
git rm backend/tests/test_auth.py backend/tests/test_models.py backend/tests/test_schemas.py
git commit -m "test: replace stale tests with health check; stub conftest"
```

---

## Task 5: Stub frontend API modules

**Files:**
- Rewrite: `frontend/src/lib/api/client.ts`
- Rewrite: `frontend/src/lib/api/auth.ts`
- Rewrite: `frontend/src/lib/api/content.ts`
- Rewrite: `frontend/src/lib/api/feed.ts`
- Rewrite: `frontend/src/lib/api/progress.ts`
- Rewrite: `frontend/src/lib/api/topics.ts`
- Modify: `frontend/package.json`

`types.ts` is kept unchanged — TypeScript interfaces are contracts, not implementation.

- [ ] **Step 1: Stub client.ts**

Replace the entire contents of `frontend/src/lib/api/client.ts`:

```typescript
export const TOKEN_KEY = 'id_token';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function apiFetch<T>(_path: string, _init: RequestInit = {}): Promise<T> {
  throw new Error('not implemented');
}
```

- [ ] **Step 2: Stub auth.ts**

Replace the entire contents of `frontend/src/lib/api/auth.ts`:

```typescript
import type { UserResponse } from './types';

export interface TokenResponse {
  access_token: string;
  id_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
}

export function getCognitoLoginUrl(): string {
  throw new Error('not implemented');
}

export async function exchangeCode(_code: string): Promise<TokenResponse> {
  throw new Error('not implemented');
}

export async function syncUser(_firstName: string, _lastName: string): Promise<UserResponse> {
  throw new Error('not implemented');
}

export function signOut(): void {
  throw new Error('not implemented');
}
```

- [ ] **Step 3: Stub content.ts**

Replace the entire contents of `frontend/src/lib/api/content.ts`:

```typescript
import type { ContentDetailResponse, ContentListResponse, ContentType } from './types';

export interface ContentFilters {
  topic?: string;
  t_level_id?: number;
  content_type?: ContentType;
  tag?: string;
}

export async function listContent(_filters: ContentFilters = {}): Promise<ContentListResponse[]> {
  throw new Error('not implemented');
}

export async function getContent(_id: number): Promise<ContentDetailResponse> {
  throw new Error('not implemented');
}

export async function getAudioUrl(_id: number): Promise<string> {
  throw new Error('not implemented');
}
```

- [ ] **Step 4: Stub feed.ts**

Replace the entire contents of `frontend/src/lib/api/feed.ts`:

```typescript
import type { ContentListResponse } from './types';

export async function getFeed(): Promise<ContentListResponse[]> {
  throw new Error('not implemented');
}
```

- [ ] **Step 5: Stub progress.ts**

Replace the entire contents of `frontend/src/lib/api/progress.ts`:

```typescript
import type { ProgressResponse } from './types';

export async function getProgress(): Promise<ProgressResponse[]> {
  throw new Error('not implemented');
}

export async function updateProgress(_contentId: number, _progressPct: number): Promise<void> {
  throw new Error('not implemented');
}
```

- [ ] **Step 6: Stub topics.ts**

Replace the entire contents of `frontend/src/lib/api/topics.ts`:

```typescript
import type { TLevelResponse, TopicDetailResponse, TopicResponse } from './types';

export async function listTopics(): Promise<TopicResponse[]> {
  throw new Error('not implemented');
}

export async function getTopic(_slug: string): Promise<TopicDetailResponse> {
  throw new Error('not implemented');
}

export async function getTLevel(_slug: string, _tLevelId: number): Promise<TLevelResponse> {
  throw new Error('not implemented');
}

export async function getUserTopics(): Promise<TopicResponse[]> {
  throw new Error('not implemented');
}
```

- [ ] **Step 7: Remove `marked` from package.json**

In `frontend/package.json`, delete the `"marked"` line from `dependencies`:

```json
  "dependencies": {},
```

Then regenerate the lock file:

```bash
cd frontend && npm install
```

Expected: `package-lock.json` updated, `marked` no longer listed under `node_modules`.

- [ ] **Step 8: Verify the existing scaffold test still passes**

```bash
cd frontend && npm run test:unit -- --run
```

Expected:

```
 ✓ src/lib/scaffold.test.ts (3)
   ✓ API types > types module exports required interfaces
   ✓ Stores > user store initialises to null
   ✓ Stores > allTopics store initialises to empty array

Test Files  1 passed (1)
Tests       3 passed (3)
```

If any test fails, check that `types.ts` and `src/lib/stores/user.ts` / `topics.ts` are unchanged.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/lib/api/client.ts frontend/src/lib/api/auth.ts \
        frontend/src/lib/api/content.ts frontend/src/lib/api/feed.ts \
        frontend/src/lib/api/progress.ts frontend/src/lib/api/topics.ts \
        frontend/package.json frontend/package-lock.json
git commit -m "chore: stub all frontend API modules; remove marked dependency"
```

---

## Task 6: Strip frontend routes

**Files:**
- Rewrite: `frontend/src/routes/+page.svelte`
- Delete: `frontend/src/routes/(app)/` (entire directory)
- Delete: `frontend/src/routes/auth/` (entire directory)

`frontend/src/routes/+layout.ts` is kept unchanged — it sets `ssr = false` and `prerender = false`, which are required SvelteKit config.

- [ ] **Step 1: Replace +page.svelte with a placeholder**

Replace the entire contents of `frontend/src/routes/+page.svelte`:

```svelte
<h1>Amazon T-Level Project 2026</h1>
<p>Coming soon.</p>
```

- [ ] **Step 2: Delete all non-root route directories**

```bash
rm -rf frontend/src/routes/\(app\)/ frontend/src/routes/auth/
```

- [ ] **Step 3: Verify no broken imports**

```bash
cd frontend && npm run check
```

Expected: `svelte-check` reports 0 errors. If it reports missing imports from deleted routes, ensure +page.svelte no longer references any deleted modules.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/+page.svelte
git rm -r "frontend/src/routes/(app)" frontend/src/routes/auth
git commit -m "chore: strip frontend routes to placeholder home page"
```

---

## Task 7: Add Docker Compose

**Files:**
- Create: `docker-compose.yml`
- Create: `frontend/Dockerfile`
- Modify: `frontend/.env.example`

- [ ] **Step 1: Create frontend/Dockerfile**

Create `frontend/Dockerfile`:

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
```

- [ ] **Step 2: Update frontend/.env.example**

Replace the entire contents of `frontend/.env.example`:

```
VITE_API_BASE_URL=http://localhost:8000
```

- [ ] **Step 3: Create docker-compose.yml**

Create `docker-compose.yml` at the repo root:

```yaml
services:
  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: app
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      # Mount only source dirs so the Poetry .venv built into the image is preserved.
      - ./backend/app:/app/app
      - ./backend/tests:/app/tests
    env_file: ./backend/.env
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      # Preserve node_modules installed into the image layer.
      - /app/node_modules
    depends_on:
      - backend

volumes:
  postgres_data:
```

- [ ] **Step 4: Create backend/.env from the example**

The developer running locally must create `backend/.env`. This file is gitignored. Run:

```bash
cp backend/.env.example backend/.env
```

Then edit `backend/.env` and set a real `SECRET_KEY` value (any random string for local dev).

- [ ] **Step 5: Verify docker-compose builds without errors**

```bash
docker compose build
```

Expected: all three images build successfully. If the backend build fails with a Poetry error, confirm `backend/poetry.lock` was committed in Task 2.

- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml frontend/Dockerfile frontend/.env.example
git commit -m "chore: add Docker Compose for local development"
```

---

## Task 8: Refactor CI pipelines

**Files:**
- Rewrite: `.github/workflows/backend.yml`
- Rewrite: `.github/workflows/frontend.yml`

AWS deploy, build-and-push, and S3 sync jobs are removed. Both pipelines now only lint and test.

- [ ] **Step 1: Rewrite backend.yml**

Replace the entire contents of `.github/workflows/backend.yml`:

```yaml
name: Backend

on:
  push:
    branches: [main]
    paths: ['backend/**']
  pull_request:
    paths: ['backend/**']

concurrency:
  group: backend-${{ github.head_ref || github.ref_name }}
  cancel-in-progress: true

permissions: {}

jobs:
  lint-autofix:
    name: Lint & Autofix
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: read
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.head_ref || github.ref_name }}
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install ruff
        run: pip install ruff

      - name: Autofix — ruff check
        run: ruff check --fix backend/ || true

      - name: Autofix — ruff format
        run: ruff format backend/ || true

      - name: Commit autofixes (PRs only)
        if: github.event_name == 'pull_request'
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: 'style: autofix Python linting [skip ci]'
          file_pattern: 'backend/**/*.py'

      - name: Report remaining warnings
        run: ruff check backend/ --output-format=github || true

  test:
    name: Test
    runs-on: ubuntu-latest
    needs: lint-autofix
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Poetry
        run: pip install poetry

      - name: Install dependencies
        run: cd backend && poetry install --no-root --no-interaction

      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test
          SECRET_KEY: test-secret-key-for-ci
          ENVIRONMENT: testing
          ALLOWED_ORIGINS: http://localhost:5173
        run: cd backend && poetry run pytest tests/ -v --tb=short
```

- [ ] **Step 2: Rewrite frontend.yml**

Replace the entire contents of `.github/workflows/frontend.yml`:

```yaml
name: Frontend

on:
  push:
    branches: [main]
    paths: ['frontend/**']
  pull_request:
    paths: ['frontend/**']

concurrency:
  group: frontend-${{ github.head_ref || github.ref_name }}
  cancel-in-progress: true

permissions: {}

jobs:
  lint-autofix:
    name: Lint & Autofix
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: read
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.head_ref || github.ref_name }}
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: npm
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Autofix — Prettier
        run: cd frontend && npx prettier --write . || true

      - name: Autofix — ESLint
        run: cd frontend && npx eslint --fix . || true

      - name: Commit autofixes (PRs only)
        if: github.event_name == 'pull_request'
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: 'style: autofix frontend linting [skip ci]'
          file_pattern: 'frontend/**'

      - name: Report remaining warnings
        run: cd frontend && npx eslint . || true

  test:
    name: Test
    runs-on: ubuntu-latest
    needs: lint-autofix
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: npm
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Run unit tests
        run: cd frontend && npm run test:unit -- --run
```

- [ ] **Step 3: Verify pipelines parse correctly**

```bash
# Requires GitHub CLI
gh workflow list
```

Alternatively, push to a branch and confirm the Actions tab shows only two jobs per workflow (Lint & Autofix, Test).

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/backend.yml .github/workflows/frontend.yml
git commit -m "ci: strip AWS deploy stages; switch backend to Poetry"
```

---

## Task 9: Rename repository directory

This task renames the working directory on disk and updates any local symlinks. Run this **after all other tasks are committed** — changing the working directory mid-session will break the current shell.

- [ ] **Step 1: From the parent directory, rename the folder**

Open a new terminal tab. Navigate to the parent:

```bash
cd /home/harley/vault/projects/_college/aws
mv exe_coll_t_level_aws_2026 amazon_tlevel_project_2026
```

Expected: no output on success.

- [ ] **Step 2: Update the symlink in ~/Projects**

There is a symlink at `/home/harley/Projects/_college/aws/exe_coll_t_level_aws_2026` pointing to the old path. Update it:

```bash
rm /home/harley/Projects/_college/aws/exe_coll_t_level_aws_2026
ln -s /home/harley/vault/projects/_college/aws/amazon_tlevel_project_2026 \
      /home/harley/Projects/_college/aws/amazon_tlevel_project_2026
```

- [ ] **Step 3: Verify git still works from the new path**

```bash
cd /home/harley/vault/projects/_college/aws/amazon_tlevel_project_2026
git log --oneline -5
```

Expected: recent commits are visible. Git stores its history internally and does not care about the directory name.

- [ ] **Step 4: Verify CLAUDE.md / memory paths**

If Claude Code is configured with project-specific settings, update any hardcoded paths in `.claude/settings.json` to reference the new directory name.

No git commit needed — this is a filesystem change only.
