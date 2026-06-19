# GHCR Release Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two independent GitHub Actions release workflows that bump a VERSION file, create a git tag, and push a versioned Docker image to GHCR whenever a PR with a `bump-{service}:{level}` label is merged into main.

**Architecture:** Two separate workflow files (`release-backend.yml`, `release-frontend.yml`) each triggered by `pull_request: closed` on main. Each reads its own `VERSION` file, applies a semver bump driven by the PR label, commits and tags directly to main, then builds and pushes the Docker image to GHCR. All auth uses the built-in `GITHUB_TOKEN` — no extra secrets needed.

**Tech Stack:** GitHub Actions, Docker (via `docker/build-push-action@v6`), GHCR, bash semver bump script

---

## File Map

| Action | Path |
|---|---|
| Create | `backend/VERSION` |
| Create | `frontend/VERSION` |
| Create | `.github/workflows/release-backend.yml` |
| Create | `.github/workflows/release-frontend.yml` |

---

### Task 1: Create VERSION files

**Files:**
- Create: `backend/VERSION`
- Create: `frontend/VERSION`

- [ ] **Step 1: Create backend/VERSION**

  ```
  0.1.0
  ```
  File must be plain text with no trailing newline issues — write it with:
  ```bash
  echo -n "0.1.0" > backend/VERSION
  ```

- [ ] **Step 2: Create frontend/VERSION**

  ```bash
  echo -n "0.1.0" > frontend/VERSION
  ```

- [ ] **Step 3: Verify contents**

  ```bash
  cat backend/VERSION && echo && cat frontend/VERSION
  ```
  Expected output:
  ```
  0.1.0
  0.1.0
  ```

- [ ] **Step 4: Commit**

  ```bash
  git add backend/VERSION frontend/VERSION
  git commit -m "chore: add VERSION files at 0.1.0"
  ```

---

### Task 2: Create GitHub labels

**Files:** No files — GitHub repo labels via CLI.

These labels control which service gets bumped and by how much. Run each command from the repo root (requires `gh` CLI authenticated).

- [ ] **Step 1: Create backend bump labels**

  ```bash
  gh label create "bump-backend:patch" --color "0075ca" --description "Increment backend patch version"
  gh label create "bump-backend:minor" --color "e4e669" --description "Increment backend minor version"
  gh label create "bump-backend:major" --color "d93f0b" --description "Increment backend major version"
  ```

- [ ] **Step 2: Create frontend bump labels**

  ```bash
  gh label create "bump-frontend:patch" --color "0075ca" --description "Increment frontend patch version"
  gh label create "bump-frontend:minor" --color "e4e669" --description "Increment frontend minor version"
  gh label create "bump-frontend:major" --color "d93f0b" --description "Increment frontend major version"
  ```

- [ ] **Step 3: Verify labels exist**

  ```bash
  gh label list | grep bump
  ```
  Expected: six lines, one per label above.

---

### Task 3: Set repository variables

**Files:** No files — GitHub repo variables via CLI or UI.

These are `vars.*` (not secrets) — they are baked into the frontend Docker image at build time. You must supply real production values.

- [ ] **Step 1: Set each variable**

  Replace the placeholder values with your actual production values:
  ```bash
  gh variable set VITE_API_BASE_URL --body "https://api.yourdomain.com"
  gh variable set VITE_COGNITO_DOMAIN --body "your-pool.auth.eu-west-1.amazoncognito.com"
  gh variable set VITE_COGNITO_CLIENT_ID --body "your-client-id"
  gh variable set VITE_COGNITO_REDIRECT_URI --body "https://yourdomain.com/auth/callback"
  ```

- [ ] **Step 2: Verify variables are set**

  ```bash
  gh variable list
  ```
  Expected: four rows, one per variable above.

---

### Task 4: Allow github-actions[bot] to push to main

**Files:** No files — GitHub branch protection settings.

The release workflow commits the VERSION bump directly to main. If main has branch protection requiring PRs, the bot will be rejected unless it is listed as a bypass actor.

- [ ] **Step 1: Open branch protection settings**

  Navigate to: `https://github.com/<owner>/<repo>/settings/branches`

  Click **Edit** on the main branch rule.

- [ ] **Step 2: Add bypass actor**

  Under **"Allow specified actors to bypass required pull requests"**, search for and add:
  - `github-actions[bot]`

  Save the rule.

- [ ] **Step 3: Confirm** (optional CLI check)

  ```bash
  gh api repos/:owner/:repo/branches/main/protection --jq '.required_pull_request_reviews'
  ```
  This step can be skipped if you know branch protection is not enabled — the workflows will still work without it.

---

### Task 5: Create release-backend.yml

**Files:**
- Create: `.github/workflows/release-backend.yml`

- [ ] **Step 1: Create the workflow file**

  ```yaml
  name: Release Backend

  on:
    pull_request:
      types: [closed]
      branches: [main]

  permissions: {}

  jobs:
    release:
      name: Release
      if: |
        github.event.pull_request.merged == true && (
          contains(github.event.pull_request.labels.*.name, 'bump-backend:patch') ||
          contains(github.event.pull_request.labels.*.name, 'bump-backend:minor') ||
          contains(github.event.pull_request.labels.*.name, 'bump-backend:major')
        )
      runs-on: ubuntu-latest
      permissions:
        contents: write
        packages: write
      steps:
        - uses: actions/checkout@v4
          with:
            token: ${{ secrets.GITHUB_TOKEN }}
            fetch-depth: 0

        - name: Determine bump type
          id: bump
          run: |
            if [[ "${{ contains(github.event.pull_request.labels.*.name, 'bump-backend:major') }}" == "true" ]]; then
              echo "type=major" >> $GITHUB_OUTPUT
            elif [[ "${{ contains(github.event.pull_request.labels.*.name, 'bump-backend:minor') }}" == "true" ]]; then
              echo "type=minor" >> $GITHUB_OUTPUT
            else
              echo "type=patch" >> $GITHUB_OUTPUT
            fi

        - name: Bump version
          id: version
          run: |
            current=$(cat backend/VERSION)
            IFS='.' read -r major minor patch <<< "$current"
            case "${{ steps.bump.outputs.type }}" in
              major) major=$((major + 1)); minor=0; patch=0 ;;
              minor) minor=$((minor + 1)); patch=0 ;;
              patch) patch=$((patch + 1)) ;;
            esac
            new="$major.$minor.$patch"
            echo "$new" > backend/VERSION
            echo "new=$new" >> $GITHUB_OUTPUT

        - name: Commit and tag
          run: |
            git config user.name "github-actions[bot]"
            git config user.email "github-actions[bot]@users.noreply.github.com"
            git add backend/VERSION
            git commit -m "chore: bump backend to v${{ steps.version.outputs.new }} [skip ci]"
            git tag "backend-v${{ steps.version.outputs.new }}"
            git push origin main --follow-tags

        - name: Set lowercase image name
          id: image
          run: echo "name=$(echo 'ghcr.io/${{ github.repository }}-backend' | tr '[:upper:]' '[:lower:]')" >> $GITHUB_OUTPUT

        - name: Log in to GHCR
          uses: docker/login-action@v3
          with:
            registry: ghcr.io
            username: ${{ github.actor }}
            password: ${{ secrets.GITHUB_TOKEN }}

        - uses: docker/setup-buildx-action@v3

        - name: Build and push
          uses: docker/build-push-action@v6
          with:
            context: ./backend
            push: true
            tags: |
              ${{ steps.image.outputs.name }}:v${{ steps.version.outputs.new }}
              ${{ steps.image.outputs.name }}:latest
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add .github/workflows/release-backend.yml
  git commit -m "ci: add backend release workflow"
  ```

---

### Task 6: Create release-frontend.yml

**Files:**
- Create: `.github/workflows/release-frontend.yml`

- [ ] **Step 1: Create the workflow file**

  ```yaml
  name: Release Frontend

  on:
    pull_request:
      types: [closed]
      branches: [main]

  permissions: {}

  jobs:
    release:
      name: Release
      if: |
        github.event.pull_request.merged == true && (
          contains(github.event.pull_request.labels.*.name, 'bump-frontend:patch') ||
          contains(github.event.pull_request.labels.*.name, 'bump-frontend:minor') ||
          contains(github.event.pull_request.labels.*.name, 'bump-frontend:major')
        )
      runs-on: ubuntu-latest
      permissions:
        contents: write
        packages: write
      steps:
        - uses: actions/checkout@v4
          with:
            token: ${{ secrets.GITHUB_TOKEN }}
            fetch-depth: 0

        - name: Determine bump type
          id: bump
          run: |
            if [[ "${{ contains(github.event.pull_request.labels.*.name, 'bump-frontend:major') }}" == "true" ]]; then
              echo "type=major" >> $GITHUB_OUTPUT
            elif [[ "${{ contains(github.event.pull_request.labels.*.name, 'bump-frontend:minor') }}" == "true" ]]; then
              echo "type=minor" >> $GITHUB_OUTPUT
            else
              echo "type=patch" >> $GITHUB_OUTPUT
            fi

        - name: Bump version
          id: version
          run: |
            current=$(cat frontend/VERSION)
            IFS='.' read -r major minor patch <<< "$current"
            case "${{ steps.bump.outputs.type }}" in
              major) major=$((major + 1)); minor=0; patch=0 ;;
              minor) minor=$((minor + 1)); patch=0 ;;
              patch) patch=$((patch + 1)) ;;
            esac
            new="$major.$minor.$patch"
            echo "$new" > frontend/VERSION
            echo "new=$new" >> $GITHUB_OUTPUT

        - name: Commit and tag
          run: |
            git config user.name "github-actions[bot]"
            git config user.email "github-actions[bot]@users.noreply.github.com"
            git add frontend/VERSION
            git commit -m "chore: bump frontend to v${{ steps.version.outputs.new }} [skip ci]"
            git tag "frontend-v${{ steps.version.outputs.new }}"
            git push origin main --follow-tags

        - name: Set lowercase image name
          id: image
          run: echo "name=$(echo 'ghcr.io/${{ github.repository }}-frontend' | tr '[:upper:]' '[:lower:]')" >> $GITHUB_OUTPUT

        - name: Log in to GHCR
          uses: docker/login-action@v3
          with:
            registry: ghcr.io
            username: ${{ github.actor }}
            password: ${{ secrets.GITHUB_TOKEN }}

        - uses: docker/setup-buildx-action@v3

        - name: Build and push
          uses: docker/build-push-action@v6
          with:
            context: ./frontend
            push: true
            build-args: |
              VITE_API_BASE_URL=${{ vars.VITE_API_BASE_URL }}
              VITE_COGNITO_DOMAIN=${{ vars.VITE_COGNITO_DOMAIN }}
              VITE_COGNITO_CLIENT_ID=${{ vars.VITE_COGNITO_CLIENT_ID }}
              VITE_COGNITO_REDIRECT_URI=${{ vars.VITE_COGNITO_REDIRECT_URI }}
            tags: |
              ${{ steps.image.outputs.name }}:v${{ steps.version.outputs.new }}
              ${{ steps.image.outputs.name }}:latest
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add .github/workflows/release-frontend.yml
  git commit -m "ci: add frontend release workflow"
  ```

---

### Task 7: Smoke test

**Files:** No files — live validation on GitHub.

There are no unit tests for YAML workflows — validation is a live end-to-end run.

- [ ] **Step 1: Push the dev branch and open a PR**

  ```bash
  git push origin dev
  gh pr create --base main --head dev --title "ci: release pipeline" --body "Smoke test — merge with bump-backend:patch label"
  ```

- [ ] **Step 2: Add the bump-backend:patch label to the PR**

  ```bash
  gh pr edit <PR-number> --add-label "bump-backend:patch"
  ```

- [ ] **Step 3: Merge the PR**

  ```bash
  gh pr merge <PR-number> --merge
  ```

- [ ] **Step 4: Watch the workflow run**

  ```bash
  gh run watch
  ```
  Expected: `Release Backend` workflow triggered, completes successfully.

- [ ] **Step 5: Verify the version bump commit on main**

  ```bash
  git fetch origin main
  git log origin/main --oneline -3
  ```
  Expected: top commit is `chore: bump backend to v0.1.1 [skip ci]`

- [ ] **Step 6: Verify the git tag**

  ```bash
  git fetch --tags
  git tag | grep backend
  ```
  Expected: `backend-v0.1.1`

- [ ] **Step 7: Verify the image on GHCR**

  ```bash
  gh api /user/packages/container/amazon_tlevel_project_2026-backend/versions --jq '.[].metadata.container.tags'
  ```
  Expected: `["v0.1.1", "latest"]`

  Alternatively, visit `https://github.com/<owner>?tab=packages` in a browser and confirm the package appears.
