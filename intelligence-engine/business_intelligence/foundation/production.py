"""Phase 3.0 Business Intelligence Foundation — production facade.

Ask is NOT wired here. Callers use analyse() / module endpoints only after
the Business Intelligence Acceptance Test passes.
"""

from __future__ import annotations

from typing import Any, Optional

from business_intelligence.foundation.comparison import compare_companies
from business_intelligence.foundation.engines import (
    analyse_business_model,
    analyse_growth,
    analyse_industry,
    analyse_lifecycle,
    analyse_management,
    analyse_moat,
    analyse_risks,
    analyse_unit_economics,
    analyse_value_drivers,
)
from business_intelligence.foundation.evidence import assemble_evidence
from business_intelligence.foundation.graph import build_knowledge_graph
from business_intelligence.foundation.industry_drivers import INDUSTRY_TEMPLATES, template_for
from business_intelligence.foundation.orchestrator import analyse as _analyse
from business_intelligence.foundation.schema import (
    BI_VERSION,
    BUSINESS_TYPES,
    LIFECYCLE_STAGES,
    MOAT_DIMENSIONS,
    PROGRAMME,
    RISK_TYPES,
    SPEC,
)
from business_intelligence.foundation.taxonomy import classify_industry


def health() -> dict[str, Any]:
    return {
        "ok": True,
        "status": "ok",
        "programme": PROGRAMME,
        "version": BI_VERSION,
        "spec": SPEC,
        "ask_wired": False,
        "uses_llm": False,
        "fabricated": False,
        "modules": [
            "business_model",
            "value_drivers",
            "unit_economics",
            "moat",
            "industry",
            "growth",
            "management",
            "risks",
            "lifecycle",
            "comparison",
            "knowledge_graph",
        ],
        "industry_templates": sorted(INDUSTRY_TEMPLATES.keys()),
        "business_types": list(BUSINESS_TYPES),
        "moat_dimensions": list(MOAT_DIMENSIONS),
    }


def dashboard() -> dict[str, Any]:
    h = health()
    return {
        "programme": PROGRAMME,
        "version": BI_VERSION,
        "ask_wired": False,
        "module_count": len(h["modules"]),
        "industry_template_count": len(h["industry_templates"]),
        "lifecycle_stages": list(LIFECYCLE_STAGES),
        "risk_types": list(RISK_TYPES),
        "note": "Ask integration deferred until BI Acceptance Test ≥95%.",
        "fabricated": False,
    }


def analyse(question: str, *, ticker: Optional[str] = None, industry: Optional[str] = None) -> dict[str, Any]:
    return _analyse(question, ticker=ticker, industry_hint=industry)


def company(ticker: str, question: str = "") -> dict[str, Any]:
    q = question or f"What is {ticker}'s business model?"
    return _analyse(q, ticker=ticker.upper())


def industry(industry_key: str) -> dict[str, Any]:
    key = classify_industry(industry=industry_key, question=industry_key)
    tmpl = template_for(key)
    ev = {"industry_key": key, "company": {}, "question": industry_key, "evidence": []}
    return {
        "industry": key,
        "template": tmpl,
        "value_drivers": analyse_value_drivers(ev),
        "unit_economics": analyse_unit_economics(ev),
        "industry_structure": analyse_industry(ev),
        "lifecycle": analyse_lifecycle(ev),
        "fabricated": False,
        "version": BI_VERSION,
    }


def moat(question: str = "", *, ticker: Optional[str] = None) -> dict[str, Any]:
    ev = assemble_evidence(question or f"What is the moat of {ticker}?", ticker=ticker)
    return analyse_moat(ev)


def compare(question: str) -> dict[str, Any]:
    return compare_companies(question)


def graph(ticker: str) -> dict[str, Any]:
    ev = assemble_evidence(f"Explain {ticker}", ticker=ticker.upper())
    return build_knowledge_graph(ev)


def soft_slice_for_ask_agi(question: str = "", *_args: Any, ticker: Optional[str] = None, **_kwargs: Any) -> dict[str, Any]:
    """Reserved soft-slice — disabled until acceptance gate passes."""
    return {
        "enabled": False,
        "ask_wired": False,
        "reason": "Phase 3.0 Ask integration deferred until BI Acceptance Test ≥95%.",
        "preview_available_via": "business_intelligence.foundation.production.analyse",
        "fabricated": False,
    }
