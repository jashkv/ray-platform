output "vpc_id" {
  description = "The VPC ID"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "The VPC CIDR block"
  value       = module.vpc.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "List of private subnet IDs for EKS node groups and Ray pods"
  value       = module.vpc.private_subnet_ids
}

output "s3_gateway_endpoint_id" {
  description = "S3 Gateway VPC Endpoint ID (zero-cost data transfer to S3)"
  value       = module.vpc.s3_gateway_endpoint_id
}

output "ray_internal_security_group_id" {
  description = "Security group ID for Ray internal communication"
  value       = aws_security_group.ray_internal.id
}
