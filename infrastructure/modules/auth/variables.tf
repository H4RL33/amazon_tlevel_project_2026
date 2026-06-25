variable "env_name" {
  type = string
}

variable "public_domain" {
  type        = string
  description = "Custom domain pointed at the deployed frontend — used to build Cognito callback and sign-out URLs"
}
