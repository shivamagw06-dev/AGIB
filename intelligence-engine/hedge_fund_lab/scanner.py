"""Live strategy scanner — runs strategies across the NSE universe.

Every candidate carries the reason it surfaced. These are research
observations built from market data, never recommendations: no buy, no sell,
no price target of AGI's own.
"""

from __future__ import annotations

import statistics as stats
from typing import Any, Optional


def _num(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


# Vendor data carries occasional nonsense (an 11,360% "net margin", a 0.2 P/E
# on collapsed earnings). Anything outside a plausible band is treated as
# missing rather than surfaced as an opportunity.
_SANE_BOUNDS: dict[str, tuple[float, float]] = {
    "pe": (3.0, 200.0),
    "forward_pe": (3.0, 200.0),
    "pb": (0.05, 50.0),
    "ev_ebitda": (1.0, 80.0),
    "ev_sales": (0.05, 60.0),
    "roe": (-100.0, 150.0),
    "profit_margin": (-100.0, 100.0),
    "dividend_yield": (0.0, 25.0),
    "debt_to_equity": (0.0, 1000.0),
}


def _sane(row: dict[str, Any], field: str) -> Optional[float]:
    """A metric only if it is inside a believable range."""
    value = _num(row.get(field))
    if value is None:
        return None
    low, high = _SANE_BOUNDS.get(field, (float("-inf"), float("inf")))
    return value if low <= value <= high else None


def _median(values: list[Any]) -> Optional[float]:
    clean = [v for v in (_num(x) for x in values) if v is not None]
    return round(stats.median(clean), 2) if clean else None


def _universe() -> list[dict[str, Any]]:
    """Companies with both market multiples and consensus attached."""
    try:
        from valuation_consensus.store import get_row as consensus_row
        from valuation_terminal.store import all_rows
    except Exception:
        return []

    out: list[dict[str, Any]] = []
    for ticker, row in (all_rows() or {}).items():
        merged = dict(row)
        merged["ticker"] = ticker
        merged["consensus"] = consensus_row(ticker) or {}
        out.append(merged)
    return out


def _primary_metric(dna: Optional[str]) -> str:
    try:
        from valuation_terminal.sector_lens import lens_for

        return lens_for(dna)["primary_metric"]
    except Exception:
        return "pe"


def _industry_medians(universe: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in universe:
        industry = row.get("primary_industry")
        if industry:
            groups.setdefault(industry, []).append(row)
    out: dict[str, dict[str, Any]] = {}
    for industry, members in groups.items():
        out[industry] = {
            "count": len(members),
            "pe": _median([_sane(m, "pe") for m in members]),
            "pb": _median([_sane(m, "pb") for m in members]),
            "ev_ebitda": _median([_sane(m, "ev_ebitda") for m in members]),
            "roe": _median([_sane(m, "roe") for m in members]),
            "dividend_yield": _median([m.get("dividend_yield") for m in members]),
            "return_1y": _median([(m.get("consensus") or {}).get("return_1y") for m in members]),
            "profit_margin": _median([_sane(m, "profit_margin") for m in members]),
        }
    return out


def _base(row: dict[str, Any]) -> dict[str, Any]:
    consensus = row.get("consensus") or {}
    return {
        "ticker": row["ticker"],
        "company_name": row.get("company_name"),
        "sector": row.get("primary_sector"),
        "industry": row.get("primary_industry"),
        "market_cap": row.get("market_cap"),
        "consensus_upside": consensus.get("upside"),
        "coverage": consensus.get("coverage"),
        "return_1y": consensus.get("return_1y"),
    }


# ---------------------------------------------------------------------------
# Market regime, derived from the universe itself
# ---------------------------------------------------------------------------
def market_regime() -> dict[str, Any]:
    universe = _universe()
    if not universe:
        return {"ok": False, "error": "universe_empty"}

    returns = [
        _num((r.get("consensus") or {}).get("return_1y"))
        for r in universe
        if _num((r.get("consensus") or {}).get("return_1y")) is not None
    ]
    advancing = sum(1 for r in returns if r > 0)
    breadth = round((advancing / len(returns)) * 100.0, 1) if returns else None
    median_return = _median(returns)
    median_pe = _median([r.get("pe") for r in universe])
    median_upside = _median([(r.get("consensus") or {}).get("upside") for r in universe])

    if breadth is None:
        stance = "Unknown"
    elif breadth >= 60 and (median_return or 0) > 5:
        stance = "Risk On"
    elif breadth <= 40:
        stance = "Risk Off"
    else:
        stance = "Mixed"

    # Strategy suitability follows the regime, not a fixed opinion.
    def stars(n: int) -> int:
        return max(1, min(5, n))

    risk_on = stance == "Risk On"
    risk_off = stance == "Risk Off"
    suitability = [
        {
            "strategy": "Long / Short Equity",
            "stars": stars(5 if stance == "Mixed" else 4),
            "why": "Pays on dispersion, which is widest when the market is not moving as one.",
        },
        {
            "strategy": "Momentum / CTA Trend",
            "stars": stars(5 if risk_on else 2),
            "why": "Needs sustained direction; chops up in range-bound tape.",
        },
        {
            "strategy": "Equity Market Neutral",
            "stars": stars(4 if not risk_off else 3),
            "why": "Independent of direction, but vulnerable to factor unwinds in stress.",
        },
        {
            "strategy": "Value / Deep Value",
            "stars": stars(4 if median_pe and median_pe > 25 else 3),
            "why": "Dispersion in multiples creates the gap value strategies close.",
        },
        {
            "strategy": "Merger Arbitrage",
            "stars": stars(2 if risk_off else 3),
            "why": "Spread capture depends on deals closing and credit staying open.",
        },
        {
            "strategy": "Distressed",
            "stars": stars(4 if risk_off else 2),
            "why": "Feeds on forced selling, which only appears under stress.",
        },
    ]

    return {
        "ok": True,
        "stance": stance,
        "breadth_advancing_pct": breadth,
        "median_return_1y_pct": median_return,
        "median_pe": median_pe,
        "median_consensus_upside_pct": median_upside,
        "universe": len(universe),
        "strategy_suitability": suitability,
        "note": (
            "Regime is derived from the covered universe's own breadth, returns and "
            "valuation, not from an external macro feed."
        ),
    }


# ---------------------------------------------------------------------------
# Scanners
# ---------------------------------------------------------------------------
def _scan_value(universe, medians, limit) -> list[dict[str, Any]]:
    out = []
    for row in universe:
        industry = row.get("primary_industry")
        med = medians.get(industry) or {}
        if (med.get("count") or 0) < 5:
            continue
        metric = _primary_metric(row.get("industry_dna"))
        value, benchmark = _sane(row, metric), _num(med.get(metric))
        roe, roe_med = _sane(row, "roe"), _num(med.get("roe"))
        if value is None or not benchmark or value <= 0:
            continue
        discount = round(((value / benchmark) - 1.0) * 100.0, 1)
        if discount > -25:
            continue
        # A cheap multiple with sub-par returns is a trap, not value.
        trap = roe is not None and roe_med is not None and roe < roe_med
        out.append(
            {
                **_base(row),
                "metric": metric,
                "value": value,
                "industry_median": benchmark,
                "discount_pct": discount,
                "roe": roe,
                "industry_median_roe": roe_med,
                "classification": "Potential value trap" if trap else "Deep value",
                "why": (
                    f"Trades at {value} on {metric.upper()} against an industry median of "
                    f"{benchmark}, a {abs(discount)}% discount"
                    + (
                        f", but return on equity of {roe}% is below the industry's {roe_med}% — "
                        "the discount may be deserved."
                        if trap
                        else f", while return on equity of {roe}% is at or above the industry's "
                        f"{roe_med}%." if roe is not None and roe_med is not None
                        else "."
                    )
                ),
            }
        )
    out.sort(key=lambda r: r["discount_pct"])
    return out[:limit]


def _scan_quality(universe, medians, limit) -> list[dict[str, Any]]:
    out = []
    for row in universe:
        roe = _sane(row, "roe")
        margin = _sane(row, "profit_margin")
        debt = _sane(row, "debt_to_equity")
        if roe is None or margin is None or roe < 15 or margin < 10:
            continue
        if debt is not None and debt > 150:
            continue
        out.append(
            {
                **_base(row),
                "roe": roe,
                "profit_margin": margin,
                "debt_to_equity": debt,
                "quality_score": round(min(100.0, roe + margin / 2 - (debt or 0) / 20), 1),
                "why": (
                    f"Return on equity of {roe}% on a {margin}% net margin"
                    + (f" with debt/equity at {debt}" if debt is not None else "")
                    + " — the profitability profile institutions screen for."
                ),
            }
        )
    out.sort(key=lambda r: -r["quality_score"])
    return out[:limit]


def _scan_momentum(universe, medians, limit) -> list[dict[str, Any]]:
    out = []
    for row in universe:
        consensus = row.get("consensus") or {}
        r1 = _num(consensus.get("return_1y"))
        industry = row.get("primary_industry")
        med = (medians.get(industry) or {}).get("return_1y")
        if r1 is None or r1 < 35:
            continue
        relative = round(r1 - (_num(med) or 0.0), 1)
        if relative < 15:
            continue
        out.append(
            {
                **_base(row),
                "return_1y": r1,
                "return_3y": consensus.get("return_3y"),
                "industry_median_return_1y": med,
                "relative_strength": relative,
                "why": (
                    f"Up {r1}% over a year against an industry median of {med}%, "
                    f"a relative strength of {relative} points."
                ),
            }
        )
    out.sort(key=lambda r: -r["relative_strength"])
    return out[:limit]


def _scan_conviction(universe, medians, limit) -> list[dict[str, Any]]:
    out = []
    for row in universe:
        consensus = row.get("consensus") or {}
        coverage = _num(consensus.get("coverage")) or 0
        buy = _num(consensus.get("buy_count")) or 0
        upside = _num(consensus.get("upside"))
        if coverage < 8 or upside is None:
            continue
        share = round((buy / coverage) * 100.0, 1) if coverage else 0.0
        if share < 60:
            continue
        out.append(
            {
                **_base(row),
                "buy_share_pct": share,
                "buy": buy,
                "consensus_upside": upside,
                "why": (
                    f"{int(buy)} of {int(coverage)} brokers positive ({share}%) with "
                    f"{upside}% implied upside — high sell-side conviction, which is an "
                    "expectation to test rather than accept."
                ),
            }
        )
    out.sort(key=lambda r: -(r["buy_share_pct"] * (r["consensus_upside"] or 0)))
    return out[:limit]


def _scan_stress(universe, medians, limit) -> list[dict[str, Any]]:
    out = []
    for row in universe:
        debt = _sane(row, "debt_to_equity")
        margin = _sane(row, "profit_margin")
        r1 = _num((row.get("consensus") or {}).get("return_1y"))
        flags = []
        if debt is not None and debt > 150:
            flags.append(f"debt/equity at {debt}")
        if margin is not None and margin < 0:
            flags.append(f"negative net margin of {margin}%")
        if r1 is not None and r1 < -20:
            flags.append(f"shares down {abs(r1)}% over a year")
        if len(flags) < 2:
            continue
        out.append(
            {
                **_base(row),
                "debt_to_equity": debt,
                "profit_margin": margin,
                "stress_flags": flags,
                "why": "Balance sheet and price both signalling stress: " + "; ".join(flags) + ".",
            }
        )
    out.sort(key=lambda r: -(len(r["stress_flags"])))
    return out[:limit]


def _scan_pairs(universe, medians, limit) -> list[dict[str, Any]]:
    """Cheapest against richest within the same industry — a market-neutral leg pair."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in universe:
        industry = row.get("primary_industry")
        metric = _primary_metric(row.get("industry_dna"))
        value = _sane(row, metric)
        if industry and value and value > 0:
            groups.setdefault(industry, []).append({**row, "_metric": metric, "_value": value})

    out = []
    for industry, members in groups.items():
        if len(members) < 6:
            continue
        members.sort(key=lambda m: m["_value"])
        cheap, rich = members[0], members[-1]
        spread = round((rich["_value"] / cheap["_value"]), 2)
        if spread < 2.0:
            continue
        metric = cheap["_metric"]
        out.append(
            {
                "industry": industry,
                "metric": metric,
                "long_leg": {
                    **_base(cheap),
                    "value": cheap["_value"],
                    "roe": cheap.get("roe"),
                },
                "short_leg": {
                    **_base(rich),
                    "value": rich["_value"],
                    "roe": rich.get("roe"),
                },
                "spread_multiple": spread,
                "industry_median": (medians.get(industry) or {}).get(metric),
                "peers": len(members),
                "why": (
                    f"Within {industry}, {cheap.get('company_name')} trades at "
                    f"{cheap['_value']} on {metric.upper()} while "
                    f"{rich.get('company_name')} trades at {rich['_value']} — a "
                    f"{spread}× spread across {len(members)} peers. A market-neutral "
                    "expression is long the cheaper leg against the richer one, provided "
                    "the gap is not explained by profitability."
                ),
                "caution": (
                    "Valuation gaps within an industry usually reflect real differences in "
                    "returns, growth or governance. Check those before treating the spread "
                    "as mispricing."
                ),
            }
        )
    out.sort(key=lambda r: -r["spread_multiple"])
    return out[:limit]


_SCANNERS = {
    "value": ("Value", _scan_value),
    "quality": ("Quality", _scan_quality),
    "momentum": ("Momentum", _scan_momentum),
    "conviction": ("Consensus conviction", _scan_conviction),
    "stress": ("Distressed / stress", _scan_stress),
    "pairs": ("Market-neutral pairs", _scan_pairs),
}


def scan(strategy: str, *, limit: int = 15, sector: Optional[str] = None) -> dict[str, Any]:
    key = str(strategy or "").strip().lower()
    if key not in _SCANNERS:
        return {"ok": False, "error": "unknown_scan", "available": sorted(_SCANNERS)}

    universe = _universe()
    if sector:
        universe = [r for r in universe if str(r.get("primary_sector") or "").lower() == sector.lower()]
    if not universe:
        return {"ok": False, "error": "universe_empty"}

    medians = _industry_medians(universe)
    label, fn = _SCANNERS[key]
    results = fn(universe, medians, max(1, min(50, int(limit or 15))))
    return {
        "ok": True,
        "scan": key,
        "label": label,
        "universe_scanned": len(universe),
        "results": results,
        "count": len(results),
        "sources": {
            "market_data": "yahoo_finance",
            "consensus": "capital_iq",
            "classification": "capital_iq_registry",
            "interpretation": "agi",
        },
        "policy": "Research observations only — no buy, sell or price target.",
    }


def daily_monitor(limit: int = 6) -> dict[str, Any]:
    """The evening sweep: what moved and what stands out today."""
    universe = _universe()
    if not universe:
        return {"ok": False, "error": "universe_empty"}
    medians = _industry_medians(universe)
    return {
        "ok": True,
        "regime": market_regime(),
        "sections": [
            {"id": key, "label": label, "results": fn(universe, medians, limit)}
            for key, (label, fn) in _SCANNERS.items()
        ],
        "universe": len(universe),
        "policy": "Research observations only — no buy, sell or price target.",
    }
