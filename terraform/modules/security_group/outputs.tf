output "security_group_id" {
  description = "The security group id"
  value = aws_security_group.instance.id
}