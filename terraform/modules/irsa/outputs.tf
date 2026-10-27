output "role_arn" {
  description = "The IRSA IAM Role ARN"
  value       = aws_iam_role.ray_workload.arn
}

output "role_name" {
  description = "The IRSA IAM Role Name"
  value       = aws_iam_role.ray_workload.name
}

output "service_account_annotation" {
  description = "Kubernetes ServiceAccount annotation string"
  value       = "eks.amazonaws.com/role-arn: ${aws_iam_role.ray_workload.arn}"
}
