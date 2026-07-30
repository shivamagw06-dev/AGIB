"""Risk budget — volatility / drawdown / risk contribution proxies."""

from __future__ import annotations

from typing import Any

# Sector vol priors (annualised approx)
_SECTOR_VOL = {
    "banks": 0.22,
    "it_services": 0.20,
    "fmcg": 0.16,
    "telecom": 0.28,
    "consumer_internet": 0.38,
    "energy_conglomerate": 0.24,
    "other": 0.25,
}


def risk_budget(
    holdings: list[dict[str, Any]],
    *,
    max_drawdown: float,
    avg_corr: float,
) -> dict[str, Any]:
    # Simple variance proxy: w'Σw with sector vols + avg corr
    contrib = []
    var = 0.0
    for h in holdings:
        w = float(h.get("weight") or 0)
        vol = _SECTOR_VOL.get(str(h.get("sector") or "other"), 0.25)
        # marginal risk contribution proxy
        mrc = w * vol * (0.5 + 0.5 * avg_corr)
        var += (w * vol) ** 2
        contrib.append(
            {
                "ticker": h.get("ticker"),
                "weight": round(w, 4),
                "vol_prior": vol,
                "risk_contribution_proxy": round(mrc, 4),
            }
        )
    # add cross terms roughly
    port_vol = (var + avg_corr * 0.02) ** 0.5
    port_vol = min(0.45, max(0.08, port_vol + avg_corr * 0.05))
    dd_usage = min(1.5, port_vol * 2.2 / max(0.05, float(max_drawdown or 0.25)))

    score = max(0.0, min(100.0, 100.0 - (port_vol - 0.12) * 250 - max(0.0, dd_usage - 1.0) * 40))
    return {
        "risk_score": round(score, 1),
        "expected_volatility": round(port_vol, 3),
        "downside_risk_proxy": round(port_vol * 1.15, 3),
        "max_drawdown_budget": max_drawdown,
        "drawdown_budget_usage": round(dd_usage, 3),
        "contributions": sorted(contrib, key=lambda c: -c["risk_contribution_proxy"])[:10],
        "stress_concentration": "elevated" if dd_usage > 1.1 else "within_budget",
    }
