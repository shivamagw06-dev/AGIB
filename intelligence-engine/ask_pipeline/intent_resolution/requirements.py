"""Evidence requirements derived from resolved intent (feeds IERE)."""

from __future__ import annotations

from typing import Any

_REQUIREMENTS: dict[str, list[str]] = {
    "Explain": ["FINANCIAL_METRICS", "RELATIONSHIP_GRAPH", "DOCUMENT_SECTIONS"],
    "Compare": ["FINANCIAL_METRICS", "RELATIONSHIP_GRAPH", "HISTORICAL_VALUATION", "OWNERSHIP"],
    "Analyse": [
        "FINANCIAL_METRICS",
        "CORPORATE_EVENTS",
        "DOCUMENT_SECTIONS",
        "RISK_FACTORS",
        "HISTORICAL_VALUATION",
    ],
    "Valuation": ["FINANCIAL_METRICS", "HISTORICAL_VALUATION", "OWNERSHIP", "DOCUMENT_SECTIONS"],
    "Portfolio": ["FINANCIAL_METRICS", "OWNERSHIP", "RELATIONSHIP_GRAPH", "CORPORATE_EVENTS"],
    "Education": ["FINANCIAL_METRICS", "DOCUMENT_SECTIONS"],
    "HistoricalReplay": ["FINANCIAL_METRICS", "DOCUMENT_SECTIONS", "CORPORATE_EVENTS", "TIMELINES"],
    "Risk": ["RISK_FACTORS", "FINANCIAL_METRICS", "CORPORATE_EVENTS", "MACRO_INDICATORS"],
    "Accounting": ["FINANCIAL_METRICS", "ACCOUNTING_NOTES", "DOCUMENT_SECTIONS"],
    "Industry": ["RELATIONSHIP_GRAPH", "MACRO_INDICATORS", "FINANCIAL_METRICS"],
    "Macro": ["MACRO_INDICATORS", "GOVERNMENT_POLICIES", "ALTERNATIVE_DATA"],
    "Government": ["GOVERNMENT_POLICIES", "MACRO_INDICATORS", "RELATIONSHIP_GRAPH"],
    "CorporateEvents": ["CORPORATE_EVENTS", "TIMELINES", "DOCUMENT_SECTIONS"],
    "Documents": [
        "DOCUMENT_SECTIONS",
        "RISK_FACTORS",
        "MANAGEMENT_COMMENTARY",
        "ACCOUNTING_NOTES",
        "INVESTOR_PRESENTATIONS",
    ],
    "CrossDomain": [
        "MACRO_INDICATORS",
        "GOVERNMENT_POLICIES",
        "ALTERNATIVE_DATA",
        "RELATIONSHIP_GRAPH",
        "FINANCIAL_METRICS",
        "CORPORATE_EVENTS",
    ],
    "Unknown": ["FINANCIAL_METRICS", "DOCUMENT_SECTIONS"],
}


def evidence_requirements(
    intent: str,
    *,
    concept_mode: bool,
    temporal: dict[str, Any] | None = None,
) -> dict[str, Any]:
    required = list(_REQUIREMENTS.get(intent) or _REQUIREMENTS["Unknown"])
    if temporal and temporal.get("is_historical"):
        if "TIMELINES" not in required:
            required.append("TIMELINES")
        if "HISTORICAL_VALUATION" not in required:
            required.append("HISTORICAL_VALUATION")
    return {
        "intent": intent,
        "evidence_types_required": required,
        "concept_mode": concept_mode,
        "require_company_object": (not concept_mode) and intent
        not in {"Education", "Explain", "Macro", "Government", "Industry", "CrossDomain", "Unknown"},
        "allow_empty_entity": concept_mode
        or intent
        in {
            "Education",
            "Explain",
            "Industry",
            "Macro",
            "Government",
            "CrossDomain",
            "Documents",
            "HistoricalReplay",
        },
        "fabricated": False,
    }
