"""Financial Analyst — Are the financials improving?"""

from __future__ import annotations

from typing import Any

from institutional_analysts.base import as_list, company_name, pick_confidence, structured_opinion


def analyse(ctx: dict[str, Any]) -> dict[str, Any]:
    ca = ctx.get("company_analysis") if isinstance(ctx.get("company_analysis"), dict) else {}
    cid = ctx.get("company_dossier") if isinstance(ctx.get("company_dossier"), dict) else {}
    dvc = ctx.get("data_validation") if isinstance(ctx.get("data_validation"), dict) else {}
    yfp = ctx.get("yahoo_enrichment") if isinstance(ctx.get("yahoo_enrichment"), dict) else {}
    fin = ca.get("financial_intelligence") if isinstance(ca.get("financial_intelligence"), dict) else {}
    hist = cid.get("financial_statements") if isinstance(cid.get("financial_statements"), dict) else {}
    name = company_name(ctx)

    def metric(*keys: str, default: str = "n/a") -> str:
        for src in (fin, hist, yfp, dvc):
            if not isinstance(src, dict):
                continue
            for k in keys:
                if src.get(k) not in (None, "", []):
                    return str(src.get(k))
            metrics = src.get("metrics") if isinstance(src.get("metrics"), dict) else {}
            for k in keys:
                if metrics.get(k) not in (None, "", []):
                    return str(metrics.get(k))
        return default

    quality = fin.get("financial_quality") or fin.get("quality") or "Mixed — track cash conversion and return on capital"
    trend = str(fin.get("trend") or fin.get("what_changed") or "")
    stance = "Bullish" if "improv" in trend.lower() or "strong" in str(quality).lower() else "Neutral"
    if "deterior" in trend.lower() or "weak" in str(quality).lower():
        stance = "Bearish"

    evidence = as_list(fin.get("evidence") or fin.get("what_deserves_monitoring") or dvc.get("checks"), limit=6)
    if not evidence:
        evidence = [f"Financial statement history for {name}", "Validated institutional financial metrics"]

    coverage = pick_confidence(fin.get("confidence"), dvc.get("confidence"), dvc.get("coverage_pct"), default=0.56)
    return structured_opinion(
        role="financial",
        summary=f"{name}: financial quality rests on earnings durability, cash conversion, and balance-sheet resilience.",
        strengths=as_list([metric("roe", default=""), metric("cash_flow", "fcf", "operating_cash_flow", default=""), quality], limit=4)
        or ["Earnings durability under review"],
        weaknesses=as_list(fin.get("what_deserves_monitoring") or ["Cash conversion confirmation", "Leverage path"], limit=4),
        evidence=evidence,
        unanswered_questions=[
            "Is incremental return on capital expanding or fading?",
            "How clean is cash conversion versus reported earnings?",
        ],
        sections={
            "revenue": metric("revenue", "sales", "total_revenue", default="See latest reported revenue trend"),
            "margins": metric("margins", "ebitda_margin", "operating_margin", default="Margin trajectory under review"),
            "ebitda": metric("ebitda"),
            "ebit": metric("ebit", "operating_profit"),
            "net_profit": metric("net_profit", "pat", "net_income"),
            "cash_flow": metric("cash_flow", "fcf", "operating_cash_flow", default="Cash conversion needs confirmation"),
            "roe": metric("roe"),
            "roic": metric("roic", "roce"),
            "debt": metric("debt", "net_debt", "leverage", default="Leverage within franchise norms if capital ratios hold"),
            "working_capital": metric("working_capital", "nwc"),
            "capital_allocation": fin.get("capital_allocation") or "Balance growth investment against returns to owners",
            "financial_quality": quality,
            "trend": trend or "Monitor sequential and year-on-year prints",
        },
        stance=stance,
        confidence={
            "evidence": pick_confidence(0.45 + 0.08 * min(len(evidence), 5), default=0.5),
            "knowledge": coverage,
            "freshness": pick_confidence(dvc.get("freshness"), default=0.55),
            "coverage": coverage,
        },
        ctx=ctx,
    )
