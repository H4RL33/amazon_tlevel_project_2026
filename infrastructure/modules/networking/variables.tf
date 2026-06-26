variable "env_name" {
  type = string
}

variable "public_domain" {
  type        = string
  description = "Custom domain pointed at the ALB for the deployed frontend"
}

variable "api_domain" {
  type        = string
  description = "Custom domain pointed at the ALB for the deployed backend API"
}
