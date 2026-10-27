"""
Unit tests for Deterministic Entity Resolver Engine.
Tests exact ID matching, fuzzy name matching, corroboration, ambiguity quarantine, and canonical ID generation.
"""

import pytest
from application.src.entity_resolver import EntityResolverEngine
from application.src.normalizer import clean_company_name, generate_canonical_id, levenshtein_ratio

def test_clean_company_name():
    assert clean_company_name("Acme Corporation, Inc.") == "acme"
    assert clean_company_name("Globex   Technologies LLC") == "globex technologies"
    assert clean_company_name("Initech Limited Liability Company") == "initech"
    assert clean_company_name("Vandelay Industries Ltd.") == "vandelay industries"

def test_levenshtein_ratio():
    assert levenshtein_ratio("acme", "acme") == 1.0
    assert levenshtein_ratio("acme corp", "acme crop") >= 0.75
    assert levenshtein_ratio("acme", "zyxwv") <= 0.2

def test_canonical_id_stability():
    id1 = generate_canonical_id(tax_id="12-3456789")
    id2 = generate_canonical_id(tax_id="12-3456789")
    assert id1 == id2
    assert id1.startswith("COMP-")

def test_strong_tax_id_matching():
    resolver = EntityResolverEngine()
    ent1, is_new1 = resolver.resolve_record(
        raw_name="Acme Corp.",
        tax_id="99-8887777",
        country="US",
        founded_year=1995,
        employee_count=100,
        industry="Technology",
        revenue=10000000.0,
        source_dataset="s1",
        source_id="SUP-01"
    )
    assert is_new1 is True

    ent2, is_new2 = resolver.resolve_record(
        raw_name="Acme Corporation International LLC",
        tax_id="99-8887777",
        country="US",
        founded_year=1995,
        employee_count=120,
        industry="Technology",
        revenue=12000000.0,
        source_dataset="s2",
        source_id="FIN-01"
    )
    assert is_new2 is False
    assert ent1.company_id == ent2.company_id
    assert "s1" in ent2.sources
    assert "s2" in ent2.sources
    assert ent2.annual_revenue == 12000000.0  # Financial source audited revenue updated

def test_fuzzy_name_matching_with_corroboration():
    resolver = EntityResolverEngine(fuzzy_threshold=0.85)
    ent1, is_new1 = resolver.resolve_record(
        raw_name="Horizon Technologies Inc",
        tax_id=None,
        country="DE",
        founded_year=2005,
        employee_count=200,
        industry="Manufacturing",
        revenue=25000000.0,
        source_dataset="s1",
        source_id="SUP-02"
    )
    assert is_new1 is True

    # Same entity with slight typo and different legal suffix
    ent2, is_new2 = resolver.resolve_record(
        raw_name="Horizon Technologes GmbH",
        tax_id=None,
        country="DE",
        founded_year=2005,
        employee_count=200,
        industry="Manufacturing",
        revenue=26000000.0,
        source_dataset="s2",
        source_id="FIN-02"
    )
    assert is_new2 is False
    assert ent1.company_id == ent2.company_id

def test_ambiguity_quarantine_differing_country():
    resolver = EntityResolverEngine(fuzzy_threshold=0.90, ambiguity_threshold=0.60)
    # Entity in US
    resolver.resolve_record(
        raw_name="Zenith Innovations LLC",
        tax_id=None,
        country="US",
        founded_year=2010,
        employee_count=50,
        industry="Healthcare",
        revenue=5000000.0,
        source_dataset="s1",
        source_id="SUP-03"
    )

    # Identical name in JP should NOT be blindly merged
    ent_jp, is_new_jp = resolver.resolve_record(
        raw_name="Zenith Innovations Ltd",
        tax_id=None,
        country="JP",
        founded_year=2010,
        employee_count=50,
        industry="Healthcare",
        revenue=5000000.0,
        source_dataset="s2",
        source_id="FIN-03"
    )
    assert is_new_jp is True
    # Different countries receive separate canonical IDs
    assert resolver.canonical_entities[ent_jp.company_id].country == "JP"
