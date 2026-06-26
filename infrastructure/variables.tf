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

variable "public_domain" {
  type        = string
  default     = "tlevels.h4rl3y.xyz"
  description = "Custom domain pointed at the ALB for the deployed frontend"
}

variable "api_domain" {
  type        = string
  default     = "api.tlevels.h4rl3y.xyz"
  description = "Custom domain pointed at the ALB for the deployed backend API"
}
