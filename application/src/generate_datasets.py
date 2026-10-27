#!/usr/bin/env python3
"""
Synthetic Corporate Dataset Generator for Ray AI Platform.
Generates two reproducible CSV datasets (>= 1,000 records each):
1. supply_chain_data_s1.csv
2. financial_data_s2.csv

Includes realistic name noise, corporate entity overlap, disambiguating identifiers,
and correlated financial features for machine learning revenue regression.
"""

import os
import random
import csv
from typing import List, Dict, Tuple

# Fixed seed for 100% deterministic reproducibility
RANDOM_SEED = 42

INDUSTRIES = [
    "Technology",
    "Manufacturing",
    "Healthcare",
    "Financial Services",
    "Retail",
    "Energy",
    "Telecommunications",
    "Logistics",
]

COUNTRIES = ["US", "DE", "GB", "FR", "JP", "CA", "AU", "NL"]

LEGAL_SUFFIXES_S1 = ["Corp.", "Inc.", "LLC", "Ltd.", "Co.", "Holdings", "Group"]
LEGAL_SUFFIXES_S2 = ["Corporation", "Incorporated", "Limited Liability Company", "Limited", "Company", "Holdings Inc.", "Group PLC"]

COMPANY_ROOTS = [
    "Apex", "Beacon", "Crest", "Dynasty", "Echo", "Falcon", "Genesis", "Horizon",
    "Infinity", "Jupiter", "Keystone", "Lumina", "Matrix", "Nexus", "Omega", "Pinnacle",
    "Quantum", "Radiant", "Summit", "Titan", "Unity", "Vanguard", "Zenith", "Acro",
    "BlueSky", "Cyberdyne", "Delta", "Eclipse", "Fusion", "Global", "Helios", "IronClad",
    "JetStream", "Krypton", "Logic", "Meta", "Nova", "Orbit", "Pulse", "Quasar",
    "Redwood", "Sierra", "Terra", "Ultra", "Vertex", "Wave", "Xcel", "Yield",
    "AeroTech", "BioHealth", "CloudNet", "DataCore", "EcoPower", "FutureTech", "GreenEnergy"
]

COMPANY_MODIFIERS = [
    "Solutions", "Technologies", "Systems", "Enterprises", "Industries", "Logistics",
    "Networks", "Dynamics", "Innovations", "Ventures", "Digital", "Robotics", "Analytics"
]

def generate_base_entities(n_entities: int = 1500) -> List[Dict]:
    """Generate ground-truth company entities with deterministic attributes."""
    random.seed(RANDOM_SEED)
    entities = []
    
    for i in range(1, n_entities + 1):
        root = random.choice(COMPANY_ROOTS)
        mod = random.choice(COMPANY_MODIFIERS)
        base_name = f"{root} {mod} {i}"
        country = random.choice(COUNTRIES)
        founded_year = random.randint(1975, 2022)
        company_age = 2025 - founded_year
        industry = random.choice(INDUSTRIES)
        
        # Log-normal distribution for employees
        employees = int(random.lognormvariate(5.5, 1.2)) + 15
        
        # Base revenue formula with industry multipliers and noise
        industry_multipliers = {
            "Technology": 280000,
            "Manufacturing": 190000,
            "Healthcare": 240000,
            "Financial Services": 350000,
            "Retail": 150000,
            "Energy": 420000,
            "Telecommunications": 310000,
            "Logistics": 180000,
        }
        revenue_per_employee = industry_multipliers.get(industry, 200000)
        base_revenue = employees * revenue_per_employee * (1 + 0.015 * company_age)
        noise = random.uniform(0.85, 1.15)
        annual_revenue = round(base_revenue * noise, 2)
        
        # Shared Tax Identifier / EIN: XX-XXXXXXX
        tax_id = f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}"
        # DUNS Number: XX-XXX-XXXX
        duns_number = f"{random.randint(10, 99)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        
        entities.append({
            "entity_idx": i,
            "base_name": base_name,
            "tax_id": tax_id,
            "duns_number": duns_number,
            "country": country,
            "founded_year": founded_year,
            "industry": industry,
            "employees": employees,
            "annual_revenue": annual_revenue,
        })
    return entities

def introduce_name_noise(name: str) -> str:
    """Simulate real-world typo, whitespace, or case noise."""
    r = random.random()
    if r < 0.08:
        # Lowercase
        return name.lower()
    elif r < 0.15:
        # Extra whitespace or punctuation
        return name.replace(" ", "  ")
    elif r < 0.22 and len(name) > 6:
        # Transpose two characters (typo)
        idx = random.randint(2, len(name) - 3)
        return name[:idx] + name[idx+1] + name[idx] + name[idx+2:]
    return name

def create_datasets(output_dir: str, n_records: int = 1200) -> Tuple[str, str]:
    """Creates supply_chain_data_s1.csv and financial_data_s2.csv (1,200 rows each)."""
    os.makedirs(output_dir, exist_ok=True)
    entities = generate_base_entities(n_entities=1600)
    
    # 70% shared overlap, 30% distinct per dataset
    shared_count = int(n_records * 0.70)  # 840 shared
    unique_count = n_records - shared_count  # 360 unique each
    
    shared_pool = entities[:shared_count]
    s1_pool = shared_pool + entities[shared_count : shared_count + unique_count]
    s2_pool = shared_pool + entities[shared_count + unique_count : shared_count + 2 * unique_count]
    
    random.shuffle(s1_pool)
    random.shuffle(s2_pool)
    
    # ---------------------------------------------------------
    # Dataset 1: Supply Chain (S1)
    # ---------------------------------------------------------
    s1_path = os.path.join(output_dir, "supply_chain_data_s1.csv")
    with open(s1_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "supplier_id",
            "corporate_name",
            "tax_identifier",
            "headquarters_country",
            "founded_year",
            "employee_count",
            "industry_sector",
            "spend_volume_usd",
            "risk_score",
            "reported_revenue_usd"
        ])
        for idx, ent in enumerate(s1_pool, start=10001):
            suffix = random.choice(LEGAL_SUFFIXES_S1)
            raw_name = f"{ent['base_name']} {suffix}"
            noisy_name = introduce_name_noise(raw_name)
            spend_vol = round(ent["annual_revenue"] * random.uniform(0.05, 0.25), 2)
            risk = round(random.uniform(0.05, 0.95), 3)
            # Reported revenue may have slight reporting noise
            reported_rev = round(ent["annual_revenue"] * random.uniform(0.96, 1.04), 2)
            
            writer.writerow([
                f"SUP-{idx}",
                noisy_name,
                ent["tax_id"],
                ent["country"],
                ent["founded_year"],
                ent["employees"],
                ent["industry"],
                spend_vol,
                risk,
                reported_rev
            ])
            
    # ---------------------------------------------------------
    # Dataset 2: Financial Registry (S2)
    # ---------------------------------------------------------
    s2_path = os.path.join(output_dir, "financial_data_s2.csv")
    with open(s2_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "registration_number",
            "legal_name",
            "duns_number",
            "country_code",
            "incorporation_year",
            "employee_count",
            "industry_sector",
            "total_assets_usd",
            "operating_margin_pct",
            "credit_rating",
            "fiscal_year",
            "audited_annual_revenue"
        ])
        for ent in s2_pool:
            suffix = random.choice(LEGAL_SUFFIXES_S2)
            raw_name = f"{ent['base_name']} {suffix}"
            assets = round(ent["annual_revenue"] * random.uniform(1.2, 3.5), 2)
            margin = round(random.uniform(-5.0, 28.0), 2)
            rating = random.choice(["AAA", "AA", "A", "BBB", "BB", "B"])
            
            writer.writerow([
                ent["tax_id"],  # registration_number matches tax_id for overlap
                raw_name,
                ent["duns_number"],
                ent["country"],
                ent["founded_year"],
                ent["employees"],
                ent["industry"],
                assets,
                margin,
                rating,
                2024,
                ent["annual_revenue"]
            ])
            
    return s1_path, s2_path

if __name__ == "__main__":
    target_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    s1, s2 = create_datasets(target_dir, n_records=1200)
    print(f"Generated S1: {s1}")
    print(f"Generated S2: {s2}")
