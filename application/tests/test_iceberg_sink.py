"""
Comprehensive Apache Iceberg Transactional Integration Tests.
Verifies real PyIceberg commits, snapshot lineage, idempotency, and read-back integrity.
"""

import os
import tempfile
import pytest
from datetime import datetime, timezone
import pyarrow as pa
from pyiceberg.catalog import load_catalog

from application.src.schema_validator import CanonicalCompanyEntity
from application.src.catalog_factory import get_iceberg_catalog
from application.src.iceberg_sink import write_to_iceberg, CORPORATE_REGISTRY_ICEBERG_SCHEMA

def test_iceberg_catalog_initialization():
    with tempfile.TemporaryDirectory() as tmp_dir:
        catalog = get_iceberg_catalog(catalog_type="sqlite", warehouse_path=tmp_dir)
        assert catalog is not None
        # Verify namespace creation
        catalog.create_namespace("test_db")
        namespaces = catalog.list_namespaces()
        assert ("test_db",) in namespaces

def test_iceberg_transactional_commit_and_snapshot_lineage():
    with tempfile.TemporaryDirectory() as tmp_dir:
        entities_batch_1 = [
            CanonicalCompanyEntity(
                company_id="COMP-TEST-0001",
                canonical_name="Acme Corporation",
                tax_identifier="11-2233445",
                country="US",
                founded_year=1998,
                employee_count=150,
                industry_sector="Technology",
                annual_revenue=15000000.0,
                sources=["s1"],
                match_rule="RULE_STRONG_TAX_ID",
                match_confidence=1.0,
                status="RESOLVED"
            ),
            CanonicalCompanyEntity(
                company_id="COMP-TEST-0002",
                canonical_name="Globex Enterprises",
                tax_identifier="22-3344556",
                country="DE",
                founded_year=2004,
                employee_count=320,
                industry_sector="Manufacturing",
                annual_revenue=48000000.0,
                sources=["s1", "s2"],
                match_rule="RULE_FUZZY_CORROBORATED",
                match_confidence=0.94,
                status="RESOLVED"
            )
        ]

        # First Commit
        commit_1 = write_to_iceberg(
            entities=entities_batch_1,
            catalog_type="sqlite",
            warehouse_path=tmp_dir,
            database_name="corp_db",
            table_name="corporate_registry"
        )
        assert commit_1["status"] == "TRANSACTION_COMMITTED"
        assert commit_1["total_records"] == 2
        snapshot_id_1 = commit_1["snapshot_id"]
        assert snapshot_id_1 is not None

        # Verify readback directly from catalog table
        catalog = get_iceberg_catalog(catalog_type="sqlite", warehouse_path=tmp_dir)
        table = catalog.load_table("corp_db.corporate_registry")
        arrow_table = table.scan().to_arrow()
        assert len(arrow_table) == 2
        assert arrow_table.column("company_id").to_pylist() == ["COMP-TEST-0001", "COMP-TEST-0002"]

        # Second Commit (Idempotent Overwrite / Merge with Updated Record)
        entities_batch_2 = list(entities_batch_1)
        entities_batch_2[0].annual_revenue = 16500000.0  # Revenue update
        entities_batch_2.append(
            CanonicalCompanyEntity(
                company_id="COMP-TEST-0003",
                canonical_name="Initech LLC",
                tax_identifier="33-4455667",
                country="GB",
                founded_year=2012,
                employee_count=75,
                industry_sector="Financial Services",
                annual_revenue=9500000.0,
                sources=["s2"],
                match_rule="RULE_STRONG_TAX_ID",
                match_confidence=1.0,
                status="RESOLVED"
            )
        )

        commit_2 = write_to_iceberg(
            entities=entities_batch_2,
            catalog_type="sqlite",
            warehouse_path=tmp_dir,
            database_name="corp_db",
            table_name="corporate_registry"
        )
        assert commit_2["status"] == "TRANSACTION_COMMITTED"
        assert commit_2["total_records"] == 3
        snapshot_id_2 = commit_2["snapshot_id"]
        assert snapshot_id_2 != snapshot_id_1, "New snapshot ID must be minted upon commit"

        # Verify updated snapshot has 3 records and new revenue
        table.refresh()
        arrow_table_2 = table.scan().to_arrow()
        assert len(arrow_table_2) == 3
        company_rev_map = dict(zip(arrow_table_2.column("company_id").to_pylist(), arrow_table_2.column("annual_revenue").to_pylist()))
        assert company_rev_map["COMP-TEST-0001"] == 16500000.0
