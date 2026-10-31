"""
Tests for Data-Agnostic Ingestion of Unforeseen Schemas and Dirty Formats.
Verifies that the pipeline ingests arbitrary CSV headers, dirty currency strings,
and unforeseen company records without raising exceptions.
"""

import os
import csv
import tempfile
import pytest

from application.src.entity_resolver import EntityResolverEngine
from application.src.ingest import ingest_dataset_file, auto_detect_columns
from application.src.schema_validator import parse_numeric_value, parse_int_value

def test_auto_detect_columns():
    # Test case 1: Supply chain variant
    headers1 = ["Vendor_Name", "Tax_Id", "Nation", "Headcount", "Turnover", "Reg_No"]
    map1 = auto_detect_columns(headers1)
    assert map1["name"] == "Vendor_Name"
    assert map1["tax_id"] == "Tax_Id"
    assert map1["country"] == "Nation"
    assert map1["employee_count"] == "Headcount"
    assert map1["revenue"] == "Turnover"

    # Test case 2: Arbitrary enterprise ledger variant
    headers2 = ["Organization", "EIN", "Creation_Year", "Staff", "Gross_Revenue", "Vertical"]
    map2 = auto_detect_columns(headers2)
    assert map2["name"] == "Organization"
    assert map2["tax_id"] == "EIN"
    assert map2["founded_year"] == "Creation_Year"
    assert map2["employee_count"] == "Staff"
    assert map2["revenue"] == "Gross_Revenue"
    assert map2["industry"] == "Vertical"

def test_parse_dirty_numeric_values():
    assert parse_numeric_value("$ 12,500,000.50") == 12500000.50
    assert parse_numeric_value("1.5M") == 1500000.0
    assert parse_numeric_value("750k") == 750000.0
    assert parse_numeric_value("2.1B") == 2100000000.0
    assert parse_numeric_value("N/A") == 0.0
    assert parse_numeric_value(None) == 0.0
    assert parse_numeric_value("") == 0.0

def test_parse_int_values():
    assert parse_int_value("150") == 150
    assert parse_int_value("1,200") == 1200
    assert parse_int_value("N/A", default=50) == 50

def test_ingest_unforeseen_csv_schema():
    """Verify that an unforeseen CSV schema with arbitrary headers is ingested cleanly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_path = os.path.join(tmp_dir, "unforeseen_partners.csv")
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Client_Entity", "EIN_Code", "Country_HQ", "Year_Est", "Team_Size", "Sector", "Annual_Sales"])
            writer.writerow(["Acme Global Robotics", "12-3456789", "US", "2010", "150", "Technology", "$ 45,000,000"])
            writer.writerow(["Bavaria Mechatronics AG", "99-8877665", "DE", "1995", "450", "Manufacturing", "120.5M"])
            writer.writerow(["Pacific Logistics Partners", "", "JP", "2018", "85", "Logistics", "18500k"])

        resolver = EntityResolverEngine()
        ingested = ingest_dataset_file(csv_path, "unforeseen_feed", resolver)

        assert ingested == 3
        canonical = resolver.get_canonical_entities()
        assert len(canonical) == 3

        # Verify attributes resolved correctly
        acme = [c for c in canonical if "acme global robotics" in c.canonical_name.lower()][0]
        assert acme.tax_identifier == "12-3456789"
        assert acme.employee_count == 150
        assert acme.annual_revenue == 45000000.0

        bavaria = [c for c in canonical if "bavaria" in c.canonical_name.lower()][0]
        assert bavaria.annual_revenue == 120500000.0
