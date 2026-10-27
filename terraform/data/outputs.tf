output "data_bucket_id" {
  description = "S3 data bucket ID"
  value       = module.s3_data_lakehouse.bucket_id
}

output "data_bucket_arn" {
  description = "S3 data bucket ARN"
  value       = module.s3_data_lakehouse.bucket_arn
}

output "glue_database_name" {
  description = "AWS Glue Data Catalog database name"
  value       = aws_glue_catalog_database.iceberg_db.name
}

output "glue_database_arn" {
  description = "AWS Glue Data Catalog database ARN"
  value       = aws_glue_catalog_database.iceberg_db.arn
}

output "ledger_table_name" {
  description = "DynamoDB processing ledger table name"
  value       = module.ledger.table_name
}

output "ledger_table_arn" {
  description = "DynamoDB processing ledger table ARN"
  value       = module.ledger.table_arn
}

output "ray_pipeline_role_arn" {
  description = "IRSA Role ARN to annotate on Kubernetes ServiceAccount"
  value       = module.ray_irsa.role_arn
}

output "service_account_annotation" {
  description = "The exact annotation required on Kubernetes ServiceAccount ray-pipeline-sa"
  value       = module.ray_irsa.service_account_annotation
}
