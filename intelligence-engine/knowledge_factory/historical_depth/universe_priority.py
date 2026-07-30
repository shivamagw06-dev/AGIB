"""Supported listed-company universe with smart backfill prioritisation."""

from __future__ import annotations

from typing import Any


def _tickers_from_rows(rows: list[dict[str, Any]] | list[Any]) -> list[str]:
    out: list[str] = []
    for r in rows:
        if isinstance(r, dict):
            t = str(r.get("ticker") or "").upper()
        else:
            t = str(r or "").upper()
        if t:
            out.append(t)
    return out


def nifty_50() -> list[str]:
    try:
        from institutional_reasoning.fundamentals.universe import NIFTY_50

        return list(NIFTY_50)
    except Exception:
        try:
            from app.kc.universes import nifty50_tickers

            return sorted(nifty50_tickers())
        except Exception:
            return ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY"]


def nifty_next_50() -> list[str]:
    try:
        from app.kc.universes import nifty_next50_tickers

        return sorted(nifty_next50_tickers())
    except Exception:
        try:
            from institutional_reasoning.fundamentals.universe import NIFTY_100_EXTRA

            return list(NIFTY_100_EXTRA)[:50]
        except Exception:
            return []


def nifty_500() -> list[str]:
    try:
        from knowledge_factory.coverage import NIFTY_500

        return list(NIFTY_500)
    except Exception:
        try:
            from institutional_reasoning.fundamentals.nifty500_universe import NIFTY_500 as N5

            return list(N5)
        except Exception:
            return list(dict.fromkeys([*nifty_50(), *nifty_next_50()]))


def nse_listed() -> list[str]:
    """Full NSE cash equities available for trading (EQUITY_L → NIFTYstocks)."""
    try:
        from trading_universe.loader import list_symbols

        return list_symbols()
    except Exception:
        return []


def supported_universe() -> list[str]:
    """Full supported listed set: Nifty 500 ∪ NSE EQUITY_L trading book."""
    return list(dict.fromkeys([*nifty_500(), *nse_listed()]))


def priority_tier(symbol: str) -> int:
    """Lower number = higher priority. 1=Nifty50 … 5=BSE-only residual."""
    s = symbol.upper()
    n50 = set(nifty_50())
    if s in n50:
        return 1
    nnext = set(nifty_next_50())
    if s in nnext:
        return 2
    n500 = set(nifty_500())
    if s in n500:
        return 3
    nse = set(nse_listed())
    if s in nse:
        return 4
    return 5


def prioritised_universe(*, coverage_years: dict[str, float] | None = None) -> list[str]:
    """Nifty50 → Next50 → Nifty500 → residual; within tier lowest coverage first."""
    coverage_years = coverage_years or {}
    universe = supported_universe()
    return sorted(
        universe,
        key=lambda s: (
            priority_tier(s),
            float(coverage_years.get(s.upper(), 0.0)),
            s,
        ),
    )


def tier_label(tier: int) -> str:
    return {
        1: "nifty_50",
        2: "nifty_next_50",
        3: "nifty_500",
        4: "nse_listed",
        5: "bse_only",
    }.get(tier, "other")
