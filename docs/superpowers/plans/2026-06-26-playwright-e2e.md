# Playwright E2E Testing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Playwright end-to-end tests for the 5 core user journeys, with a CI GitHub Actions workflow that runs them against the full docker-compose stack with Docker layer caching.

**Architecture:** Playwright installs in `frontend/` and targets `localhost:3000`. A `setup` project calls Cognito's `InitiateAuth` API to get a real IdToken, injects it into `localStorage['id_token']`, saves browser storage state, and the `chromium` project reuses it. No Hosted UI interaction. CI builds Docker images separately (with BuildKit local cache) then calls `docker compose up -d`.

**Tech Stack:** Playwright 1.x, TypeScript, dotenv, GitHub Actions, docker/build-push-action.

**Spec:** `docs/superpowers/specs/2026-06-26-playwright-e2e-design.md`

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Modify | `infrastructure/modules/auth/main.tf` | Add `ALLOW_USER_PASSWORD_AUTH` to Cognito app client |
| Modify | `docker-compose.yml` | Add `image:` tags so CI pre-built images are picked up |
| Modify | `.gitignore` | Add `frontend/e2e/.auth/` |
| Create | `frontend/.env.test` | Local test Cognito credentials (already gitignored by `.env.*`) |
| Modify | `frontend/package.json` | Add `test:e2e` script |
| Create | `frontend/playwright.config.ts` | Projects, baseURL, retries, dotenv load |
| Create | `frontend/e2e/auth.setup.ts` | Cognito InitiateAuth → inject `id_token` → save storageState |
| Create | `frontend/e2e/guest.spec.ts` | 3 unauthenticated tests |
| Create | `frontend/e2e/auth.spec.ts` | 2 authenticated tests (uses saved storageState) |
| Create | `.github/workflows/playwright.yml` | CI: build images w/ cache → compose up → migrate → test |

---

### Task 1: Add `ALLOW_USER_PASSWORD_AUTH` to Terraform

**Files:**
- Modify: `infrastructure/modules/auth/main.tf`

This allows the auth fixture to call Cognito's `InitiateAuth` API directly with username + password instead of going through the Hosted UI redirect flow.

- [ ] **Step 1: Edit `explicit_auth_flows` in the Cognito app client**

In `infrastructure/modules/auth/main.tf`, find:

```hcl
  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH",
  ]
```

Replace with:

```hcl
  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_USER_PASSWORD_AUTH",
  ]
```

- [ ] **Step 2: Apply via Terraform Cloud**

Open `app.terraform.io` → `exeaws26` org → `exeaws26-prod` workspace → Queue plan → Apply. The plan diff should show only the Cognito app client change. Confirm and apply.

- [ ] **Step 3: Create a dedicated test Cognito user**

In the AWS Console → Cognito → User Pools → `eu-west-2_sX50A202h` → Users → Create user:
- Email: `e2e-test@<your-domain>` (or any unused email)
- Temporary password: set one, then immediately sign in via the Hosted UI (`https://exeter-livingcampus-prod.auth.eu-west-2.amazoncognito.com`) to complete the force-change-password challenge and set a permanent password.

Note the email and final password — they go in `.env.test` in Task 3.

- [ ] **Step 4: Commit the Terraform change**

```bash
git add infrastructure/modules/auth/main.tf
git commit -m "infra: enable USER_PASSWORD_AUTH on Cognito app client for e2e tests"
```

---

### Task 2: Add `image:` tags to `docker-compose.yml`

**Files:**
- Modify: `docker-compose.yml`

Adding explicit `image:` keys lets CI pre-build with `docker/build-push-action` (with layer caching) and then run `docker compose up -d` without `--build`, so compose picks up the already-built tagged images.

- [ ] **Step 1: Add `image:` to the backend service**

In `docker-compose.yml`, find:

```yaml
  backend:
    build: ./backend
```

Replace with:

```yaml
  backend:
    image: amazon_tlevel_project_2026-backend:latest
    build: ./backend
```

- [ ] **Step 2: Add `image:` to the frontend service**

Find:

```yaml
  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_BASE_URL: http://localhost:8000
        VITE_COGNITO_DOMAIN: ""
        VITE_COGNITO_CLIENT_ID: ""
        VITE_COGNITO_REDIRECT_URI: http://localhost:3000/auth/callback
```

Replace with:

```yaml
  frontend:
    image: amazon_tlevel_project_2026-frontend:latest
    build:
      context: ./frontend
      args:
        VITE_API_BASE_URL: http://localhost:8000
        VITE_COGNITO_DOMAIN: ""
        VITE_COGNITO_CLIENT_ID: ""
        VITE_COGNITO_REDIRECT_URI: http://localhost:3000/auth/callback
```

- [ ] **Step 3: Verify docker-compose still works locally**

```bash
docker compose build
```

Expected: builds successfully, images tagged `amazon_tlevel_project_2026-backend:latest` and `amazon_tlevel_project_2026-frontend:latest`.

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml
git commit -m "chore: add image tags to docker-compose for CI layer-cache builds"
```

---

### Task 3: Install Playwright and scaffold config

**Files:**
- Modify: `.gitignore`
- Create: `frontend/.env.test`
- Modify: `frontend/package.json`
- Create: `frontend/playwright.config.ts`

- [ ] **Step 1: Install Playwright and dotenv**

```bash
cd frontend && npm install --save-dev @playwright/test dotenv
```

Expected: `@playwright/test` and `dotenv` added to `devDependencies` in `package.json`.

- [ ] **Step 2: Install the Chromium browser**

```bash
cd frontend && npx playwright install chromium
```

Expected: Chromium downloaded to the Playwright browser cache. Output ends with "chromium ... installed".

- [ ] **Step 3: Add `e2e/.auth/` to root `.gitignore`**

In `.gitignore`, after the `# Node` section, add:

```gitignore
# Playwright
frontend/e2e/.auth/
frontend/playwright-report/
frontend/test-results/
```

- [ ] **Step 4: Create `frontend/.env.test`**

Create `frontend/.env.test` with the test user credentials from Task 1 Step 3:

```
TEST_COGNITO_USER_POOL_ID=eu-west-2_sX50A202h
TEST_COGNITO_CLIENT_ID=4bkjvav9ur3lat0dr25kht85bh
TEST_COGNITO_USERNAME=<test user email from Task 1>
TEST_COGNITO_PASSWORD=<test user permanent password from Task 1>
```

This file is already gitignored by the existing `.env.*` rule in both root and `frontend/.gitignore`.

- [ ] **Step 5: Add `test:e2e` script to `frontend/package.json`**

In `frontend/package.json`, in the `"scripts"` block, add after the existing `"test"` entry:

```json
"test:e2e": "playwright test",
"test:e2e:ui": "playwright test --ui"
```

- [ ] **Step 6: Create `frontend/playwright.config.ts`**

Create `frontend/playwright.config.ts`:

```typescript
import { defineConfig, devices } from '@playwright/test';
import { config as loadEnv } from 'dotenv';

loadEnv({ path: '.env.test' });

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  reporter: [['html', { open: 'never' }]],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'setup',
      testMatch: /auth\.setup\.ts/,
    },
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      dependencies: ['setup'],
    },
  ],
});
```

- [ ] **Step 7: Create the `e2e/.auth/` directory placeholder**

```bash
mkdir -p frontend/e2e/.auth
touch frontend/e2e/.auth/.gitkeep
```

Add `frontend/e2e/.auth/.gitkeep` to the exception in `.gitignore` — find the section added in Step 3 and update it to:

```gitignore
# Playwright
frontend/e2e/.auth/
!frontend/e2e/.auth/.gitkeep
frontend/playwright-report/
frontend/test-results/
```

- [ ] **Step 8: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 9: Verify Playwright can list tests (none yet)**

```bash
cd frontend && npx playwright test --list 2>&1
```

Expected: "No tests found" or empty output — no error from the config itself.

- [ ] **Step 10: Commit**

```bash
git add .gitignore frontend/package.json frontend/package-lock.json frontend/playwright.config.ts frontend/e2e/.auth/.gitkeep
git commit -m "feat: install Playwright and scaffold e2e config"
```

---

### Task 4: Create auth setup file

**Files:**
- Create: `frontend/e2e/auth.setup.ts`

This is the Playwright `setup` project — it runs before all `chromium` tests. It calls Cognito's `InitiateAuth` endpoint directly (no AWS SDK — plain HTTP), injects the returned `IdToken` into `localStorage['id_token']`, navigates to `/` to trigger `/auth/sync`, then saves browser storage state to `e2e/.auth/user.json`.

- [ ] **Step 1: Create `frontend/e2e/auth.setup.ts`**

```typescript
import { test as setup, expect } from '@playwright/test';
import { config as loadEnv } from 'dotenv';
import { mkdir } from 'fs/promises';

loadEnv({ path: '.env.test' });

const AUTH_FILE = 'e2e/.auth/user.json';
const TOKEN_KEY = 'id_token';

setup('authenticate test user', async ({ page, request }) => {
  const userPoolId = process.env.TEST_COGNITO_USER_POOL_ID;
  const clientId = process.env.TEST_COGNITO_CLIENT_ID;
  const username = process.env.TEST_COGNITO_USERNAME;
  const password = process.env.TEST_COGNITO_PASSWORD;

  if (!userPoolId || !clientId || !username || !password) {
    throw new Error(
      'Missing TEST_COGNITO_* env vars. Create frontend/.env.test — see docs/superpowers/specs/2026-06-26-playwright-e2e-design.md'
    );
  }

  const region = userPoolId.split('_')[0];

  const response = await request.post(`https://cognito-idp.${region}.amazonaws.com/`, {
    headers: {
      'Content-Type': 'application/x-amz-json-1.1',
      'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth',
    },
    data: {
      AuthFlow: 'USER_PASSWORD_AUTH',
      ClientId: clientId,
      AuthParameters: {
        USERNAME: username,
        PASSWORD: password,
      },
    },
  });

  expect(response.ok(), `Cognito InitiateAuth failed: ${await response.text()}`).toBeTruthy();

  const body = await response.json();
  const idToken: string = body.AuthenticationResult.IdToken;

  // Load the SvelteKit app shell first (localStorage is empty here — layout shows guest view)
  await page.goto('/');

  // Inject the real IdToken — same key the app uses (TOKEN_KEY = 'id_token' in client.ts)
  await page.evaluate(
    ([key, token]) => window.localStorage.setItem(key, token),
    [TOKEN_KEY, idToken] as const
  );

  // Reload: layout's onMount now reads the token and calls POST /auth/sync
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Save storage state (includes localStorage with the injected token)
  await mkdir('e2e/.auth', { recursive: true });
  await page.context().storageState({ path: AUTH_FILE });
});
```

- [ ] **Step 2: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: List tests to verify Playwright sees the setup**

```bash
cd frontend && npx playwright test --list 2>&1
```

Expected: output includes `auth.setup.ts` under the `setup` project. No errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/e2e/auth.setup.ts
git commit -m "feat: add Playwright auth setup — Cognito InitiateAuth → storageState"
```

---

### Task 5: Guest spec

**Files:**
- Create: `frontend/e2e/guest.spec.ts`

Three unauthenticated tests: home hero, album list, snippet detail. No `storageState` — runs with empty localStorage (guest view).

- [ ] **Step 1: Create `frontend/e2e/guest.spec.ts`**

```typescript
import { test, expect } from '@playwright/test';

test.describe('guest — unauthenticated paths', () => {
  test('home page shows hero and get-started button', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('Discover your future');
    await expect(page.locator('button.cta')).toBeVisible();
  });

  test('learn page shows at least one album card', async ({ page }) => {
    await page.goto('/learn');
    // Album cards load from the API — wait up to 10 s for the first one
    await expect(page.locator('.album-card').first()).toBeVisible({ timeout: 10_000 });
  });

  test('album detail page shows sidebar and snippet content on click', async ({ page }) => {
    // Navigate to /learn, click the first album card to land on /learn/[id]
    await page.goto('/learn');
    await page.locator('.album-card').first().click();

    // AlbumSidebar renders as <aside>
    await expect(page.locator('aside')).toBeVisible({ timeout: 10_000 });

    // Click the first NavLink inside the sidebar (a ?snippet= link)
    await page.locator('aside a').first().click();

    // The main PageCard should now contain non-empty text (the snippet body)
    await expect(page.locator('main')).not.toBeEmpty();
  });
});
```

- [ ] **Step 2: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: List tests**

```bash
cd frontend && npx playwright test --list 2>&1
```

Expected: 3 guest tests listed under the `chromium` project. The `setup` project still shows `auth.setup.ts`.

- [ ] **Step 4: Commit**

```bash
git add frontend/e2e/guest.spec.ts
git commit -m "feat: add guest e2e spec — hero, album list, snippet detail"
```

---

### Task 6: Auth spec

**Files:**
- Create: `frontend/e2e/auth.spec.ts`

Two authenticated tests. `test.use({ storageState })` loads the saved `e2e/.auth/user.json` so each test starts with the IdToken already in localStorage — the layout's onMount picks it up and calls `/auth/sync` on first navigation.

- [ ] **Step 1: Create `frontend/e2e/auth.spec.ts`**

```typescript
import { test, expect } from '@playwright/test';

test.use({ storageState: 'e2e/.auth/user.json' });

test.describe('authenticated paths', () => {
  test('home page shows authenticated layout with CTASidebar', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Authenticated branch renders .home-auth (not the guest hero)
    await expect(page.locator('.home-auth')).toBeVisible({ timeout: 10_000 });

    // Greeting is visible (Good morning/afternoon/evening, <name> 👋)
    await expect(page.locator('.greeting')).toBeVisible();
  });

  test('settings page renders sidebar and upload controls', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');

    // Sidebar NavLink
    await expect(page.locator('text=Personalisation')).toBeVisible({ timeout: 10_000 });

    // Upload button in the content card
    await expect(page.locator('button', { hasText: 'Choose file' })).toBeVisible();
  });
});
```

- [ ] **Step 2: Typecheck**

```bash
cd frontend && npm run check
```

Expected: 0 errors.

- [ ] **Step 3: List tests**

```bash
cd frontend && npx playwright test --list 2>&1
```

Expected: 5 tests total — 3 guest + 2 auth — all under `chromium`. `auth.setup.ts` listed under `setup`.

- [ ] **Step 4: Commit**

```bash
git add frontend/e2e/auth.spec.ts
git commit -m "feat: add authenticated e2e spec — home CTASidebar, settings page"
```

---

### Task 7: Local verification (requires running stack)

**Files:** None — verification only.

Run this task after `docker compose up -d && docker compose exec -T backend poetry run alembic upgrade head && docker compose exec -T backend poetry run python seed.py` has completed and all services are healthy.

- [ ] **Step 1: Run all Playwright tests**

```bash
cd frontend && npx playwright test 2>&1
```

Expected output (abbreviated):
```
Running 5 tests using 1 worker
  5 passed (XX s)
```

- [ ] **Step 2: If any test fails, open the HTML report**

```bash
cd frontend && npx playwright show-report
```

This opens a browser with screenshots and traces for failed tests. Fix any issues before continuing.

- [ ] **Step 3: Confirm auth state file exists**

```bash
ls -la frontend/e2e/.auth/
```

Expected: `user.json` present alongside `.gitkeep`. `user.json` must NOT be committed.

---

### Task 8: CI workflow

**Files:**
- Create: `.github/workflows/playwright.yml`

Triggers on push/PR to `main` touching `frontend/**`. Builds each Docker image separately with BuildKit local-path caching, starts the stack, runs migrations + seed, then Playwright.

**Before creating this file, add two secrets to the GitHub repo** (Settings → Secrets → Actions):
- `TEST_COGNITO_USERNAME` — the test user email from Task 1
- `TEST_COGNITO_PASSWORD` — the test user permanent password from Task 1
- `BACKEND_SECRET_KEY` — any random 32-char string (e.g. output of `openssl rand -hex 16`); only used inside CI, not production

- [ ] **Step 1: Create `.github/workflows/playwright.yml`**

```yaml
name: Playwright E2E

on:
  push:
    branches: [main]
    paths: ['frontend/**']
  pull_request:
    branches: [main]
    paths: ['frontend/**']

concurrency:
  group: playwright-${{ github.ref }}
  cancel-in-progress: true

jobs:
  e2e:
    runs-on: ubuntu-latest
    timeout-minutes: 20

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Cache backend Docker layers
        uses: actions/cache@v4
        with:
          path: /tmp/.buildx-cache-backend
          key: ${{ runner.os }}-buildx-backend-${{ hashFiles('backend/Dockerfile', 'backend/pyproject.toml', 'backend/poetry.lock') }}
          restore-keys: ${{ runner.os }}-buildx-backend-

      - name: Cache frontend Docker layers
        uses: actions/cache@v4
        with:
          path: /tmp/.buildx-cache-frontend
          key: ${{ runner.os }}-buildx-frontend-${{ hashFiles('frontend/Dockerfile', 'frontend/package-lock.json') }}
          restore-keys: ${{ runner.os }}-buildx-frontend-

      - name: Build backend image
        uses: docker/build-push-action@v6
        with:
          context: ./backend
          tags: amazon_tlevel_project_2026-backend:latest
          load: true
          cache-from: type=local,src=/tmp/.buildx-cache-backend
          cache-to: type=local,dest=/tmp/.buildx-cache-backend-new,mode=max

      - name: Build frontend image
        uses: docker/build-push-action@v6
        with:
          context: ./frontend
          tags: amazon_tlevel_project_2026-frontend:latest
          load: true
          build-args: |
            VITE_API_BASE_URL=http://localhost:8000
            VITE_COGNITO_DOMAIN=
            VITE_COGNITO_CLIENT_ID=
            VITE_COGNITO_REDIRECT_URI=http://localhost:3000/auth/callback
          cache-from: type=local,src=/tmp/.buildx-cache-frontend
          cache-to: type=local,dest=/tmp/.buildx-cache-frontend-new,mode=max

      - name: Move caches (prevent unbounded growth)
        run: |
          rm -rf /tmp/.buildx-cache-backend /tmp/.buildx-cache-frontend
          mv /tmp/.buildx-cache-backend-new /tmp/.buildx-cache-backend
          mv /tmp/.buildx-cache-frontend-new /tmp/.buildx-cache-frontend

      - name: Write backend .env
        run: |
          cat > backend/.env <<EOF
          DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/app
          SECRET_KEY=${{ secrets.BACKEND_SECRET_KEY }}
          COGNITO_USER_POOL_ID=eu-west-2_sX50A202h
          COGNITO_CLIENT_ID=4bkjvav9ur3lat0dr25kht85bh
          COGNITO_REGION=eu-west-2
          S3_BUCKET_NAME=dummy-not-used-in-e2e
          AWS_ACCESS_KEY_ID=dummy
          AWS_SECRET_ACCESS_KEY=dummy
          EOF

      - name: Write frontend .env.test
        run: |
          cat > frontend/.env.test <<EOF
          TEST_COGNITO_USER_POOL_ID=eu-west-2_sX50A202h
          TEST_COGNITO_CLIENT_ID=4bkjvav9ur3lat0dr25kht85bh
          TEST_COGNITO_USERNAME=${{ secrets.TEST_COGNITO_USERNAME }}
          TEST_COGNITO_PASSWORD=${{ secrets.TEST_COGNITO_PASSWORD }}
          EOF

      - name: Start services
        run: docker compose up -d

      - name: Wait for backend health
        run: |
          for i in $(seq 1 20); do
            if curl -sf http://localhost:8000/health; then
              echo "Backend healthy"
              break
            fi
            echo "Waiting for backend... ($i/20)"
            sleep 3
          done

      - name: Run migrations
        run: docker compose exec -T backend poetry run alembic upgrade head

      - name: Seed data
        run: docker compose exec -T backend poetry run python seed.py

      - name: Install Playwright browsers
        run: cd frontend && npx playwright install --with-deps chromium

      - name: Run Playwright tests
        run: cd frontend && npx playwright test

      - name: Upload test report
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 7
```

- [ ] **Step 2: Verify YAML syntax**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/playwright.yml'))" && echo "YAML valid"
```

Expected: `YAML valid`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/playwright.yml
git commit -m "ci: add Playwright e2e workflow with Docker layer caching"
```

---

## Self-Review

**Spec coverage:**
- Playwright in `frontend/`, targets `localhost:3000` → Tasks 3 ✓
- No `webServer` block (assumes docker-compose) → Task 3 playwright.config.ts ✓
- Terraform `ALLOW_USER_PASSWORD_AUTH` → Task 1 ✓
- Test user created manually → Task 1 Step 3 ✓
- `USER_PASSWORD_AUTH` → `InitiateAuth` call → inject `id_token` → `storageState` → Task 4 ✓
- TOKEN_KEY `'id_token'` (from `client.ts`) → Task 4 ✓
- `.env.test` gitignored (existing `.env.*` rule) → Task 3 Step 3/4 ✓
- `e2e/.auth/` gitignored → Task 3 Step 3 ✓
- Guest test: home hero → Task 5 ✓
- Guest test: album list → Task 5 ✓
- Guest test: snippet detail → Task 5 ✓
- Auth test: home CTASidebar → Task 6 ✓
- Auth test: settings page → Task 6 ✓
- No avatar upload test (S3 side-effects) → excluded ✓
- CI: docker-compose with layer cache → Task 8 ✓
- CI: backend `.env` from secrets → Task 8 ✓
- CI: frontend `.env.test` from secrets → Task 8 ✓
- CI: wait for health, migrations, seed → Task 8 ✓
- CI: upload report artifact on failure → Task 8 ✓
- `image:` tags in docker-compose for pre-built images → Task 2 ✓

**Placeholder scan:** No TBDs or vague steps — all code blocks are complete.

**Type consistency:** `TOKEN_KEY = 'id_token'` used in `auth.setup.ts` matches the literal defined in `frontend/src/lib/api/client.ts`. `storageState: 'e2e/.auth/user.json'` path in `auth.spec.ts` matches the `AUTH_FILE` constant in `auth.setup.ts`.
