"""Industry Registry — first-class industry keys and alias resolution."""

from __future__ import annotations

import re
from typing import Optional

from industry_intelligence.dna_catalog import INDUSTRY_DNA, list_industries

# Explicit alias map (lowercase) → canonical key
_ALIAS_MAP: dict[str, str] = {}
for _key, _dna in INDUSTRY_DNA.items():
    _ALIAS_MAP[_key.replace("_", " ")] = _key
    _ALIAS_MAP[_key] = _key
    for a in _dna.aliases:
        _ALIAS_MAP[a.lower()] = _key

# Extra pedagogy aliases
_ALIAS_MAP.update(
    {
        "saas": "software",
        "software as a service": "software",
        "it": "it_services",
        "information technology": "it_services",
        "oil and gas": "oil_gas",
        "oil & gas": "oil_gas",
        "o&g": "oil_gas",
        "auto": "automobile",
        "automobiles": "automobile",
        "cars": "automobile",
        "quick service restaurants": "qsr",
        "restaurants": "qsr",
        "qsr": "qsr",
        "internet": "internet_platforms",
        "platform": "internet_platforms",
        "platforms": "internet_platforms",
        "marketplace": "internet_platforms",
        "data centre": "data_centers",
        "data center": "data_centers",
        "datacenter": "data_centers",
        "renewable": "renewables",
        "renewable energy": "renewables",
        "real estate": "real_estate",
        "realty": "real_estate",
        "consumer staple": "fmcg",
        "staples": "fmcg",
        "paint": "fmcg",
        "paints": "fmcg",
        "hospital": "hospitals",
        "healthcare": "hospitals",
        "insurer": "insurance",
        "insurers": "insurance",
        "life insurance": "insurance",
        "airline": "airlines",
        "aviation": "airlines",
        "telecoms": "telecom",
        "telecommunications": "telecom",
        "pharma": "pharma",
        "pharmaceuticals": "pharma",
        "metal": "metals",
        "steel": "metals",
        "utility": "utilities",
        "power distribution": "utilities",
        "generation": "power",
        "asset manager": "asset_management",
        "mutual funds": "asset_management",
    }
)


def resolve_industry(text: Optional[str]) -> Optional[str]:
    """Resolve free text to a canonical industry key."""
    if not text:
        return None
    low = re.sub(r"\s+", " ", str(text).strip().lower())
    if low in _ALIAS_MAP:
        return _ALIAS_MAP[low]
    # Prefer longer aliases
    for alias, key in sorted(_ALIAS_MAP.items(), key=lambda kv: -len(kv[0])):
        if len(alias) < 3:
            continue
        if re.search(rf"\b{re.escape(alias)}\b", low):
            return key
    return None


def all_industry_keys() -> list[str]:
    return list_industries()


def registry_snapshot() -> dict:
    return {
        "n": len(INDUSTRY_DNA),
        "industries": [
            {"key": k, "name": d.name, "aliases": list(d.aliases)}
            for k, d in sorted(INDUSTRY_DNA.items())
        ],
        "fabricated": False,
    }
