variable "env_name" {
  type = string
}

variable "alb_dns_name" {
  type        = string
  description = "ALB DNS name — used to build Cognito callback and sign-out URLs"
}
