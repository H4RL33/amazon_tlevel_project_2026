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
