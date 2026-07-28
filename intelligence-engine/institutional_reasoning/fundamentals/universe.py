"""Universe coverage registry — explicit Nifty/global coverage reporting.

Tracks which symbols have primitives, risk series, or are declared but
uncovered. Soft registry only — does not invent live quotes.
"""

from __future__ import annotations

from typing import Any

from institutional_reasoning.fundamentals.market_series import monthly_returns
from institutional_reasoning.fundamentals.primitives import covered_entities, has_primitives

UNIVERSE_VERSION = "universe-coverage-v1.0.0"

# Starter Nifty-50 subset — expand toward 100/500/global without claiming coverage.
NIFTY_50: tuple[str, ...] = (
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "ITC", "BHARTIARTL",
    "SBIN", "HINDUNILVR", "LT", "BAJFINANCE", "HCLTECH", "AXISBANK", "MARUTI",
    "SUNPHARMA", "TITAN", "ULTRACEMCO", "NTPC", "POWERGRID", "ASIANPAINT",
    "WIPRO", "NESTLEIND", "M&M", "TATASTEEL", "ADANIENT", "JSWSTEEL", "ONGC",
    "COALINDIA", "TECHM", "BAJAJFINSV", "ADANIPORTS", "TATAMOTORS", "INDUSINDBK",
    "CIPLA", "GRASIM", "BPCL", "HINDALCO", "DRREDDY", "EICHERMOT", "APOLLOHOSP",
    "SBILIFE", "HDFCLIFE", "DIVISLAB", "BRITANNIA", "HEROMOTOCO", "TATACONSUM",
    "BAJAJ-AUTO", "SHRIRAMFIN", "TRENT", "BEL",
)

NIFTY_100_EXTRA: tuple[str, ...] = (
    "ZOMATO", "PERSISTENT", "DMART", "PIDILITIND", "HAVELLS", "SIEMENS",
    "DLF", "GODREJCP", "AMBUJACEM", "ICICIPRULI", "NAUKRI", "INDIGO",
    "ABB", "ADANIGREEN", "ALKEM", "AUROPHARMA", "BANKBARODA", "BOSCHLTD",
    "CANBK", "CHOLAFIN", "COLPAL", "DABUR", "HAL", "ICICIGI",
    "INDHOTEL", "IOC", "IRCTC", "JINDALSTEL", "LTIM", "LUPIN",
    "MARICO", "MAXHEALTH", "MUTHOOTFIN", "NHPC", "NMDC", "OFSS",
    "PAGEIND", "PETRONET", "PFC", "POLYCAB", "RECLTD", "SAIL",
    "SBICARD", "SHREECEM", "SRF", "TVSMOTOR", "VBL", "YESBANK",
    "ZYDUSLIFE", "BERGEPAINT",
)

GLOBAL_SEED: tuple[str, ...] = (
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK.B", "JPM", "V", "UNH",
)

TIERS = ("nifty_50", "nifty_100", "nifty_500", "global")


def _status(ticker: str) -> dict[str, Any]:
    t = ticker.upper()
    prim = has_primitives(t)
    risk = monthly_returns(t) is not None
    if prim and risk:
        level = "full"
    elif prim:
        level = "fundamentals"
    elif risk:
        level = "risk_only"
    else:
        level = "uncovered"
    return {
        "ticker": t,
        "primitives": prim,
        "risk_series": risk,
        "coverage": level,
    }


def coverage_for(ticker: str) -> dict[str, Any]:
    return {
        "universe_version": UNIVERSE_VERSION,
        **_status(ticker),
    }


def tier_report(tier: str = "nifty_50") -> dict[str, Any]:
    tier = tier.lower()
    if tier == "nifty_50":
        symbols = NIFTY_50
    elif tier == "nifty_100":
        symbols = tuple(dict.fromkeys([*NIFTY_50, *NIFTY_100_EXTRA]))
    elif tier == "nifty_500":
        # Explicit: 500 not fully seeded — report declared + known coverage only.
        symbols = tuple(dict.fromkeys([*NIFTY_50, *NIFTY_100_EXTRA, *covered_entities()]))
    elif tier == "global":
        symbols = tuple(dict.fromkeys([*NIFTY_50, *NIFTY_100_EXTRA, *GLOBAL_SEED, *covered_entities()]))
    else:
        symbols = NIFTY_50

    rows = [_status(s) for s in symbols]
    by_level = {"full": 0, "fundamentals": 0, "risk_only": 0, "uncovered": 0}
    for r in rows:
        by_level[r["coverage"]] = by_level.get(r["coverage"], 0) + 1
    covered_n = by_level["full"] + by_level["fundamentals"] + by_level["risk_only"]
    return {
        "universe_version": UNIVERSE_VERSION,
        "tier": tier,
        "declared": len(symbols),
        "covered": covered_n,
        "coverage_pct": round(100.0 * covered_n / len(symbols), 2) if symbols else 0.0,
        "by_level": by_level,
        "primitive_entities": covered_entities(),
        "rows": rows,
        "honest_gap": {
            "nifty_500_full_panel": False,
            "global_live_quotes": False,
            "note": "Uncovered symbols are reported explicitly — never silently filled.",
        },
    }


def universe_health() -> dict[str, Any]:
    return {
        "status": "ok",
        "universe_version": UNIVERSE_VERSION,
        "tiers": {t: tier_report(t) for t in ("nifty_50", "nifty_100", "global")},
    }
