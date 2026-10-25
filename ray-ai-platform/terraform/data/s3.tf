module "s3_data_lakehouse" {
  source = "../modules/s3_iceberg"

  bucket_name = local.bucket_name
  kms_key_arn = aws_kms_key.data.arn
  environment = var.environment
  tags        = var.tags
}

# Standard Lakehouse Prefixes
resource "aws_s3_object" "prefix_incoming" {
  bucket  = module.s3_data_lakehouse.bucket_id
  key     = "incoming/"
  content = ""
}

resource "aws_s3_object" "prefix_manifests" {
  bucket  = module.s3_data_lakehouse.bucket_id
  key     = "manifests/"
  content = ""
}

resource "aws_s3_object" "prefix_quarantine" {
  bucket  = module.s3_data_lakehouse.bucket_id
  key     = "quarantine/"
  content = ""
}

resource "aws_s3_object" "prefix_iceberg_warehouse" {
  bucket  = module.s3_data_lakehouse.bucket_id
  key     = "iceberg-warehouse/"
  content = ""
}

resource "aws_s3_object" "prefix_models" {
  bucket  = module.s3_data_lakehouse.bucket_id
  key     = "models/"
  content = ""
}
