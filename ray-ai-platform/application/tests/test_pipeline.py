"""
Integration test for full end-to-end pipeline execution.
Verifies ingestion, entity resolution, Iceberg commit, and ML revenue prediction.
"""

import os
import json
import tempfile
import pytest

from application.src.generate_datasets import create_datasets
from application.src.ray_pipeline import run_pipeline

def test_full_pipeline_execution():
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Generate test datasets (100 records each for fast test run)
        data_dir = os.path.join(tmp_dir, "data")
        s1_path, s2_path = create_datasets(data_dir, n_records=150)

        model_dir = os.path.join(tmp_dir, "models")
        warehouse_dir = os.path.join(tmp_dir, "warehouse")

        # 2. Execute pipeline
        summary = run_pipeline(
            s1_path=s1_path,
            s2_path=s2_path,
            output_dir=model_dir,
            iceberg_catalog_type="sqlite",
            warehouse_path=warehouse_dir
        )

        # 3. Assertions
        assert summary["status"] == "SUCCESS"
        assert summary["ingestion"]["total_records_ingested"] >= 250
        assert summary["ingestion"]["canonical_companies_resolved"] > 100

        # Iceberg commit verification
        assert summary["iceberg"]["status"] == "TRANSACTION_COMMITTED"
        assert summary["iceberg"]["total_records"] == summary["ingestion"]["canonical_companies_resolved"]
        assert summary["iceberg"]["snapshot_id"] is not None

        # ML Model metrics verification
        metrics = summary["model_training"]["evaluation_metrics"]
        assert metrics["test_mae_usd"] > 0.0
        assert metrics["test_rmse_usd"] > 0.0
        assert metrics["test_r2_score"] > 0.40, f"Expected R2 > 0.40, got {metrics['test_r2_score']}"

        # Verify artifacts written to disk
        assert os.path.exists(os.path.join(model_dir, "metrics.json"))
        model_exists = (
            os.path.exists(os.path.join(model_dir, "revenue_model.joblib")) or
            os.path.exists(os.path.join(model_dir, "revenue_model.pkl"))
        )
        assert model_exists, "Model artifact file missing from model directory"
