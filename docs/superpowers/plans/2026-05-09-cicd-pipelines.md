# CI/CD Pipelines Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up GitHub Actions CI/CD pipelines that automatically lint (autofix + warn), test, build, and deploy both the SvelteKit frontend and FastAPI backend to AWS on every merge to `main`.

**Architecture:** Two workflow files (one per service) each containing four jobs — `lint-autofix`, `test`, `build`, and `deploy`. Linting autofixes on PRs by committing back to the branch; it never fails the pipeline. Tests must pass. Deploy only runs on `main` using GitHub's OIDC federation to assume an AWS IAM role (no stored credentials). Frontend goes to S3 + CloudFront; backend goes to App Runner via ECR.

**Tech Stack:** GitHub Actions, Python 3.12, Ruff, pytest, Node 20, ESLint, Prettier, Vitest, Docker, AWS ECR, AWS App Runner, AWS S3, AWS CloudFront, `stefanzweifel/git-auto-commit-action`, `aws-actions/configure-aws-credentials` (OIDC)

---

## File Map

| File | Purpose |
|------|---------|
| `.github/workflows/backend.yml` | Backend lint → test → build → deploy pipeline |
| `.github/workflows/frontend.yml` | Frontend lint → test → build → deploy pipeline |
| `backend/pyproject.toml` | Ruff linting/formatting config |
| `backend/Dockerfile` | Container image for App Runner |
| `frontend/eslint.config.js` | ESLint flat config with Svelte plugin |
| `frontend/prettier.config.js` | Prettier config (includes Svelte plugin) |

---

## Task 1: Branch Protection (Do This First)

Branch protection ensures autofix commit-back works correctly (it targets PR branches, not main directly). Set this up before any workflow runs.

**Files:** GitHub repository settings (no files to edit)

- [ ] **Step 1: Open branch protection settings**

  Go to: `https://github.com/H4RL33/exe_coll_t_level_aws_2026/settings/branches` → "Add branch protection rule"

- [ ] **Step 2: Configure the rule**

  - Branch name pattern: `main`
  - ✅ Require a pull request before merging
  - ✅ Require status checks to pass before merging
    - (Add the check names after the workflows exist: `Backend / Test`, `Frontend / Test`)
  - ✅ Require branches to be up to date before merging
  - ✅ Do not allow bypassing the above settings (uncheck for yourself if you need escape hatches)

- [ ] **Step 3: Save the rule**

---

## Task 2: Backend Linting Config

**Files:**
- Create: `backend/pyproject.toml`

- [ ] **Step 1: Create `backend/pyproject.toml`**

  ```toml
  [tool.ruff]
  target-version = "py312"
  line-length = 88

  [tool.ruff.lint]
  # E/W = pycodestyle, F = pyflakes, I = isort, UP = pyupgrade
  select = ["E", "W", "F", "I", "UP"]
  # Don't fail on line-length warnings — they're style, not bugs
  ignore = ["E501"]
  fixable = ["ALL"]

  [tool.ruff.format]
  quote-style = "double"
  indent-style = "space"
  ```

- [ ] **Step 2: Verify ruff works locally**

  ```bash
  cd backend
  pip install ruff
  ruff check --fix .
  ruff format .
  ```

  Expected: ruff processes files, outputs any unfixable warnings, exits 0.

- [ ] **Step 3: Commit**

  ```bash
  git add backend/pyproject.toml
  git commit -m "chore: add ruff linting config for backend"
  ```

---

## Task 3: Frontend Linting Config

**Files:**
- Create: `frontend/eslint.config.js`
- Create: `frontend/prettier.config.js`

These assume the SvelteKit project has already been scaffolded with `npm create svelte@latest frontend`. If not, scaffold it first: `npm create svelte@latest frontend` (choose skeleton, TypeScript, ESLint, Prettier, Vitest options).

- [ ] **Step 1: Install linting packages**

  ```bash
  cd frontend
  npm install --save-dev eslint eslint-plugin-svelte @typescript-eslint/eslint-plugin @typescript-eslint/parser prettier prettier-plugin-svelte globals
  ```

- [ ] **Step 2: Create `frontend/eslint.config.js`**

  ```js
  import js from '@eslint/js';
  import ts from '@typescript-eslint/eslint-plugin';
  import tsParser from '@typescript-eslint/parser';
  import svelte from 'eslint-plugin-svelte';
  import svelteParser from 'svelte-eslint-parser';
  import globals from 'globals';

  export default [
    js.configs.recommended,
    {
      files: ['**/*.ts'],
      plugins: { '@typescript-eslint': ts },
      languageOptions: {
        parser: tsParser,
        globals: { ...globals.browser, ...globals.node },
      },
      rules: {
        ...ts.configs.recommended.rules,
        // Warn only — never block the pipeline
        '@typescript-eslint/no-explicit-any': 'warn',
        '@typescript-eslint/no-unused-vars': 'warn',
      },
    },
    {
      files: ['**/*.svelte'],
      plugins: { svelte },
      languageOptions: {
        parser: svelteParser,
        parserOptions: { parser: tsParser },
        globals: { ...globals.browser },
      },
      rules: {
        ...svelte.configs.recommended.rules,
      },
    },
    {
      ignores: ['.svelte-kit/**', 'build/**', 'node_modules/**'],
    },
  ];
  ```

- [ ] **Step 3: Create `frontend/prettier.config.js`**

  ```js
  export default {
    useTabs: false,
    tabWidth: 2,
    singleQuote: true,
    trailingComma: 'es5',
    printWidth: 100,
    plugins: ['prettier-plugin-svelte'],
    overrides: [{ files: '*.svelte', options: { parser: 'svelte' } }],
  };
  ```

- [ ] **Step 4: Verify locally**

  ```bash
  cd frontend
  npx prettier --write .
  npx eslint .
  ```

  Expected: Prettier reformats files silently. ESLint may output warnings but exits 0 (all rules are `warn`).

- [ ] **Step 5: Commit**

  ```bash
  git add frontend/eslint.config.js frontend/prettier.config.js frontend/package.json frontend/package-lock.json
  git commit -m "chore: add eslint and prettier config for frontend"
  ```

---

## Task 4: Backend Dockerfile

**Files:**
- Create: `backend/Dockerfile`

- [ ] **Step 1: Create `backend/Dockerfile`**

  ```dockerfile
  FROM python:3.12-slim

  WORKDIR /app

  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  COPY . .

  EXPOSE 8000
  CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

  This assumes `backend/main.py` has a FastAPI `app` instance and `backend/requirements.txt` exists with at least `fastapi` and `uvicorn[standard]`.

- [ ] **Step 2: Verify the image builds**

  ```bash
  cd backend
  docker build -t backend-test .
  docker run --rm -p 8000:8000 backend-test
  # Ctrl+C to stop
  ```

  Expected: FastAPI server starts, `http://localhost:8000/docs` loads.

- [ ] **Step 3: Commit**

  ```bash
  git add backend/Dockerfile
  git commit -m "chore: add backend Dockerfile for App Runner"
  ```

---

## Task 5: AWS OIDC IAM Role

This lets GitHub Actions assume an AWS role without storing long-lived credentials in GitHub Secrets. Do this once in the AWS console or via Terraform.

**Files:** AWS IAM (no repo files) + GitHub Secrets configuration

- [ ] **Step 1: Create the OIDC identity provider in AWS IAM**

  In the AWS Console → IAM → Identity Providers → Add provider:
  - Provider type: OpenID Connect
  - Provider URL: `https://token.actions.githubusercontent.com`
  - Audience: `sts.amazonaws.com`

  Click "Get thumbprint" then "Add provider".

- [ ] **Step 2: Create an IAM role for GitHub Actions**

  IAM → Roles → Create role → Web identity:
  - Identity provider: `token.actions.githubusercontent.com`
  - Audience: `sts.amazonaws.com`
  - Condition: `token.actions.githubusercontent.com:sub` = `repo:H4RL33/exe_coll_t_level_aws_2026:ref:refs/heads/main`

  Attach these managed policies (or create a custom policy scoped more tightly later):
  - `AmazonS3FullAccess` (frontend deploy)
  - `CloudFrontFullAccess` (cache invalidation)
  - `AmazonEC2ContainerRegistryFullAccess` (push Docker images)
  - `AWSAppRunnerFullAccess` (backend deploy)

  Name the role: `github-actions-cicd`

- [ ] **Step 3: Add GitHub Secrets**

  Go to: `https://github.com/H4RL33/exe_coll_t_level_aws_2026/settings/secrets/actions`

  Add these secrets (values come from your AWS setup):

  | Secret name | Value |
  |-------------|-------|
  | `AWS_ROLE_ARN` | `arn:aws:iam::<ACCOUNT_ID>:role/github-actions-cicd` |
  | `AWS_REGION` | `eu-west-2` (London — pick your region) |
  | `S3_BUCKET` | The S3 bucket name for the frontend (e.g. `tlevel-frontend-prod`) |
  | `CLOUDFRONT_DISTRIBUTION_ID` | From your CloudFront distribution |
  | `ECR_REPOSITORY` | Full ECR URI, e.g. `<ACCOUNT>.dkr.ecr.eu-west-2.amazonaws.com/tlevel-backend` |
  | `APP_RUNNER_SERVICE_ARN` | From your App Runner service |

---

## Task 6: Backend GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/backend.yml`

- [ ] **Step 1: Create `.github/workflows/backend.yml`**

  ```yaml
  name: Backend

  on:
    push:
      branches: [main]
      paths: ['backend/**']
    pull_request:
      paths: ['backend/**']

  permissions:
    contents: write       # allows autofix commit-back on PRs
    id-token: write       # allows OIDC AWS auth on deploy
    pull-requests: read

  jobs:
    lint-autofix:
      name: Lint & Autofix
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
          with:
            # On PRs, check out the actual branch so we can commit back
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
          run: ruff format backend/

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

        - name: Install dependencies
          run: |
            cd backend
            pip install -r requirements.txt
            pip install pytest pytest-asyncio httpx

        - name: Run tests
          run: pytest backend/tests/ -v --tb=short

    build-and-push:
      name: Build & Push Image
      runs-on: ubuntu-latest
      needs: test
      # Only build/push the image on main — not on PRs
      if: github.ref == 'refs/heads/main' && github.event_name == 'push'
      outputs:
        image-uri: ${{ steps.push.outputs.image-uri }}
      steps:
        - uses: actions/checkout@v4

        - name: Configure AWS credentials (OIDC)
          uses: aws-actions/configure-aws-credentials@v4
          with:
            role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
            aws-region: ${{ secrets.AWS_REGION }}

        - name: Log in to ECR
          id: login-ecr
          uses: aws-actions/amazon-ecr-login@v2

        - name: Build, tag, and push image
          id: push
          env:
            ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
            IMAGE_TAG: ${{ github.sha }}
          run: |
            docker build -t $ECR_REGISTRY/${{ secrets.ECR_REPOSITORY }}:$IMAGE_TAG backend/
            docker push $ECR_REGISTRY/${{ secrets.ECR_REPOSITORY }}:$IMAGE_TAG
            echo "image-uri=$ECR_REGISTRY/${{ secrets.ECR_REPOSITORY }}:$IMAGE_TAG" >> "$GITHUB_OUTPUT"

    deploy:
      name: Deploy to App Runner
      runs-on: ubuntu-latest
      needs: build-and-push
      if: github.ref == 'refs/heads/main' && github.event_name == 'push'
      steps:
        - name: Configure AWS credentials (OIDC)
          uses: aws-actions/configure-aws-credentials@v4
          with:
            role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
            aws-region: ${{ secrets.AWS_REGION }}

        - name: Deploy new image to App Runner
          run: |
            aws apprunner start-deployment \
              --service-arn ${{ secrets.APP_RUNNER_SERVICE_ARN }}

        - name: Wait for deployment to complete
          run: |
            aws apprunner wait service-running \
              --service-arn ${{ secrets.APP_RUNNER_SERVICE_ARN }}
            echo "Backend deployed successfully."
  ```

- [ ] **Step 2: Create the workflow via a PR (not a direct push to main)**

  ```bash
  git checkout -b chore/backend-ci-workflow
  git add .github/workflows/backend.yml
  git commit -m "ci: add backend GitHub Actions workflow"
  git push -u origin chore/backend-ci-workflow
  gh pr create --title "ci: add backend CI/CD workflow" --body "Adds lint-autofix, test, build, and deploy pipeline for the FastAPI backend."
  ```

- [ ] **Step 3: Verify the workflow runs**

  After opening the PR, watch the Actions tab. Expected: `lint-autofix` runs and passes, `test` runs (may fail if no tests exist yet — that's fine, add a placeholder). `build-and-push` and `deploy` should be skipped on the PR.

---

## Task 7: Frontend GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/frontend.yml`

- [ ] **Step 1: Create `.github/workflows/frontend.yml`**

  ```yaml
  name: Frontend

  on:
    push:
      branches: [main]
      paths: ['frontend/**']
    pull_request:
      paths: ['frontend/**']

  permissions:
    contents: write
    id-token: write
    pull-requests: read

  jobs:
    lint-autofix:
      name: Lint & Autofix
      runs-on: ubuntu-latest
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
          run: cd frontend && npx prettier --write .

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

    build:
      name: Build
      runs-on: ubuntu-latest
      needs: test
      steps:
        - uses: actions/checkout@v4

        - uses: actions/setup-node@v4
          with:
            node-version: '20'
            cache: npm
            cache-dependency-path: frontend/package-lock.json

        - name: Install dependencies
          run: cd frontend && npm ci

        - name: Build
          run: cd frontend && npm run build

        - name: Upload build artifact
          uses: actions/upload-artifact@v4
          with:
            name: frontend-build-${{ github.sha }}
            path: frontend/build/
            retention-days: 1

    deploy:
      name: Deploy to S3 + CloudFront
      runs-on: ubuntu-latest
      needs: build
      if: github.ref == 'refs/heads/main' && github.event_name == 'push'
      steps:
        - name: Download build artifact
          uses: actions/download-artifact@v4
          with:
            name: frontend-build-${{ github.sha }}
            path: build/

        - name: Configure AWS credentials (OIDC)
          uses: aws-actions/configure-aws-credentials@v4
          with:
            role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
            aws-region: ${{ secrets.AWS_REGION }}

        - name: Sync to S3
          run: |
            aws s3 sync build/ s3://${{ secrets.S3_BUCKET }}/ \
              --delete \
              --cache-control "public, max-age=31536000, immutable" \
              --exclude "*.html"
            # HTML files should not be aggressively cached
            aws s3 sync build/ s3://${{ secrets.S3_BUCKET }}/ \
              --exclude "*" \
              --include "*.html" \
              --cache-control "no-cache"

        - name: Invalidate CloudFront cache
          run: |
            aws cloudfront create-invalidation \
              --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} \
              --paths "/*"
            echo "Frontend deployed successfully."
  ```

  > **Note on SvelteKit adapter:** The `build/` output directory assumes `@sveltejs/adapter-static` is configured in `svelte.config.js`. If using `adapter-node`, the deploy target changes (you'd containerize and deploy to App Runner the same way as the backend, not S3). For a content-heavy knowledge base, `adapter-static` is the right choice.

- [ ] **Step 2: Verify SvelteKit is using adapter-static**

  In `frontend/svelte.config.js`:

  ```js
  import adapter from '@sveltejs/adapter-static';
  export default {
    kit: {
      adapter: adapter({ fallback: '200.html' }),
    },
  };
  ```

  Install if needed: `cd frontend && npm install --save-dev @sveltejs/adapter-static`

- [ ] **Step 3: Create and merge via a PR**

  ```bash
  git checkout -b chore/frontend-ci-workflow
  git add .github/workflows/frontend.yml frontend/svelte.config.js
  git commit -m "ci: add frontend GitHub Actions workflow"
  git push -u origin chore/frontend-ci-workflow
  gh pr create --title "ci: add frontend CI/CD workflow" --body "Adds lint-autofix, test, build, and deploy pipeline for the SvelteKit frontend."
  ```

---

## Task 8: Placeholder Tests (Unblock CI)

The test jobs will fail if there are no test files. Add minimal placeholder tests so the CI can go green while Bobby and Ahad write the real logic.

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_placeholder.py`
- Create: `frontend/src/lib/placeholder.test.ts`

- [ ] **Step 1: Create backend placeholder test**

  `backend/tests/__init__.py` — empty file.

  `backend/tests/test_placeholder.py`:
  ```python
  def test_placeholder():
      """Remove this once real tests exist."""
      assert True
  ```

- [ ] **Step 2: Verify backend test runs**

  ```bash
  cd backend
  pytest tests/ -v
  ```

  Expected:
  ```
  tests/test_placeholder.py::test_placeholder PASSED
  1 passed in 0.01s
  ```

- [ ] **Step 3: Create frontend placeholder test**

  `frontend/src/lib/placeholder.test.ts`:
  ```ts
  import { describe, it, expect } from 'vitest';

  describe('placeholder', () => {
    it('passes', () => {
      expect(true).toBe(true);
    });
  });
  ```

- [ ] **Step 4: Verify frontend test runs**

  ```bash
  cd frontend
  npm run test:unit -- --run
  ```

  Expected:
  ```
  ✓ src/lib/placeholder.test.ts (1)
  Test Files  1 passed (1)
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add backend/tests/ frontend/src/lib/placeholder.test.ts
  git commit -m "test: add placeholder tests to unblock CI"
  ```

---

## Summary: What Each Developer Needs to Know

Add this section to the project README or a `docs/contributing.md` for Bobby and Ahad:

```
### How CI/CD Works

**On a pull request:**
1. Linting runs automatically. If it can fix issues (formatting, import order), it will
   commit those fixes back to your branch automatically. You don't need to do anything.
2. Any remaining style warnings appear in the PR checks — these are informational only
   and don't block merging.
3. Tests must pass. If tests fail, the PR cannot merge.

**On merge to main:**
1. Tests run again.
2. If tests pass, the app deploys automatically — frontend to CloudFront, backend to
   App Runner.
3. Deployment takes ~2-5 minutes. Check the Actions tab to monitor progress.

**Before you push:**
Run these locally to avoid CI noise:
- Backend: `cd backend && ruff check --fix . && ruff format . && pytest tests/`
- Frontend: `cd frontend && npm run lint && npm test -- --run`
```

---

## Self-Review Checklist

- [x] **Autofix on PR, warn on direct push** — `stefanzweifel/git-auto-commit-action` only runs when `github.event_name == 'pull_request'`; lint steps use `|| true` so they never fail
- [x] **Tests must pass** — `test` job has no `continue-on-error`, no `|| true`; deploy `needs: test`
- [x] **Deploy only on main** — `if: github.ref == 'refs/heads/main' && github.event_name == 'push'` on all deploy/build-push jobs
- [x] **No static AWS credentials** — OIDC via `aws-actions/configure-aws-credentials` with `id-token: write` permission
- [x] **Path filters** — workflows only trigger when relevant files change (`paths: ['backend/**']` etc.) to avoid unnecessary runs
- [x] **Placeholder tests** — Task 8 unblocks CI before real tests exist
- [x] **Branch protection** — Task 1 must be done first or autofix commit-back can break on direct pushes to main
- [x] **SvelteKit adapter** — noted in Task 7; static adapter required for S3 deploy
- [x] **Cache invalidation** — HTML files use `no-cache` so users always get the latest; assets use long-lived cache with `--delete` to purge stale files
