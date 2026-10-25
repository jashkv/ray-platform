module "ledger" {
  source = "../modules/ledger"

  table_name  = local.table_name
  kms_key_arn = aws_kms_key.data.arn
  tags        = var.tags
}
