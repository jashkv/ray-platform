"""
Unit & Integration Tests for the Serverless Alternative Pipeline Handlers.
Validates:
1. Handler Discovery & SHA256 Lease Hash
2. Dynamic Schema Validation & Malformed Row Isolation
3. Deterministic Entity Resolution & Quarantine Isolation
4. Apache Iceberg Transactional Sink Commit
5. Revenue Prediction Model Training (assert R2 >= 0.85)
6. End-to-End Serverless Pipeline Runner Execution
"""

import os
import shutil
import tempfile
from pathlib import Path
import pytest

from application.src.serverless.handlers import (
    handler_discovery,
    handler_validator,
    handler_resolver,
    handler_iceberg_sink,
    handler_trainer,
    handler_finalizer,
)
from application.src.serverless.serverless_pipeline import run_serverless_pipeline


@pytest.fixture(scope="module")
def sample_csv_paths():
    """Verify input test data paths dynamically."""
    base_dir = Path(__file__).resolve().parent.parent / "data"
    s1 = str(base_dir / "supply_chain_data_s1.csv")
    s2 = str(base_dir / "financial_data_s2.csv")
    if not os.path.exists(s1):
        s1 = "application/data/supply_chain_data_s1.csv"
        s2 = "application/data/financial_data_s2.csv"
    assert os.path.exists(s1), f"Missing test dataset {s1}"
    assert os.path.exists(s2), f"Missing test dataset {s2}"
    return s1, s2


@pytest.fixture
def temp_dirs():
    """Create isolated temporary directories for Iceberg and model storage."""
    wh_dir = tempfile.mkdtemp(prefix="test_wh_")
    mod_dir = tempfile.mkdtemp(prefix="test_mod_")
    yield wh_dir, mod_dir
    shutil.rmtree(wh_dir, ignore_errors=True)
    shutil.rmtree(mod_dir, ignore_errors=True)


def test_handler_discovery(sample_csv_paths):
    """Verify discovery handler generates idempotent execution ID."""
    s1, s2 = sample_csv_paths
    res = handler_discovery({"s1_input": s1, "s2_input": s2})
    assert res["statusCode"] == 200
    assert res["execution_id"].startswith("sfn-run-")
    assert len(res["run_hash"]) == 16


def test_handler_validator_dynamic_schema(sample_csv_paths):
    """Verify validator normalizes varied column schemas and isolates malformed rows."""
    s1, s2 = sample_csv_paths
    v1 = handler_validator({"file_path": s1, "source_name": "S1"})
    assert v1["valid_count"] == 1200
    assert v1["malformed_count"] == 0
    assert "company_name" in v1["records"][0]
    assert "annual_revenue" in v1["records"][0]

    v2 = handler_validator({"file_path": s2, "source_name": "S2"})
    assert v2["valid_count"] == 1200
    assert v2["malformed_count"] == 0
    assert "company_name" in v2["records"][0]


def test_handler_resolver_multi_tier(sample_csv_paths):
    """Verify entity resolver deduplicates cross-source entities and isolates ambiguities."""
    s1, s2 = sample_csv_paths
    v1 = handler_validator({"file_path": s1, "source_name": "S1"})
    v2 = handler_validator({"file_path": s2, "source_name": "S2"})

    res = handler_resolver({"validated_datasets": [v1, v2]})
    assert res["total_input_records"] == 2400
    assert res["canonical_count"] > 1000
    assert res["quarantined_count"] > 0
    assert len(res["canonical_entities"]) == res["canonical_count"]


def test_handler_iceberg_and_training(sample_csv_paths, temp_dirs):
    """Verify transactional commit to Iceberg and ML model training."""
    s1, s2 = sample_csv_paths
    wh_dir, mod_dir = temp_dirs

    v1 = handler_validator({"file_path": s1, "source_name": "S1"})
    v2 = handler_validator({"file_path": s2, "source_name": "S2"})
    res = handler_resolver({"validated_datasets": [v1, v2]})

    # Iceberg Sink
    ice_res = handler_iceberg_sink({
        "canonical_entities": res["canonical_entities"],
        "warehouse_path": wh_dir,
        "catalog_type": "sqlite",
        "db_name": "corporate_data_db",
        "table_name": "corporate_registry",
    })
    assert ice_res["statusCode"] == 200
    assert ice_res["status"] == "COMMITTED"
    assert int(ice_res["snapshot_id"]) > 0

    # Model Training
    ml_res = handler_trainer({
        "canonical_entities": res["canonical_entities"],
        "model_dir": mod_dir,
    })
    assert ml_res["statusCode"] == 200
    assert ml_res["r2_score"] >= 0.85
    assert os.path.exists(os.path.join(mod_dir, "metrics.json"))


def test_end_to_end_serverless_pipeline(sample_csv_paths, temp_dirs):
    """Verify entire Serverless Alternative pipeline runner runs to completion."""
    s1, s2 = sample_csv_paths
    wh_dir, mod_dir = temp_dirs

    summary = run_serverless_pipeline(
        s1_path=s1,
        s2_path=s2,
        warehouse_path=wh_dir,
        model_dir=mod_dir,
        catalog_type="sqlite",
    )

    assert summary["status"] == "COMPLETED"
    assert summary["valid_s1_records"] == 1200
    assert summary["valid_s2_records"] == 1200
    assert summary["canonical_entities"] == 1557
    assert summary["quarantined_records"] == 711
    assert summary["model_r2_score"] >= 0.85
