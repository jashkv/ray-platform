output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "The CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs where EKS nodes and Ray pods reside"
  value       = aws_subnet.private[*].id
}

output "s3_gateway_endpoint_id" {
  description = "The S3 Gateway VPC Endpoint ID"
  value       = aws_vpc_endpoint.s3.id
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = aws_nat_gateway.nat[*].id
}
