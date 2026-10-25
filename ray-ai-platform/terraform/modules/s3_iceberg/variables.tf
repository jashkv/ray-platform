variable "bucket_name" {
  description = "Name of the S3 data lakehouse bucket"
  type        = string
}

variable "kms_key_arn" {
  description = "KMS Key ARN for server-side encryption"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
