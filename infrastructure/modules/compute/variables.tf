variable "env_name" {
  type = string
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "ECS tasks run here with public IPs (no NAT Gateway) to keep costs down"
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
  description = "Full GHCR image URI including tag for backend"
}

variable "frontend_image" {
  type        = string
  description = "Full GHCR image URI including tag for frontend"
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
  type        = string
  description = "Cognito app client ID — validated as the JWT audience by the backend"
}

variable "bedrock_embedding_model_id" {
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
  description = "Bedrock model used to embed Content/Album text for pgvector search and the Dynamic Mentor"
}

variable "bedrock_generation_model_id" {
  type        = string
  default     = "amazon.nova-lite-v1:0"
  description = "Bedrock model used for Dynamic Mentor chat generation — must support on-demand InvokeModel (no inference profile required)"
}

variable "s3_bucket_name" {
  type = string
}

variable "alb_dns_name" {
  type = string
}

variable "public_domain" {
  type        = string
  description = "Custom domain pointed at the deployed frontend — included in the backend's CORS allow-list"
}

variable "aws_region" {
  type    = string
  default = "eu-west-2"
}
