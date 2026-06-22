# Standardise on GHCR — Design Spec

## Background

Two release paths for Docker images currently exist in this repo, pointed at two different registries:

1. `.github/workflows/release-backend.yml` and `release-frontend.yml` (added 2026-06-19, per `docs/superpowers/plans/2026-06-19-ghcr-release-pipeline.md`) build and push to **GHCR** (`ghcr.io/...`) using the built-in `GITHUB_TOKEN` — no extra secrets.
2. `infrastructure/modules/registry/` provisions **ECR** repositories (`exeaws26/backend`, `exeaws26/frontend`) via Terraform, and `infrastructure/main.tf` wires `module.compute`'s `backend_image`/`frontend_image` to those ECR repo URLs.

These were never reconciled — no PR with a `bump-*` label has ever been merged to `main`, so the GHCR workflows have never actually run, and ECS would currently try to pull from ECR repos that have nothing pushed to them. This spec standardises on GHCR as the single source of truth for deployed images and removes the ECR path.

## Decisions

- **GHCR packages will be public.** ECS pulling from a public package needs no credentials. This matches the existing release workflows' "no extra secrets" design and is acceptable for this project (student/educational, no proprietary backend logic). The alternative (private packages + a PAT in Secrets Manager + `repositoryCredentials` on the ECS task definitions) is rejected as unnecessary complexity for this project.
- **`infrastructure/modules/registry/` (ECR) is deleted entirely**, not just unreferenced. GHCR is managed by GitHub, not Terraform — there is no Terraform-managed registry resource in the new design. Keeping unused ECR repos around would cost money and create ambiguity about which registry is authoritative.
- **No networking changes.** ECS tasks already run in private subnets with `assign_public_ip = false`, routed to the internet via the existing single NAT gateway (`modules/networking/main.tf`). That egress path already satisfies what's needed to reach `ghcr.io` (AWS has no PrivateLink endpoint for GHCR, unlike ECR, so internet egress is the only option regardless of registry choice — this was already true before this change).
- **No IAM/task-definition changes.** `modules/compute`'s ECS task execution role and task definitions need no `repositoryCredentials` block, since the packages are public.

## Changes

### `infrastructure/modules/registry/`
Delete the directory entirely (`main.tf`, `outputs.tf` — ECR repos, lifecycle policies, both outputs).

### `infrastructure/main.tf`
- Remove the `module "registry" { ... }` block.
- Add a `ghcr_namespace` variable reference (see below) and rebuild `backend_image`/`frontend_image` as:
  ```
  backend_image  = "ghcr.io/${var.ghcr_namespace}-backend:${var.backend_image_tag}"
  frontend_image = "ghcr.io/${var.ghcr_namespace}-frontend:${var.frontend_image_tag}"
  ```
  This matches the lowercase naming the release workflows already produce (`ghcr.io/${{ github.repository }}-backend`, lowercased).

### `infrastructure/variables.tf`
- Add `ghcr_namespace` (string, default `"h4rl33/amazon_tlevel_project_2026"`) — the lowercased `owner/repo` GHCR namespace. A single place to update if the repo is ever renamed or forked.
- Update `backend_image_tag` / `frontend_image_tag` descriptions from "ECR image tag to deploy for the ___ service" to "GHCR image tag to deploy for the ___ service". No behavioural change — both remain required variables with no default, matching the existing manual-bump deployment pattern.

### `infrastructure/outputs.tf`
- Remove the `backend_ecr_url` and `frontend_ecr_url` outputs (nothing references ECR after this change).

## Non-Terraform follow-up (manual, called out but not automated)

Once the first image is actually pushed by a release workflow, someone must set that GHCR package's visibility to **public** in GitHub (Settings → Packages, or `gh api` package visibility endpoint). This can't happen before the first push (the package doesn't exist yet) and isn't a Terraform-managed resource, so it's a manual one-time step per package (backend, frontend), not part of the implementation plan's automated steps — just a note in the plan's smoke-test section.

## Out of scope

- Changing how image tags reach Terraform (still a manually-set `var.backend_image_tag`/`frontend_image_tag` — no automatic redeploy-on-release wiring).
- Running the actual smoke test / first release (separate from this infra change; can happen once this is merged).
- Setting the frontend's `VITE_*` GitHub Actions variables (tracked separately — those depend on this Cognito/ALB infrastructure being applied at all).
