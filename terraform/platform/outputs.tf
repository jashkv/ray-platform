output "ecr_repository_url" {
  description = "The URL of the Amazon ECR container registry"
  value       = aws_ecr_repository.app.repository_url
}

output "github_actions_deployer_role_arn" {
  description = "IAM Role ARN to configure as AWS_DEPLOYMENT_ROLE_ARN secret in GitHub"
  value       = aws_iam_role.github_actions_deployer.arn
}
