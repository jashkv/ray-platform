output "cluster_name" {
  description = "The EKS cluster name"
  value       = aws_eks_cluster.main.name
}

output "cluster_id" {
  description = "The EKS cluster ID"
  value       = aws_eks_cluster.main.id
}

output "cluster_arn" {
  description = "The EKS cluster ARN"
  value       = aws_eks_cluster.main.arn
}

output "cluster_endpoint" {
  description = "The Kubernetes API server endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.main.certificate_authority[0].data
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS control plane"
  value       = aws_security_group.cluster.id
}

output "oidc_provider_arn" {
  description = "The ARN of the OIDC Provider for IRSA"
  value       = aws_iam_openid_connect_provider.oidc.arn
}

output "oidc_provider_url" {
  description = "The URL of the OIDC Provider without protocol"
  value       = replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")
}

output "node_role_arn" {
  description = "The IAM role ARN used by EKS node groups"
  value       = aws_iam_role.node_group.arn
}

output "head_system_node_group_arn" {
  description = "ARN of the Head/System node group"
  value       = aws_eks_node_group.head_system.arn
}

output "worker_spot_node_group_arn" {
  description = "ARN of the Spot Worker node group"
  value       = aws_eks_node_group.worker_spot.arn
}
