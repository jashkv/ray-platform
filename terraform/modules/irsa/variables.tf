variable "role_name" {
  description = "IAM role name for Ray pipeline workloads"
  type        = string
}

variable "oidc_provider_arn" {
  description = "OIDC Provider ARN from EKS"
  type        = string
}

variable "oidc_provider_url" {
  description = "OIDC Provider URL (without https://)"
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace for the Ray service account"
  type        = string
  default     = "ray-workloads"
}

variable "service_account_name" {
  description = "Kubernetes ServiceAccount name"
  type        = string
  default     = "ray-pipeline-sa"
}

variable "data_bucket_arn" {
  description = "ARN of the S3 data lakehouse bucket"
  type        = string
}

variable "glue_database_arn" {
  description = "ARN of the Glue Catalog database"
  type        = string
}

variable "ledger_table_arn" {
  description = "ARN of the DynamoDB processing ledger table"
  type        = string
}

variable "kms_key_arn" {
  description = "KMS CMK ARN for encryption"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
