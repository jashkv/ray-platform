# ==============================================================================
# File: application/src/schema_validator.py
# Role: Data Schema Validation & Canonical Entity Models
# Description: Defines Pydantic data models for structural input validation and canonical
#              Lakehouse storage. Provides robust string sanitization utilities for dirty numbers.
# Inputs: Raw dictionaries or strings representing corporate attributes and financial metrics.
# Outputs: Validated SupplyChainInputRecord, FinancialInputRecord, and CanonicalCompanyEntity instances.
# Key Features:
#   - parse_numeric_value(): Converts dirty strings ('$ 14.5M', 'EUR', 'k', 'N/A') to floats
#   - parse_int_value(): Safely extracts integers from arbitrary strings with fallbacks
#   - CanonicalCompanyEntity: Standardized schema with metadata dictionary for Lakehouse storage
# ==============================================================================
"""
Data Schema Validation & Canonical Entity Models for Ray AI Platform.
Provides robust parsing of unforeseen data, dirty numeric strings, and standardized lakehouse entities.
"""

import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

def parse_numeric_value(val: Any, default: float = 0.0) -> float:
    """
    Safely parse arbitrary numeric strings, handling currency symbols, commas,
    whitespace, and standard magnitude suffixes (k, M, B).
    
    Examples:
      "$ 12,500,000" -> 12500000.0
      "1.2M"         -> 1200000.0
      "500k"         -> 500000.0
      "2.5B"         -> 2500000000.0
      "N/A" / ""     -> 0.0
    """
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)

    s = str(val).strip()
    if not s or s.lower() in ("n/a", "na", "null", "none", "nan", "-"):
        return default

    # Remove currency symbols and formatting characters
    cleaned = re.sub(r"[^\d.\-+kKmMbB]", "", s)
    if not cleaned:
        return default

    multiplier = 1.0
    suffix = cleaned[-1].upper()
    if suffix == "K":
        multiplier = 1e3
        cleaned = cleaned[:-1]
    elif suffix == "M":
        multiplier = 1e6
        cleaned = cleaned[:-1]
    elif suffix == "B":
        multiplier = 1e9
        cleaned = cleaned[:-1]

    try:
        return float(cleaned) * multiplier
    except (ValueError, TypeError):
        return default

def parse_int_value(val: Any, default: int = 0) -> int:
    """Safely parse integer fields from arbitrary strings."""
    if val is None:
        return default
    if isinstance(val, int):
        return val
    try:
        float_val = parse_numeric_value(val, default=float(default))
        return int(float_val)
    except (ValueError, TypeError):
        return default

class SupplyChainInputRecord(BaseModel):
    """Backward-compatible model for standard supply chain feeds."""
    supplier_id: str
    corporate_name: str
    tax_identifier: Optional[str] = None
    headquarters_country: str = "US"
    founded_year: int
    employee_count: int
    industry_sector: str
    spend_volume_usd: Optional[float] = 0.0
    risk_score: Optional[float] = 0.0
    reported_revenue_usd: float

    @field_validator("employee_count", "founded_year")
    @classmethod
    def check_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"Value must be positive, got {v}")
        return v

class FinancialInputRecord(BaseModel):
    """Backward-compatible model for standard financial registry feeds."""
    registration_number: Optional[str] = None
    legal_name: str
    duns_number: Optional[str] = None
    country_code: str = "US"
    incorporation_year: int
    employee_count: int
    industry_sector: str
    total_assets_usd: Optional[float] = 0.0
    operating_margin_pct: Optional[float] = 0.0
    credit_rating: Optional[str] = "BBB"
    fiscal_year: int = 2024
    audited_annual_revenue: float

class CanonicalCompanyEntity(BaseModel):
    """Standardized entity schema committed transactionally to Apache Iceberg."""
    company_id: str = Field(description="Deterministic canonical company ID")
    canonical_name: str
    tax_identifier: Optional[str] = None
    country: str = "US"
    founded_year: int = 2000
    employee_count: int = 50
    industry_sector: str = "General"
    annual_revenue: float = Field(description="Harmonized ground-truth annual revenue in USD")
    sources: List[str] = Field(default_factory=list)
    match_rule: str = "INITIAL_INGEST"
    match_confidence: float = 1.0
    status: str = "RESOLVED"  # RESOLVED, AMBIGUOUS, QUARANTINED
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary unmapped attributes")
