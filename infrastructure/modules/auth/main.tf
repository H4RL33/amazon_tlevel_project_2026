resource "aws_cognito_user_pool" "main" {
  name                = "${var.env_name}-user-pool"
  deletion_protection = "ACTIVE"

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

  # Cognito requires HTTPS callback URLs except for localhost. Both are kept:
  # localhost for manual e2e verification against a local docker-compose
  # frontend, and the real domain for the deployed ECS frontend.
  callback_urls = [
    "http://localhost:3000/auth/callback",
    "https://${var.public_domain}/auth/callback",
  ]
  logout_urls = [
    "http://localhost:3000/",
    "https://${var.public_domain}/",
  ]

  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH",
  ]
}

resource "aws_cognito_user_pool_domain" "main" {
  domain       = "exeter-livingcampus-${var.env_name}"
  user_pool_id = aws_cognito_user_pool.main.id
}
