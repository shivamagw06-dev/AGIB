"""Market Analyst — What is the market saying?"""

from __future__ import annotations

from typing import Any

from institutional_analysts.base import as_list, company_name, opinion, pick_confidence


def analyse(ctx: dict[str, Any]) -> dict[str, Any]:
    cid = ctx.get("company_dossier") if isinstance(ctx.get("company_dossier"), dict) else {}
    leo = ctx.get("live_evidence") if isinstance(ctx.get("live_evidence"), dict) else {}
    de = ctx.get("decision_engine") if isinstance(ctx.get("decision_engine"), dict) else {}
    layers = {str(l.get("id")): l for l in (de.get("layers") or []) if isinstance(l, dict)}
    tech = layers.get("technical") or {}
    market = cid.get("market_intelligence") if isinstance(cid.get("market_intelligence"), dict) else {}
    md = cid.get("market_data") if isinstance(cid.get("market_data"), dict) else {}
    src = market or md or {}
    name = company_name(ctx)

    evidence = as_list(leo.get("market_data_used") or src.get("evidence") or tech.get("evidence"), limit=6)
    if not evidence:
        evidence = ["Price/volume context from institutional market tape", "Technical and liquidity cross-checks"]

    return opinion(
        role="market",
        question="What is the market saying?",
        headline=f"{name}: market tape reflects trend, liquidity, and positioning — not fundamental fair value alone.",
        sections={
            "price_trend": src.get("trend") or tech.get("reasoning") or "Trend context assessed from recent price action",
            "momentum": src.get("momentum") or "Momentum mixed unless confirmed by breadth and volume",
            "volume": src.get("volume") or "Volume confirmation required for breakout conviction",
            "liquidity": src.get("liquidity") or "Large-cap liquidity generally supports institutional sizing",
            "range_52w": src.get("fifty_two_week") or src.get("range_52w") or "Position within the 52-week range informs entry staging",
            "volatility": src.get("volatility") or tech.get("score") or "Volatility informs position sizing and staging",
            "institutional_activity": src.get("institutional_activity") or "Watch ownership and flow signals around results",
            "technical_context": tech.get("reasoning") or src.get("technical") or "Technicals are a timing overlay, not the investment case",
        },
        evidence=evidence,
        confidence=pick_confidence(src.get("confidence"), tech.get("score"), default=0.5),
        score=tech.get("score"),
        word_limit=400,
    )
