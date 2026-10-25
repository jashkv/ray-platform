# ==============================================================================
# AWS Glue Data Catalog Database for Apache Iceberg Lakehouse
# ==============================================================================
resource "aws_glue_catalog_database" "iceberg_db" {
  name        = local.db_name
  description = "Glue Catalog database hosting the Apache Iceberg corporate_registry table"

  location_uri = "s3://${module.s3_data_lakehouse.bucket_id}/iceberg-warehouse/"

  tags = merge(
    var.tags,
    {
      DatabaseName = local.db_name
      CatalogType  = "ApacheIceberg"
    }
  )
}
