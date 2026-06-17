# Terraform IaC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provision all AWS infrastructure for the production platform using Terraform (state in Terraform Cloud), and prepare production-ready Dockerfiles, Alembic migrations, and seed data.

**Architecture:** Single Terraform root with 6 child modules (networking, auth, storage, database, registry, compute). Root `main.tf` is a pure wiring file — no AWS resources at root level. GitHub Actions runs `terraform plan` on PR and `terraform apply` on merge to main, authenticating via Terraform Cloud.

**Tech Stack:** Terraform ≥ 1.9, AWS provider ~5.0, Terraform Cloud (free tier), ECS Fargate, RDS PostgreSQL 17, Cognito, S3, ECR, ALB, Application Auto Scaling; Python 3.12 / Poetry / Alembic; SvelteKit with `@sveltejs/adapter-node`.

---

## File Map

**Created:**
- `infrastructure/terraform.tf`
- `infrastructure/providers.tf`
- `infrastructure/variables.tf`
- `infrastructure/outputs.tf`
- `infrastructure/main.tf`
- `infrastructure/modules/networking/{main,variables,outputs}.tf`
- `infrastructure/modules/auth/{main,variables,outputs}.tf`
- `infrastructure/modules/storage/{main,variables,outputs}.tf`
- `infrastructure/modules/database/{main,variables,outputs}.tf`
- `infrastructure/modules/registry/{main,variables,outputs}.tf`
- `infrastructure/modules/compute/{main,variables,outputs}.tf`
- `.github/workflows/terraform.yml`
- `backend/migrations/` (via `alembic init`)
- `backend/seed.py`

**Modified:**
- `backend/Dockerfile` — remove `--reload`
- `backend/pyproject.toml` — add `alembic`, `boto3`
- `backend/app/config.py` — add `COGNITO_REGION`, `COGNITO_USER_POOL_ID`, `S3_BUCKET_NAME`, `AWS_REGION`
- `backend/migrations/env.py` — async SQLAlchemy config (replaces generated stub)
- `frontend/Dockerfile` — multi-stage, `adapter-node`
- `frontend/package.json` — swap `adapter-static` for `adapter-node`
- `frontend/svelte.config.js` — swap adapter

---

## Prerequisites

Before Task 1: set up Terraform Cloud.

- [ ] Sign in to [app.terraform.io](https://app.terraform.io) and create an organisation (e.g. `exeaws26`)
- [ ] Create a workspace named `exeaws26-prod`, execution mode **Remote**
- [ ] Add workspace variables:
  - `AWS_ACCESS_KEY_ID` (env var, sensitive) — your IAM access key
  - `AWS_SECRET_ACCESS_KEY` (env var, sensitive) — your IAM secret key
  - `db_password` (Terraform variable, sensitive) — choose a strong password
  - `secret_key` (Terraform variable, sensitive) — choose a long random string
- [ ] Create a Terraform Cloud API token: **User Settings → Tokens → Create an API token**. Save it — you'll add it as a GitHub secret named `TF_API_TOKEN` in Task 9.

---

## Task 1: Bootstrap Root Terraform Config

**Files:**
- Create: `infrastructure/terraform.tf`
- Create: `infrastructure/providers.tf`
- Create: `infrastructure/variables.tf`
- Create: `infrastructure/outputs.tf`
- Create: `infrastructure/main.tf`

- [ ] **Step 1: Create `infrastructure/terraform.tf`**

```hcl
terraform {
  cloud {
    organization = "exeaws26"
    workspaces {
      name = "exeaws26-prod"
    }
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  required_version = ">= 1.9"
}
```

- [ ] **Step 2: Create `infrastructure/providers.tf`**

```hcl
provider "aws" {
  region = "eu-west-2"
}
```

- [ ] **Step 3: Create `infrastructure/variables.tf`**

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

- [ ] **Step 4: Create `infrastructure/outputs.tf`** (empty stubs — filled in Task 8)

```hcl
# Outputs are defined in Task 8 after all modules are wired.
```

- [ ] **Step 5: Create `infrastructure/main.tf`** (empty — modules are added per task)

```hcl
# Module calls are added in Tasks 2–7. Root main.tf is a wiring file only.
```

- [ ] **Step 6: Verify Terraform CLI is installed and can authenticate**

```bash
cd infrastructure
terraform login       # opens browser, paste API token
terraform init        # should connect to Terraform Cloud
```

Expected: `Terraform has been successfully initialized!`

- [ ] **Step 7: Commit**

```bash
git add infrastructure/
git commit -m "feat: bootstrap Terraform root config with Terraform Cloud backend"
```

---

## Task 2: Networking Module

**Files:**
- Create: `infrastructure/modules/networking/main.tf`
- Create: `infrastructure/modules/networking/variables.tf`
- Create: `infrastructure/modules/networking/outputs.tf`

- [ ] **Step 1: Create `infrastructure/modules/networking/variables.tf`**

```hcl
variable "env_name" {
  type = string
}
```

- [ ] **Step 2: Create `infrastructure/modules/networking/main.tf`**

```hcl
# ── VPC ──────────────────────────────────────────────────────────────────────
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = { Name = "${var.env_name}-vpc" }
}

# ── Subnets ───────────────────────────────────────────────────────────────────
resource "aws_subnet" "public_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "eu-west-2a"
  tags = { Name = "${var.env_name}-public-a" }
}

resource "aws_subnet" "public_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "eu-west-2b"
  tags = { Name = "${var.env_name}-public-b" }
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "eu-west-2a"
  tags = { Name = "${var.env_name}-private-a" }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.4.0/24"
  availability_zone = "eu-west-2b"
  tags = { Name = "${var.env_name}-private-b" }
}

# ── Internet Gateway ──────────────────────────────────────────────────────────
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags = { Name = "${var.env_name}-igw" }
}

# ── NAT Gateway (single, in public_a) ────────────────────────────────────────
resource "aws_eip" "nat" {
  domain = "vpc"
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public_a.id
  tags = { Name = "${var.env_name}-nat" }
  depends_on = [aws_internet_gateway.main]
}

# ── Route Tables ──────────────────────────────────────────────────────────────
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  tags = { Name = "${var.env_name}-public-rt" }
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }
  tags = { Name = "${var.env_name}-private-rt" }
}

resource "aws_route_table_association" "private_a" {
  subnet_id      = aws_subnet.private_a.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_b" {
  subnet_id      = aws_subnet.private_b.id
  route_table_id = aws_route_table.private.id
}

# ── Security Groups ───────────────────────────────────────────────────────────
resource "aws_security_group" "alb" {
  name   = "${var.env_name}-sg-alb"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.env_name}-sg-alb" }
}

resource "aws_security_group" "ecs" {
  name   = "${var.env_name}-sg-ecs"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.env_name}-sg-ecs" }
}

resource "aws_security_group" "rds" {
  name   = "${var.env_name}-sg-rds"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  tags = { Name = "${var.env_name}-sg-rds" }
}

# ── Application Load Balancer ─────────────────────────────────────────────────
resource "aws_lb" "main" {
  name               = "${var.env_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]
  tags = { Name = "${var.env_name}-alb" }
}

# ── Target Groups ─────────────────────────────────────────────────────────────
resource "aws_lb_target_group" "frontend" {
  name        = "${var.env_name}-tg-frontend"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
  }

  tags = { Name = "${var.env_name}-tg-frontend" }
}

resource "aws_lb_target_group" "backend" {
  name        = "${var.env_name}-tg-backend"
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

  tags = { Name = "${var.env_name}-tg-backend" }
}

# ── ALB Listeners ─────────────────────────────────────────────────────────────
resource "aws_lb_listener" "frontend" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

resource "aws_lb_listener" "backend" {
  load_balancer_arn = aws_lb.main.arn
  port              = 8000
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}
```

- [ ] **Step 3: Create `infrastructure/modules/networking/outputs.tf`**

```hcl
output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

output "private_subnet_ids" {
  value = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}

output "sg_ecs_id" {
  value = aws_security_group.ecs.id
}

output "sg_rds_id" {
  value = aws_security_group.rds.id
}

output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "frontend_target_group_arn" {
  value = aws_lb_target_group.frontend.arn
}

output "backend_target_group_arn" {
  value = aws_lb_target_group.backend.arn
}
```

- [ ] **Step 4: Commit**

```bash
git add infrastructure/modules/networking/
git commit -m "feat: add networking Terraform module"
```

---

## Task 3: Auth Module

**Files:**
- Create: `infrastructure/modules/auth/main.tf`
- Create: `infrastructure/modules/auth/variables.tf`
- Create: `infrastructure/modules/auth/outputs.tf`

- [ ] **Step 1: Create `infrastructure/modules/auth/variables.tf`**

```hcl
variable "env_name" {
  type = string
}

variable "alb_dns_name" {
  type        = string
  description = "ALB DNS name — used to build Cognito callback and sign-out URLs"
}
```

- [ ] **Step 2: Create `infrastructure/modules/auth/main.tf`**

```hcl
resource "aws_cognito_user_pool" "main" {
  name = "${var.env_name}-user-pool"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_uppercase = true
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
  }

  tags = { Name = "${var.env_name}-user-pool" }
}

resource "aws_cognito_user_pool_client" "main" {
  name         = "${var.env_name}-app-client"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret = false

  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]
  supported_identity_providers         = ["COGNITO"]

  callback_urls = ["http://${var.alb_dns_name}/auth/callback"]
  logout_urls   = ["http://${var.alb_dns_name}/"]

  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH",
  ]
}

resource "aws_cognito_user_pool_domain" "main" {
  domain       = "exeaws26"
  user_pool_id = aws_cognito_user_pool.main.id
}
```

- [ ] **Step 3: Create `infrastructure/modules/auth/outputs.tf`**

```hcl
output "user_pool_id" {
  value = aws_cognito_user_pool.main.id
}

output "user_pool_arn" {
  value = aws_cognito_user_pool.main.arn
}

output "client_id" {
  value = aws_cognito_user_pool_client.main.id
}

output "hosted_ui_domain" {
  value = "https://${aws_cognito_user_pool_domain.main.domain}.auth.eu-west-2.amazoncognito.com"
}
```

- [ ] **Step 4: Commit**

```bash
git add infrastructure/modules/auth/
git commit -m "feat: add auth Terraform module (Cognito)"
```

---

## Task 4: Storage Module

**Files:**
- Create: `infrastructure/modules/storage/main.tf`
- Create: `infrastructure/modules/storage/variables.tf`
- Create: `infrastructure/modules/storage/outputs.tf`

- [ ] **Step 1: Create `infrastructure/modules/storage/variables.tf`**

```hcl
variable "env_name" {
  type = string
}
```

- [ ] **Step 2: Create `infrastructure/modules/storage/main.tf`**

```hcl
resource "aws_s3_bucket" "content" {
  bucket = "exeaws26-content-${var.env_name}"
  tags = { Name = "exeaws26-content-${var.env_name}" }
}

resource "aws_s3_bucket_public_access_block" "content" {
  bucket = aws_s3_bucket.content.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_iam_policy" "s3_content" {
  name        = "${var.env_name}-s3-content-policy"
  description = "Allow ECS task role to read and write content objects"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["s3:GetObject", "s3:PutObject"]
      Resource = "${aws_s3_bucket.content.arn}/*"
    }]
  })
}
```

- [ ] **Step 3: Create `infrastructure/modules/storage/outputs.tf`**

```hcl
output "bucket_name" {
  value = aws_s3_bucket.content.bucket
}

output "bucket_arn" {
  value = aws_s3_bucket.content.arn
}

output "s3_policy_arn" {
  value = aws_iam_policy.s3_content.arn
}
```

- [ ] **Step 4: Commit**

```bash
git add infrastructure/modules/storage/
git commit -m "feat: add storage Terraform module (S3)"
```

---

## Task 5: Database Module

**Files:**
- Create: `infrastructure/modules/database/main.tf`
- Create: `infrastructure/modules/database/variables.tf`
- Create: `infrastructure/modules/database/outputs.tf`

- [ ] **Step 1: Create `infrastructure/modules/database/variables.tf`**

```hcl
variable "env_name" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "sg_rds_id" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}
```

- [ ] **Step 2: Create `infrastructure/modules/database/main.tf`**

```hcl
resource "aws_db_subnet_group" "main" {
  name       = "${var.env_name}-db-subnet-group"
  subnet_ids = var.private_subnet_ids
  tags = { Name = "${var.env_name}-db-subnet-group" }
}

resource "aws_db_instance" "main" {
  identifier             = "${var.env_name}-postgres"
  engine                 = "postgres"
  engine_version         = "17"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  storage_type           = "gp2"
  db_name                = "exeaws26"
  username               = "exeaws26"
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.sg_rds_id]
  multi_az               = false
  publicly_accessible    = false
  deletion_protection    = true
  skip_final_snapshot    = false
  final_snapshot_identifier = "${var.env_name}-postgres-final-snapshot"

  tags = { Name = "${var.env_name}-postgres" }
}
```

- [ ] **Step 3: Create `infrastructure/modules/database/outputs.tf`**

```hcl
output "endpoint" {
  value = aws_db_instance.main.endpoint
}

output "db_name" {
  value = aws_db_instance.main.db_name
}

output "port" {
  value = aws_db_instance.main.port
}
```

- [ ] **Step 4: Commit**

```bash
git add infrastructure/modules/database/
git commit -m "feat: add database Terraform module (RDS PostgreSQL 17)"
```

---

## Task 6: Registry Module

**Files:**
- Create: `infrastructure/modules/registry/main.tf`
- Create: `infrastructure/modules/registry/variables.tf`
- Create: `infrastructure/modules/registry/outputs.tf`

- [ ] **Step 1: Create `infrastructure/modules/registry/variables.tf`**

```hcl
variable "env_name" {
  type = string
}
```

- [ ] **Step 2: Create `infrastructure/modules/registry/main.tf`**

```hcl
resource "aws_ecr_repository" "backend" {
  name                 = "exeaws26/backend"
  image_tag_mutability = "MUTABLE"
  tags = { Name = "exeaws26-backend" }
}

resource "aws_ecr_repository" "frontend" {
  name                 = "exeaws26/frontend"
  image_tag_mutability = "MUTABLE"
  tags = { Name = "exeaws26-frontend" }
}

locals {
  lifecycle_policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 tagged images"
        selection = {
          tagStatus   = "tagged"
          tagPrefixList = ["v"]
          countType   = "imageCountMoreThan"
          countNumber = 5
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 2
        description  = "Expire untagged images after 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = { type = "expire" }
      }
    ]
  })
}

resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name
  policy     = local.lifecycle_policy
}

resource "aws_ecr_lifecycle_policy" "frontend" {
  repository = aws_ecr_repository.frontend.name
  policy     = local.lifecycle_policy
}
```

- [ ] **Step 3: Create `infrastructure/modules/registry/outputs.tf`**

```hcl
output "backend_repo_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "frontend_repo_url" {
  value = aws_ecr_repository.frontend.repository_url
}
```

- [ ] **Step 4: Commit**

```bash
git add infrastructure/modules/registry/
git commit -m "feat: add registry Terraform module (ECR)"
```

---

## Task 7: Compute Module

**Files:**
- Create: `infrastructure/modules/compute/main.tf`
- Create: `infrastructure/modules/compute/variables.tf`
- Create: `infrastructure/modules/compute/outputs.tf`

- [ ] **Step 1: Create `infrastructure/modules/compute/variables.tf`**

```hcl
variable "env_name" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "sg_ecs_id" {
  type = string
}

variable "frontend_target_group_arn" {
  type = string
}

variable "backend_target_group_arn" {
  type = string
}

variable "s3_policy_arn" {
  type = string
}

variable "backend_image" {
  type        = string
  description = "Full ECR image URI including tag for backend"
}

variable "frontend_image" {
  type        = string
  description = "Full ECR image URI including tag for frontend"
}

variable "database_url" {
  type      = string
  sensitive = true
}

variable "secret_key" {
  type      = string
  sensitive = true
}

variable "cognito_user_pool_id" {
  type = string
}

variable "cognito_client_id" {
  type = string
}

variable "s3_bucket_name" {
  type = string
}

variable "alb_dns_name" {
  type = string
}
```

- [ ] **Step 2: Create `infrastructure/modules/compute/main.tf`**

```hcl
# ── IAM: Task Execution Role (ECS agent — pulls images, writes logs) ──────────
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.env_name}-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ── IAM: Task Role (running container identity — S3 access) ───────────────────
resource "aws_iam_role" "ecs_task" {
  name = "${var.env_name}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_s3" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = var.s3_policy_arn
}

# ── CloudWatch Log Groups ─────────────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/exeaws26-backend"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/exeaws26-frontend"
  retention_in_days = 30
}

# ── ECS Cluster ───────────────────────────────────────────────────────────────
resource "aws_ecs_cluster" "main" {
  name = "${var.env_name}-cluster"
  tags = { Name = "${var.env_name}-cluster" }
}

# ── Backend Task Definition ───────────────────────────────────────────────────
resource "aws_ecs_task_definition" "backend" {
  family                   = "exeaws26-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "backend"
    image     = var.backend_image
    essential = true

    portMappings = [{ containerPort = 8000, protocol = "tcp" }]

    environment = [
      { name = "DATABASE_URL",          value = var.database_url },
      { name = "SECRET_KEY",            value = var.secret_key },
      { name = "ENVIRONMENT",           value = "production" },
      { name = "COGNITO_REGION",        value = "eu-west-2" },
      { name = "COGNITO_USER_POOL_ID",  value = var.cognito_user_pool_id },
      { name = "S3_BUCKET_NAME",        value = var.s3_bucket_name },
      { name = "AWS_REGION",            value = "eu-west-2" },
      { name = "ALLOWED_ORIGINS",       value = "http://${var.alb_dns_name}" },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.backend.name
        "awslogs-region"        = "eu-west-2"
        "awslogs-stream-prefix" = "backend"
      }
    }
  }])
}

# ── Frontend Task Definition ──────────────────────────────────────────────────
# VITE_* vars are baked into the image at build time — no runtime env vars here.
resource "aws_ecs_task_definition" "frontend" {
  family                   = "exeaws26-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "frontend"
    image     = var.frontend_image
    essential = true

    portMappings = [{ containerPort = 3000, protocol = "tcp" }]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.frontend.name
        "awslogs-region"        = "eu-west-2"
        "awslogs-stream-prefix" = "frontend"
      }
    }
  }])
}

# ── ECS Services ──────────────────────────────────────────────────────────────
resource "aws_ecs_service" "backend" {
  name            = "backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.sg_ecs_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.backend_target_group_arn
    container_name   = "backend"
    container_port   = 8000
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  lifecycle {
    ignore_changes = [desired_count]
  }
}

resource "aws_ecs_service" "frontend" {
  name            = "frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.sg_ecs_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.frontend_target_group_arn
    container_name   = "frontend"
    container_port   = 3000
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  lifecycle {
    ignore_changes = [desired_count]
  }
}

# ── Auto Scaling ──────────────────────────────────────────────────────────────
resource "aws_appautoscaling_target" "backend" {
  max_capacity       = 4
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "backend_cpu" {
  name               = "${var.env_name}-backend-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend.resource_id
  scalable_dimension = aws_appautoscaling_target.backend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

resource "aws_appautoscaling_target" "frontend" {
  max_capacity       = 4
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.frontend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "frontend_cpu" {
  name               = "${var.env_name}-frontend-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.frontend.resource_id
  scalable_dimension = aws_appautoscaling_target.frontend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.frontend.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}
```

- [ ] **Step 3: Create `infrastructure/modules/compute/outputs.tf`**

```hcl
output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "backend_task_definition_family" {
  value = aws_ecs_task_definition.backend.family
}
```

- [ ] **Step 4: Commit**

```bash
git add infrastructure/modules/compute/
git commit -m "feat: add compute Terraform module (ECS Fargate + auto-scaling)"
```

---

## Task 8: Wire Root main.tf and Run terraform plan

**Files:**
- Modify: `infrastructure/main.tf`
- Modify: `infrastructure/outputs.tf`

- [ ] **Step 1: Replace `infrastructure/main.tf` with module wiring**

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
  source   = "./modules/registry"
  env_name = var.env_name
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
  database_url              = "postgresql+asyncpg://${module.database.db_name}:${var.db_password}@${module.database.endpoint}/${module.database.db_name}"
  secret_key                = var.secret_key
  cognito_user_pool_id      = module.auth.user_pool_id
  cognito_client_id         = module.auth.client_id
  s3_bucket_name            = module.storage.bucket_name
  alb_dns_name              = module.networking.alb_dns_name
}
```

- [ ] **Step 2: Replace `infrastructure/outputs.tf` with real outputs**

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

- [ ] **Step 3: Run terraform init and plan**

```bash
cd infrastructure
terraform init
terraform plan -var="backend_image_tag=placeholder" -var="frontend_image_tag=placeholder"
```

Expected: A plan with ~40–60 resources to create, no errors. Review the plan output. The `database_url` construction will show the endpoint placeholder until the database exists.

- [ ] **Step 4: Commit**

```bash
git add infrastructure/main.tf infrastructure/outputs.tf
git commit -m "feat: wire all Terraform modules in root main.tf"
```

---

## Task 9: CI Workflow for Terraform

**Files:**
- Create: `.github/workflows/terraform.yml`

- [ ] **Step 1: Add `TF_API_TOKEN` GitHub secret**

In your GitHub repo: Settings → Secrets and variables → Actions → New repository secret.
Name: `TF_API_TOKEN`, Value: the Terraform Cloud API token you created in Prerequisites.

- [ ] **Step 2: Create `.github/workflows/terraform.yml`**

```yaml
name: Terraform

on:
  pull_request:
    paths: ['infrastructure/**']
  push:
    branches: [main]
    paths: ['infrastructure/**']

concurrency:
  group: terraform-${{ github.head_ref || github.ref_name }}
  cancel-in-progress: true

permissions: {}

jobs:
  plan:
    name: Plan
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    permissions:
      contents: read
      pull-requests: write
    env:
      TF_API_TOKEN: ${{ secrets.TF_API_TOKEN }}
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          cli_config_credentials_token: ${{ secrets.TF_API_TOKEN }}

      - name: Terraform Init
        run: terraform init
        working-directory: infrastructure

      - name: Terraform Plan
        id: plan
        run: terraform plan -no-color -input=false
        working-directory: infrastructure
        continue-on-error: true

      - name: Post plan as PR comment
        uses: actions/github-script@v7
        with:
          script: |
            const output = `#### Terraform Plan \`${{ steps.plan.outcome }}\`
            <details><summary>Show Plan</summary>

            \`\`\`terraform
            ${{ steps.plan.outputs.stdout }}
            \`\`\`

            </details>`;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: output
            });

      - name: Fail if plan failed
        if: steps.plan.outcome == 'failure'
        run: exit 1

  apply:
    name: Apply
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    permissions:
      contents: read
    env:
      TF_API_TOKEN: ${{ secrets.TF_API_TOKEN }}
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          cli_config_credentials_token: ${{ secrets.TF_API_TOKEN }}

      - name: Terraform Init
        run: terraform init
        working-directory: infrastructure

      - name: Terraform Apply
        run: terraform apply -auto-approve -input=false
        working-directory: infrastructure
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/terraform.yml
git commit -m "feat: add Terraform CI workflow (plan on PR, apply on main)"
```

---

## Task 10: Production Dockerfiles

**Files:**
- Modify: `backend/Dockerfile`
- Modify: `frontend/Dockerfile`
- Modify: `frontend/package.json`
- Modify: `frontend/svelte.config.js`

- [ ] **Step 1: Fix backend Dockerfile — remove `--reload`**

Replace the current content of `backend/Dockerfile` with:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry==1.8.5

ENV POETRY_VIRTUALENVS_IN_PROJECT=1

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-interaction --without dev

COPY . .

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Key changes: removed `--reload` (dev-only), added `--without dev` to skip dev dependencies, added `COPY . .`, added `EXPOSE 8000`.

- [ ] **Step 2: Switch frontend to `adapter-node`**

In `frontend/`, run:

```bash
cd frontend
npm install @sveltejs/adapter-node
npm uninstall @sveltejs/adapter-static
```

This updates `package.json` automatically.

- [ ] **Step 3: Update `frontend/svelte.config.js`**

```js
import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter(),
  },
};

export default config;
```

- [ ] **Step 4: Rewrite `frontend/Dockerfile` as multi-stage**

SvelteKit with `adapter-node` produces a `build/` directory and a `node_modules/` snapshot. The production image runs `node build/index.js`. `VITE_*` build args are provided here — they are baked into the bundle by Vite at build time.

```dockerfile
# ── Build stage ───────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# VITE_* vars are baked into the bundle at build time
ARG VITE_API_BASE_URL
ARG VITE_COGNITO_DOMAIN
ARG VITE_COGNITO_CLIENT_ID
ARG VITE_COGNITO_REDIRECT_URI

RUN npm run build

# ── Production stage ──────────────────────────────────────────────────────────
FROM node:20-alpine

WORKDIR /app

COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json ./package.json

ENV NODE_ENV=production
ENV PORT=3000

EXPOSE 3000

CMD ["node", "build/index.js"]
```

- [ ] **Step 5: Verify the frontend builds locally**

```bash
cd frontend
VITE_API_BASE_URL=http://localhost:8000 \
VITE_COGNITO_DOMAIN=https://exeaws26.auth.eu-west-2.amazoncognito.com \
VITE_COGNITO_CLIENT_ID=placeholder \
VITE_COGNITO_REDIRECT_URI=http://localhost/auth/callback \
npm run build
```

Expected: `build/` directory created with `index.js` inside.

- [ ] **Step 6: Commit**

```bash
git add backend/Dockerfile frontend/Dockerfile frontend/svelte.config.js frontend/package.json frontend/package-lock.json
git commit -m "feat: production Dockerfiles — remove --reload, switch frontend to adapter-node"
```

---

## Task 11: Alembic Setup

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/alembic.ini` (via `alembic init`)
- Create: `backend/migrations/` (via `alembic init`)
- Modify: `backend/migrations/env.py`
- Modify: `backend/app/config.py`

- [ ] **Step 1: Add `alembic` and `boto3` to backend dependencies**

In `backend/pyproject.toml`, add to `[tool.poetry.dependencies]`:

```toml
alembic = "^1.14.0"
boto3 = "^1.35.0"
```

Then install:

```bash
cd backend
poetry install --no-root --no-interaction
```

- [ ] **Step 2: Add missing config fields to `backend/app/config.py`**

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    COGNITO_REGION: str = "eu-west-2"
    COGNITO_USER_POOL_ID: str = ""
    S3_BUCKET_NAME: str = ""
    AWS_REGION: str = "eu-west-2"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 3: Initialise Alembic**

```bash
cd backend
poetry run alembic init migrations
```

This creates `alembic.ini` and `migrations/` with `env.py`, `script.py.mako`, and `versions/`.

- [ ] **Step 4: Edit `alembic.ini` — point `script_location` to `migrations`**

The generated `alembic.ini` sets `script_location = alembic`. Change it to:

```ini
script_location = migrations
```

Also comment out `sqlalchemy.url` (we set it in `env.py` programmatically):

```ini
# sqlalchemy.url = driver://user:pass@localhost/dbname
```

- [ ] **Step 5: Replace `backend/migrations/env.py` with async-aware config**

The generated `env.py` uses synchronous SQLAlchemy. Replace the entire file:

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.models import Base  # noqa: F401 — imports all model classes, registering them with Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = get_settings().DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(get_settings().DATABASE_URL)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

- [ ] **Step 6: Generate the initial migration from existing models**

```bash
cd backend
poetry run alembic revision --autogenerate -m "initial schema"
```

Expected: A new file created at `backend/migrations/versions/<hash>_initial_schema.py`.

- [ ] **Step 7: Verify the migration locally**

You need a running PostgreSQL. If you have Docker:

```bash
docker run -d --name pg-test -e POSTGRES_PASSWORD=test -e POSTGRES_USER=test -e POSTGRES_DB=test -p 5432:5432 postgres:17
DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test poetry run alembic upgrade head
```

Expected: `Running upgrade  -> <hash>, initial schema` — no errors.

```bash
docker stop pg-test && docker rm pg-test
```

- [ ] **Step 8: Commit**

```bash
git add backend/pyproject.toml backend/poetry.lock backend/alembic.ini backend/migrations/ backend/app/config.py
git commit -m "feat: add Alembic async migration setup with initial schema"
```

---

## Task 12: Seed Data Script

**Files:**
- Create: `backend/seed.py`

Seed data covers: 5 topics (one per T-Level pathway), and at least one T-Level per topic. All inserts use `INSERT ... ON CONFLICT DO NOTHING` so running the script twice is safe.

- [ ] **Step 1: Create `backend/seed.py`**

```python
"""
Idempotent seed script. Run via:
  poetry run python seed.py

Uses ON CONFLICT DO NOTHING so it is safe to run multiple times.
Designed to be invoked as a one-off ECS task in production.
"""
import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

TOPICS = [
    {
        "slug": "digital-production-design-development",
        "name": "Digital Production, Design and Development",
        "description": "Learn to design, build, and test digital products including software, systems, and services.",
        "accent_colour": "#0066CC",
        "t_levels": [
            {
                "name": "Digital Production, Design and Development",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English and maths.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            }
        ],
    },
    {
        "slug": "digital-business-services",
        "name": "Digital Business Services",
        "description": "Understand how digital tools and services support modern business operations.",
        "accent_colour": "#00994C",
        "t_levels": [
            {
                "name": "Digital Business Services",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English and maths.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            }
        ],
    },
    {
        "slug": "digital-infrastructure",
        "name": "Digital Infrastructure",
        "description": "Explore the networks, cloud platforms, and systems that underpin digital services.",
        "accent_colour": "#CC3300",
        "t_levels": [
            {
                "name": "Digital Infrastructure",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English and maths.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            }
        ],
    },
    {
        "slug": "design-surveying-planning",
        "name": "Design, Surveying and Planning",
        "description": "Discover careers in built environment design, including architecture and civil engineering.",
        "accent_colour": "#996600",
        "t_levels": [
            {
                "name": "Design, Surveying and Planning for Construction",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English, maths, and ideally a science.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            }
        ],
    },
    {
        "slug": "health",
        "name": "Health",
        "description": "Prepare for a career in healthcare, covering clinical environments and patient support.",
        "accent_colour": "#660099",
        "t_levels": [
            {
                "name": "Health (Nursing)",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English, maths, and a science.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            },
            {
                "name": "Health (Midwifery)",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English, maths, and a science.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            },
        ],
    },
]


async def seed() -> None:
    engine = create_async_engine(get_settings().DATABASE_URL, echo=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        await _seed_topics(session)
    await engine.dispose()
    print("Seed complete.")


async def _seed_topics(session: AsyncSession) -> None:
    for topic_data in TOPICS:
        t_levels = topic_data.pop("t_levels")

        await session.execute(
            text("""
                INSERT INTO topics (slug, name, description, accent_colour)
                VALUES (:slug, :name, :description, :accent_colour)
                ON CONFLICT (slug) DO NOTHING
            """),
            topic_data,
        )
        await session.flush()

        result = await session.execute(
            text("SELECT id FROM topics WHERE slug = :slug"),
            {"slug": topic_data["slug"]},
        )
        topic_id = result.scalar_one()

        for tl in t_levels:
            await session.execute(
                text("""
                    INSERT INTO t_levels (topic_id, name, entry_requirements, how_to_apply)
                    SELECT :topic_id, :name, :entry_requirements, :how_to_apply
                    WHERE NOT EXISTS (
                        SELECT 1 FROM t_levels WHERE topic_id = :topic_id AND name = :name
                    )
                """),
                {**tl, "topic_id": topic_id},
            )

    await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
```

- [ ] **Step 2: Run seed script locally to verify it works**

```bash
cd backend
docker run -d --name pg-seed -e POSTGRES_PASSWORD=test -e POSTGRES_USER=test -e POSTGRES_DB=test -p 5432:5432 postgres:17
DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test poetry run alembic upgrade head
DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test poetry run python seed.py
```

Expected: Seed inserts logged, `Seed complete.` printed.

- [ ] **Step 3: Verify idempotency — run seed a second time**

```bash
DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test poetry run python seed.py
```

Expected: Same output, no duplicates, no errors.

```bash
docker stop pg-seed && docker rm pg-seed
```

- [ ] **Step 4: Commit**

```bash
git add backend/seed.py
git commit -m "feat: add idempotent seed script for topics and T-levels"
```

---

## First Deploy Sequence (reference)

Once all tasks are complete and the branch is merged to main, follow this order:

1. **`terraform apply` (first run)** — CI runs on merge to main. All infra is created including the ALB. Read `alb_dns_name` from Terraform Cloud outputs UI or `terraform output alb_dns_name`.

2. **Build and push images** — use the ALB DNS name as build args:
   ```bash
   ALB_DNS=<value from terraform output>
   AWS_ACCOUNT=<your account id>
   REGION=eu-west-2

   aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com

   docker build \
     --build-arg VITE_API_BASE_URL=http://$ALB_DNS:8000 \
     --build-arg VITE_COGNITO_DOMAIN=https://exeaws26.auth.$REGION.amazoncognito.com \
     --build-arg VITE_COGNITO_CLIENT_ID=<cognito_client_id from terraform output> \
     --build-arg VITE_COGNITO_REDIRECT_URI=http://$ALB_DNS/auth/callback \
     -t $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/exeaws26/frontend:v1 \
     frontend/

   docker push $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/exeaws26/frontend:v1

   docker build -t $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/exeaws26/backend:v1 backend/
   docker push $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/exeaws26/backend:v1
   ```

3. **Set image tags in Terraform Cloud** — update the `backend_image_tag` and `frontend_image_tag` workspace variables to `v1`, then trigger another apply (or push a trivial change to `infrastructure/`).

4. **Run migration task:**
   ```bash
   aws ecs run-task \
     --cluster exeaws26-prod \
     --task-definition exeaws26-backend \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[<private_subnet_a>],securityGroups=[<sg_ecs_id>],assignPublicIp=DISABLED}" \
     --overrides '{"containerOverrides":[{"name":"backend","command":["poetry","run","alembic","upgrade","head"]}]}'
   ```
   Wait: `aws ecs wait tasks-stopped --cluster exeaws26-prod --tasks <task-arn>`

5. **Run seed task (first deploy only):**
   ```bash
   aws ecs run-task \
     --cluster exeaws26-prod \
     --task-definition exeaws26-backend \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[<private_subnet_a>],securityGroups=[<sg_ecs_id>],assignPublicIp=DISABLED}" \
     --overrides '{"containerOverrides":[{"name":"backend","command":["poetry","run","python","seed.py"]}]}'
   ```

The platform is then live at `http://<alb_dns_name>`.
