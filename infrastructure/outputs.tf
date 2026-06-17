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
