"""Risk Analyst — What can go wrong?"""

from __future__ import annotations

from typing import Any

from institutional_analysts.base import as_list, company_name, opinion, pick_confidence


def analyse(ctx: dict[str, Any]) -> dict[str, Any]:
    cm = ctx.get("company_monitor") if isinstance(ctx.get("company_monitor"), dict) else {}
    ca = ctx.get("company_analysis") if isinstance(ctx.get("company_analysis"), dict) else {}
    de = ctx.get("decision_engine") if isinstance(ctx.get("decision_engine"), dict) else {}
    layers = {str(l.get("id")): l for l in (de.get("layers") or []) if isinstance(l, dict)}
    risk_layer = layers.get("risk") or {}
    ail = ctx.get("intelligence_layer") if isinstance(ctx.get("intelligence_layer"), dict) else {}
    name = company_name(ctx)

    what = cm.get("what_changed") if isinstance(cm.get("what_changed"), dict) else cm
    business_risks = as_list(
        ca.get("key_risks")
        or (ca.get("investment_thesis") or {}).get("risks")
        or what.get("risks")
        or risk_layer.get("negative"),
        limit=6,
    )
    financial_risks = as_list((ca.get("financial_intelligence") or {}).get("what_deserves_monitoring"), limit=4)
    if not business_risks:
        business_risks = ["Execution miss", "Competitive intensity", "Regulatory change"]
    if not financial_risks:
        financial_risks = ["Earnings volatility", "Balance-sheet stress"]

    evidence = as_list(cm.get("alerts") or risk_layer.get("evidence") or ail.get("contradictory_evidence_ids"), limit=6)
    if not evidence:
        evidence = ["Risk register from institutional monitoring", "Thesis invalidation conditions"]

    return opinion(
        role="risk",
        question="What can go wrong?",
        headline=f"{name}: downside is a function of business, financial, macro, and valuation shocks.",
        sections={
            "business_risks": business_risks,
            "financial_risks": financial_risks,
            "macro_risks": as_list(risk_layer.get("macro_risks") or ["Rate shock", "Growth slowdown"], limit=4),
            "execution_risks": as_list(what.get("execution_risks") or ["Delivery against guidance", "Integration / ops complexity"], limit=4),
            "valuation_risks": as_list(["Multiple compression", "Expectations reset"], limit=4),
            "probability": risk_layer.get("reasoning") or "Probability of severe impairment is moderate unless several risks coincide",
            "impact": "High-impact risks are those that impair franchise returns or capital",
            "monitoring": as_list(what.get("monitor") or ca.get("monitoring") or ["Next earnings", "Guidance", "Asset quality / margins"], limit=5),
        },
        evidence=evidence,
        confidence=pick_confidence(risk_layer.get("score"), cm.get("confidence"), default=0.57),
        score=risk_layer.get("score"),
        word_limit=450,
    )
