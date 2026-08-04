"""Sector historical percentile — rank today's sector median in its own history.

Expected pipeline:

  Company historical PE → daily sector median → historical series
  → rank(today's median) → sector historical percentile

Polarity matches HVIE company stats: higher percentile = more expensive vs history.
Does NOT use cross-sectional peer ranks (those median to ~50 by construction).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Optional

from historical_valuation_intelligence.models import ENGINE_CODE, VERSION
from historical_valuation_intelligence.statistics import _num, _percentile_of

# Institutional floor — below this, return Unavailable (never invent 50).
MIN_SECTOR_HISTORY_OBS = 24

# One-pass reconstruction cache: metric → {sector → points}.
# Cleared only for tests via clear_reconstruction_cache().
_RECON_CACHE: dict[str, dict[str, list[dict[str, Any]]]] = {}


def clear_reconstruction_cache() -> None:
    """Test helper — drop in-process reconstruction cache."""
    _RECON_CACHE.clear()


def load_sector_median_series(
    sector: str,
    *,
    metric: str = "pe",
    limit: int = 5000,
) -> dict[str, Any]:
    """Load historical sector median time series for percentile ranking.

    Preference order:
      1. warehouse.historical_sector_medians (HVIE weekly persist)
      2. Reconstruct from warehouse.historical_valuation daily PE medians
    """
    sector_name = str(sector or "").strip()
    if not sector_name:
        return {"ok": False, "error": "sector_required", "points": [], "source": None}

    points = _from_persisted_medians(sector_name, metric=metric, limit=limit)
    source = "warehouse.historical_sector_medians"
    if len(points) < MIN_SECTOR_HISTORY_OBS:
        rebuilt = _reconstruct_from_valuation(sector_name, metric=metric, limit=limit)
        if len(rebuilt) > len(points):
            points = rebuilt
            source = "warehouse.historical_valuation.reconstructed_sector_median"

    values = [p["value"] for p in points]
    return {
        "ok": True,
        "sector": sector_name,
        "metric": metric,
        "points": points,
        "values": values,
        "observation_count": len(points),
        "first_observation": points[0]["period"] if points else None,
        "last_observation": points[-1]["period"] if points else None,
        "source": source if points else None,
        "engine": ENGINE_CODE,
        "version": VERSION,
    }


def sector_historical_percentile(
    sector: str,
    *,
    current_median: Optional[float] = None,
    metric: str = "pe",
    min_obs: int = MIN_SECTOR_HISTORY_OBS,
) -> dict[str, Any]:
    """Rank today's sector median within the historical sector-median series.

    Returns historical_percentile=None with reason when history is insufficient.
    Never defaults to 50.
    """
    series = load_sector_median_series(sector, metric=metric)
    values = list(series.get("values") or [])
    points = list(series.get("points") or [])
    current = _num(current_median)
    if current is None and values:
        current = values[-1]

    obs = len(values)
    if obs < max(1, int(min_obs)):
        return {
            "ok": True,
            "sector": series.get("sector") or sector,
            "metric": metric,
            "historical_percentile": None,
            "current_median": current,
            "historical_median": None,
            "historical_min": min(values) if values else None,
            "historical_max": max(values) if values else None,
            "observation_count": obs,
            "first_observation": series.get("first_observation"),
            "last_observation": series.get("last_observation"),
            "sufficient": False,
            "status": "INSUFFICIENT_HISTORY",
            "reason": (
                f"Insufficient history — observed {obs} sector medians; "
                f"need ≥{min_obs}."
            ),
            "source": series.get("source"),
            "engine": ENGINE_CODE,
            "version": VERSION,
        }

    # Include current in ranking set when it is today's live median (not already last point).
    rank_values = list(values)
    if current is not None:
        # Replace last point with live current when dating matches, else append.
        last_period = points[-1]["period"] if points else None
        from datetime import date

        today = date.today().isoformat()
        if last_period == today:
            rank_values[-1] = current
        else:
            rank_values.append(current)

    pct = _percentile_of(current, rank_values) if current is not None else None
    hist_median = sorted(values)[len(values) // 2] if values else None
    try:
        import statistics as stats

        hist_median = stats.median(values) if values else None
    except Exception:
        pass

    return {
        "ok": True,
        "sector": series.get("sector") or sector,
        "metric": metric,
        "historical_percentile": pct,
        "current_median": current,
        "historical_median": round(hist_median, 4) if hist_median is not None else None,
        "historical_min": round(min(values), 4),
        "historical_max": round(max(values), 4),
        "observation_count": obs,
        "first_observation": series.get("first_observation"),
        "last_observation": series.get("last_observation"),
        "sufficient": True,
        "status": "OK",
        "reason": None,
        "source": series.get("source"),
        "definition": (
            "Rank of today's sector median within the historical sector-median "
            "time series (HVIE polarity: higher = more expensive vs history)."
        ),
        "engine": ENGINE_CODE,
        "version": VERSION,
    }


def _paged_warehouse_rows(tab_id: str, *, max_rows: int = 100_000) -> list[dict[str, Any]]:
    """Page past store.MAX_LIMIT (5000). ``all_rows(limit=50000)`` silently clamps."""
    try:
        from institutional_warehouse import store
    except Exception:
        return []

    page_size = 5000
    offset = 0
    out: list[dict[str, Any]] = []
    while offset < max_rows:
        try:
            page = store.fetch(tab_id, limit=page_size, offset=offset)
        except Exception:
            break
        rows = page.get("rows") or []
        if not rows:
            break
        out.extend(rows)
        total = int(page.get("total") or 0)
        offset += len(rows)
        if offset >= total or len(rows) < page_size:
            break
    return out


def _from_persisted_medians(sector: str, *, metric: str, limit: int) -> list[dict[str, Any]]:
    try:
        from institutional_warehouse import store
    except Exception:
        return []
    try:
        rows = store.fetch(
            "historical_sector_medians",
            filters={"sector": sector, "metric": metric},
            limit=limit,
        ).get("rows") or []
    except Exception:
        rows = []
    # Soft case-insensitive match if exact filter missed aliases
    if not rows:
        try:
            all_rows = _paged_warehouse_rows("historical_sector_medians", max_rows=max(limit, 50_000))
            rows = [
                r for r in all_rows
                if str(r.get("sector") or "").strip().lower() == sector.lower()
                and str(r.get("metric") or "pe").lower() == metric.lower()
            ]
        except Exception:
            rows = []
    points: list[dict[str, Any]] = []
    seen: set[str] = set()
    for r in sorted(rows, key=lambda x: str(x.get("as_of") or "")):
        period = str(r.get("as_of") or "")[:10]
        val = _num(r.get("median_value"))
        if not period or val is None or val <= 0 or period in seen:
            continue
        seen.add(period)
        points.append({"period": period, "value": val, "company_count": r.get("company_count")})
    return points


def _reconstruct_from_valuation(sector: str, *, metric: str, limit: int) -> list[dict[str, Any]]:
    """Build daily sector medians from historical_valuation when persist table is thin."""
    by_sector = _reconstruct_all_sectors(metric=metric)
    points = list(by_sector.get(sector.lower()) or [])
    return points[-limit:]


def _reconstruct_all_sectors(*, metric: str) -> dict[str, list[dict[str, Any]]]:
    """One-pass scan of historical_valuation → {sector_lower: dated median points}.

    Must page past warehouse MAX_LIMIT=5000. A single ``all_rows(limit=50000)``
    only returns 5k rows (~2 as-of dates at universe scale), which made every
    sector report INSUFFICIENT_HISTORY after the peer-rank heatmap fix.
    """
    metric_key = str(metric or "pe").lower()
    cached = _RECON_CACHE.get(metric_key)
    if cached is not None:
        return cached

    try:
        import statistics as stats
    except Exception:
        _RECON_CACHE[metric_key] = {}
        return _RECON_CACHE[metric_key]

    masters = {
        str(r.get("symbol") or "").upper(): str(r.get("sector") or "").strip()
        for r in _paged_warehouse_rows("company_master", max_rows=20_000)
        if str(r.get("symbol") or "").strip() and str(r.get("sector") or "").strip()
    }
    if not masters:
        _RECON_CACHE[metric_key] = {}
        return _RECON_CACHE[metric_key]

    rows = _paged_warehouse_rows("historical_valuation", max_rows=200_000)
    # sector_lower → date → values
    by_sector_date: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        sym = str(r.get("symbol") or "").upper()
        sector = masters.get(sym)
        if not sector:
            continue
        period = str(r.get("date") or r.get("as_of") or "")[:10]
        val = _num(r.get(metric_key) if metric_key in r else r.get(metric))
        if not period or val is None or val <= 0:
            continue
        by_sector_date[sector.lower()][period].append(val)

    out: dict[str, list[dict[str, Any]]] = {}
    for sector_key, by_date in by_sector_date.items():
        points: list[dict[str, Any]] = []
        for period in sorted(by_date):
            vals = by_date[period]
            if len(vals) < 2:
                continue
            points.append({
                "period": period,
                "value": round(stats.median(vals), 4),
                "company_count": len(vals),
            })
        out[sector_key] = points

    _RECON_CACHE[metric_key] = out
    return out
