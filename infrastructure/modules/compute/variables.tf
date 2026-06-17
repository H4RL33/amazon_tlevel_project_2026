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
