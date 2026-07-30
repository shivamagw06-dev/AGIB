"""Yahoo symbol resolution — NSE/BSE/US aliases → Yahoo tickers."""

from __future__ import annotations

import re

# Explicit NSE mappings for AGI tracked universe + common aliases
NSE_YAHOO: dict[str, str] = {
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "SBIN": "SBIN.NS",
    "AXISBANK": "AXISBANK.NS",
    "KOTAKBANK": "KOTAKBANK.NS",
    "INFY": "INFY.NS",
    "TCS": "TCS.NS",
    "WIPRO": "WIPRO.NS",
    "HCLTECH": "HCLTECH.NS",
    "TECHM": "TECHM.NS",
    "RELIANCE": "RELIANCE.NS",
    "ULTRACEMCO": "ULTRACEMCO.NS",
    "ASIANPAINT": "ASIANPAINT.NS",
    "TATASTEEL": "TATASTEEL.NS",
    "SUNPHARMA": "SUNPHARMA.NS",
    "POWERGRID": "POWERGRID.NS",
    "ITC": "ITC.NS",
    "HINDUNILVR": "HINDUNILVR.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "LT": "LT.NS",
    "M&M": "M&M.NS",
    "BAJFINANCE": "BAJFINANCE.NS",
    "NESTLEIND": "NESTLEIND.NS",
    "MARUTI": "MARUTI.NS",
    "TITAN": "TITAN.NS",
    "NTPC": "NTPC.NS",
    "ONGC": "ONGC.NS",
}

QUERY_ALIASES: dict[str, str] = {
    "hdfc bank": "HDFCBANK.NS",
    "hdfc": "HDFCBANK.NS",
    "infosys": "INFY.NS",
    "reliance": "RELIANCE.NS",
    "reliance industries": "RELIANCE.NS",
    "ultratech": "ULTRACEMCO.NS",
    "ultratech cement": "ULTRACEMCO.NS",
    "asian paints": "ASIANPAINT.NS",
    "tata steel": "TATASTEEL.NS",
    "sun pharma": "SUNPHARMA.NS",
    "power grid": "POWERGRID.NS",
    "tcs": "TCS.NS",
}


def to_yahoo_symbol(symbol: str | None, *, exchange: str = "NSE") -> str:
    """Map AGI ticker / query fragment to Yahoo symbol."""
    raw = (symbol or "").strip()
    if not raw:
        return ""
    # Already Yahoo-like
    if any(x in raw for x in (".", "=", "^")):
        return raw
    upper = raw.upper()
    if upper in NSE_YAHOO:
        return NSE_YAHOO[upper]
    lower = raw.lower()
    if lower in QUERY_ALIASES:
        return QUERY_ALIASES[lower]
    # Strip spaces
    compact = re.sub(r"\s+", "", upper)
    if compact in NSE_YAHOO:
        return NSE_YAHOO[compact]
    if exchange.upper() == "BSE":
        return f"{upper}.BO"
    if exchange.upper() in {"US", "NYSE", "NASDAQ"}:
        return upper
    # Default India NSE
    return f"{upper}.NS"


def from_yahoo_symbol(yahoo_symbol: str | None) -> str:
    """Strip exchange suffix for AGI canonical ticker."""
    s = (yahoo_symbol or "").strip().upper()
    if s.endswith(".NS") or s.endswith(".BO"):
        return s[:-3]
    return s
