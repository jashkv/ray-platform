data "aws_caller_identity" "current" {}

locals {
  account_id  = data.aws_caller_identity.current.account_id
  bucket_name = "${var.project_name}-${var.environment}-data-${local.account_id}"
  table_name  = "${var.project_name}-${var.environment}-processing-ledger"
  db_name     = "${replace(var.project_name, "-", "_")}_${var.environment}_db"
  role_name   = "${var.project_name}-${var.environment}-ray-pipeline-irsa"
}

# ==============================================================================
# KMS Customer Managed Key for Data Lakehouse & Ledger Encryption
# ==============================================================================
resource "aws_kms_key" "data" {
  description             = "KMS CMK for S3 lakehouse and DynamoDB ledger encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-data-kms"
    }
  )
}

resource "aws_kms_alias" "data" {
  name          = "alias/${var.project_name}-${var.environment}-data"
  target_key_id = aws_kms_key.data.key_id
}
