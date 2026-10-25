#!/usr/bin/env python3
"""
Diagnostic utility to inspect and audit Apache Iceberg 'corporate_registry' table.
"""

import sys
import argparse
from application.src.catalog_factory import get_iceberg_catalog

def inspect_iceberg_table(catalog_type: str, warehouse_path: str, db_name: str, table_name: str):
    print("==================================================================")
    print("Apache Iceberg Lakehouse Table Inspector")
    print("==================================================================")
    print(f"Catalog Type:   {catalog_type}")
    print(f"Warehouse Path: {warehouse_path}")
    print(f"Table:          {db_name}.{table_name}")
    print("------------------------------------------------------------------")

    try:
        catalog = get_iceberg_catalog(catalog_type=catalog_type, warehouse_path=warehouse_path, database_name=db_name)
        table_identifier = f"{db_name}.{table_name}"
        table = catalog.load_table(table_identifier)
        
        current_snapshot = table.current_snapshot()
        print(f"[+] Table Loaded Successfully!")
        print(f"[+] Current Snapshot ID: {current_snapshot.snapshot_id if current_snapshot else 'None'}")
        if current_snapshot:
            print(f"[+] Snapshot Timestamp:   {current_snapshot.timestamp_ms}")
            print(f"[+] Manifest List:       {current_snapshot.manifest_list}")
        
        df = table.scan().to_arrow()
        print(f"[+] Total Committed Records: {len(df)}")
        print("\n--- First 5 Records ---")
        sample_df = df.slice(0, 5).to_pandas()
        print(sample_df[["company_id", "canonical_name", "country", "annual_revenue", "status"]])
        print("==================================================================")
    except Exception as e:
        print(f"[-] Error loading Iceberg table: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect Iceberg Table")
    parser.add_argument("--catalog-type", default="sqlite", choices=["sqlite", "glue"])
    parser.add_argument("--warehouse-path", default="/tmp/iceberg_warehouse")
    parser.add_argument("--database", default="corporate_data_db")
    parser.add_argument("--table", default="corporate_registry")
    args = parser.parse_args()

    inspect_iceberg_table(args.catalog_type, args.warehouse_path, args.database, args.table)
