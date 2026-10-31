#!/usr/bin/env python3
# ==============================================================================
# File: application/src/ray_pipeline.py
# Role: Master Distributed Ray Data & Machine Learning Pipeline Entrypoint
# Description: Central orchestrator executing the 4-phase end-to-end distributed pipeline:
#              1. Data-Agnostic CSV Ingestion & Schema Auto-Discovery
#              2. Deterministic Multi-Tier Entity Resolution (EntityResolver Actor)
#              3. Transactional Apache Iceberg Table Persistence (corporate_registry)
#              4. Econometric Revenue Prediction Model Training & Evaluation (Ray Train)
# Inputs: CLI arguments (--s1-input, --s2-input, --catalog-type, --warehouse-path, --output-model-dir).
# Outputs: JSON execution summary with ingestion counts, Iceberg commit snapshot, and ML evaluation metrics.
# Key Features: Local simulation and AWS cloud execution, structured logging, failure isolation.
# ==============================================================================
"""
Ray AI Pipeline Entrypoint — Distributed AI Foundation.
Orchestrates:
1. Distributed CSV Ingestion
2. Deterministic Multi-Tier Entity Resolution (EntityResolver Actor)
3. Transactional Apache Iceberg Persistence (corporate_registry)
4. Revenue Prediction Machine Learning (Ray Train / XGBoost)
5. Comprehensive Status & Metric Reporting
"""

import os
import sys
import argparse
import json
import logging
from typing import Dict, Any

from application.src.entity_resolver import EntityResolverEngine
from application.src.ingest import ingest_and_resolve
from application.src.train_model import train_and_evaluate_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("RayPipeline")

def run_pipeline(
    s1_path: str,
    s2_path: str,
    output_dir: str = "application/models",
    iceberg_catalog_type: str = "sqlite",
    iceberg_warehouse: str = "/tmp/iceberg_warehouse",
    warehouse_path: str = None
) -> Dict[str, Any]:
    """Execute end-to-end data processing, entity resolution, and ML training."""
    warehouse = warehouse_path if warehouse_path is not None else iceberg_warehouse
    logger.info("==================================================================")
    logger.info("Starting Distributed Ray Data & ML Pipeline")
    logger.info("==================================================================")
    logger.info(f"Input S1: {s1_path}")
    logger.info(f"Input S2: {s2_path}")
    logger.info(f"Iceberg Catalog: {iceberg_catalog_type} at {warehouse}")

    # Step 1: Initialize Entity Resolver
    logger.info("[Step 1/4] Initializing Deterministic EntityResolver Engine...")
    resolver = EntityResolverEngine(fuzzy_threshold=0.88, ambiguity_threshold=0.65)

    # Step 2: Ingest & Resolve
    logger.info("[Step 2/4] Ingesting CSV datasets and performing entity resolution...")
    total_ingested, total_canonical, total_quarantined = ingest_and_resolve(
        s1_path=s1_path,
        s2_path=s2_path,
        resolver=resolver
    )
    logger.info(f"[+] Total Ingested Records: {total_ingested}")
    logger.info(f"[+] Canonical Unique Companies: {total_canonical}")
    logger.info(f"[+] Ambiguous Quarantined Records: {total_quarantined}")

    canonical_entities = resolver.get_canonical_entities()

    # Step 3: Apache Iceberg Transactional Upsert
    logger.info("[Step 3/4] Persisting harmonized entities to Apache Iceberg table 'corporate_registry'...")
    from application.src.iceberg_sink import write_to_iceberg
    iceberg_commit_info = write_to_iceberg(
        entities=canonical_entities,
        catalog_type=iceberg_catalog_type,
        warehouse_path=warehouse
    )
    logger.info(f"[+] Iceberg Commit Verified: Snapshot ID {iceberg_commit_info.get('snapshot_id')} with {iceberg_commit_info.get('total_records')} records")

    # Step 4: Machine Learning Model Training
    logger.info("[Step 4/4] Training and evaluating revenue prediction model...")
    training_results = train_and_evaluate_model(
        entities=canonical_entities,
        output_model_dir=output_dir
    )
    metrics = training_results["metrics"]["evaluation_metrics"]
    logger.info(f"[+] Model Evaluation Complete:")
    logger.info(f"    - Test MAE:  ${metrics['test_mae_usd']:,.2f}")
    logger.info(f"    - Test RMSE: ${metrics['test_rmse_usd']:,.2f}")
    logger.info(f"    - Test R2:   {metrics['test_r2_score']:.4f}")

    summary = {
        "status": "SUCCESS",
        "ingestion": {
            "total_records_ingested": total_ingested,
            "canonical_companies_resolved": total_canonical,
            "quarantined_records": total_quarantined
        },
        "iceberg": iceberg_commit_info,
        "model_training": training_results["metrics"]
    }

    logger.info("==================================================================")
    logger.info("Pipeline Finished Successfully!")
    logger.info("==================================================================")
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ray AI Platform Data Pipeline")
    parser.add_argument("--s1-input", default="application/data/supply_chain_data_s1.csv", help="Path to S1 CSV")
    parser.add_argument("--s2-input", default="application/data/financial_data_s2.csv", help="Path to S2 CSV")
    parser.add_argument("--output-model-dir", default="application/models", help="Model artifact directory")
    parser.add_argument("--catalog-type", default="sqlite", choices=["sqlite", "glue", "rest"], help="Iceberg catalog type")
    parser.add_argument("--warehouse-path", default="/tmp/iceberg_warehouse", help="Iceberg warehouse URI")

    args = parser.parse_args()
    summary = run_pipeline(
        s1_path=args.s1_input,
        s2_path=args.s2_input,
        output_dir=args.output_model_dir,
        iceberg_catalog_type=args.catalog_type,
        warehouse_path=args.warehouse_path
    )
    print(json.dumps(summary, indent=2))
