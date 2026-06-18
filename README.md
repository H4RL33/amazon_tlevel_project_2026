# amazon_tlevel_project_2026
Interactive learning / information platform — Amazon T-Level Project 2026.

## Running locally

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

### 1. Configure the backend environment

Create `backend/.env` (if it doesn't already exist):

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/app
SECRET_KEY=change-me-in-production
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:3000
```

### 2. Start all services

```sh
docker compose up --build
```

This starts:

| Service  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:3000        |
| Backend  | http://localhost:8000        |
| API docs | http://localhost:8000/docs   |
| Database | localhost:5432               |

### 3. Run migrations

On first run (or after schema changes), apply Alembic migrations:

```sh
docker compose exec backend poetry run alembic upgrade head
```

### 4. Seed reference data (optional)

Populate topics and T-levels:

```sh
docker compose exec backend poetry run python seed.py
```

### Rebuilding after dependency changes

```sh
docker compose build --no-cache
```
