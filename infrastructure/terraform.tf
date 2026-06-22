terraform {
  cloud {
    organization = "exeaws26"
    workspaces {
      name = "exeaws26-prod"
    }
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  required_version = ">= 1.9"
}
