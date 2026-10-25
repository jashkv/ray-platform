variable "table_name" {
  description = "Name of the DynamoDB ledger table"
  type        = string
}

variable "kms_key_arn" {
  description = "KMS Key ARN for DynamoDB SSE"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
