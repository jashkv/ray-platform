"""
Company Name Normalization, String Similarity, and Canonical Identifier Engine.
"""

import re
import unicodedata
import uuid

# Namespace for deterministic Canonical Company UUIDv5 generation
CANONICAL_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "corporate-registry.ray.internal")

LEGAL_SUFFIXES = [
    r"\bcorporation\b",
    r"\bincorporated\b",
    r"\blimited liability company\b",
    r"\blimited\b",
    r"\bcompany\b",
    r"\bholdings\b",
    r"\bcorp\b",
    r"\binc\b",
    r"\bllc\b",
    r"\bltd\b",
    r"\bco\b",
    r"\bgmbh\b",
    r"\bsa\b",
    r"\bag\b",
    r"\bplc\b",
    r"\bgroup\b",
]

def clean_company_name(name: str) -> str:
    """
    Standardize corporate names:
    - Unicode NFKD decomposition
    - Lowercase
    - Remove punctuation
    - Strip corporate legal entity suffixes
    - Collapse whitespace
    """
    if not name or not isinstance(name, str):
        return ""

    # Normalize unicode
    text = unicodedata.normalize("NFKD", name)
    text = text.encode("ascii", "ignore").decode("utf-8")
    text = text.lower().strip()

    # Replace punctuation with whitespace
    text = re.sub(r"[^\w\s]", " ", text)

    # Remove legal suffixes
    for suffix_pattern in LEGAL_SUFFIXES:
        text = re.sub(suffix_pattern, "", text, flags=re.IGNORECASE)

    # Collapse multiple whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text

def levenshtein_ratio(s1: str, s2: str) -> float:
    """
    Pure Python Levenshtein similarity ratio: 1.0 - (edit_distance / max(len1, len2))
    Returns float between 0.0 (completely dissimilar) and 1.0 (identical).
    """
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    len1, len2 = len(s1), len(s2)
    prev_row = list(range(len2 + 1))
    current_row = [0] * (len2 + 1)

    for i in range(len1):
        current_row[0] = i + 1
        for j in range(len2):
            cost = 0 if s1[i] == s2[j] else 1
            current_row[j + 1] = min(
                prev_row[j + 1] + 1,       # deletion
                current_row[j] + 1,        # insertion
                prev_row[j] + cost         # substitution
            )
        prev_row = list(current_row)

    edit_distance = current_row[len2]
    return max(0.0, 1.0 - (edit_distance / max(len1, len2)))

def generate_canonical_id(tax_id: str = None, country: str = "", clean_name: str = "") -> str:
    """
    Generate an immutable, deterministic canonical company identifier.
    Prioritizes strong Tax ID if present, otherwise combines country and clean name.
    """
    if tax_id and len(tax_id.strip()) > 4:
        seed_key = f"TAX:{tax_id.strip().upper()}"
    else:
        seed_key = f"NAME:{country.strip().upper()}:{clean_name.strip()}"

    u = uuid.uuid5(CANONICAL_NAMESPACE, seed_key)
    return f"COMP-{str(u)[:8].upper()}-{str(u)[9:13].upper()}"
