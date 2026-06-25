module "networking" {
  source        = "./modules/networking"
  env_name      = var.env_name
  public_domain = var.public_domain
  api_domain    = var.api_domain
}

module "auth" {
  source        = "./modules/auth"
  env_name      = var.env_name
  public_domain = var.public_domain
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
  public_subnet_ids         = module.networking.public_subnet_ids
  sg_ecs_id                 = module.networking.sg_ecs_id
  frontend_target_group_arn = module.networking.frontend_target_group_arn
  backend_target_group_arn  = module.networking.backend_target_group_arn
  s3_policy_arn             = module.storage.s3_policy_arn
  backend_image             = "ghcr.io/${var.ghcr_namespace}-backend:${var.backend_image_tag}"
  frontend_image            = "ghcr.io/${var.ghcr_namespace}-frontend:${var.frontend_image_tag}"
  # aws_db_instance.endpoint already includes port (e.g. host:5432) — do NOT append :${module.database.port}
  database_url         = "postgresql+asyncpg://exeaws26:${var.db_password}@${module.database.endpoint}/exeaws26"
  secret_key           = var.secret_key
  cognito_user_pool_id = module.auth.user_pool_id
  s3_bucket_name       = module.storage.bucket_name
  alb_dns_name         = module.networking.alb_dns_name
  public_domain        = var.public_domain
}

# ── CD credentials for GitHub Actions ─────────────────────────────────────────
# Scoped to exactly what release-backend.yml/release-frontend.yml need to force
# an ECS redeploy after pushing a new :latest image — nothing else.
resource "aws_iam_user" "github_actions_deploy" {
  name = "${var.env_name}-github-actions-deploy"
}

resource "aws_iam_user_policy" "github_actions_ecs_redeploy" {
  name = "ecs-redeploy"
  user = aws_iam_user.github_actions_deploy.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ecs:UpdateService", "ecs:DescribeServices"]
      Resource = [module.compute.backend_service_arn, module.compute.frontend_service_arn]
    }]
  })
}

resource "aws_iam_access_key" "github_actions_deploy" {
  user = aws_iam_user.github_actions_deploy.name
}
