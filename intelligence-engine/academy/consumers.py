"""Soft consumption views — engines consume knowledge objects without redesign.

Locked engines (KF, KCV, IIE, VE, FLE, IRP, FIML) are not modified.
Composition roots or future soft-wiring call these helpers.
"""

from __future__ import annotations

from typing import Any

from academy.causal_models import all_causal_models
from academy.graph import concept_neighborhood
from academy.knowledge_objects import knowledge_by_id
from academy.mental_models import all_mental_models
from academy.teaching import teach


def _bundle_concepts(ids: list[str]) -> list[dict[str, Any]]:
    kb = knowledge_by_id()
    out = []
    for cid in ids:
        ko = kb.get(cid)
        if ko:
            out.append(ko.to_dict())
    return out


def for_kf(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """KF: ingest canonical macro/micro knowledge objects into corpus views."""
    p = payload or {}
    focus = p.get("concepts") or ["gdp", "inflation", "monetary_policy", "fiscal_policy", "supply_and_demand"]
    return {
        "consumer": "KF",
        "usage": "Attach published Academy knowledge objects as structured macro/theme knowledge",
        "knowledge_objects": _bundle_concepts(list(focus)),
        "mental_models": [m.to_dict() for m in all_mental_models()],
    }


def for_kcv(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """KCV: quality-reviewed objects ready for corpus population."""
    from academy.quality import review_corpus

    review = review_corpus()
    return {
        "consumer": "KCV",
        "usage": "Only publish Academy objects that pass quality review",
        "quality": {"passed": review["passed"], "publishable": review["publishable"], "rejected": review["rejected"]},
        "objects": _bundle_concepts(["inflation", "gdp", "unemployment", "elasticity", "discount_rate"]),
    }


def for_iie(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """IIE: industry/company impact slices for thesis construction."""
    p = payload or {}
    cid = str(p.get("concept_id") or "monetary_policy")
    ko = knowledge_by_id().get(cid)
    return {
        "consumer": "IIE",
        "concept_id": cid,
        "industry_impact": ko.industry_impact if ko else {},
        "company_impact": ko.company_impact if ko else {},
        "investment_impact": ko.investment_impact if ko else [],
        "decision_framework": ko.decision_framework if ko else [],
        "causal_models": [c.to_dict() for c in all_causal_models() if cid in c.related_concepts],
    }


def for_ve(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """VE: valuation impact guidance from economics concepts (does not value)."""
    p = payload or {}
    ids = p.get("concepts") or ["inflation", "discount_rate", "gdp", "monetary_policy", "market_power"]
    guidance = []
    kb = knowledge_by_id()
    for cid in ids:
        ko = kb.get(cid)
        if ko:
            guidance.append(
                {
                    "concept_id": cid,
                    "valuation_impact": ko.valuation_impact,
                    "investment_impact": ko.investment_impact,
                }
            )
    return {
        "consumer": "VE",
        "note": "Academy advises valuation implications; VE performs valuation",
        "guidance": guidance,
    }


def for_fle(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """FLE: forecast-driver mappings from macro concepts."""
    p = payload or {}
    ids = p.get("concepts") or ["gdp", "inflation", "monetary_policy", "credit", "exchange_rates"]
    kb = knowledge_by_id()
    drivers = []
    for cid in ids:
        ko = kb.get(cid)
        if ko:
            drivers.append({"concept_id": cid, "forecast_impact": ko.forecast_impact, "effects": ko.effects})
    return {
        "consumer": "FLE",
        "usage": "Map macro concepts into revenue/margin/cash-flow forecast assumptions",
        "drivers": drivers,
        "example_chain": next(c.to_dict() for c in all_causal_models() if c.model_id == "gdp_to_cash_flows"),
    }


def for_irp(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """IRP: explainability + teaching answers for reasoning traces."""
    p = payload or {}
    cid = str(p.get("concept_id") or "inflation")
    return {
        "consumer": "IRP",
        "teaching": teach(cid),
        "neighborhood": concept_neighborhood(cid),
        "usage": "Use Academy explainability blocks in institutional reasoning traces",
    }


def for_fiml(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """FIML: economics/macro domain enrichment without modifying FIML package code paths beyond soft call."""
    p = payload or {}
    return {
        "consumer": "FIML",
        "usage": "Consume Academy concepts as curriculum substrate for economics/macro models",
        "economics_concepts": _bundle_concepts(
            p.get("concepts")
            or ["gdp", "inflation", "monetary_policy", "aggregate_demand", "aggregate_supply", "exchange_rates"]
        ),
        "causal_models": [c.to_dict() for c in all_causal_models()],
    }


CONSUMER_MAP = {
    "kf": for_kf,
    "kcv": for_kcv,
    "kc": for_kcv,
    "iie": for_iie,
    "ve": for_ve,
    "fle": for_fle,
    "irp": for_irp,
    "fiml": for_fiml,
}


def for_engine(engine: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    key = (engine or "").lower().strip()
    fn = CONSUMER_MAP.get(key)
    if not fn:
        raise KeyError(f"Unknown Academy consumer: {engine}")
    return fn(payload or {})
