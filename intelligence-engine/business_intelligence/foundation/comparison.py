"""Competitive comparison across business axes — not ratio-only."""

from __future__ import annotations

from typing import Any

from business_intelligence.foundation.engines import (
    analyse_business_model,
    analyse_moat,
    analyse_growth,
    analyse_lifecycle,
    analyse_value_drivers,
)
from business_intelligence.foundation.evidence import assemble_evidence
from business_intelligence.foundation.taxonomy import classify_industry


def compare_companies(question: str, names_or_tickers: list[str] | None = None) -> dict[str, Any]:
    ev0 = assemble_evidence(question)
    names = names_or_tickers or ev0.get("compare_names") or []
    companies_ev: list[dict[str, Any]] = []
    if ev0.get("compare_companies"):
        for c in ev0["compare_companies"]:
            tk = c.get("ticker")
            companies_ev.append(
                assemble_evidence(f"Explain {c.get('company_name') or tk}", ticker=tk)
            )
    elif names:
        for n in names[:2]:
            companies_ev.append(assemble_evidence(f"Explain {n}"))
    elif ev0.get("ticker"):
        companies_ev.append(ev0)

    if len(companies_ev) < 2:
        # Try to still answer with industry-level comparison frame.
        return {
            "ok": False,
            "companies": names,
            "summary": (
                "Competitive comparison requires two identifiable companies. "
                "Provide names or tickers (e.g. 'Compare TCS vs Infosys')."
            ),
            "axes": {},
            "confidence": 0.2,
            "fabricated": False,
        }

    axes: dict[str, dict[str, Any]] = {}
    labels = []
    for cev in companies_ev[:2]:
        co = cev.get("company") or {}
        label = co.get("company_name") or cev.get("ticker") or "Company"
        labels.append(label)
        bm = analyse_business_model(cev)
        moat = analyse_moat(cev)
        growth = analyse_growth(cev)
        life = analyse_lifecycle(cev)
        vd = analyse_value_drivers(cev)
        axes[label] = {
            "ticker": cev.get("ticker"),
            "industry": cev.get("industry_key"),
            "business_type": bm.get("business_type"),
            "how_it_makes_money": (bm.get("how_it_makes_money") or "")[:220],
            "capital_intensity": bm.get("capital_intensity"),
            "operating_leverage": bm.get("operating_leverage"),
            "primary_moats": moat.get("primary_moats"),
            "moat_durability": moat.get("durability"),
            "growth_modes": growth.get("primary_modes"),
            "lifecycle": life.get("stage"),
            "value_drivers": vd.get("value_drivers"),
            "cash_conversion_lens": bm.get("working_capital_profile"),
            "management_note": "Compare capital allocation and execution only with filing-backed evidence.",
        }

    a, b = labels[0], labels[1]
    summary = (
        f"{a} vs {b}: compare business type ({axes[a].get('business_type')} vs {axes[b].get('business_type')}), "
        f"moat durability ({axes[a].get('moat_durability')} vs {axes[b].get('moat_durability')}), "
        f"growth modes, capital intensity, and industry value drivers — not ratios alone."
    )
    return {
        "ok": True,
        "companies": labels,
        "axes": axes,
        "summary": summary,
        "confidence": 0.8,
        "fabricated": False,
        "policy": "business_axes_not_ratios_only",
    }


def industry_for_question(question: str) -> str:
    return classify_industry(question=question)
