# Terraform IaC Design — T-Level AWS Academy Platform

**Date:** 2026-06-17
**Status:** Approved
**Author:** Harley (via brainstorming session)

---

## Purpose

Provision all AWS infrastructure for the production environment of the Amazon T-Level Project 2026 platform using Terraform, with state managed by Terraform Cloud. The goal is a single `terraform apply` that brings up the full stack: networking, auth, media storage, database, container registry, and compute.

---

## Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Environments | Production only | Single deployment target; no staging complexity |
| State backend | Terraform Cloud | Zero AWS bootstrapping; free tier; UI + run history |
| Compute | ECS Fargate | Matches Docker Compose dev workflow; no EC2 management |
| Structure | Modules-based (single root) | One concern per module; root is a wiring file; extensible |
| HTTPS | HTTP for now | No domain name; ALB listener left with a comment block for future ACM upgrade |
| ALB layout | Single ALB, two listeners (port 80 → frontend, port 8000 → backend) | One ALB cost; browser calls backend directly on port 8000 |
| DB | RDS PostgreSQL 17, `db.t3.micro`, single-AZ | Free-tier eligible; matches local Postgres 17 dev image |
| Secrets | Sensitive Terraform variables in Terraform Cloud | Never in source control |
| CI | GitHub Actions — plan on PR, apply on merge to main | Reviewable infrastructure changes; automated deploys |

---

## Directory Layout

```
infrastructure/
  terraform.tf        ← Terraform Cloud workspace + required_providers
  providers.tf        ← AWS provider (region = eu-west-2)
  main.tf             ← root: calls all modules, wires outputs → inputs
  variables.tf        ← top-level inputs (image tags, secrets, env name)
  outputs.tf          ← ALB DNS names, ECR repo URLs, Cognito pool ID
  modules/
    networking/
      main.tf
      variables.tf
      outputs.tf
    auth/
      main.tf
      variables.tf
      outputs.tf
    storage/
      main.tf
      variables.tf
      outputs.tf
    database/
      main.tf
      variables.tf
      outputs.tf
    registry/
      main.tf
      variables.tf
      outputs.tf
    compute/
      main.tf
      variables.tf
      outputs.tf
```

The root `main.tf` is a wiring file only — it calls each module and passes outputs from one as inputs to another. No AWS resources are defined at the root level.

---

## Module Designs

### networking

**Provisions:**
- VPC `10.0.0.0/16`
- 2 public subnets (`10.0.1.0/24`, `10.0.2.0/24`) in eu-west-2a and eu-west-2b — ALB lives here
- 2 private subnets (`10.0.3.0/24`, `10.0.4.0/24`) in eu-west-2a and eu-west-2b — ECS tasks and RDS live here
- Internet Gateway (public egress for ALB)
- Single NAT Gateway in one public subnet (private subnet egress: ECR pulls, Cognito calls, S3 calls)
- Route tables: public → IGW, private → NAT
- Three security groups:
  - `sg_alb` — inbound 80 and 8000 from `0.0.0.0/0`; outbound all
  - `sg_ecs` — inbound from `sg_alb` only; outbound all
  - `sg_rds` — inbound 5432 from `sg_ecs` only; no outbound
- Application Load Balancer in public subnets (`sg_alb`)
  - Listener port 80 → frontend target group (health check `GET /`)
  - Listener port 8000 → backend target group (health check `GET /health`)

> **HTTPS upgrade path:** to add HTTPS, provision an ACM certificate for a domain, add a listener on port 443 with the cert, and redirect the port 80/8000 listeners to HTTPS. No structural changes required.

**Outputs:** VPC ID, public subnet IDs, private subnet IDs, `sg_ecs` ID, `sg_rds` ID, ALB DNS name, frontend target group ARN, backend target group ARN.

---

### auth

**Provisions:**
- `aws_cognito_user_pool` — email sign-in, email verification, standard password policy (min 8 chars, upper, lower, number)
- `aws_cognito_user_pool_client` — PKCE flow, no client secret, callback URL = `http://<alb-dns>/auth/callback`, sign-out URL = `http://<alb-dns>/`
- `aws_cognito_user_pool_domain` — Hosted UI at `exeaws26.auth.eu-west-2.amazoncognito.com`

**Outputs:** user pool ID, user pool ARN, app client ID, Hosted UI domain.

---

### storage

**Provisions:**
- `aws_s3_bucket` — `exeaws26-content-prod` (or similar unique name)
- `aws_s3_bucket_public_access_block` — all public access blocked; pre-signed URLs handle read access
- `aws_iam_policy` — `s3:GetObject` and `s3:PutObject` on the bucket ARN

**Outputs:** bucket name, bucket ARN, IAM policy ARN.

---

### database

**Provisions:**
- `aws_db_subnet_group` — using private subnet IDs from networking module
- `aws_db_instance` — PostgreSQL 17, `db.t3.micro`, single-AZ, 20 GB gp2 storage, `sg_rds` security group, deletion protection enabled, final snapshot on destroy
- DB password sourced from a sensitive Terraform variable (stored in Terraform Cloud, never in source)

**Outputs:** RDS endpoint, database name, database port.

---

### registry

**Provisions:**
- `aws_ecr_repository` — `exeaws26/backend`
- `aws_ecr_repository` — `exeaws26/frontend`
- `aws_ecr_lifecycle_policy` on each — keep last 5 tagged images, expire untagged images after 1 day

**Outputs:** backend repo URL, frontend repo URL.

---

### compute

**Provisions:**

**IAM:**
- Task execution role — allows ECS to pull images from ECR and write logs to CloudWatch (uses `AmazonECSTaskExecutionRolePolicy` managed policy)
- Task role — the identity the running container assumes; storage module's S3 IAM policy is attached here

**CloudWatch:**
- Log group `/ecs/exeaws26-backend` — 30-day retention
- Log group `/ecs/exeaws26-frontend` — 30-day retention

**ECS Cluster:** `exeaws26-prod`

**Backend task definition** — Fargate, 512 CPU / 1024 MB RAM

| Environment Variable | Source |
|---|---|
| `DATABASE_URL` | Constructed from database module outputs |
| `SECRET_KEY` | Sensitive Terraform variable |
| `ENVIRONMENT` | `production` |
| `COGNITO_REGION` | `eu-west-2` |
| `COGNITO_USER_POOL_ID` | Auth module output |
| `S3_BUCKET_NAME` | Storage module output |
| `AWS_REGION` | `eu-west-2` |
| `ALLOWED_ORIGINS` | `http://<alb-dns>` |

**Frontend task definition** — Fargate, 256 CPU / 512 MB RAM

SvelteKit's `VITE_*` variables are baked into the bundle at build time by Vite — they cannot be injected as ECS environment variables at runtime. They must be passed as Docker build arguments when the image is built in CI. The frontend task definition therefore carries **no environment variables**; the values are already compiled into the image.

**Docker build arguments (passed during `docker build` in CI, sourced from Terraform outputs):**

| Build Arg | Source |
|---|---|
| `VITE_API_BASE_URL` | `http://<alb-dns>:8000` (Terraform output `alb_dns_name`) |
| `VITE_COGNITO_DOMAIN` | Terraform output `cognito_hosted_ui_domain` |
| `VITE_COGNITO_CLIENT_ID` | Terraform output `cognito_client_id` |
| `VITE_COGNITO_REDIRECT_URI` | `http://<alb-dns>/auth/callback` (derived from `alb_dns_name`) |

**Deploy order consequence:** the ALB DNS name is only known after `terraform apply` completes. The correct first-deploy sequence is:
1. `terraform apply` — creates all infrastructure including the ALB
2. Read `alb_dns_name` from Terraform outputs
3. Build and push backend + frontend Docker images to ECR (frontend built with the above build args)
4. `terraform apply` again — ECS services pick up the new image tags and deploy

**ECS Services:**
- `backend` — `desired_count = 1`, private subnets, `sg_ecs`, registers with backend target group
- `frontend` — `desired_count = 1`, private subnets, `sg_ecs`, registers with frontend target group

Both services use the `LATEST` platform version and have deployment circuit breakers enabled (auto-rollback on failed deploy).

**Auto-scaling** — both services register as Application Auto Scaling targets. Each gets a target-tracking policy on average CPU utilisation:

| Service | Min tasks | Max tasks | Scale-out threshold |
|---|---|---|---|
| `backend` | 1 | 4 | 70% CPU |
| `frontend` | 1 | 4 | 70% CPU |

AWS manages the CloudWatch alarms automatically with target-tracking — no alarms are written manually. Scale-in has a 300-second cooldown to avoid thrashing.

Resources per service: `aws_appautoscaling_target` + `aws_appautoscaling_policy`.

---

## Migrations & Seed Data

Neither Alembic migrations nor seed data loading require new Terraform resources. Both run as **one-off ECS tasks** using the backend task definition with a command override, triggered from the CI deploy pipeline after `terraform apply` completes.

**Prerequisites (backend codebase):**
- `alembic` added to `pyproject.toml` dependencies
- `alembic.ini` and `backend/migrations/` directory initialised (`alembic init`)
- Migration versions generated from the existing SQLAlchemy models

**Migration task** — runs `alembic upgrade head` against the production database:
```
aws ecs run-task \
  --cluster exeaws26-prod \
  --task-definition exeaws26-backend \
  --launch-type FARGATE \
  --network-configuration "..." \
  --overrides '{"containerOverrides":[{"name":"backend","command":["poetry","run","alembic","upgrade","head"]}]}'
```
CI waits for the task to stop (`aws ecs wait tasks-stopped`) and checks the exit code before proceeding. A non-zero exit code fails the deploy.

**Seed task** — runs `python seed.py` (or similar) using the same override pattern. Only triggered manually or on first deploy via a CI workflow input (`workflow_dispatch` with a `run_seed` boolean input). Idempotent seed logic is required — running it twice must not duplicate data.

**Updated deploy sequence (after first infrastructure apply):**
1. `terraform apply` — infrastructure up, ALB DNS known
2. Build + push backend and frontend images to ECR
3. `terraform apply` — ECS services updated with new image tags
4. Run migration task — wait for exit 0
5. (First deploy only) Run seed task — wait for exit 0

---

## Root Variables

| Variable | Type | Sensitive | Description |
|---|---|---|---|
| `backend_image_tag` | `string` | No | ECR image tag to deploy for backend |
| `frontend_image_tag` | `string` | No | ECR image tag to deploy for frontend |
| `db_password` | `string` | Yes | RDS master password |
| `secret_key` | `string` | Yes | FastAPI `SECRET_KEY` |
| `env_name` | `string` | No | Environment label (default: `prod`) |

Sensitive variables are stored in the Terraform Cloud workspace and never written to any file.

---

## Root Outputs

| Output | Description |
|---|---|
| `alb_dns_name` | Public DNS name for the ALB — paste into Cognito callback URL, frontend env var |
| `backend_ecr_url` | ECR repo URL for CI push |
| `frontend_ecr_url` | ECR repo URL for CI push |
| `cognito_user_pool_id` | For backend JWT validation config |
| `cognito_client_id` | For frontend Cognito SDK config |
| `rds_endpoint` | For manual DB access / debugging |

---

## CI Integration

`.github/workflows/terraform.yml`:

```
on:
  pull_request:
    paths: ['infrastructure/**']
  push:
    branches: [main]
    paths: ['infrastructure/**']
```

**On pull request:** `terraform init` → `terraform plan` → post plan output as PR comment via `actions/github-script`

**On push to main:** `terraform init` → `terraform apply -auto-approve`

Both jobs use `TF_API_TOKEN` (GitHub secret) to authenticate with Terraform Cloud. AWS credentials are configured in the Terraform Cloud workspace as `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` environment variables — GitHub Actions never holds AWS credentials directly.

---

## Out of Scope

- HTTPS / ACM / Route 53 (no domain name; upgrade path documented above)
- Multiple environments (staging, dev)
- CloudFront CDN
- AWS Secrets Manager integration (env vars in task definition are sufficient for now)
