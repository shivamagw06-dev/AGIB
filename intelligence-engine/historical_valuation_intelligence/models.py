"""HVIE vocabulary and window definitions."""

from __future__ import annotations

ENGINE_CODE = "historical_valuation_intelligence_engine"
VERSION = "8.3"

# Spec windows — never assume 20y; MAX = listing history.
WINDOWS: dict[str, int | None] = {
    "1y": 365,
    "3y": 1095,
    "5y": 1826,
    "10y": 3652,
    "15y": 5479,
    "20y": 7305,
    "max": None,
}

METRICS = (
    "pe",
    "pb",
    "ev_ebitda",
    "ev_sales",
    "price_sales",
    "dividend_yield",
    "market_cap",
    "enterprise_value",
)

REGIME_BANDS = (
    (0, 20, "VERY_CHEAP"),
    (20, 40, "CHEAP"),
    (40, 60, "FAIR"),
    (60, 80, "EXPENSIVE"),
    (80, 101, "VERY_EXPENSIVE"),
)

MIN_STATS_OBS = 6
EXTREME_PE = 500.0
EXTREME_PB = 100.0
EXTREME_EV = 200.0
