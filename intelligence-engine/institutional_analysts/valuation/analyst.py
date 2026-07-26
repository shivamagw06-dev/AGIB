"""Valuation Analyst — Is today's valuation attractive?"""

from __future__ import annotations

from typing import Any

from institutional_analysts.base import as_list, company_name, pick_confidence, structured_opinion


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
    mos = str(src.get("margin_of_safety") or "").lower()
    stance = "Neutral"
    if any(w in mos for w in ("high", "wide", "attractive", "ample")):
        stance = "Bullish"
    elif any(w in mos for w in ("modest", "thin", "limited", "rich", "low")):
        stance = "Bearish"
    pe = multiples.get("pe") or multiples.get("trailing_pe") or src.get("pe")
    try:
        if pe is not None and float(pe) >= 22:
            stance = "Bearish"
    except Exception:
        pass

    evidence = as_list(src.get("evidence") or src.get("peer_set") or dvc.get("valuation_checks"), limit=6)
    if not evidence:
        evidence = [f"Current valuation cross-checks for {name}", "Peer and history triangulation"]

    expected = summary.get("expected_return_12m_pct") or src.get("expected_return") or briefing.get("expected_return")
    coverage = pick_confidence(src.get("confidence"), summary.get("confidence_pct"), default=0.54)

    return structured_opinion(
        role="valuation",
        summary=f"{name}: attractiveness depends on multiples versus history, peers, and expected return — not franchise storytelling.",
        strengths=as_list(
            [
                f"Expected return context: {expected}" if expected is not None else "",
                src.get("peer_comparison") or "Peer multiples available as a cross-check",
            ],
            limit=4,
        )
        or ["Historical multiple context available"],
        weaknesses=as_list(src.get("risks") or ["Multiple compression", "Earnings miss versus expectations"], limit=4),
        evidence=evidence,
        unanswered_questions=[
            "How much growth is already discounted in today's multiple?",
            "What margin of safety remains if earnings undershoot?",
        ],
        sections={
            "historical_valuation": src.get("historical") or src.get("history") or "Compare current multiples with the franchise's own history",
            "current_multiples": {
                "pe": pe,
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
        },
        stance=stance,
        confidence={
            "evidence": pick_confidence(0.5 + 0.05 * min(len(evidence), 4), default=0.5),
            "knowledge": coverage,
            "freshness": pick_confidence(dvc.get("freshness"), default=0.52),
            "coverage": coverage,
        },
        ctx=ctx,
    )
