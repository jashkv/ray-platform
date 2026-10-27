variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "test"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "ray-platform"
}

variable "data_bucket_name" {
  description = "Name of S3 bucket for data lakehouse and raw files"
  type        = string
  default     = "ray-platform-test-data"
}

variable "ledger_table_name" {
  description = "Name of DynamoDB table for processing ledger"
  type        = string
  default     = "ray-platform-test-processing-ledger"
}

variable "glue_database_name" {
  description = "Name of AWS Glue Data Catalog database"
  type        = string
  default     = "corporate_data_db"
}

variable "kms_key_arn" {
  description = "ARN of KMS CMK for data and state machine encryption"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
