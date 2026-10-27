"""
Master Serverless Alternative Pipeline Orchestrator.
Can be executed directly via Python CLI or orchestrates stages sequentially
mimicking the AWS Step Functions State Machine workflow.
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any

from application.src.serverless.handlers import (
    handler_discovery,
    handler_validator,
    handler_resolver,
    handler_iceberg_sink,
    handler_trainer,
    handler_finalizer,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("serverless_pipeline_runner")


def run_serverless_pipeline(
    s1_path: str = "application/data/supply_chain_data_s1.csv",
    s2_path: str = "application/data/financial_data_s2.csv",
    warehouse_path: str = "/tmp/iceberg_warehouse",
    model_dir: str = "/tmp/serverless_models",
    catalog_type: str = "sqlite",
) -> Dict[str, Any]:
    """
    Executes the 6-stage Serverless pipeline matching the Step Functions State Machine:
    1. Discovery -> 2. Parallel Validation -> 3. Entity Resolution -> 4. Iceberg Sink -> 5. ML Training -> 6. Finalization
    """
    logger.info("================================================================================")
    logger.info("  STARTING AWS SERVERLESS ALTERNATIVE PIPELINE EXECUTION")
    logger.info("================================================================================")

    # Stage 1: Discovery
    logger.info("--> [Stage 1/6] Discovery & Ledger Claim...")
    discovery_res = handler_discovery({"s1_input": s1_path, "s2_input": s2_path})
    execution_id = discovery_res["execution_id"]

    # Stage 2: Schema Validation (Parallel in Step Functions, serialized in local runner)
    logger.info("--> [Stage 2/6] Validating Schemas (S1 & S2)...")
    v1_res = handler_validator({"file_path": s1_path, "source_name": "SUPPLY_CHAIN_S1"})
    v2_res = handler_validator({"file_path": s2_path, "source_name": "FINANCIAL_S2"})
    logger.info("    S1 Valid Records: %d, Malformed: %d", v1_res["valid_count"], v1_res["malformed_count"])
    logger.info("    S2 Valid Records: %d, Malformed: %d", v2_res["valid_count"], v2_res["malformed_count"])

    # Stage 3: Multi-Tier Entity Resolution
    logger.info("--> [Stage 3/6] Running Deterministic Multi-Tier Entity Resolution...")
    resolution_res = handler_resolver({"validated_datasets": [v1_res, v2_res]})
    canonical_entities = resolution_res["canonical_entities"]
    logger.info(
        "    Input: %d -> Canonical Entities: %d, Quarantined: %d",
        resolution_res["total_input_records"],
        resolution_res["canonical_count"],
        resolution_res["quarantined_count"],
    )

    # Stage 4: Apache Iceberg Transactional Table Sink
    logger.info("--> [Stage 4/6] Persisting to Apache Iceberg Table (ACID commit)...")
    iceberg_res = handler_iceberg_sink({
        "canonical_entities": canonical_entities,
        "warehouse_path": warehouse_path,
        "catalog_type": catalog_type,
        "db_name": "corporate_data_db",
        "table_name": "corporate_registry",
    })
    logger.info("    Iceberg Snapshot ID: %s", iceberg_res["snapshot_id"])

    # Stage 5: Machine Learning Training (Revenue Prediction)
    logger.info("--> [Stage 5/6] Training Distributed Gradient Boosting Regressor...")
    ml_res = handler_trainer({
        "canonical_entities": canonical_entities,
        "model_dir": model_dir,
    })
    logger.info("    Model Performance: R^2 = %.4f, RMSE = %.2f, MAE = %.2f", ml_res["r2_score"], ml_res["rmse"], ml_res["mae"])

    # Stage 6: Finalization & Audit
    logger.info("--> [Stage 6/6] Finalizing Ledger & Run Metrics...")
    final_res = handler_finalizer({
        "execution_id": execution_id,
        "canonical_count": resolution_res["canonical_count"],
        "snapshot_id": iceberg_res["snapshot_id"],
        "r2_score": ml_res["r2_score"],
    })

    logger.info("================================================================================")
    logger.info("  SERVERLESS ALTERNATIVE PIPELINE COMPLETED SUCCESSFULLY (Status: %s)", final_res["pipeline_status"])
    logger.info("================================================================================")

    return {
        "execution_id": execution_id,
        "valid_s1_records": v1_res["valid_count"],
        "valid_s2_records": v2_res["valid_count"],
        "canonical_entities": resolution_res["canonical_count"],
        "quarantined_records": resolution_res["quarantined_count"],
        "iceberg_snapshot_id": iceberg_res["snapshot_id"],
        "model_r2_score": ml_res["r2_score"],
        "status": final_res["pipeline_status"],
    }


def main():
    parser = argparse.ArgumentParser(description="Execute the Serverless Alternative Data Pipeline")
    parser.add_argument("--s1-input", default="application/data/supply_chain_data_s1.csv", help="Path to S1 CSV")
    parser.add_argument("--s2-input", default="application/data/financial_data_s2.csv", help="Path to S2 CSV")
    parser.add_argument("--warehouse", default="/tmp/iceberg_warehouse", help="Iceberg warehouse URI")
    parser.add_argument("--model-dir", default="/tmp/serverless_models", help="Model artifact directory")
    parser.add_argument("--catalog-type", default="sqlite", help="Iceberg catalog type (glue or sqlite)")

    args = parser.parse_args()
    try:
        run_serverless_pipeline(
            s1_path=args.s1_input,
            s2_path=args.s2_input,
            warehouse_path=args.warehouse,
            model_dir=args.model_dir,
            catalog_type=args.catalog_type,
        )
    except Exception as exc:
        logger.error("Pipeline failed with exception: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
