"""Primitive market series for risk derivations (deterministic fixtures).

Returns are synthetic monthly series seeded by ticker so tests and offline
packs remain reproducible. Production should replace with live OHLC feeds.

Calibrated roughly to equity-like annualised vol (~18–28%) and beta near 1.
"""

from __future__ import annotations

from typing import Any


def _mix(bench: list[float], idio: list[float], beta: float) -> list[float]:
    """asset ≈ beta * bench + idiosyncratic residual (percent)."""
    return [round(beta * b + e, 4) for b, e in zip(bench, idio)]


# Benchmark ~22% ann vol → monthly stdev ≈ 6.4%.
_BENCHMARK = [
    5.2, -4.1, 7.8, 2.1, -6.4, 8.5, 3.6, -7.2, 5.9, 6.4, -3.2, 8.1,
    2.8, -5.5, 6.9, -2.4, 9.1, 1.5, -6.8, 5.4, 4.2, -4.0, 7.3, 4.6,
]

_IDIO: dict[str, tuple[float, list[float]]] = {
    "INFY": (
        0.95,
        [1.1, -0.8, 1.4, -0.5, 0.9, 1.6, -1.0, 0.6, -0.4, 1.2, -0.7, 1.0,
         0.5, -0.9, 0.8, -0.5, 1.3, -0.3, 0.6, -0.8, 1.0, -0.5, 0.7, 0.3],
    ),
    "TCS": (
        0.88,
        [0.6, -0.5, 0.8, -0.3, 0.5, 1.0, -0.7, 0.4, -0.5, 0.7, -0.3, 0.6,
         0.3, -0.7, 0.5, -0.3, 0.8, 0.0, 0.4, -0.5, 0.5, -0.3, 0.5, 0.2],
    ),
    "HCLTECH": (
        1.05,
        [1.5, -1.3, 1.8, -0.8, 1.1, 2.0, -1.5, 0.9, -0.6, 1.5, -1.0, 1.3,
         0.8, -1.3, 1.1, -0.8, 1.8, -0.5, 0.8, -1.1, 1.3, -0.8, 1.1, 0.5],
    ),
    "WIPRO": (
        1.10,
        [1.3, -1.5, 1.1, -1.0, 0.8, 1.4, -1.3, 0.6, -0.8, 1.1, -1.3, 0.9,
         0.6, -1.1, 0.8, -0.8, 1.3, -0.5, 0.6, -1.3, 0.8, -1.0, 1.0, 0.3],
    ),
    "TECHM": (
        1.15,
        [1.8, -1.8, 1.5, -1.3, 1.3, 2.0, -1.8, 1.0, -1.0, 1.5, -1.5, 1.3,
         1.0, -1.5, 1.3, -1.0, 1.8, -0.8, 0.8, -1.5, 1.3, -1.3, 1.5, 0.5],
    ),
    "HDFCBANK": (
        1.05,
        [0.8, -0.5, 1.0, 0.3, -0.8, 1.2, -0.5, 0.5, 0.3, 0.8, -0.3, 1.0,
         0.5, -0.8, 0.8, -0.3, 1.0, 0.3, -0.5, 0.5, 0.5, -0.3, 0.8, 0.5],
    ),
    "ICICIBANK": (
        1.15,
        [1.3, -1.0, 1.5, 0.5, -1.3, 1.8, -0.8, 0.8, 0.5, 1.3, -0.5, 1.5,
         0.8, -1.0, 1.3, -0.5, 1.5, 0.3, -0.8, 1.0, 0.8, -0.5, 1.3, 0.8],
    ),
    "RELIANCE": (
        1.10,
        [1.5, -1.3, 1.3, -0.5, 1.0, 1.8, -1.0, 0.8, -0.8, 1.3, -1.0, 1.5,
         0.8, -1.3, 1.0, -0.8, 1.5, -0.3, 0.5, -1.0, 1.0, -0.8, 1.3, 0.5],
    ),
    "ZOMATO": (
        1.40,
        [4.5, -5.5, 5.2, -3.8, 4.8, -4.5, 3.5, -6.0, 4.0, -3.0, 5.5, -4.2,
         3.2, -4.8, 4.5, -3.5, 5.8, -4.5, 2.8, -5.2, 4.2, -3.6, 5.0, -2.5],
    ),
}

_MONTHLY_RETURNS: dict[str, list[float]] = {
    t: _mix(_BENCHMARK, idio, beta) for t, (beta, idio) in _IDIO.items()
}


def monthly_returns(ticker: str) -> list[float] | None:
    key = ticker.upper()
    return list(_MONTHLY_RETURNS[key]) if key in _MONTHLY_RETURNS else None


def benchmark_returns() -> list[float]:
    return list(_BENCHMARK)


def risk_primitives(ticker: str) -> dict[str, Any] | None:
    rets = monthly_returns(ticker)
    if not rets:
        return None
    return {
        "ticker": ticker.upper(),
        "monthly_returns": rets,
        "benchmark_returns": benchmark_returns(),
        "horizon_months": len(rets),
        "currency": "INR",
    }
