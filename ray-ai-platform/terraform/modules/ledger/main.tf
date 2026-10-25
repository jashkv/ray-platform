resource "aws_dynamodb_table" "ledger" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "file_uri"
  range_key    = "version_id"

  attribute {
    name = "file_uri"
    type = "S"
  }

  attribute {
    name = "version_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "lease_expiration"
    type = "N"
  }

  global_secondary_index {
    name            = "status-lease-index"
    hash_key        = "status"
    range_key       = "lease_expiration"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = var.tags
}
