"""Soft consumption views — engines consume knowledge objects without redesign.

Locked engines are not modified. Academy framework pattern unchanged.
"""

from __future__ import annotations

from typing import Any

from academy.accounting.earnings_quality import score_earnings_quality
from academy.accounting.red_flags import score_red_flags
from academy.catalog import all_causal_models, all_mental_models, knowledge_by_id, teach
from academy.graph import concept_neighborhood


def _bundle_concepts(ids: list[str]) -> list[dict[str, Any]]:
    kb = knowledge_by_id()
    out = []
    for cid in ids:
        ko = kb.get(cid)
        if ko:
            out.append(ko.to_dict())
    return out


def for_kf(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    p = payload or {}
    focus = p.get("concepts") or [
        "gdp",
        "inflation",
        "monetary_policy",
        "earnings_quality",
        "free_cash_flow",
        "working_capital",
        "revenue_recognition",
    ]
    return {
        "consumer": "KF",
        "usage": "Store canonical economics + accounting knowledge objects in the corpus",
        "knowledge_objects": _bundle_concepts(list(focus)),
        "mental_models": [m.to_dict() for m in all_mental_models()],
    }


def for_kcv(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    from academy.quality import review_corpus

    review = review_corpus()
    return {
        "consumer": "KCV",
        "usage": "Only publish Academy objects that pass quality review",
        "quality": {"passed": review["passed"], "publishable": review["publishable"], "rejected": review["rejected"]},
        "objects": _bundle_concepts(
            ["inflation", "gdp", "earnings_quality", "accruals", "free_cash_flow", "revenue_recognition"]
        ),
    }


def for_eve(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """EVE: accounting consistency checks and anomaly/red-flag detection."""
    p = payload or {}
    eq = score_earnings_quality(p)
    flags = score_red_flags(p)
    return {
        "consumer": "EVE",
        "usage": "Verify accounting consistency and detect statement anomalies",
        "earnings_quality": eq,
        "red_flags": flags,
        "concepts": _bundle_concepts(["earnings_quality", "accruals", "restatements", "revenue_recognition"]),
        "anomaly": (not flags.get("clean")) or eq.get("label") == "low",
    }


def for_iie(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    p = payload or {}
    cid = str(p.get("concept_id") or "earnings_quality")
    ko = knowledge_by_id().get(cid)
    eq = score_earnings_quality(p)
    return {
        "consumer": "IIE",
        "concept_id": cid,
        "industry_impact": ko.industry_impact if ko else {},
        "company_impact": ko.company_impact if ko else {},
        "investment_impact": ko.investment_impact if ko else [],
        "decision_framework": ko.decision_framework if ko else [],
        "earnings_quality": eq,
        "business_quality_note": "Haircut business quality when earnings quality is low",
        "causal_models": [c.to_dict() for c in all_causal_models() if cid in c.related_concepts],
    }


def for_ve(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    p = payload or {}
    ids = p.get("concepts") or [
        "free_cash_flow",
        "earnings_quality",
        "ebitda",
        "working_capital",
        "roic",
        "leases",
        "share_based_compensation",
    ]
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
                    "red_flags": ko.red_flags,
                }
            )
    eq = score_earnings_quality(p)
    return {
        "consumer": "VE",
        "note": "Academy advises cash-flow measure selection and quality haircuts; VE values",
        "preferred_cash_flow": "FCFF from clean EBIT(1-t) after WC and capex — not raw EBITDA",
        "earnings_quality": eq,
        "guidance": guidance,
    }


def for_fle(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    p = payload or {}
    ids = p.get("concepts") or [
        "gdp",
        "revenue_recognition",
        "gross_profit",
        "working_capital",
        "free_cash_flow",
        "earnings_quality",
    ]
    kb = knowledge_by_id()
    drivers = []
    for cid in ids:
        ko = kb.get(cid)
        if ko:
            drivers.append({"concept_id": cid, "forecast_impact": ko.forecast_impact, "effects": ko.effects})
    return {
        "consumer": "FLE",
        "usage": "Forecast with accounting drivers: revenue quality, margins, WC days, cash conversion",
        "drivers": drivers,
        "earnings_quality": score_earnings_quality(p),
        "example_chain": next(c.to_dict() for c in all_causal_models() if c.model_id == "revenue_to_intrinsic_value"),
    }


def for_irp(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    p = payload or {}
    cid = str(p.get("concept_id") or "earnings_quality")
    return {
        "consumer": "IRP",
        "teaching": teach(cid),
        "neighborhood": concept_neighborhood(cid),
        "earnings_quality": score_earnings_quality(p),
        "usage": "Explain accounting effects inside institutional reasoning traces",
    }


def for_fiml(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    p = payload or {}
    return {
        "consumer": "FIML",
        "usage": "Consume Academy economics + accounting concepts as curriculum substrate",
        "economics_concepts": _bundle_concepts(
            p.get("economics_concepts")
            or ["gdp", "inflation", "monetary_policy", "aggregate_demand", "exchange_rates"]
        ),
        "accounting_concepts": _bundle_concepts(
            p.get("accounting_concepts")
            or ["earnings_quality", "free_cash_flow", "working_capital", "revenue_recognition", "roic"]
        ),
        "causal_models": [c.to_dict() for c in all_causal_models()],
        "earnings_quality": score_earnings_quality(p),
    }


CONSUMER_MAP = {
    "kf": for_kf,
    "kcv": for_kcv,
    "kc": for_kcv,
    "eve": for_eve,
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
