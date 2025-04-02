variable "aws_region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "prefix" {
  description = "Prefix for all resources"
  type        = string
  default     = "ansible-test"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "key_name" {
  description = "The name of the key pair to use for SSH access"
  type        = string
}

variable "default_ami" {
  description = "Default AMI to use for instances (Amazon Linux 2023 Free Tier eligible)"
  type        = string
  default     = "ami-0230bd60aa48260c6" # Amazon Linux 2023 in us-east-1, update for other regions
}

variable "default_instance_type" {
  description = "Default instance type to use (Free Tier eligible)"
  type        = string
  default     = "t2.micro"
}

variable "default_tags" {
  description = "Default tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "testing"
    Project     = "ansible-testing"
    ManagedBy   = "terraform"
  }
}

variable "instances" {
  description = "Map of instance configurations"
  type = map(object({
    count         = number
    ami           = string
    instance_type = string
    user_data     = string
    tags          = map(string)
  }))
  default = {
    "instance1" = {
      count         = 0
      ami           = ""
      instance_type = ""
      user_data     = ""
      tags          = {}
    }
  }
}