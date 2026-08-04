"""API-facing HVIE surface."""

from __future__ import annotations

from typing import Any, Optional

from historical_valuation_intelligence import compute, engine
from historical_valuation_intelligence.models import ENGINE_CODE, VERSION


def health() -> dict[str, Any]:
    return {
        "ok": True,
        "engine": ENGINE_CODE,
        "version": VERSION,
        "role": "institutional_historical_valuation_source_of_truth",
        "vendor_historical_ratios": False,
        "reconstruction": "prices + statements + corporate actions + VPAE",
        "windows": ["1y", "3y", "5y", "10y", "15y", "20y", "max"],
        "gates": ["valuation_policy"],
        "endpoints": [
            "/v1/historical-valuation/health",
            "/v1/historical-valuation/company/{symbol}",
            "/v1/historical-valuation/history/{symbol}",
            "/v1/historical-valuation/statistics/{symbol}",
            "/v1/historical-valuation/bands/{symbol}",
            "/v1/historical-valuation/percentiles/{symbol}",
            "/v1/historical-valuation/regimes/{symbol}",
            "/v1/historical-valuation/rerating/{symbol}",
            "/v1/historical-valuation/coverage/{symbol}",
            "/v1/historical-valuation/reconstruct/{symbol}",
        ],
    }


def company(symbol: str, *, metric: Optional[str] = None, window: str = "10y") -> dict[str, Any]:
    return engine.company_pack(symbol, metric=metric, window=window)


def history(
    symbol: str,
    *,
    metric: Optional[str] = None,
    window: str = "max",
    limit: int = 5000,
) -> dict[str, Any]:
    return engine.history_for(symbol, metric=metric, window=window, limit=limit)


def statistics(
    symbol: str,
    *,
    metric: str = "pe",
    window: Optional[str] = None,
) -> dict[str, Any]:
    return engine.statistics_for(symbol, metric=metric, window=window)


def bands(symbol: str, *, metric: str = "pe", window: str = "max") -> dict[str, Any]:
    return engine.bands_for(symbol, metric=metric, window=window)


def percentiles(symbol: str, *, metric: str = "pe") -> dict[str, Any]:
    return engine.percentiles_for(symbol, metric=metric)


def regimes(symbol: str, *, metric: str = "pe", window: str = "max") -> dict[str, Any]:
    return engine.regimes_for(symbol, metric=metric, window=window)


def rerating(symbol: str, *, metric: str = "pe", window: str = "max") -> dict[str, Any]:
    return engine.rerating_for(symbol, metric=metric, window=window)


def coverage(symbol: str, *, metric: Optional[str] = None) -> dict[str, Any]:
    return engine.coverage_for(symbol, metric=metric)


def reconstruct(
    symbol: str,
    *,
    cadence: str = "daily",
    start: Optional[str] = None,
    end: Optional[str] = None,
    incremental: bool = False,
) -> dict[str, Any]:
    if incremental:
        return compute.incremental_price_update(symbol)
    return compute.reconstruct(symbol, cadence=cadence, start=start, end=end)
