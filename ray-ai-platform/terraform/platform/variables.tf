variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "ray-platform"
}

variable "github_repository" {
  description = "GitHub repository (owner/repo) permitted to assume deployment role"
  type        = string
  default     = "org/ray-ai-platform"
}

variable "eks_cluster_arn" {
  description = "ARN of the EKS cluster"
  type        = string
  default     = "arn:aws:eks:us-east-1:123456789012:cluster/ray-platform-dev-eks"
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
