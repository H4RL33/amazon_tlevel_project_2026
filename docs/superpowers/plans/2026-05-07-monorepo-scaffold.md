# Monorepo Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold a production-grade monorepo with SvelteKit frontend, FastAPI backend, Terraform infrastructure, and GitHub Actions CI/CD — all files stubbed and wired together, ready for feature development.

**Architecture:** Three-tier app deployed on AWS — SvelteKit on ECS Fargate behind CloudFront/ALB, FastAPI on ECS Fargate with RDS PostgreSQL, Terraform managing all infra. Frontend and backend are independent Docker images pushed to ECR on merge to `main`.

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy (async) / pydantic-settings / pytest / ruff | SvelteKit / TypeScript / Vite / Vitest / svelte-check | Terraform | GitHub Actions

---

## File Map

```
exe_coll_t_level_aws_2026/
├── .editorconfig
├── .gitignore
├── CLAUDE.md
├── CONTRIBUTING.md
│
├── backend/
│   ├── .env.example
│   ├── Dockerfile
│   ├── pyproject.toml               ← ruff config + pytest config
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  ← FastAPI app, CORS, health route, router mounts
│   │   ├── config.py                ← pydantic-settings Settings, get_settings()
│   │   ├── database.py              ← async SQLAlchemy engine, AsyncSession, get_db()
│   │   ├── models/
│   │   │   ├── __init__.py          ← Base, exports User
│   │   │   └── user.py              ← User ORM model
│   │   ├── schemas/
│   │   │   ├── __init__.py          ← exports UserCreate, UserResponse
│   │   │   └── user.py              ← UserCreate, UserResponse Pydantic models
│   │   ├── routers/
│   │   │   ├── __init__.py          ← exports users router
│   │   │   └── users.py             ← CRUD route stubs
│   │   └── services/
│   │       ├── __init__.py          ← exports user_service functions
│   │       └── user_service.py      ← async service stubs
│   └── tests/
│       ├── __init__.py
│       └── test_main.py             ← health check + basic smoke tests
│
├── frontend/
│   ├── package.json
│   ├── svelte.config.js
│   ├── vite.config.js               ← includes Vitest config
│   ├── tsconfig.json
│   ├── static/
│   │   └── .gitkeep
│   └── src/
│       ├── app.html
│       ├── lib/
│       │   ├── api/
│       │   │   ├── client.ts        ← base fetch wrapper, auth headers, error handling
│       │   │   └── users.ts         ← typed API functions mirroring backend routes
│       │   ├── components/
│       │   │   ├── Navbar.svelte
│       │   │   ├── Button.svelte
│       │   │   └── Card.svelte
│       │   └── stores/
│       │       └── user.ts          ← writable user store
│       └── routes/
│           ├── +layout.svelte       ← imports Navbar
│           └── +page.svelte         ← placeholder home page
│
├── infra/
│   ├── main.tf                      ← AWS provider, S3+DynamoDB remote state backend
│   ├── variables.tf                 ← all input variables
│   ├── outputs.tf                   ← key output values
│   ├── vpc.tf                       ← VPC, subnets, NAT gateway
│   ├── ecs.tf                       ← ECS cluster, task defs, Fargate services
│   ├── alb.tf                       ← ALB, target groups, listeners
│   ├── rds.tf                       ← RDS PostgreSQL, Multi-AZ
│   ├── ecr.tf                       ← ECR repos (frontend, backend)
│   ├── cloudfront.tf                ← CloudFront distribution
│   ├── waf.tf                       ← WAF web ACL
│   ├── iam.tf                       ← IAM roles, least-privilege policies
│   ├── secrets.tf                   ← Secrets Manager entries
│   └── cloudwatch.tf                ← log groups, dashboards, alarms
│
└── .github/
    └── workflows/
        ├── ci.yml                   ← lint + test on PR to dev/main
        └── deploy.yml               ← build+push ECR, update ECS on merge to main
```

---

## Task 1: Project Foundation

**Files:**
- Create: `.gitignore`
- Create: `.editorconfig`
- Create: `CLAUDE.md`

- [ ] **Step 1: Create `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo
.venv/
venv/
dist/
build/
*.egg-info/
.pytest_cache/
.ruff_cache/
htmlcov/
.coverage

# Node
node_modules/
.svelte-kit/
.vercel/
build/
dist/

# Terraform
.terraform/
.terraform.lock.hcl
*.tfstate
*.tfstate.backup
*.tfplan
crash.log

# Env files — NEVER commit secrets
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 2: Create `.editorconfig`**

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
indent_size = 2
indent_style = space
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_size = 4

[Makefile]
indent_style = tab
```

- [ ] **Step 3: Create `CLAUDE.md`**

```markdown
# exe_coll_t_level_aws_2026

T-Level AWS project for Exeter College — 2026.

## Project Overview

Full-stack AWS application with:
- **Frontend:** SvelteKit (TypeScript), deployed as Docker image on ECS Fargate
- **Backend:** FastAPI (Python 3.12), deployed as Docker image on ECS Fargate
- **Database:** RDS PostgreSQL (async SQLAlchemy)
- **Infrastructure:** Terraform (S3 + DynamoDB remote state)
- **CI/CD:** GitHub Actions → ECR → ECS rolling deploy

## Monorepo Layout

| Path | Purpose |
|------|---------|
| `backend/` | FastAPI application |
| `frontend/` | SvelteKit application |
| `infra/` | Terraform IaC |
| `.github/workflows/` | CI (ci.yml) and CD (deploy.yml) |

## Backend Patterns

Router → Service → Database. Never put business logic in routers.

```
routers/users.py  →  services/user_service.py  →  database.py
```

- All DB operations use `AsyncSession` via `get_db()` dependency injection.
- Settings are read through `get_settings()` (pydantic-settings). Never hardcode config.
- Add new resources by creating: `models/foo.py`, `schemas/foo.py`, `routers/foo.py`, `services/foo_service.py`, then registering the router in `main.py`.

## Frontend Patterns

All API calls go through `src/lib/api/client.ts`. Never call `fetch` directly in components.

- Add a new page: create `src/routes/your-page/+page.svelte`
- Add a new API resource: create `src/lib/api/resource.ts` mirroring backend routes
- Shared state lives in `src/lib/stores/`

## Development Workflow

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest
ruff check .
```

### Frontend
```bash
cd frontend
npm install
npm run dev
npm run check     # svelte-check
npm run test      # vitest
```

### Infrastructure
```bash
cd infra
terraform init
terraform plan
terraform apply
```

## Branch Convention

- `feature/<name>` — new features
- `fix/<name>` — bug fixes
- `chore/<name>` — maintenance / dependency updates

PRs target `dev`. `main` is production; merging to `main` triggers deploy.

## Environment Variables

Never commit `.env`. Copy `backend/.env.example` → `backend/.env` locally.
Production secrets live in AWS Secrets Manager (see `infra/secrets.tf`).

## Testing

- Backend: `pytest` from `backend/` — tests live in `backend/tests/`
- Frontend: `npm run test` from `frontend/` — colocate test files as `*.test.ts`

## Key AWS Resources (Terraform outputs)

After `terraform apply`, outputs include:
- `alb_dns_name` — backend URL
- `cloudfront_domain` — frontend URL
- `rds_endpoint` — database host (internal)
- `ecr_backend_url` / `ecr_frontend_url` — image registry URLs
```

- [ ] **Step 4: Commit**

```bash
git -C exe_coll_t_level_aws_2026 add .gitignore .editorconfig CLAUDE.md
git -C exe_coll_t_level_aws_2026 commit -m "chore: add project foundation files (gitignore, editorconfig, CLAUDE.md)"
```

---

## Task 2: CONTRIBUTING.md

**Files:**
- Create: `CONTRIBUTING.md`

- [ ] **Step 1: Create `CONTRIBUTING.md`**

```markdown
# Contributing

## Prerequisites

- Python 3.12+, Node 20+, Terraform 1.7+, Docker, AWS CLI v2

## Local Setup

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in values
uvicorn app.main:app --reload   # http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

## Adding a New Page (SvelteKit)

SvelteKit uses file-based routing. Create a file and it becomes a route:

```
src/routes/dashboard/+page.svelte   →   /dashboard
src/routes/users/[id]/+page.svelte  →   /users/:id
```

1. Create `src/routes/<name>/+page.svelte`.
2. If the page needs data, add a `+page.ts` loader beside it.
3. Add a nav link in `src/lib/components/Navbar.svelte`.

## Adding a New API Route

Follow the Router → Service pattern strictly — business logic never goes in routers.

**1. Add the Pydantic schemas** (`backend/app/schemas/foo.py`):
```python
from pydantic import BaseModel

class FooCreate(BaseModel):
    name: str

class FooResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
```

**2. Add the ORM model** (`backend/app/models/foo.py`):
```python
from datetime import datetime
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models import Base

class Foo(Base):
    __tablename__ = "foos"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

**3. Add the service** (`backend/app/services/foo_service.py`):
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.foo import FooCreate, FooResponse

async def create_foo(db: AsyncSession, payload: FooCreate) -> FooResponse:
    """Create a new Foo record."""
    ...
```

**4. Add the router** (`backend/app/routers/foo.py`):
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.foo import FooCreate, FooResponse
from app.services import foo_service

router = APIRouter(prefix="/foos", tags=["foos"])

@router.get("/", response_model=list[FooResponse])
async def list_foos(db: AsyncSession = Depends(get_db)):
    return await foo_service.list_foos(db)
```

**5. Register the router** in `backend/app/main.py`:
```python
from app.routers import foo
app.include_router(foo.router)
```

**6. Add the frontend API client** (`frontend/src/lib/api/foos.ts`):
```typescript
import { apiFetch } from "./client";

export async function listFoos() {
  return apiFetch<FooResponse[]>("/foos");
}
```

## Adding a New Database Model

See the "Adding a New API Route" section — it walks through the full model → schema → router chain.

After creating the model, generate and apply an Alembic migration:
```bash
cd backend
alembic revision --autogenerate -m "add foos table"
alembic upgrade head
```

## Branch Naming

| Prefix | Use for |
|--------|---------|
| `feature/` | New functionality |
| `fix/` | Bug fixes |
| `chore/` | Dependencies, tooling, docs |

Examples: `feature/user-auth`, `fix/login-redirect`, `chore/bump-fastapi`

## PR Process

1. Open a **draft PR** targeting `dev` as soon as you push.
2. Keep commits small and focused — one logical change per commit.
3. Request review before marking ready; don't self-merge.
4. `main` is production — only merge to `main` via a `dev → main` PR after QA.

## Secrets Policy

- **Never commit `.env` files or any credentials.**
- Locally: copy `backend/.env.example` → `backend/.env` and fill in values.
- CI/CD: secrets are injected via GitHub Actions secrets.
- Production: all secrets live in AWS Secrets Manager (see `infra/secrets.tf`).
```

- [ ] **Step 2: Commit**

```bash
git -C exe_coll_t_level_aws_2026 add CONTRIBUTING.md
git -C exe_coll_t_level_aws_2026 commit -m "docs: add CONTRIBUTING.md with dev workflow and patterns"
```

---

## Task 3: Backend Core

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/main.py`

- [ ] **Step 1: Create `backend/requirements.txt`**

```
fastapi==0.115.5
uvicorn[standard]==0.32.1
pydantic-settings==2.6.1
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.0
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.28.0
ruff==0.8.3
```

- [ ] **Step 2: Create `backend/pyproject.toml`**

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP"]
ignore = []

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 3: Create `backend/.env.example`**

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/appdb
SECRET_KEY=change-me-in-production
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:5173
```

- [ ] **Step 4: Create `backend/app/__init__.py`** (empty)

- [ ] **Step 5: Create `backend/app/config.py`**

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

- [ ] **Step 6: Create `backend/app/database.py`**

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

_engine = create_async_engine(get_settings().DATABASE_URL, echo=False)
_async_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _async_session_factory() as session:
        yield session
```

- [ ] **Step 7: Create `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import users

settings = get_settings()

app = FastAPI(title="exe_coll_t_level_aws_2026 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 8: Commit**

```bash
git -C exe_coll_t_level_aws_2026 add backend/
git -C exe_coll_t_level_aws_2026 commit -m "feat(backend): scaffold core app — config, database, main with health route"
```

---

## Task 4: Backend Models & Schemas

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/user.py`

- [ ] **Step 1: Create `backend/app/models/__init__.py`**

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models.user import User  # noqa: E402, F401
```

- [ ] **Step 2: Create `backend/app/models/user.py`**

```python
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
```

- [ ] **Step 3: Create `backend/app/schemas/__init__.py`**

```python
from app.schemas.user import UserCreate, UserResponse  # noqa: F401
```

- [ ] **Step 4: Create `backend/app/schemas/user.py`**

```python
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 5: Commit**

```bash
git -C exe_coll_t_level_aws_2026 add backend/app/models/ backend/app/schemas/
git -C exe_coll_t_level_aws_2026 commit -m "feat(backend): add User ORM model and Pydantic schemas"
```

---

## Task 5: Backend Routers & Services

**Files:**
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/users.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/user_service.py`

- [ ] **Step 1: Create `backend/app/services/__init__.py`**

```python
from app.services import user_service  # noqa: F401
```

- [ ] **Step 2: Create `backend/app/services/user_service.py`**

```python
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate, UserResponse


async def list_users(db: AsyncSession) -> list[UserResponse]:
    """Return all users.

    Must NOT expose hashed_password in the return value.
    """
    raise NotImplementedError


async def get_user(db: AsyncSession, user_id: int) -> UserResponse:
    """Return a single user by primary key.

    Raises 404 HTTPException (caller's responsibility) if not found.
    Must NOT expose hashed_password.
    """
    raise NotImplementedError


async def create_user(db: AsyncSession, payload: UserCreate) -> UserResponse:
    """Create a new user, hashing the password before persisting.

    Must NOT store plain-text passwords.
    Raises 409 HTTPException if email already exists.
    """
    raise NotImplementedError


async def delete_user(db: AsyncSession, user_id: int) -> None:
    """Delete a user by primary key.

    Raises 404 HTTPException if not found.
    """
    raise NotImplementedError
```

- [ ] **Step 3: Create `backend/app/routers/__init__.py`**

```python
from app.routers import users  # noqa: F401
```

- [ ] **Step 4: Create `backend/app/routers/users.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserResponse], summary="List all users")
async def list_users(db: AsyncSession = Depends(get_db)) -> list[UserResponse]:
    """Return a list of all registered users."""
    return await user_service.list_users(db)


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)) -> UserResponse:
    """Return a single user by their ID."""
    return await user_service.get_user(db, user_id)


@router.post("/", response_model=UserResponse, status_code=201, summary="Create user")
async def create_user(
    payload: UserCreate, db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Register a new user."""
    return await user_service.create_user(db, payload)


@router.delete("/{user_id}", status_code=204, summary="Delete user")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """Delete a user by their ID."""
    await user_service.delete_user(db, user_id)
```

- [ ] **Step 5: Commit**

```bash
git -C exe_coll_t_level_aws_2026 add backend/app/routers/ backend/app/services/
git -C exe_coll_t_level_aws_2026 commit -m "feat(backend): stub users router and service with typed signatures and docstrings"
```

---

## Task 6: Backend Tests & Dockerfile

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_main.py`
- Create: `backend/Dockerfile`

- [ ] **Step 1: Write the failing test first**

Create `backend/tests/__init__.py` (empty), then `backend/tests/test_main.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_health_check_returns_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_check_content_type_is_json(client):
    response = await client.get("/health")
    assert "application/json" in response.headers["content-type"]
```

- [ ] **Step 2: Run tests (expect pass for health, since main.py already has the route)**

```bash
cd exe_coll_t_level_aws_2026/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL=postgresql+asyncpg://x:x@localhost/x SECRET_KEY=test pytest tests/test_main.py -v
```

Expected: Both health tests PASS. (DB is not called by the health route.)

- [ ] **Step 3: Create `backend/Dockerfile`**

```dockerfile
# Build stage
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime stage
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY app/ ./app/
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 4: Commit**

```bash
git -C exe_coll_t_level_aws_2026 add backend/tests/ backend/Dockerfile
git -C exe_coll_t_level_aws_2026 commit -m "feat(backend): add health check tests and multi-stage Dockerfile"
```

---

## Task 7: Frontend Setup

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/svelte.config.js`
- Create: `frontend/vite.config.js`
- Create: `frontend/tsconfig.json`
- Create: `frontend/src/app.html`
- Create: `frontend/static/.gitkeep`

- [ ] **Step 1: Create `frontend/package.json`**

```json
{
  "name": "exe-coll-t-level-aws-2026-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite dev",
    "build": "vite build",
    "preview": "vite preview",
    "check": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json",
    "check:watch": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json --watch",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "devDependencies": {
    "@sveltejs/adapter-node": "^5.2.9",
    "@sveltejs/kit": "^2.8.3",
    "@sveltejs/vite-plugin-svelte": "^4.0.2",
    "svelte": "^5.2.9",
    "svelte-check": "^4.1.0",
    "typescript": "^5.7.2",
    "vite": "^6.0.3",
    "vitest": "^2.1.6"
  }
}
```

- [ ] **Step 2: Create `frontend/svelte.config.js`**

```js
import adapter from "@sveltejs/adapter-node";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter(),
  },
};

export default config;
```

- [ ] **Step 3: Create `frontend/vite.config.js`**

```js
import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [sveltekit()],
  test: {
    include: ["src/**/*.test.ts"],
  },
});
```

- [ ] **Step 4: Create `frontend/tsconfig.json`**

```json
{
  "extends": "./.svelte-kit/tsconfig.json",
  "compilerOptions": {
    "allowJs": true,
    "checkJs": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "sourceMap": true,
    "strict": true
  }
}
```

- [ ] **Step 5: Create `frontend/src/app.html`**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%sveltekit.assets%/favicon.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    %sveltekit.head%
  </head>
  <body data-sveltekit-preload-data="hover">
    <div style="display: contents">%sveltekit.body%</div>
  </body>
</html>
```

- [ ] **Step 6: Create `frontend/static/.gitkeep`** (empty file)

- [ ] **Step 7: Commit**

```bash
git -C exe_coll_t_level_aws_2026 add frontend/
git -C exe_coll_t_level_aws_2026 commit -m "feat(frontend): scaffold SvelteKit project config (package.json, vite, svelte, tsconfig)"
```

---

## Task 8: Frontend API Layer

**Files:**
- Create: `frontend/src/lib/api/client.ts`
- Create: `frontend/src/lib/api/users.ts`

- [ ] **Step 1: Create `frontend/src/lib/api/client.ts`**

```typescript
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const token =
    typeof localStorage !== "undefined" ? localStorage.getItem("token") : null;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...init.headers,
  };

  const response = await fetch(`${BASE_URL}${path}`, { ...init, headers });

  if (!response.ok) {
    const text = await response.text().catch(() => response.statusText);
    throw new ApiError(response.status, text);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
```

- [ ] **Step 2: Create `frontend/src/lib/api/users.ts`**

```typescript
import { apiFetch } from "./client";

export interface UserResponse {
  id: number;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  email: string;
  password: string;
}

export async function listUsers(): Promise<UserResponse[]> {
  return apiFetch<UserResponse[]>("/users");
}

export async function getUser(id: number): Promise<UserResponse> {
  return apiFetch<UserResponse>(`/users/${id}`);
}

export async function createUser(payload: UserCreate): Promise<UserResponse> {
  return apiFetch<UserResponse>("/users", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteUser(id: number): Promise<void> {
  return apiFetch<void>(`/users/${id}`, { method: "DELETE" });
}
```

- [ ] **Step 3: Commit**

```bash
git -C exe_coll_t_level_aws_2026 add frontend/src/lib/api/
git -C exe_coll_t_level_aws_2026 commit -m "feat(frontend): add typed API client and users API module"
```

---

## Task 9: Frontend Components & Stores

**Files:**
- Create: `frontend/src/lib/components/Navbar.svelte`
- Create: `frontend/src/lib/components/Button.svelte`
- Create: `frontend/src/lib/components/Card.svelte`
- Create: `frontend/src/lib/stores/user.ts`

- [ ] **Step 1: Create `frontend/src/lib/stores/user.ts`**

```typescript
import { writable } from "svelte/store";
import type { UserResponse } from "$lib/api/users";

/**
 * Currently authenticated user. null when logged out.
 * Set after a successful login; cleared on logout.
 */
export const currentUser = writable<UserResponse | null>(null);
```

- [ ] **Step 2: Create `frontend/src/lib/components/Navbar.svelte`**

```svelte
<!--
  Navbar
  Props: none
  Uses: currentUser store to show login/logout state
  Renders: top navigation bar with site title and auth links
-->
<script lang="ts">
  import { currentUser } from "$lib/stores/user";
</script>

<nav>
  <a href="/">Home</a>

  {#if $currentUser}
    <span>{$currentUser.email}</span>
  {:else}
    <a href="/login">Login</a>
  {/if}
</nav>
```

- [ ] **Step 3: Create `frontend/src/lib/components/Button.svelte`**

```svelte
<!--
  Button
  Props:
    - variant: "primary" | "secondary" | "danger" (default: "primary")
    - disabled: boolean (default: false)
    - type: HTMLButtonElement["type"] (default: "button")
  Slots: default (button label text)
  Emits: click (forwarded from the native button)
-->
<script lang="ts">
  export let variant: "primary" | "secondary" | "danger" = "primary";
  export let disabled = false;
  export let type: "button" | "submit" | "reset" = "button";
</script>

<button {type} {disabled} class={`btn btn--${variant}`} on:click>
  <slot />
</button>

<style>
  .btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
  }
  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  .btn--primary {
    background: #0070f3;
    color: #fff;
  }
  .btn--secondary {
    background: #eee;
    color: #333;
  }
  .btn--danger {
    background: #e00;
    color: #fff;
  }
</style>
```

- [ ] **Step 4: Create `frontend/src/lib/components/Card.svelte`**

```svelte
<!--
  Card
  Props:
    - title: string (optional card heading)
  Slots:
    - default: card body content
    - actions: optional footer with action buttons
-->
<script lang="ts">
  export let title: string | undefined = undefined;
</script>

<div class="card">
  {#if title}
    <h2 class="card__title">{title}</h2>
  {/if}
  <div class="card__body">
    <slot />
  </div>
  <div class="card__actions">
    <slot name="actions" />
  </div>
</div>

<style>
  .card {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 1.5rem;
    background: #fff;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  }
  .card__title {
    margin: 0 0 1rem;
    font-size: 1.25rem;
  }
  .card__actions {
    margin-top: 1rem;
    display: flex;
    gap: 0.5rem;
  }
</style>
```

- [ ] **Step 5: Commit**

```bash
git -C exe_coll_t_level_aws_2026 add frontend/src/lib/components/ frontend/src/lib/stores/
git -C exe_coll_t_level_aws_2026 commit -m "feat(frontend): add Navbar, Button, Card components and user store"
```

---

## Task 10: Frontend Routes

**Files:**
- Create: `frontend/src/routes/+layout.svelte`
- Create: `frontend/src/routes/+page.svelte`

- [ ] **Step 1: Create `frontend/src/routes/+layout.svelte`**

```svelte
<script lang="ts">
  import Navbar from "$lib/components/Navbar.svelte";
</script>

<Navbar />

<main>
  <slot />
</main>

<style>
  main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem 1rem;
  }
</style>
```

- [ ] **Step 2: Create `frontend/src/routes/+page.svelte`**

```svelte
<script lang="ts">
  import Card from "$lib/components/Card.svelte";
</script>

<svelte:head>
  <title>Home — exe_coll_t_level_aws_2026</title>
</svelte:head>

<Card title="Welcome">
  <p>T-Level AWS project — Exeter College 2026.</p>
  <p>This is the placeholder home page. Replace with real content.</p>
</Card>
```

- [ ] **Step 3: Commit**

```bash
git -C exe_coll_t_level_aws_2026 add frontend/src/routes/
git -C exe_coll_t_level_aws_2026 commit -m "feat(frontend): add layout with Navbar and placeholder home page"
```

---

## Task 11: Infrastructure (Terraform)

**Files:**
- Create: `infra/main.tf`
- Create: `infra/variables.tf`
- Create: `infra/outputs.tf`
- Create: `infra/vpc.tf`
- Create: `infra/ecs.tf`
- Create: `infra/alb.tf`
- Create: `infra/rds.tf`
- Create: `infra/ecr.tf`
- Create: `infra/cloudfront.tf`
- Create: `infra/waf.tf`
- Create: `infra/iam.tf`
- Create: `infra/secrets.tf`
- Create: `infra/cloudwatch.tf`

- [ ] **Step 1: Create `infra/variables.tf`**

```hcl
variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "eu-west-2"
}

variable "project_name" {
  description = "Short identifier used in all resource names"
  type        = string
  default     = "exeaws26"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "backend_container_cpu" {
  description = "CPU units for backend ECS task (1024 = 1 vCPU)"
  type        = number
  default     = 256
}

variable "backend_container_memory" {
  description = "Memory (MB) for backend ECS task"
  type        = number
  default     = 512
}

variable "frontend_container_cpu" {
  type    = number
  default = 256
}

variable "frontend_container_memory" {
  type    = number
  default = 512
}
```

- [ ] **Step 2: Create `infra/main.tf`**

```hcl
terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    # Bucket and DynamoDB table must exist before first apply.
    # Create with: aws s3 mb s3://<bucket> && aws dynamodb create-table ...
    bucket         = "exeaws26-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "eu-west-2"
    dynamodb_table = "exeaws26-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
```

- [ ] **Step 3: Create `infra/outputs.tf`**

```hcl
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer (backend entry point)"
  value       = aws_lb.main.dns_name
}

output "cloudfront_domain" {
  description = "CloudFront domain name (frontend entry point)"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint (internal)"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "ecr_backend_url" {
  description = "ECR repository URL for the backend image"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_url" {
  description = "ECR repository URL for the frontend image"
  value       = aws_ecr_repository.frontend.repository_url
}
```

- [ ] **Step 4: Create `infra/ecr.tf`**

```hcl
resource "aws_ecr_repository" "backend" {
  name                 = "${var.project_name}-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "frontend" {
  name                 = "${var.project_name}-frontend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

resource "aws_ecr_lifecycle_policy" "frontend" {
  repository = aws_ecr_repository.frontend.name
  policy     = aws_ecr_lifecycle_policy.backend.policy
}
```

- [ ] **Step 5: Create `infra/vpc.tf`**

```hcl
data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = data.aws_availability_zones.available.names[count.index]
}

resource "aws_eip" "nat" {
  domain = "vpc"
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
  depends_on    = [aws_internet_gateway.main]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }
}

resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}
```

- [ ] **Step 6: Create `infra/alb.tf`**

```hcl
resource "aws_security_group" "alb" {
  name   = "${var.project_name}-alb-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
}

resource "aws_lb_target_group" "backend" {
  name        = "${var.project_name}-backend-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}
```

- [ ] **Step 7: Create `infra/rds.tf`**

```hcl
resource "aws_security_group" "rds" {
  name   = "${var.project_name}-rds-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_backend.id]
  }
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_db_instance" "postgres" {
  identifier             = "${var.project_name}-postgres"
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = var.db_instance_class
  allocated_storage      = 20
  storage_encrypted      = true
  db_name                = "appdb"
  username               = "appuser"
  password               = data.aws_secretsmanager_secret_version.db_password.secret_string
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  multi_az               = true
  skip_final_snapshot    = false
  final_snapshot_identifier = "${var.project_name}-final-snapshot"
  backup_retention_period = 7
  deletion_protection    = true
}
```

- [ ] **Step 8: Create `infra/ecs.tf`**

```hcl
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_security_group" "ecs_backend" {
  name   = "${var.project_name}-ecs-backend-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project_name}-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.backend_container_cpu
  memory                   = var.backend_container_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "backend"
    image     = "${aws_ecr_repository.backend.repository_url}:latest"
    essential = true
    portMappings = [{ containerPort = 8000, protocol = "tcp" }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.backend.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "ecs"
      }
    }
    secrets = [{
      name      = "DATABASE_URL"
      valueFrom = aws_secretsmanager_secret.database_url.arn
    }]
    environment = [{
      name  = "ENVIRONMENT"
      value = var.environment
    }]
  }])
}

resource "aws_ecs_service" "backend" {
  name            = "${var.project_name}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs_backend.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
}
```

- [ ] **Step 9: Create `infra/iam.tf`**

```hcl
data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name               = "${var.project_name}-ecs-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_policy" "ecs_secrets_read" {
  name = "${var.project_name}-ecs-secrets-read"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = [aws_secretsmanager_secret.database_url.arn]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_secrets" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = aws_iam_policy.ecs_secrets_read.arn
}

resource "aws_iam_role" "ecs_task" {
  name               = "${var.project_name}-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
}
```

- [ ] **Step 10: Create `infra/secrets.tf`**

```hcl
resource "aws_secretsmanager_secret" "database_url" {
  name                    = "${var.project_name}/database-url"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${var.project_name}/db-password"
  recovery_window_in_days = 7
}

data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  depends_on = [aws_secretsmanager_secret.db_password]
}
```

- [ ] **Step 11: Create `infra/cloudwatch.tf`**

```hcl
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.project_name}/backend"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${var.project_name}/frontend"
  retention_in_days = 30
}

resource "aws_cloudwatch_metric_alarm" "backend_5xx" {
  alarm_name          = "${var.project_name}-backend-5xx"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Backend returning >10 5xx errors per minute"
  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
    TargetGroup  = aws_lb_target_group.backend.arn_suffix
  }
}
```

- [ ] **Step 12: Create `infra/cloudfront.tf`**

```hcl
resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100"

  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = "alb-backend"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = "alb-backend"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]

    forwarded_values {
      query_string = true
      cookies { forward = "none" }
    }
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  web_acl_id = aws_wafv2_web_acl.main.arn
}
```

- [ ] **Step 13: Create `infra/waf.tf`**

```hcl
resource "aws_wafv2_web_acl" "main" {
  name  = "${var.project_name}-waf"
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action { none {} }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-waf"
    sampled_requests_enabled   = true
  }
}
```

- [ ] **Step 14: Commit**

```bash
git -C exe_coll_t_level_aws_2026 add infra/
git -C exe_coll_t_level_aws_2026 commit -m "feat(infra): scaffold complete Terraform configuration (VPC, ECS, ALB, RDS, ECR, CloudFront, WAF, IAM, Secrets, CloudWatch)"
```

---

## Task 12: CI/CD GitHub Actions Workflows

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/deploy.yml`

- [ ] **Step 1: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  pull_request:
    branches: [dev, main]

jobs:
  backend:
    name: Backend — lint & test
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: backend/requirements.txt

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Lint (ruff)
        run: ruff check .

      - name: Test (pytest)
        run: pytest -v
        env:
          DATABASE_URL: postgresql+asyncpg://x:x@localhost/x
          SECRET_KEY: ci-test-secret

  frontend:
    name: Frontend — type check & test
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Type check (svelte-check)
        run: npm run check

      - name: Test (vitest)
        run: npm run test
```

- [ ] **Step 2: Create `.github/workflows/deploy.yml`**

```yaml
name: Deploy

on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    name: Build → ECR → ECS
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: eu-west-2

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build & push backend image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/exeaws26-backend:$IMAGE_TAG ./backend
          docker push $ECR_REGISTRY/exeaws26-backend:$IMAGE_TAG
          docker tag $ECR_REGISTRY/exeaws26-backend:$IMAGE_TAG $ECR_REGISTRY/exeaws26-backend:latest
          docker push $ECR_REGISTRY/exeaws26-backend:latest

      - name: Build & push frontend image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/exeaws26-frontend:$IMAGE_TAG ./frontend
          docker push $ECR_REGISTRY/exeaws26-frontend:$IMAGE_TAG
          docker tag $ECR_REGISTRY/exeaws26-frontend:$IMAGE_TAG $ECR_REGISTRY/exeaws26-frontend:latest
          docker push $ECR_REGISTRY/exeaws26-frontend:latest

      - name: Force new ECS deployment (backend)
        run: |
          aws ecs update-service \
            --cluster exeaws26-cluster \
            --service exeaws26-backend \
            --force-new-deployment

      - name: Force new ECS deployment (frontend)
        run: |
          aws ecs update-service \
            --cluster exeaws26-cluster \
            --service exeaws26-frontend \
            --force-new-deployment || true
```

- [ ] **Step 3: Commit**

```bash
git -C exe_coll_t_level_aws_2026 add .github/
git -C exe_coll_t_level_aws_2026 commit -m "feat(ci): add GitHub Actions CI (lint+test on PR) and CD (ECR+ECS deploy on main)"
```

---

## Task 13: Push & Branch Setup

- [ ] **Step 1: Set remote to use HTTPS if SSH is not available**

```bash
git -C exe_coll_t_level_aws_2026 remote set-url origin https://github.com/H4RL33/exe_coll_t_level_aws_2026.git
```

- [ ] **Step 2: Push main**

```bash
git -C exe_coll_t_level_aws_2026 push origin main
```

- [ ] **Step 3: Create and push `dev` branch**

```bash
git -C exe_coll_t_level_aws_2026 checkout -b dev
git -C exe_coll_t_level_aws_2026 push origin dev
```

- [ ] **Step 4: Set default branch to `dev` and configure branch protection**

```bash
# Set default branch to dev
gh repo edit H4RL33/exe_coll_t_level_aws_2026 --default-branch dev

# Protect main: require PR + CI passing before merge
gh api repos/H4RL33/exe_coll_t_level_aws_2026/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["Backend — lint & test","Frontend — type check & test"]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null

# Protect dev: require CI passing before merge
gh api repos/H4RL33/exe_coll_t_level_aws_2026/branches/dev/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["Backend — lint & test","Frontend — type check & test"]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews=null \
  --field restrictions=null
```

---

## Self-Review Checklist

### Spec Coverage (SKELETON.md)

| Requirement | Task |
|-------------|------|
| `main.py` with CORS, health route, router mounts | Task 3 |
| `config.py` with pydantic-settings | Task 3 |
| `database.py` with AsyncSession and get_db() | Task 3 |
| `models/` with Base + User (id, created_at, updated_at) | Task 4 |
| `schemas/` with UserCreate, UserResponse | Task 4 |
| `routers/users.py` CRUD stubs with decorators, type hints, docstrings | Task 5 |
| `services/user_service.py` async stubs with NOT-DO docstrings | Task 5 |
| `lib/api/client.ts` base fetch wrapper with auth/error handling | Task 8 |
| `lib/api/users.ts` mirroring backend routes | Task 8 |
| `lib/components/Navbar.svelte`, `Button.svelte`, `Card.svelte` | Task 9 |
| `lib/stores/user.ts` with writable | Task 9 |
| `routes/+layout.svelte` with Navbar | Task 10 |
| `routes/+page.svelte` placeholder home | Task 10 |
| `CONTRIBUTING.md` covering all required topics | Task 2 |
| `ci.yml` — lint + test on PR to dev/main | Task 12 |
| `deploy.yml` — build+push ECR, update ECS on main | Task 12 |
| Backend Dockerfile multi-stage python:3.12-slim | Task 6 |
| `.env.example` | Task 3 |
| All infra .tf files | Task 11 |

All requirements covered. No gaps found.
