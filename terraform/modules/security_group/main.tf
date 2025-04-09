# Create a security group
resource "aws_security_group" "instance" {
  name        = "${var.prefix}-sg"
  description = "Allow SSH and required ports for Ansible testing"
  vpc_id      = var.vpc_id

  dynamic "ingress" {
    for_each = var.node_ingress
    content {
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
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