variable "prefix" {
  description = "Prefix for all resources"
  type        = string
  default     = "ansible-test"
}

variable "node_ingress" {
  description = "Port to allow for ingress on nodes"
  type        = list(number)
}

variable "vpc_id" {
  description = "The VPC id for the security group"
  type = string
}