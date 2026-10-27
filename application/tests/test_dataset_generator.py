"""
Unit tests for Synthetic Dataset Generator.
Verifies record counts (>= 1,000 rows each) and schema completeness.
"""

import os
import csv
import tempfile
import pytest

from application.src.generate_datasets import create_datasets

def test_dataset_generation_row_counts_and_schemas():
    with tempfile.TemporaryDirectory() as tmp_dir:
        s1_path, s2_path = create_datasets(tmp_dir, n_records=1100)

        assert os.path.exists(s1_path)
        assert os.path.exists(s2_path)

        # 1. Verify Dataset 1 (Supply Chain)
        with open(s1_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            s1_rows = list(reader)
            assert len(s1_rows) >= 1000, f"Expected >= 1000 records, got {len(s1_rows)}"
            # Required columns
            required_s1_cols = {"supplier_id", "corporate_name", "tax_identifier", "headquarters_country", "reported_revenue_usd"}
            assert required_s1_cols.issubset(set(reader.fieldnames or []))

        # 2. Verify Dataset 2 (Financial)
        with open(s2_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            s2_rows = list(reader)
            assert len(s2_rows) >= 1000, f"Expected >= 1000 records, got {len(s2_rows)}"
            required_s2_cols = {"legal_name", "registration_number", "duns_number", "country_code", "audited_annual_revenue"}
            assert required_s2_cols.issubset(set(reader.fieldnames or []))
