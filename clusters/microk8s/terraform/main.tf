terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.2.0"
}

provider "aws" {
  region = var.aws_region
}

module "main" {
  source = "../../../terraform"

  aws_region = var.aws_region
  prefix = var.prefix
  key_name = var.key_name
  instances = var.instances
  node_ingress = var.node_ingress
}