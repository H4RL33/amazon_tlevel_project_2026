# Playwright E2E Testing — Design Spec

**Date:** 2026-06-26
**Status:** Approved

---

## Goal

Add end-to-end browser tests using Playwright. Tests run against the full
docker-compose stack (postgres + backend + frontend) to exercise real API
integration. A dedicated Cognito test user enables authenticated test paths
without touching the Hosted UI.

---

## Prerequisites

### Terraform: enable `USER_PASSWORD_AUTH` on the Cognito app client

`infrastructure/modules/auth/main.tf` — add `"ALLOW_USER_PASSWORD_AUTH"` to
`explicit_auth_flows`:

```hcl
explicit_auth_flows = [
  "ALLOW_REFRESH_TOKEN_AUTH",
  "ALLOW_USER_SRP_AUTH",
  "ALLOW_USER_PASSWORD_AUTH",
]
```

After applying, create a dedicated test Cognito user manually in the AWS
console (or via `aws cognito-idp admin-create-user`). The user must complete
the force-change-password challenge before tests can run — do this once via
the Hosted UI or the CLI.

### Local: `.env.test` (gitignored)

Create `frontend/.env.test`:

```
TEST_COGNITO_USER_POOL_ID=eu-west-2_sX50A202h
TEST_COGNITO_CLIENT_ID=4bkjvav9ur3lat0dr25kht85bh
TEST_COGNITO_USERNAME=<test user email>
TEST_COGNITO_PASSWORD=<test user password>
```

Add `frontend/.env.test` to `.gitignore`.

---

## Playwright Installation

Install in `frontend/` as a dev dependency:

```bash
cd frontend
npm install --save-dev @playwright/test
npx playwright install chromium
```

Config file: `frontend/playwright.config.ts`. Key settings:

- `testDir: './e2e'`
- `baseURL: 'http://localhost:3000'` (docker-compose frontend port)
- Single project: `chromium` only (keep CI fast)
- `retries: 1` in CI, `0` locally
- `reporter: [['html', { open: 'never' }]]`
- No `webServer` block — tests assume docker-compose is already running

Add `e2e/.auth/` to `.gitignore` (saved storage state, contains real tokens).

---

## File Map

```
frontend/
├── playwright.config.ts        New
├── .env.test                   New (gitignored)
└── e2e/
    ├── fixtures.ts             New — auth fixture
    ├── guest.spec.ts           New — unauthenticated paths
    └── auth.spec.ts            New — authenticated paths
```

---

## Auth Fixture (`e2e/fixtures.ts`)

The fixture calls Cognito's `InitiateAuth` API directly (no Hosted UI, no AWS
SDK) to obtain a real `IdToken` for the test user. The token is injected into
`localStorage` under the key `'id_token'` (the existing `TOKEN_KEY` in
`frontend/src/lib/api/client.ts`). Navigating to `/` triggers the root
layout's `onMount`, which reads the token and calls `POST /auth/sync` to
upsert the user row — the same path the real callback page takes.

The resulting browser storage state is saved to `e2e/.auth/user.json` using
Playwright's `storageState`. `auth.spec.ts` loads this file at the top of
each test via `use: { storageState }` rather than re-authenticating per test.

**`InitiateAuth` call:**

```
POST https://cognito-idp.eu-west-2.amazonaws.com/
Headers:
  Content-Type: application/x-amz-json-1.1
  X-Amz-Target: AWSCognitoIdentityProviderService.InitiateAuth
Body:
  {
    "AuthFlow": "USER_PASSWORD_AUTH",
    "ClientId": "<TEST_COGNITO_CLIENT_ID>",
    "AuthParameters": {
      "USERNAME": "<TEST_COGNITO_USERNAME>",
      "PASSWORD": "<TEST_COGNITO_PASSWORD>"
    }
  }
Response: { "AuthenticationResult": { "IdToken": "...", ... } }
```

No AWS credentials are required for this call — it is a public Cognito
endpoint authenticated by the user's own password.

Credentials are loaded from `frontend/.env.test` locally and from GitHub
Actions secrets in CI.

---

## Tests

### `e2e/guest.spec.ts` — unauthenticated golden paths

1. **Home hero** — visit `/`, assert "Discover your future" heading renders and
   the "Get started" button is visible.
2. **Album grid** — visit `/learn`, assert at least one album card is visible
   (waits for the API response).
3. **Snippet detail** — visit `/learn/[first-album-id]`, assert the
   `AlbumSidebar` is present and clicking the first snippet link loads content
   text in the main card.

Album IDs are not hardcoded — tests use `page.locator` to find the first
rendered card and derive the href.

### `e2e/auth.spec.ts` — authenticated golden paths

Uses `storageState: 'e2e/.auth/user.json'` (populated by the fixture in a
`setup` project run before the main tests).

4. **Authenticated home** — visit `/`, assert the `.home-auth` layout is
   present and the greeting text contains the test user's first name.
5. **Settings page** — visit `/settings`, assert the sidebar "Personalisation"
   link is visible and the "Choose file" button renders in the content card.

---

## CI Workflow (`.github/workflows/playwright.yml`)

**Trigger:** push or PR to `main` touching `frontend/**` (same as
`frontend.yml`).

**Steps:**

1. Checkout
2. Set up Docker Buildx (for layer caching)
3. Cache Docker layers — `actions/cache` on `~/.cache/buildkit` (or
   `type=gha` cache with `docker/build-push-action`)
4. Write `backend/.env` from GitHub Actions secrets/vars:
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/app
   SECRET_KEY=${{ secrets.BACKEND_SECRET_KEY }}
   COGNITO_USER_POOL_ID=eu-west-2_sX50A202h
   COGNITO_CLIENT_ID=4bkjvav9ur3lat0dr25kht85bh
   COGNITO_REGION=eu-west-2
   S3_BUCKET_NAME=dummy-not-used-in-e2e
   AWS_ACCESS_KEY_ID=dummy
   AWS_SECRET_ACCESS_KEY=dummy
   ```
   Cognito pool ID and client ID are non-sensitive; they can be hardcoded in
   the workflow. `BACKEND_SECRET_KEY` is a new GitHub secret (any random
   string — only needs to be stable within a run for JWT validation to work).
   S3 credentials are dummied out since no test exercises avatar upload.
5. Write `frontend/.env.test` from secrets:
   ```
   TEST_COGNITO_USER_POOL_ID=eu-west-2_sX50A202h
   TEST_COGNITO_CLIENT_ID=4bkjvav9ur3lat0dr25kht85bh
   TEST_COGNITO_USERNAME=${{ secrets.TEST_COGNITO_USERNAME }}
   TEST_COGNITO_PASSWORD=${{ secrets.TEST_COGNITO_PASSWORD }}
   ```
6. `docker compose up --build -d` — builds and starts all three services
7. Wait for healthy — `curl --retry 10 --retry-delay 3 --retry-connrefused
   http://localhost:8000/health` (the backend `/health` endpoint already
   exists)
8. Run migrations — `docker compose exec -T backend poetry run alembic
   upgrade head`
9. Seed data — `docker compose exec -T backend poetry run python seed.py`
10. Install Playwright browsers — `cd frontend && npx playwright install
    --with-deps chromium`
11. Run tests — `npx playwright test`
12. Upload HTML report as artifact on failure — `if: failure()` with
    `actions/upload-artifact`

**GitHub secrets required (new):**
- `BACKEND_SECRET_KEY` — any random string, used only in CI
- `TEST_COGNITO_USERNAME` — test user email
- `TEST_COGNITO_PASSWORD` — test user password

---

## What Is Not Tested

- Avatar upload (requires real S3 credentials and produces side-effects)
- Forum posting (no write-path social tests in scope for this phase)
- Mobile viewports (chromium desktop only for now)
- The Cognito Hosted UI login redirect flow (bypassed by fixture design)
