terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }

  # Configurable backend block: uncomment and fill from bootstrap output when deploying to AWS
  # backend "s3" {
  #   bucket         = "ray-platform-dev-tfstate-<account-id>"
  #   key            = "network/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "ray-platform-dev-tflock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(
      var.tags,
      {
        Project     = var.project_name
        Environment = var.environment
        ManagedBy   = "Terraform"
        Layer       = "02-network"
      }
    )
  }
}
