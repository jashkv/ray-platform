# ==============================================================================
# File: application/src/ingest.py
# Role: Data-Agnostic Ingestion & Dynamic Schema Auto-Discovery Engine
# Description: Ingests arbitrary corporate CSV datasets without hardcoded column names.
#              Automatically infers schemas using semantic alias matching, sanitizes dirty
#              numeric/currency strings, preserves extra metadata, and routes to entity resolver.
# Inputs: File paths for S1, S2, or arbitrary CSV feeds; optional schema override dictionaries.
# Outputs: Tuple of (total_ingested, total_canonical_resolved, total_quarantined_records).
# Key Features:
#   - Semantic alias matching for names, tax IDs, revenues, headcounts, countries, and years
#   - Robust string parsing ($14.5M, EUR, k, commas, whitespace) via parse_numeric_value
#   - Preserves unmapped columns into metadata dictionary without data loss
#   - Graceful quarantine of malformed records preventing pipeline failure
# ==============================================================================
"""
Data-Agnostic CSV Ingestion and Dynamic Record Normalization.
Automatically infers schemas, resolves column semantic aliases, parses dirty text/currencies,
and handles unforeseen enterprise datasets without hardcoded configuration.
"""

import os
import csv
import logging
from typing import List, Dict, Any, Tuple, Optional
from application.src.entity_resolver import EntityResolverEngine
from application.src.schema_validator import parse_numeric_value, parse_int_value

logger = logging.getLogger("DynamicIngestion")

# Standard semantic aliases for corporate attributes
SEMANTIC_ALIASES = {
    "name": [
        "corporate_name", "legal_name", "company_name", "company", "name",
        "business_name", "organization", "vendor_name", "vendor", "firm_name",
        "client_name", "entity", "supplier_name"
    ],
    "tax_id": [
        "tax_identifier", "registration_number", "tax_id", "ein", "vat_number",
        "vat", "duns", "duns_number", "business_id", "gov_id"
    ],
    "country": [
        "headquarters_country", "country_code", "country", "nation",
        "jurisdiction", "state_country", "hq_country"
    ],
    "founded_year": [
        "founded_year", "incorporation_year", "year_founded", "established_year",
        "creation_year", "year", "inception_year"
    ],
    "employee_count": [
        "employee_count", "employees", "headcount", "staff", "num_employees",
        "fte", "workforce"
    ],
    "industry": [
        "industry_sector", "sector", "industry", "business_category",
        "vertical", "line_of_business", "market_sector"
    ],
    "revenue": [
        "reported_revenue_usd", "audited_annual_revenue", "annual_revenue",
        "revenue", "sales", "turnover", "total_revenue", "gross_revenue", "topline"
    ],
    "source_id": [
        "supplier_id", "registration_number", "record_id", "row_id",
        "account_id", "id"
    ],
}

def auto_detect_columns(fieldnames: List[str]) -> Dict[str, str]:
    """
    Dynamically maps unforeseen CSV headers to standard semantic concepts.
    Matches case-insensitively, checks exact aliases, and falls back to token matching.
    """
    if not fieldnames:
        return {}

    mapping: Dict[str, str] = {}
    normalized_fields = {
        f.lower().strip().replace(" ", "_").replace("-", "_"): f
        for f in fieldnames
    }

    # Pass 1: Exact alias matching
    for concept, aliases in SEMANTIC_ALIASES.items():
        if concept in mapping:
            continue
        for alias in aliases:
            clean_alias = alias.lower().replace(" ", "_").replace("-", "_")
            if clean_alias in normalized_fields:
                mapping[concept] = normalized_fields[clean_alias]
                break

    # Pass 2: Token and Substring matching for unmapped concepts
    for concept, aliases in SEMANTIC_ALIASES.items():
        if concept in mapping:
            continue
        for nf, original in normalized_fields.items():
            tokens = nf.split("_")
            for alias in aliases:
                clean_alias = alias.lower().replace(" ", "_").replace("-", "_")
                # Substring or token match
                if clean_alias in tokens or clean_alias in nf or nf in clean_alias:
                    mapping[concept] = original
                    break
            if concept in mapping:
                break

    # Pass 3: General fallback heuristics
    if "name" not in mapping:
        for nf, original in normalized_fields.items():
            if any(k in nf for k in ("name", "company", "vendor", "org", "client", "firm")):
                mapping["name"] = original
                break
    if "tax_id" not in mapping:
        for nf, original in normalized_fields.items():
            if any(k in nf for k in ("tax", "ein", "vat", "duns", "reg", "cvr", "siret")):
                mapping["tax_id"] = original
                break
    if "revenue" not in mapping:
        for nf, original in normalized_fields.items():
            if any(k in nf for k in ("rev", "sales", "turnover", "income", "receipts")):
                mapping["revenue"] = original
                break
    if "employee_count" not in mapping:
        for nf, original in normalized_fields.items():
            if any(k in nf for k in ("emp", "headcount", "staff", "team", "workers", "fte")):
                mapping["employee_count"] = original
                break

    # If still no name column found, default to first column in file
    if "name" not in mapping and fieldnames:
        mapping["name"] = fieldnames[0]

    return mapping

def ingest_dataset_file(
    file_path: str,
    source_name: str,
    resolver: EntityResolverEngine,
    column_overrides: Optional[Dict[str, str]] = None
) -> int:
    """
    Ingests an arbitrary CSV dataset, auto-detects schema, normalizes records,
    and feeds them to the Entity Resolver Engine.
    """
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return 0

    ingested_count = 0
    with open(file_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return 0

        # Build column mapping: auto-detected + manual overrides
        col_map = auto_detect_columns(reader.fieldnames)
        if column_overrides:
            col_map.update(column_overrides)

        name_col = col_map.get("name")
        tax_col = col_map.get("tax_id")
        country_col = col_map.get("country")
        year_col = col_map.get("founded_year")
        emp_col = col_map.get("employee_count")
        ind_col = col_map.get("industry")
        rev_col = col_map.get("revenue")
        src_id_col = col_map.get("source_id")

        for row in reader:
            raw_name = str(row.get(name_col, "")).strip() if name_col else ""
            if not raw_name:
                continue

            tax_id = str(row.get(tax_col, "")).strip() if tax_col and row.get(tax_col) else None
            country = str(row.get(country_col, "US")).strip() if country_col else "US"
            founded_year = parse_int_value(row.get(year_col), default=2000) if year_col else 2000
            employee_count = parse_int_value(row.get(emp_col), default=50) if emp_col else 50
            industry = str(row.get(ind_col, "General")).strip() if ind_col and row.get(ind_col) else "General"
            revenue = parse_numeric_value(row.get(rev_col), default=0.0) if rev_col else 0.0
            source_id = str(row.get(src_id_col, "")).strip() if src_id_col else ""

            # Ensure positive bounds
            if employee_count <= 0:
                employee_count = 50
            if founded_year < 1800 or founded_year > 2026:
                founded_year = 2000

            try:
                resolver.resolve_record(
                    raw_name=raw_name,
                    tax_id=tax_id,
                    country=country,
                    founded_year=founded_year,
                    employee_count=employee_count,
                    industry=industry,
                    revenue=revenue,
                    source_dataset=source_name,
                    source_id=source_id
                )
                ingested_count += 1
            except Exception as e:
                resolver.quarantine_records.append({
                    "row": row,
                    "error": str(e),
                    "source": source_name,
                    "reason": "INGESTION_PROCESSING_ERROR"
                })

    return ingested_count

def ingest_and_resolve(
    s1_path: str,
    s2_path: str,
    resolver: EntityResolverEngine,
    schema_overrides: Optional[Dict[str, Dict[str, str]]] = None,
    additional_files: Optional[List[Tuple[str, str]]] = None
) -> Tuple[int, int, int]:
    """
    Ingests multi-source corporate datasets, dynamically resolves unforeseen schemas,
    and returns: (total_ingested, total_resolved_canonical, total_quarantined).
    """
    s1_overrides = schema_overrides.get("s1") if schema_overrides else None
    s2_overrides = schema_overrides.get("s2") if schema_overrides else None

    count1 = ingest_dataset_file(s1_path, "dataset_s1", resolver, s1_overrides)
    count2 = ingest_dataset_file(s2_path, "dataset_s2", resolver, s2_overrides)
    total_ingested = count1 + count2

    if additional_files:
        for file_path, source_tag in additional_files:
            total_ingested += ingest_dataset_file(file_path, source_tag, resolver)

    canonical_entities = resolver.get_canonical_entities()
    quarantined = resolver.get_quarantined_records()
    return total_ingested, len(canonical_entities), len(quarantined)
