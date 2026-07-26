"""Optional yfinance soft path for Yahoo financial statements / valuation.

Uses Ticker.get_income_stmt / get_balance_sheet / get_cash_flow (fundamentals-timeseries)
when quoteSummary crumb auth fails under plain httpx. Never exposes Yahoo-native payloads
outward — callers must map through yahoo_mapper canonical helpers.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

_EXEC = ThreadPoolExecutor(max_workers=2, thread_name_prefix="yahoo-yf")


def yfinance_available() -> bool:
    try:
        import yfinance  # noqa: F401

        return True
    except Exception:
        return False


def _df_to_period_rows(df: Any) -> list[dict[str, Any]]:
    """Convert yfinance statement DataFrame (rows=fields, cols=dates) → period dicts."""
    if df is None:
        return []
    try:
        import pandas as pd
    except Exception:
        return []
    if not isinstance(df, pd.DataFrame) or df.empty:
        return []

    rows: list[dict[str, Any]] = []
    for col in df.columns:
        if hasattr(col, "strftime"):
            end = col.strftime("%Y-%m-%d")
        else:
            end = str(col)[:10]
        period: dict[str, Any] = {"endDate": end}
        for field in df.index:
            try:
                val = df.at[field, col]
            except Exception:
                continue
            if val is None:
                continue
            try:
                if pd.isna(val):
                    continue
            except Exception:
                pass
            name = str(field)
            # Yahoo timeseries keys are PascalCase; quoteSummary aliases are camelCase.
            # All-caps acronyms (EBITDA, EBIT) become lowercase so field maps match.
            try:
                num = float(val)
            except (TypeError, ValueError):
                continue
            if name and name.isupper():
                period[name.lower()] = num
            elif name:
                period[name[0].lower() + name[1:]] = num
            else:
                continue
        if len(period) > 1:
            rows.append(period)
    # Newest first (matches quoteSummary history ordering expectations)
    rows.sort(key=lambda r: r.get("endDate") or "", reverse=True)
    return rows


def _fetch_package_sync(yahoo_symbol: str) -> dict[str, Any]:
    import yfinance as yf

    t = yf.Ticker(yahoo_symbol)
    income_annual = _df_to_period_rows(t.get_income_stmt(as_dict=False, pretty=False, freq="yearly"))
    income_q = _df_to_period_rows(t.get_income_stmt(as_dict=False, pretty=False, freq="quarterly"))
    balance_annual = _df_to_period_rows(t.get_balance_sheet(as_dict=False, pretty=False, freq="yearly"))
    balance_q = _df_to_period_rows(t.get_balance_sheet(as_dict=False, pretty=False, freq="quarterly"))
    cash_annual = _df_to_period_rows(t.get_cash_flow(as_dict=False, pretty=False, freq="yearly"))
    cash_q = _df_to_period_rows(t.get_cash_flow(as_dict=False, pretty=False, freq="quarterly"))

    info: dict[str, Any] = {}
    try:
        raw = t.info or {}
        if isinstance(raw, dict):
            info = raw
    except Exception:
        info = {}

    return {
        "source": "yfinance",
        "endpoint": "fundamentals-timeseries",
        "symbol": yahoo_symbol,
        "income_annual": income_annual,
        "income_quarterly": income_q,
        "balance_annual": balance_annual,
        "balance_quarterly": balance_q,
        "cash_annual": cash_annual,
        "cash_quarterly": cash_q,
        "info": info,
    }


async def fetch_yfinance_financial_package(yahoo_symbol: str) -> dict[str, Any]:
    """
    Async wrapper around yfinance Ticker statement APIs.
    Returns empty dict if yfinance missing or fetch fails.
    """
    if not yahoo_symbol or not yfinance_available():
        return {}
    import asyncio

    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(_EXEC, _fetch_package_sync, yahoo_symbol)
    except Exception:
        return {}
