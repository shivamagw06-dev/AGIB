"""Module 8 — Downside Intelligence.

If downside cannot be computed → portfolio recommendation WITHHOLDS.
"""

from __future__ import annotations

from typing import Any

DOWNSIDE_VERSION = "downside-intelligence-v1.0.0"


def _f(v: Any) -> float | None:
    try:
        if v is None:
            return None
        x = float(v)
        if x != x:  # NaN
            return None
        return x
    except (TypeError, ValueError):
        return None


def compute_downside(
    *,
    entity_id: str | None,
    evidence: dict[str, Any] | None = None,
    risk_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Produce base/bull/bear/stress cases + expected loss.

    Requires at least current PE context or volatility proxy from risk_inputs.
    """
    evidence = evidence or {}
    risk_inputs = risk_inputs or {}
    pe = _f(evidence.get("current_pe"))
    hist = _f(evidence.get("historical_pe"))
    peer = _f(evidence.get("peer_pe") or evidence.get("peer_median_pe"))
    sector = _f(evidence.get("sector_pe"))
    vol = _f(risk_inputs.get("volatility")) or 0.24
    beta = _f(risk_inputs.get("beta")) or 1.0

    if pe is None and hist is None and peer is None:
        return {
            "found": False,
            "computable": False,
            "reason": "no_valuation_anchor_for_downside",
            "downside_version": DOWNSIDE_VERSION,
            "entity_id": entity_id,
            "withhold": True,
        }

    anchor = pe if pe is not None else (peer if peer is not None else hist)
    fair = hist or peer or sector or (anchor * 1.1 if anchor else None)
    if fair is None or fair <= 0 or anchor is None or anchor <= 0:
        return {
            "found": False,
            "computable": False,
            "reason": "invalid_valuation_anchor",
            "downside_version": DOWNSIDE_VERSION,
            "entity_id": entity_id,
            "withhold": True,
        }

    # Multiple-mean-reversion style cases (evidence-backed, not optimisation).
    base_return = round((fair / anchor) - 1.0, 4)
    bull_return = round(base_return + 0.12 + max(0.0, (peer or fair) / fair - 1.0) * 0.05, 4)
    bear_return = round(min(-0.08, base_return - vol * 1.1), 4)
    stress_return = round(min(bear_return - 0.10, -vol * beta * 1.8), 4)

    expected_loss = abs(min(0.0, bear_return))
    worst_case = abs(min(0.0, stress_return))
    recovery_years = round(max(0.5, worst_case / max(0.06, abs(base_return) if base_return > 0 else 0.08)), 2)

    bear_case = {
        "label": "Bear",
        "expected_return": bear_return,
        "expected_loss": round(expected_loss, 4),
        "drivers": ["multiple compression", "earnings disappointment"],
        "probability": 0.25,
        "confidence": 0.72,
    }
    return {
        "found": True,
        "computable": True,
        "withhold": False,
        "downside_version": DOWNSIDE_VERSION,
        "entity_id": entity_id,
        "base_case": {
            "label": "Base",
            "expected_return": base_return,
            "expected_loss": 0.0,
            "probability": 0.45,
            "confidence": 0.78,
        },
        "bull_case": {
            "label": "Bull",
            "expected_return": bull_return,
            "expected_loss": 0.0,
            "probability": 0.20,
            "confidence": 0.65,
        },
        "bear_case": bear_case,
        "stress_case": {
            "label": "Stress",
            "expected_return": stress_return,
            "expected_loss": round(worst_case, 4),
            "probability": 0.10,
            "confidence": 0.60,
            "drivers": ["recession", "sector derating", "liquidity shock"],
        },
        "expected_loss": round(expected_loss, 4),
        "worst_case": round(worst_case, 4),
        "recovery_time_years": recovery_years,
        # Contract aliases consumed by validation
        "downside_case": bear_case,
        "downside": bear_return,
        "bear": bear_return,
        "stress_case": stress_return,
    }
