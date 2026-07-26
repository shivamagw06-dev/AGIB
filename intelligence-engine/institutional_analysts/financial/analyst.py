"""Financial Analyst — Are the financials improving?"""

from __future__ import annotations

from typing import Any

from institutional_analysts.base import as_list, company_name, opinion, pick_confidence, scrub_public


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
                    return scrub_public(src.get(k), limit=120)
            metrics = src.get("metrics") if isinstance(src.get("metrics"), dict) else {}
            for k in keys:
                if metrics.get(k) not in (None, "", []):
                    return scrub_public(metrics.get(k), limit=120)
        return default

    quality = fin.get("financial_quality") or fin.get("quality") or "Mixed — track cash conversion and return on capital"
    evidence = as_list(fin.get("evidence") or fin.get("what_deserves_monitoring") or dvc.get("checks"), limit=6)
    if not evidence:
        evidence = [f"Financial statement history for {name}", "Validated institutional financial metrics"]

    return opinion(
        role="financial",
        question="Are the financials improving?",
        headline=f"{name}: financial quality rests on earnings durability, cash conversion, and balance-sheet resilience.",
        sections={
            "revenue": metric("revenue", "sales", "total_revenue", default="See latest reported revenue trend"),
            "margins": metric("margins", "ebitda_margin", "operating_margin", default="Margin trajectory under review"),
            "ebitda": metric("ebitda", default="n/a"),
            "ebit": metric("ebit", "operating_profit", default="n/a"),
            "net_profit": metric("net_profit", "pat", "net_income", default="n/a"),
            "cash_flow": metric("cash_flow", "fcf", "operating_cash_flow", default="Cash conversion needs confirmation"),
            "roe": metric("roe", default="n/a"),
            "roic": metric("roic", "roce", default="n/a"),
            "debt": metric("debt", "net_debt", "leverage", default="Leverage within franchise norms if capital ratios hold"),
            "working_capital": metric("working_capital", "nwc", default="n/a"),
            "capital_allocation": fin.get("capital_allocation") or "Balance growth investment against returns to owners",
            "financial_quality": quality,
            "trend": fin.get("trend") or fin.get("what_changed") or "Monitor sequential and year-on-year prints",
        },
        evidence=evidence,
        confidence=pick_confidence(fin.get("confidence"), dvc.get("confidence"), default=0.56),
        word_limit=500,
    )
