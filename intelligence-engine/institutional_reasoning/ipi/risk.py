"""Module 3 — Risk Intelligence.

Evidence-backed risk metrics for every supported portfolio recommendation.
"""

from __future__ import annotations

from typing import Any

from institutional_reasoning.ipi.portfolio_book import default_book, holding_for

RISK_VERSION = "risk-intelligence-v1.0.0"


def _f(v: Any, default: float | None = None) -> float | None:
    try:
        if v is None:
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def compute_risk(
    *,
    entity_id: str | None,
    book: dict[str, Any] | None = None,
    candidate_weight: float | None = None,
    downside: dict[str, Any] | None = None,
) -> dict[str, Any]:
    book = book or default_book()
    symbol = str(entity_id or "").upper()
    holding = holding_for(symbol, book) or {}
    vol = _f(holding.get("volatility"), 0.24) or 0.24
    beta = _f(holding.get("beta"), 1.0) or 1.0
    weight = _f(candidate_weight)
    if weight is None:
        weight = _f(holding.get("weight"), 0.0) or 0.0

    # Portfolio vol proxy = weighted sum of vols (no full cov matrix — non-goal).
    holdings = book.get("holdings") or []
    port_vol = 0.0
    port_w = 0.0
    for h in holdings:
        w = _f(h.get("weight"), 0.0) or 0.0
        v = _f(h.get("volatility"), 0.22) or 0.22
        port_vol += w * v
        port_w += w
    port_vol = port_vol / port_w if port_w else 0.22

    # Marginal risk contribution ≈ weight * vol / portfolio_vol
    risk_contribution = round((weight * vol) / max(port_vol, 1e-6), 4) if weight > 0 else 0.0
    # Correlation bump if another same-sector name already large
    sector = str(holding.get("sector") or "")
    peer_w = sum(
        _f(h.get("weight"), 0.0) or 0.0
        for h in holdings
        if str(h.get("sector") or "") == sector and str(h.get("symbol") or "").upper() != symbol
    )
    if peer_w >= 0.15:
        risk_contribution = round(risk_contribution * (1.0 + min(0.5, peer_w)), 4)

    var_95 = round(1.65 * vol * max(weight, 0.01), 4)
    es_95 = round(2.06 * vol * max(weight, 0.01), 4)
    max_dd = round(min(0.55, vol * 2.2), 4)
    tail = round(abs(_f((downside or {}).get("worst_case"), vol * 1.8) or vol * 1.8), 4)
    liq = _f(holding.get("liquidity_score"), 0.8) or 0.8
    liquidity_risk = round(max(0.0, 1.0 - liq), 4)
    concentration_risk = round(max(weight, peer_w), 4)

    policy = book.get("policy") or {}
    risk_budget = _f(policy.get("risk_budget"), 0.12) or 0.12

    drivers = []
    if risk_contribution > (_f(policy.get("max_single_name_risk_contribution"), 0.18) or 0.18):
        drivers.append("single_name_risk_budget")
    if peer_w >= 0.15:
        drivers.append("sector_correlation")
    if liquidity_risk >= 0.45:
        drivers.append("liquidity")
    if not drivers:
        drivers = ["market_beta", "volatility"]

    return {
        "found": True,
        "risk_version": RISK_VERSION,
        "entity_id": symbol or None,
        "volatility": round(vol, 4),
        "beta": round(beta, 4),
        "var": var_95,
        "expected_shortfall": es_95,
        "maximum_drawdown": max_dd,
        "risk_contribution": risk_contribution,
        "risk_share": risk_contribution,
        "var_contribution": risk_contribution,
        "tail_risk": tail,
        "liquidity_risk": liquidity_risk,
        "concentration_risk": concentration_risk,
        "sector_risk": round(peer_w + weight, 4),
        "country_risk": 0.05 if str(holding.get("country") or "IN") == "IN" else 0.15,
        "currency_risk": 0.04 if str(holding.get("currency") or "INR") == "INR" else 0.12,
        "risk_budget": risk_budget,
        "risk_budget_used": round(min(1.0, risk_contribution / max(risk_budget, 1e-6)), 4),
        "risk_drivers": drivers,
        "portfolio_volatility_proxy": round(port_vol, 4),
    }
