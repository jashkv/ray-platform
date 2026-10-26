# ==============================================================================
# Karpenter Module Variables
# ==============================================================================

variable "cluster_name" {
  description = "Name of the target EKS cluster"
  type        = string
}

variable "cluster_arn" {
  description = "ARN of the EKS cluster"
  type        = string
  default     = ""
}

variable "oidc_provider_arn" {
  description = "IAM OIDC Provider ARN for IRSA trust relationship"
  type        = string
}

variable "oidc_provider_url" {
  description = "IAM OIDC Provider URL"
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace where Karpenter controller is deployed"
  type        = string
  default     = "kube-system"
}

variable "service_account_name" {
  description = "Name of the Karpenter Kubernetes ServiceAccount"
  type        = string
  default     = "karpenter"
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "test"
}

variable "tags" {
  description = "Resource tags applied to all Karpenter infrastructure"
  type        = map(string)
  default     = {}
}
