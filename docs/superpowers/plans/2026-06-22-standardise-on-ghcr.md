# Standardise on GHCR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the unused Terraform-provisioned ECR registry and repoint ECS at GHCR (the registry the existing release workflows already push to), so there is exactly one registry in play.

**Architecture:** Delete `infrastructure/modules/registry/` (ECR) entirely. In root `infrastructure/main.tf`, drop the `module "registry"` block and rebuild `backend_image`/`frontend_image` as literal GHCR image URIs using a new `ghcr_namespace` variable, matching the lowercase naming the release workflows already produce (`ghcr.io/${{ github.repository }}-backend`). No IAM, task-definition, or networking changes are needed — packages will be public, and the existing NAT gateway already gives ECS tasks the internet egress GHCR pulls require.

**Tech Stack:** Terraform (AWS provider), no new tooling.

See `docs/superpowers/specs/2026-06-22-standardise-on-ghcr-design.md` for the full design rationale.

---

## File Map

| Action | Path |
|---|---|
| Delete | `infrastructure/modules/registry/main.tf` |
| Delete | `infrastructure/modules/registry/outputs.tf` |
| Modify | `infrastructure/main.tf` |
| Modify | `infrastructure/variables.tf` |
| Modify | `infrastructure/outputs.tf` |

There is no Terraform CLI available in this environment to run `terraform validate`/`plan` locally (checked: `terraform` is not on `PATH`). Verification in this plan uses `grep` to confirm no dangling references to the deleted module remain. The repo's `terraform.yml` GitHub Actions workflow runs a real `terraform plan` against Terraform Cloud when a PR touching `infrastructure/**` is opened — that PR-time plan is the actual validation gate before merge.

---

### Task 1: Delete the ECR registry module

**Files:**
- Delete: `infrastructure/modules/registry/main.tf`
- Delete: `infrastructure/modules/registry/outputs.tf`

- [ ] **Step 1: Delete the module directory**

  ```bash
  cd infrastructure
  git rm -r modules/registry
  ```

- [ ] **Step 2: Verify it's gone**

  ```bash
  ls modules/
  ```
  Expected: no `registry` entry (only `auth`, `compute`, `database`, `networking`, `storage`).

---

### Task 2: Add `ghcr_namespace` variable and update image tag descriptions

**Files:**
- Modify: `infrastructure/variables.tf`

Current content of `infrastructure/variables.tf`:

```hcl
variable "backend_image_tag" {
  type        = string
  description = "ECR image tag to deploy for the backend service"
}

variable "frontend_image_tag" {
  type        = string
  description = "ECR image tag to deploy for the frontend service"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "RDS master password — stored in Terraform Cloud, never in source"
}

variable "secret_key" {
  type        = string
  sensitive   = true
  description = "FastAPI SECRET_KEY — stored in Terraform Cloud, never in source"
}

variable "env_name" {
  type        = string
  default     = "prod"
  description = "Environment label used in resource names"
}
```

- [ ] **Step 1: Replace the file contents**

  Replace the entire file with:

  ```hcl
  variable "backend_image_tag" {
    type        = string
    description = "GHCR image tag to deploy for the backend service"
  }

  variable "frontend_image_tag" {
    type        = string
    description = "GHCR image tag to deploy for the frontend service"
  }

  variable "ghcr_namespace" {
    type        = string
    default     = "h4rl33/amazon_tlevel_project_2026"
    description = "Lowercase '<owner>/<repo>' GHCR namespace images are pushed under (must match the lowercased github.repository the release workflows push to)"
  }

  variable "db_password" {
    type        = string
    sensitive   = true
    description = "RDS master password — stored in Terraform Cloud, never in source"
  }

  variable "secret_key" {
    type        = string
    sensitive   = true
    description = "FastAPI SECRET_KEY — stored in Terraform Cloud, never in source"
  }

  variable "env_name" {
    type        = string
    default     = "prod"
    description = "Environment label used in resource names"
  }
  ```

- [ ] **Step 2: Verify**

  ```bash
  grep -n "ghcr_namespace\|ECR image tag" infrastructure/variables.tf
  ```
  Expected: one `variable "ghcr_namespace"` block present, and no remaining matches for `ECR image tag` (both descriptions now say `GHCR image tag`).

---

### Task 3: Repoint `main.tf` at GHCR and remove the registry module reference

**Files:**
- Modify: `infrastructure/main.tf`

Current content of `infrastructure/main.tf`:

```hcl
module "networking" {
  source   = "./modules/networking"
  env_name = var.env_name
}

module "auth" {
  source       = "./modules/auth"
  env_name     = var.env_name
  alb_dns_name = module.networking.alb_dns_name
}

module "storage" {
  source   = "./modules/storage"
  env_name = var.env_name
}

module "database" {
  source             = "./modules/database"
  env_name           = var.env_name
  private_subnet_ids = module.networking.private_subnet_ids
  sg_rds_id          = module.networking.sg_rds_id
  db_password        = var.db_password
}

module "registry" {
  source = "./modules/registry"
  # No env_name — ECR repos are account/region-scoped, not env-scoped
}

module "compute" {
  source                    = "./modules/compute"
  env_name                  = var.env_name
  private_subnet_ids        = module.networking.private_subnet_ids
  sg_ecs_id                 = module.networking.sg_ecs_id
  frontend_target_group_arn = module.networking.frontend_target_group_arn
  backend_target_group_arn  = module.networking.backend_target_group_arn
  s3_policy_arn             = module.storage.s3_policy_arn
  backend_image             = "${module.registry.backend_repo_url}:${var.backend_image_tag}"
  frontend_image            = "${module.registry.frontend_repo_url}:${var.frontend_image_tag}"
  # aws_db_instance.endpoint already includes port (e.g. host:5432) — do NOT append :${module.database.port}
  database_url              = "postgresql+asyncpg://exeaws26:${var.db_password}@${module.database.endpoint}/exeaws26"
  secret_key                = var.secret_key
  cognito_user_pool_id      = module.auth.user_pool_id
  s3_bucket_name            = module.storage.bucket_name
  alb_dns_name              = module.networking.alb_dns_name
}
```

- [ ] **Step 1: Replace the file contents**

  Replace the entire file with (the `module "registry"` block is removed, and `backend_image`/`frontend_image` now build a literal GHCR URI from the new `var.ghcr_namespace` instead of referencing the deleted module):

  ```hcl
  module "networking" {
    source   = "./modules/networking"
    env_name = var.env_name
  }

  module "auth" {
    source       = "./modules/auth"
    env_name     = var.env_name
    alb_dns_name = module.networking.alb_dns_name
  }

  module "storage" {
    source   = "./modules/storage"
    env_name = var.env_name
  }

  module "database" {
    source             = "./modules/database"
    env_name           = var.env_name
    private_subnet_ids = module.networking.private_subnet_ids
    sg_rds_id          = module.networking.sg_rds_id
    db_password        = var.db_password
  }

  module "compute" {
    source                    = "./modules/compute"
    env_name                  = var.env_name
    private_subnet_ids        = module.networking.private_subnet_ids
    sg_ecs_id                 = module.networking.sg_ecs_id
    frontend_target_group_arn = module.networking.frontend_target_group_arn
    backend_target_group_arn  = module.networking.backend_target_group_arn
    s3_policy_arn             = module.storage.s3_policy_arn
    backend_image             = "ghcr.io/${var.ghcr_namespace}-backend:${var.backend_image_tag}"
    frontend_image            = "ghcr.io/${var.ghcr_namespace}-frontend:${var.frontend_image_tag}"
    # aws_db_instance.endpoint already includes port (e.g. host:5432) — do NOT append :${module.database.port}
    database_url              = "postgresql+asyncpg://exeaws26:${var.db_password}@${module.database.endpoint}/exeaws26"
    secret_key                = var.secret_key
    cognito_user_pool_id      = module.auth.user_pool_id
    s3_bucket_name            = module.storage.bucket_name
    alb_dns_name              = module.networking.alb_dns_name
  }
  ```

- [ ] **Step 2: Verify no dangling references to the registry module remain**

  ```bash
  grep -rn "module.registry\|module \"registry\"" infrastructure/
  ```
  Expected: no output.

---

### Task 4: Remove ECR outputs from root outputs

**Files:**
- Modify: `infrastructure/outputs.tf`

Current content of `infrastructure/outputs.tf`:

```hcl
output "alb_dns_name" {
  value       = module.networking.alb_dns_name
  description = "Public DNS name of the ALB — used for Cognito callback URLs and frontend build args"
}

output "backend_ecr_url" {
  value       = module.registry.backend_repo_url
  description = "ECR repo URL for backend — used in CI docker push"
}

output "frontend_ecr_url" {
  value       = module.registry.frontend_repo_url
  description = "ECR repo URL for frontend — used in CI docker push"
}

output "cognito_user_pool_id" {
  value       = module.auth.user_pool_id
  description = "Cognito User Pool ID — for backend JWT validation"
}

output "cognito_client_id" {
  value       = module.auth.client_id
  description = "Cognito App Client ID — for frontend PKCE flow"
}

output "cognito_hosted_ui_domain" {
  value       = module.auth.hosted_ui_domain
  description = "Cognito Hosted UI base URL"
}

output "rds_endpoint" {
  value       = module.database.endpoint
  description = "RDS endpoint — for manual DB access and debugging"
}
```

- [ ] **Step 1: Replace the file contents**

  Replace the entire file with (the `backend_ecr_url` and `frontend_ecr_url` outputs are removed):

  ```hcl
  output "alb_dns_name" {
    value       = module.networking.alb_dns_name
    description = "Public DNS name of the ALB — used for Cognito callback URLs and frontend build args"
  }

  output "cognito_user_pool_id" {
    value       = module.auth.user_pool_id
    description = "Cognito User Pool ID — for backend JWT validation"
  }

  output "cognito_client_id" {
    value       = module.auth.client_id
    description = "Cognito App Client ID — for frontend PKCE flow"
  }

  output "cognito_hosted_ui_domain" {
    value       = module.auth.hosted_ui_domain
    description = "Cognito Hosted UI base URL"
  }

  output "rds_endpoint" {
    value       = module.database.endpoint
    description = "RDS endpoint — for manual DB access and debugging"
  }
  ```

- [ ] **Step 2: Verify**

  ```bash
  grep -n "ecr" infrastructure/outputs.tf
  ```
  Expected: no output (case-sensitive grep on lowercase `ecr` finds nothing — `module.registry` is gone and no output mentions ECR).

---

### Task 5: Full-tree sanity check and commit

**Files:** None — verification and commit only.

- [ ] **Step 1: Confirm no remaining ECR/registry references anywhere in infrastructure/**

  ```bash
  grep -rn "ecr\|ECR\|registry" infrastructure/ --include='*.tf'
  ```
  Expected: no output. (If `terraform` happens to be available in your environment, also run `terraform fmt -check -recursive infrastructure/` and `terraform validate` from `infrastructure/` after `terraform init` — this plan was written without access to the Terraform CLI, so those checks haven't been run yet.)

- [ ] **Step 2: Stage and commit**

  ```bash
  git add infrastructure/
  git status
  ```
  Expected: deleted `infrastructure/modules/registry/main.tf` and `infrastructure/modules/registry/outputs.tf`; modified `infrastructure/main.tf`, `infrastructure/variables.tf`, `infrastructure/outputs.tf`.

  ```bash
  git commit -m "infra: standardise on GHCR, remove unused ECR registry module"
  ```

- [ ] **Step 3: Open a PR so the terraform.yml workflow plans the change**

  ```bash
  git push origin HEAD
  gh pr create --base main --title "infra: standardise on GHCR" --body "Removes the unused ECR registry module and repoints ECS image references at GHCR. See docs/superpowers/specs/2026-06-22-standardise-on-ghcr-design.md for the design."
  ```
  Expected: PR opens, `Terraform` workflow runs and posts a plan comment. Review the plan output before merging — it should show the ECR repos and lifecycle policies being destroyed, and no changes to networking, IAM, or ECS task definitions.

**Reminder for after the first real release runs (not a step in this plan — nothing exists to act on yet):** once `release-backend.yml`/`release-frontend.yml` have pushed their first images, someone needs to set those two GHCR packages to public visibility in GitHub (Settings → Packages). ECS will fail to pull until that's done, since this plan assumes public packages and adds no pull credentials.
