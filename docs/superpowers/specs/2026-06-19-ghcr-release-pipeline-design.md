# GHCR Release Pipeline Design

**Date:** 2026-06-19
**Status:** Approved

## Overview

Two independent GitHub Actions workflows (`release-backend.yml`, `release-frontend.yml`) that trigger on PR merge to `main`, bump a semver `VERSION` file, commit the bump, create a git tag, build a Docker image, and push it to GHCR. No deployment step — this pipeline produces versioned images only.

## Trigger

Both workflows use the `pull_request` event with type `closed`, filtered to `main`. The job runs only when the PR was actually merged (`github.event.pull_request.merged == true`) and the relevant bump label is present. Using `pull_request closed` gives direct access to the PR's label set without calling the API.

## Label Convention

Six labels must be created in the GitHub repository settings:

| Label | Effect |
|---|---|
| `bump-backend:patch` | Increments patch digit of `backend/VERSION` |
| `bump-backend:minor` | Increments minor digit, resets patch to 0 |
| `bump-backend:major` | Increments major digit, resets minor and patch to 0 |
| `bump-frontend:patch` | Increments patch digit of `frontend/VERSION` |
| `bump-frontend:minor` | Increments minor digit, resets patch to 0 |
| `bump-frontend:major` | Increments major digit, resets minor and patch to 0 |

A PR without any relevant label produces no release for that service. PRs touching both services can carry both a `bump-backend:*` and a `bump-frontend:*` label.

## Version Files

- `backend/VERSION` — plain text, e.g. `0.1.0`, committed into the repo at `0.1.0` before the pipeline exists
- `frontend/VERSION` — same format, independent version history

The pipeline reads the file, applies the semver bump in a shell script, writes the new version back, and commits it directly to `main` with the message:

```
chore: bump backend to vX.Y.Z [skip ci]
```

The `[skip ci]` token prevents the commit from re-triggering the release workflow.

## Git Tagging

After committing the version bump, the workflow creates and pushes an annotated git tag:

- Backend: `backend-vX.Y.Z`
- Frontend: `frontend-vX.Y.Z`

## GHCR Image Build & Push

**Image names:**
- `ghcr.io/${{ github.repository_owner }}/amazon_tlevel_project_2026-backend:vX.Y.Z`
- `ghcr.io/${{ github.repository_owner }}/amazon_tlevel_project_2026-backend:latest`
- `ghcr.io/${{ github.repository_owner }}/amazon_tlevel_project_2026-frontend:vX.Y.Z`
- `ghcr.io/${{ github.repository_owner }}/amazon_tlevel_project_2026-frontend:latest`

Both version and `latest` tags are pushed on every release.

**Build contexts:** `backend/Dockerfile` and `frontend/Dockerfile` unchanged.

**Frontend build args** (sourced from GitHub repo variables — not secrets):

| Variable | Purpose |
|---|---|
| `vars.VITE_API_BASE_URL` | Production API base URL |
| `vars.VITE_COGNITO_DOMAIN` | Cognito hosted UI domain |
| `vars.VITE_COGNITO_CLIENT_ID` | Cognito app client ID |
| `vars.VITE_COGNITO_REDIRECT_URI` | Post-login redirect URI |

## Permissions

Each workflow requires:

```yaml
permissions:
  contents: write    # commit version bump, push tag
  packages: write    # push to GHCR
```

Auth for both git operations and GHCR uses the built-in `GITHUB_TOKEN`. No PATs or additional secrets are needed.

## What is NOT in scope

- Deployment to ECS or any infrastructure — Terraform apply remains a separate workflow
- PR checks or test runs — those remain in the existing `backend.yml` and `frontend.yml`
- Release notes or changelogs — not part of this pipeline

## Pre-flight Checklist (before first run)

1. Create `backend/VERSION` containing `0.1.0` and commit to `main`
2. Create `frontend/VERSION` containing `0.1.0` and commit to `main`
3. Create the six labels in GitHub repo settings
4. Set the four `vars.VITE_*` repo variables in GitHub repo settings → Variables
5. Ensure GHCR is enabled for the repository (enabled by default on public repos)
