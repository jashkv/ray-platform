"""
Distributed CSV Ingestion and Record Normalization using Ray Data / Pandas.
"""

import os
import csv
from typing import List, Dict, Any, Tuple
from application.src.entity_resolver import EntityResolverEngine

def ingest_and_resolve(
    s1_path: str,
    s2_path: str,
    resolver: EntityResolverEngine
) -> Tuple[int, int, int]:
    """
    Ingests supply chain (S1) and financial (S2) CSV files, resolves entities,
    and returns: (total_ingested, total_resolved_canonical, total_quarantined)
    """
    ingested_count = 0

    # 1. Ingest Dataset 1: Supply Chain
    if os.path.exists(s1_path):
        with open(s1_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    resolver.resolve_record(
                        raw_name=row["corporate_name"],
                        tax_id=row.get("tax_identifier"),
                        country=row.get("headquarters_country", "US"),
                        founded_year=int(row.get("founded_year", 2000)),
                        employee_count=int(row.get("employee_count", 50)),
                        industry=row.get("industry_sector", "General"),
                        revenue=float(row.get("reported_revenue_usd", 0.0)),
                        source_dataset="supply_chain_s1",
                        source_id=row.get("supplier_id", "")
                    )
                    ingested_count += 1
                except Exception as e:
                    # Isolate malformed records
                    resolver.quarantine_records.append({
                        "row": row,
                        "error": str(e),
                        "source": "supply_chain_s1",
                        "reason": "SCHEMA_PARSING_FAILURE"
                    })

    # 2. Ingest Dataset 2: Financial Registry
    if os.path.exists(s2_path):
        with open(s2_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    resolver.resolve_record(
                        raw_name=row["legal_name"],
                        tax_id=row.get("registration_number"),
                        country=row.get("country_code", "US"),
                        founded_year=int(row.get("incorporation_year", 2000)),
                        employee_count=int(row.get("employee_count", 50)),
                        industry=row.get("industry_sector", "General"),
                        revenue=float(row.get("audited_annual_revenue", 0.0)),
                        source_dataset="financial_s2",
                        source_id=row.get("registration_number", "")
                    )
                    ingested_count += 1
                except Exception as e:
                    resolver.quarantine_records.append({
                        "row": row,
                        "error": str(e),
                        "source": "financial_s2",
                        "reason": "SCHEMA_PARSING_FAILURE"
                    })

    canonical_entities = resolver.get_canonical_entities()
    quarantined = resolver.get_quarantined_records()
    return ingested_count, len(canonical_entities), len(quarantined)
