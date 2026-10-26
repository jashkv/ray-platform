# ==============================================================================
# Karpenter Module Outputs
# ==============================================================================

output "controller_role_arn" {
  description = "The ARN of the Karpenter Controller IAM Role (for ServiceAccount annotation)"
  value       = aws_iam_role.controller.arn
}

output "controller_role_name" {
  description = "The name of the Karpenter Controller IAM Role"
  value       = aws_iam_role.controller.name
}

output "node_role_arn" {
  description = "The ARN of the Karpenter Node IAM Role"
  value       = aws_iam_role.node.arn
}

output "node_role_name" {
  description = "The name of the Karpenter Node IAM Role (used in EC2NodeClass)"
  value       = aws_iam_role.node.name
}

output "node_instance_profile_name" {
  description = "The name of the Karpenter Node IAM Instance Profile"
  value       = aws_iam_instance_profile.node.name
}

output "interruption_queue_name" {
  description = "The name of the SQS interruption queue for Karpenter"
  value       = aws_sqs_queue.interruption.name
}

output "interruption_queue_arn" {
  description = "The ARN of the SQS interruption queue"
  value       = aws_sqs_queue.interruption.arn
}

output "interruption_queue_url" {
  description = "The URL of the SQS interruption queue"
  value       = aws_sqs_queue.interruption.id
}
