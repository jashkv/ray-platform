"""
Deterministic Multi-Tier Entity Resolver Actor for Ray Platform.
Replaces placeholder hash() resolution with explainable evidence-based matching.

Includes:
- Strong identifier index (Tax ID / Registration number)
- Normalized name similarity with attribute corroboration (Country + Founded Year)
- Ambiguity quarantine detection
- Provenance and match confidence tracking
- Ray custom resource annotation for worker group scheduling: {"entity_resolver_slot": 1}
"""

from typing import Dict, List, Optional, Tuple, Any
from application.src.normalizer import clean_company_name, levenshtein_ratio, generate_canonical_id
from application.src.schema_validator import CanonicalCompanyEntity

class EntityResolverEngine:
    """Core deterministic entity resolution logic (usable locally and within Ray Actor)."""

    def __init__(self, fuzzy_threshold: float = 0.88, ambiguity_threshold: float = 0.65):
        self.fuzzy_threshold = fuzzy_threshold
        self.ambiguity_threshold = ambiguity_threshold
        
        # Primary lookup indices
        self.tax_id_index: Dict[str, CanonicalCompanyEntity] = {}
        self.canonical_entities: Dict[str, CanonicalCompanyEntity] = {}
        # Country-partitioned name index: country -> list of (clean_name, entity)
        self.country_name_index: Dict[str, List[Tuple[str, CanonicalCompanyEntity]]] = {}
        
        # Ambiguous records held for review
        self.quarantine_records: List[Dict[str, Any]] = []

    def resolve_record(
        self,
        raw_name: str,
        tax_id: Optional[str],
        country: str,
        founded_year: int,
        employee_count: int,
        industry: str,
        revenue: float,
        source_dataset: str,
        source_id: str
    ) -> Tuple[CanonicalCompanyEntity, bool]:
        """
        Resolves a single input record into a canonical company entity.
        Returns: (CanonicalCompanyEntity, is_new_entity)
        """
        clean_name = clean_company_name(raw_name)
        country_norm = country.strip().upper() if country else "US"
        clean_tax_id = tax_id.strip() if tax_id and len(tax_id.strip()) > 3 else None

        # -------------------------------------------------------------
        # Tier 1: Strong Identifier Matching (Tax ID / Registration #)
        # -------------------------------------------------------------
        if clean_tax_id and clean_tax_id in self.tax_id_index:
            existing = self.tax_id_index[clean_tax_id]
            # Harmonize attributes & update provenance
            if source_dataset not in existing.sources:
                existing.sources.append(source_dataset)
            # Retain higher fidelity audited revenue if from financial source or if revenue > 0
            if any(k in source_dataset.lower() for k in ("financial", "s2")) or existing.annual_revenue == 0.0:
                if revenue > 0.0:
                    existing.annual_revenue = revenue
            return existing, False

        # -------------------------------------------------------------
        # Tier 2: Normalized Name Matching with Corroboration
        # -------------------------------------------------------------
        best_match: Optional[CanonicalCompanyEntity] = None
        best_score = 0.0
        ambiguous_candidates = []

        candidate_pool = self.country_name_index.get(country_norm, [])
        for candidate_name, candidate_entity in candidate_pool:
            score = levenshtein_ratio(clean_name, candidate_name)
            if score >= self.fuzzy_threshold:
                # Corroborate founded year within +/- 2 years
                if abs(candidate_entity.founded_year - founded_year) <= 2:
                    if score > best_score:
                        best_score = score
                        best_match = candidate_entity
            elif score >= self.ambiguity_threshold:
                ambiguous_candidates.append((candidate_entity, score))

        if best_match is not None:
            if source_dataset not in best_match.sources:
                best_match.sources.append(source_dataset)
            if any(k in source_dataset.lower() for k in ("financial", "s2")) or best_match.annual_revenue == 0.0:
                if revenue > 0.0:
                    best_match.annual_revenue = revenue
            return best_match, False

        # Check for ambiguity: High similarity without attribute corroboration
        if ambiguous_candidates and best_match is None:
            highest_ambig = max(ambiguous_candidates, key=lambda x: x[1])
            self.quarantine_records.append({
                "raw_name": raw_name,
                "clean_name": clean_name,
                "tax_id": clean_tax_id,
                "country": country_norm,
                "founded_year": founded_year,
                "closest_candidate": highest_ambig[0].company_id,
                "similarity": highest_ambig[1],
                "source": f"{source_dataset}:{source_id}",
                "reason": "SIMILARITY_ABOVE_AMBIGUITY_THRESHOLD_WITHOUT_CORROBORATION"
            })

        # -------------------------------------------------------------
        # Tier 3: Register New Canonical Entity
        # -------------------------------------------------------------
        canonical_id = generate_canonical_id(tax_id=clean_tax_id, country=country_norm, clean_name=clean_name)
        new_entity = CanonicalCompanyEntity(
            company_id=canonical_id,
            canonical_name=raw_name.strip(),
            tax_identifier=clean_tax_id,
            country=country_norm,
            founded_year=founded_year,
            employee_count=employee_count,
            industry_sector=industry,
            annual_revenue=revenue,
            sources=[source_dataset],
            match_rule="RULE_STRONG_TAX_ID" if clean_tax_id else "RULE_NEW_ENTITY",
            match_confidence=1.0 if clean_tax_id else 0.85,
            status="RESOLVED"
        )

        # Index new entity
        self.canonical_entities[canonical_id] = new_entity
        if clean_tax_id:
            self.tax_id_index[clean_tax_id] = new_entity
        if country_norm not in self.country_name_index:
            self.country_name_index[country_norm] = []
        self.country_name_index[country_norm].append((clean_name, new_entity))

        return new_entity, True

    def get_canonical_entities(self) -> List[CanonicalCompanyEntity]:
        """Return all resolved entities."""
        return list(self.canonical_entities.values())

    def get_quarantined_records(self) -> List[Dict[str, Any]]:
        """Return ambiguous/quarantined records."""
        return self.quarantine_records


# ==============================================================================
# Ray Remote Actor Wrapper
# Configured with custom resource {"entity_resolver_slot": 1} to schedule
# exclusively onto Ray Worker nodes with the designated worker pool capacity.
# ==============================================================================
try:
    import ray
    
    @ray.remote(resources={"entity_resolver_slot": 1})
    class RayEntityResolver(EntityResolverEngine):
        """Ray Actor managing stateful, centralized entity resolution."""
        pass

except ImportError:
    # Fallback for environments where ray is not installed during local standalone tests
    RayEntityResolver = EntityResolverEngine
