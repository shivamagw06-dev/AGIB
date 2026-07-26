"""Valuation Analyst — Is today's valuation attractive?"""

from __future__ import annotations

from typing import Any

from institutional_analysts.base import as_list, company_name, opinion, pick_confidence, scrub_public


def analyse(ctx: dict[str, Any]) -> dict[str, Any]:
    val = ctx.get("valuation") if isinstance(ctx.get("valuation"), dict) else {}
    ca = ctx.get("company_analysis") if isinstance(ctx.get("company_analysis"), dict) else {}
    ca_val = ca.get("valuation_intelligence") if isinstance(ca.get("valuation_intelligence"), dict) else {}
    dvc = ctx.get("data_validation") if isinstance(ctx.get("data_validation"), dict) else {}
    briefing = ctx.get("institutional_briefing") if isinstance(ctx.get("institutional_briefing"), dict) else {}
    de = ctx.get("decision_engine") if isinstance(ctx.get("decision_engine"), dict) else {}
    summary = de.get("summary") if isinstance(de.get("summary"), dict) else {}
    name = company_name(ctx)

    src = ca_val or val or {}
    multiples = src.get("multiples") if isinstance(src.get("multiples"), dict) else src
    evidence = as_list(src.get("evidence") or src.get("peer_set") or dvc.get("valuation_checks"), limit=6)
    if not evidence:
        evidence = [f"Current valuation cross-checks for {name}", "Peer and history triangulation"]

    expected = (
        summary.get("expected_return_12m_pct")
        or src.get("expected_return")
        or briefing.get("expected_return")
    )

    return opinion(
        role="valuation",
        question="Is today's valuation attractive?",
        headline=f"{name}: valuation attractiveness depends on multiples versus history, peers, and expected returns.",
        sections={
            "historical_valuation": src.get("historical") or src.get("history") or "Compare current multiples with the franchise's own history",
            "current_multiples": {
                "pe": multiples.get("pe") or multiples.get("trailing_pe") or src.get("pe"),
                "forward_pe": multiples.get("forward_pe") or src.get("forward_pe"),
                "pb": multiples.get("pb") or multiples.get("price_to_book") or src.get("pb"),
                "peg": multiples.get("peg") or src.get("peg"),
                "dividend_yield": multiples.get("dividend_yield") or src.get("dividend_yield"),
            },
            "peer_comparison": src.get("peer_comparison") or src.get("peers") or "Peer multiples used as a cross-check, not a verdict",
            "intrinsic_value": src.get("intrinsic_value") or src.get("fair_value") or "Intrinsic value band remains an estimate under uncertainty",
            "margin_of_safety": src.get("margin_of_safety") or "Margin of safety rises when price embeds pessimistic assumptions",
            "valuation_risks": src.get("risks") or ["Multiple compression", "Earnings miss versus expectations"],
            "expected_return": expected if expected is not None else "Scenario-weighted return depends on earnings path and multiple",
            "perspective": scrub_public(briefing.get("valuation_perspective") or src.get("narrative") or "", limit=260),
        },
        evidence=evidence,
        confidence=pick_confidence(src.get("confidence"), summary.get("confidence_pct"), default=0.54),
        word_limit=500,
    )
