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

module "vpc" {
  source = "./modules/vpc" 

  aws_region = var.aws_region
  prefix = var.prefix
  vpc_cidr = var.vpc_cidr
  public_subnet_cidr = var.public_subnet_cidr 
}

module "security_group" {
  source = "./modules/security_group"

  prefix = var.prefix
  node_ingress = var.node_ingress
  vpc_id = module.vpc.vpc_id
}

# Create an EC2 instance
module "ec2_instance" {
  source = "./modules/ec2_instance"

  for_each = local.instances

  name                   = "${var.prefix}-${each.key}"
  ami                    = each.value.ami != "" ? each.value.ami : var.default_ami
  instance_type          = each.value.instance_type != "" ? each.value.instance_type : var.default_instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [module.security_group.security_group_id]
  subnet_id              = module.vpc.public_subnet_id
  user_data              = each.value.user_data

  tags = merge(
    var.default_tags,
    each.value.tags,
    {
      Name = "${var.prefix}-${each.key}"
    }
  )
}

# Ansible inventory file generation
resource "local_file" "ansible_inventory" {
  count = var.inventory_tmpl_path != null ? 1 : 0
  content = templatefile(var.inventory_tmpl_path, {
    instances    = module.ec2_instance
  })
  filename = "inventory.yml"

  depends_on = [module.ec2_instance]
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