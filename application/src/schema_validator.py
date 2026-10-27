"""
Data Schema Validation & Canonical Entity Models.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class SupplyChainInputRecord(BaseModel):
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
    company_id: str = Field(description="Deterministic canonical company ID")
    canonical_name: str
    tax_identifier: Optional[str] = None
    country: str
    founded_year: int
    employee_count: int
    industry_sector: str
    annual_revenue: float = Field(description="Harmonized ground-truth annual revenue in USD")
    sources: List[str] = Field(default_factory=list)
    match_rule: str
    match_confidence: float
    status: str = "RESOLVED"  # RESOLVED, AMBIGUOUS, QUARANTINED
