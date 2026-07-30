"""Historical valuation bands (10Y PE/PB/EV-EBITDA) + current percentile."""

from __future__ import annotations

from typing import Any

from valuation_intelligence.schema import HistoricalBand


def _percentile_rank(series: list[float], current: float) -> float | None:
    if not series:
        return None
    below = sum(1 for v in series if v <= current)
    return round(100.0 * below / len(series), 1)


def band_from_series(series: list[float], current: float | None, *, window: str = "10Y", source: str = "computed") -> HistoricalBand | None:
    clean = [float(v) for v in series if isinstance(v, (int, float)) and v > 0]
    if len(clean) < 3:
        return None
    clean_sorted = sorted(clean)
    n = len(clean_sorted)
    median = clean_sorted[n // 2] if n % 2 == 1 else (clean_sorted[n // 2 - 1] + clean_sorted[n // 2]) / 2.0
    cur = float(current) if isinstance(current, (int, float)) else None
    return HistoricalBand(
        window=window,
        median=round(median, 2),
        high=round(max(clean_sorted), 2),
        low=round(min(clean_sorted), 2),
        current=cur,
        percentile=_percentile_rank(clean_sorted, cur) if cur is not None else None,
        observations=n,
        source=source,
    )


def _pe_from_historical_depth(symbol: str) -> list[float]:
    try:
        from knowledge_factory.historical_depth.producers.derived import produce_derived

        derived = produce_derived(symbol)
        pe = ((derived.get("metrics") or {}).get("PE") or {}).get("points") or {}
        if isinstance(pe, dict):
            return [float(v) for v in pe.values() if isinstance(v, (int, float)) and v > 0]
    except Exception:
        return []
    return []


def _pb_ev_from_historical_depth(symbol: str) -> tuple[list[float], list[float]]:
    pb_out: list[float] = []
    ev_out: list[float] = []
    try:
        from knowledge_factory.historical_depth.producers.derived import produce_derived

        derived = produce_derived(symbol)
        metrics = derived.get("metrics") or {}
        for key, bucket in (("PB", pb_out), ("EV_EBITDA", ev_out), ("EV/EBITDA", ev_out)):
            pts = (metrics.get(key) or {}).get("points") or {}
            if isinstance(pts, dict):
                for v in pts.values():
                    if isinstance(v, (int, float)) and v > 0:
                        bucket.append(float(v))
    except Exception:
        return [], []
    return pb_out, ev_out


def _pe_from_yahoo_annual(symbol: str, annual_eps: list[tuple[str, float]]) -> list[float]:
    """Approximate FY PE = year-end close / FY EPS using Yahoo monthly chart."""
    if not annual_eps:
        return []
    try:
        import json
        import urllib.request

        sym = f"{symbol.upper()}.NS"
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1mo&range=10y"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 AGIB-Valuation/1.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        result = (data.get("chart") or {}).get("result") or []
        if not result:
            return []
        ts = result[0].get("timestamp") or []
        closes = ((result[0].get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
        if not ts or not closes:
            return []
        # Map year → last available close in that calendar year
        by_year: dict[int, float] = {}
        for t, c in zip(ts, closes):
            if c is None:
                continue
            from datetime import datetime, timezone

            yr = datetime.fromtimestamp(int(t), tz=timezone.utc).year
            by_year[yr] = float(c)
        out: list[float] = []
        for period_end, eps in annual_eps:
            if eps in (None, 0):
                continue
            try:
                year = int(str(period_end)[:4])
            except (TypeError, ValueError):
                continue
            # Prefer year of period_end, else prior year close
            px = by_year.get(year) or by_year.get(year - 1)
            if px and eps > 0:
                out.append(round(px / eps, 4))
        return out
    except Exception:
        return []


def historical_bands_for_symbol(
    symbol: str,
    *,
    current_pe: float | None,
    current_pb: float | None,
    current_ev_ebitda: float | None,
    annual_eps: list[tuple[str, float]] | None = None,
    injected_series: dict[str, list[float]] | None = None,
) -> dict[str, HistoricalBand]:
    bands: dict[str, HistoricalBand] = {}
    key = (symbol or "").upper().replace(".NS", "").replace(".BO", "")

    if isinstance(injected_series, dict):
        for metric, series in injected_series.items():
            cur = {"pe": current_pe, "pb": current_pb, "ev_ebitda": current_ev_ebitda}.get(metric)
            band = band_from_series(list(series or []), cur, source="injected")
            if band is not None:
                bands[metric] = band
        if bands:
            return bands

    pe_series = _pe_from_historical_depth(key)
    source = "historical_depth"
    if len(pe_series) < 3:
        yahoo_pe = _pe_from_yahoo_annual(key, annual_eps or [])
        if len(yahoo_pe) >= 3:
            pe_series = yahoo_pe
            source = "yahoo_chart|earnings_eps"
    pe_band = band_from_series(pe_series, current_pe, source=source)
    if pe_band is not None:
        bands["pe"] = pe_band

    pb_series, ev_series = _pb_ev_from_historical_depth(key)
    pb_band = band_from_series(pb_series, current_pb, source="historical_depth")
    ev_band = band_from_series(ev_series, current_ev_ebitda, source="historical_depth")
    if pb_band is not None:
        bands["pb"] = pb_band
    if ev_band is not None:
        bands["ev_ebitda"] = ev_band

    return bands
