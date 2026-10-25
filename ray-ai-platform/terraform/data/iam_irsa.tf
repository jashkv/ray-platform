module "ray_irsa" {
  source = "../modules/irsa"

  role_name            = local.role_name
  oidc_provider_arn    = var.oidc_provider_arn
  oidc_provider_url    = var.oidc_provider_url
  namespace            = var.namespace
  service_account_name = var.service_account_name
  data_bucket_arn      = module.s3_data_lakehouse.bucket_arn
  glue_database_arn    = aws_glue_catalog_database.iceberg_db.arn
  ledger_table_arn     = module.ledger.table_arn
  kms_key_arn          = aws_kms_key.data.arn
  tags                 = var.tags
}
