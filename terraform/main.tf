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

# Create a VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.prefix}-vpc"
  }
}

# Create an internet gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.prefix}-igw"
  }
}

# Create a public subnet
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  map_public_ip_on_launch = true
  availability_zone       = "${var.aws_region}a"

  tags = {
    Name = "${var.prefix}-public-subnet"
  }
}

# Create a route table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.prefix}-public-rt"
  }
}

# Associate the route table with the subnet
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Create a security group
resource "aws_security_group" "instance" {
  name        = "${var.prefix}-sg"
  description = "Allow SSH and required ports for Ansible testing"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH access"
  }

  # Add additional ingress rules for your Ansible testing needs
  # Example for HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "${var.prefix}-sg"
  }
}

# Create an EC2 instance
module "ec2_instance" {
  source = "./modules/ec2_instance"

  for_each = local.instances

  name                   = "${var.prefix}-${each.key}"
  ami                    = each.value.ami != "" ? each.value.ami : var.default_ami
  instance_type          = each.value.instance_type != "" ? each.value.instance_type : var.default_instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.instance.id]
  subnet_id              = aws_subnet.public.id
  user_data              = each.value.user_data

  tags = merge(
    var.default_tags,
    each.value.tags,
    {
      Name = "${var.prefix}-${each.key}"
    }
  )
}

# Output instance details
output "instance_details" {
  value = {
    for k, v in module.ec2_instance : k => {
      id                = v.instance_id
      public_ip         = v.public_ip
      public_dns        = v.public_dns
      availability_zone = v.availability_zone
    }
  }
  description = "Details of the EC2 instances"
}