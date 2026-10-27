"""
Apache Iceberg Catalog Factory.
Supports AWS Glue Data Catalog (Cloud Production) and SQL/SQLite Catalog (Local Testing).
"""

import os
from typing import Dict, Any
from pyiceberg.catalog import load_catalog, Catalog

def get_iceberg_catalog(
    catalog_type: str = "sqlite",
    warehouse_path: str = "/tmp/iceberg_warehouse",
    database_name: str = "corporate_data_db"
) -> Catalog:
    """
    Initializes and returns an Apache Iceberg Catalog instance.
    - 'glue': AWS Glue Data Catalog with S3 storage.
    - 'sqlite': Pure-python local SQLite catalog for deterministic testing.
    """
    if catalog_type.lower() == "glue":
        # Cloud Production Catalog (AWS Glue)
        catalog_properties: Dict[str, str] = {
            "type": "glue",
            "s3.endpoint": os.environ.get("AWS_S3_ENDPOINT", ""),
            "warehouse": warehouse_path,
        }
        # Clean empty properties
        props = {k: v for k, v in catalog_properties.items() if v}
        return load_catalog("glue_catalog", **props)

    elif catalog_type.lower() in ("sqlite", "sql"):
        # Local Deterministic SQL Catalog
        os.makedirs(warehouse_path, exist_ok=True)
        db_path = os.path.join(warehouse_path, "iceberg_catalog.db")
        props = {
            "type": "sql",
            "uri": f"sqlite:///{db_path}",
            "warehouse": f"file://{warehouse_path}",
        }
        return load_catalog("local_catalog", **props)

    else:
        raise ValueError(f"Unsupported Iceberg catalog type: {catalog_type}. Use 'glue' or 'sqlite'.")
