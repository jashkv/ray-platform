variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (e.g. test)"
  type        = string
  default     = "test"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "ray-platform"
}

variable "oidc_provider_arn" {
  description = "OIDC Provider ARN from EKS layer (e.g. arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/...)"
  type        = string
  default     = "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/EXAMPLE"
}

variable "oidc_provider_url" {
  description = "OIDC Provider URL without protocol"
  type        = string
  default     = "oidc.eks.us-east-1.amazonaws.com/id/EXAMPLE"
}

variable "namespace" {
  description = "Kubernetes namespace for Ray workloads"
  type        = string
  default     = "ray-workloads"
}

variable "service_account_name" {
  description = "Kubernetes ServiceAccount name for Ray pods"
  type        = string
  default     = "ray-pipeline-sa"
}

variable "tags" {
  description = "Additional resource tags"
  type        = map(string)
  default     = {}
}
