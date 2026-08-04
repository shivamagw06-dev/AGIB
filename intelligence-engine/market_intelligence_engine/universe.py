"""Warehouse-backed market universe — one row per company with latest valuation."""

from __future__ import annotations

from typing import Any, Optional

from valuation_terminal.sector_lens import lens_for, is_meaningful

_SANE = {
    "pe": (2.0, 250.0),
    "pb": (0.05, 60.0),
    "ev_ebitda": (1.0, 100.0),
    "roe": (-80.0, 120.0),
    "dividend_yield": (0.0, 20.0),
}


def _num(value: Any) -> Optional[float]:
    try:
        if value is None or isinstance(value, bool):
            return None
        out = float(value)
        return None if out != out else out
    except (TypeError, ValueError):
        return None


def _sane(field: str, value: Any) -> Optional[float]:
    n = _num(value)
    if n is None:
        return None
    low, high = _SANE.get(field, (float("-inf"), float("inf")))
    return n if low <= n <= high else None


def load_universe(*, limit: int = 5000) -> dict[str, Any]:
    """Latest valuation snapshot joined to company_master and consensus."""
    from institutional_warehouse import db, store

    masters = store.all_rows("company_master", limit=limit)
    if not masters:
        return {"ok": False, "error": "no_companies", "rows": []}

    # Latest valuation date in warehouse.
    table = db.physical_table("historical_valuation")
    latest = db.query(f'SELECT MAX("date") AS d FROM {table}')
    val_date = (latest[0].get("d") if latest else None) or None
    valuations: dict[str, dict[str, Any]] = {}
    if val_date:
        for row in store.fetch("historical_valuation", filters={"date": val_date}, limit=limit)["rows"]:
            sym = str(row.get("symbol") or "").upper()
            if sym:
                valuations[sym] = row

    # Previous day for change detection.
    prev_date = None
    prev_vals: dict[str, dict[str, Any]] = {}
    if val_date:
        prior = db.query(
            f'SELECT MAX("date") AS d FROM {table} WHERE "date" < ?',
            (val_date,),
        )
        prev_date = prior[0].get("d") if prior else None
        if prev_date:
            for row in store.fetch("historical_valuation", filters={"date": prev_date}, limit=limit)["rows"]:
                sym = str(row.get("symbol") or "").upper()
                if sym:
                    prev_vals[sym] = row

    consensus_map: dict[str, dict[str, Any]] = {}
    for row in store.all_rows("consensus", limit=limit * 2):
        sym = str(row.get("symbol") or "").upper()
        if not sym:
            continue
        existing = consensus_map.get(sym)
        if not existing or str(row.get("consensus_date") or "") > str(existing.get("consensus_date") or ""):
            consensus_map[sym] = row

    rows: list[dict[str, Any]] = []
    for master in masters:
        sym = str(master.get("symbol") or "").upper()
        if not sym:
            continue
        val = valuations.get(sym) or {}
        prev = prev_vals.get(sym) or {}
        consensus = consensus_map.get(sym) or {}
        industry_dna = master.get("industry_dna") or master.get("industry")
        lens = lens_for(industry_dna, master.get("sector")) or {}
        primary = lens.get("primary_metric") or "pe"

        pe = _sane("pe", val.get("pe"))
        pb = _sane("pb", val.get("pb"))
        ev = _sane("ev_ebitda", val.get("ev_ebitda"))
        row = {
            "symbol": sym,
            "company_name": master.get("company_name") or sym,
            "sector": master.get("sector"),
            "industry": master.get("industry"),
            "industry_dna": industry_dna,
            "primary_metric": primary,
            "cmp": _num(val.get("cmp")),
            "market_cap": _num(val.get("market_cap")),
            "pe": pe,
            "pb": pb,
            "ev_ebitda": ev,
            "dividend_yield": _sane("dividend_yield", val.get("dividend_yield")),
            "percentile": _num(val.get("percentile")),
            "sector_median_pe": _num(val.get("sector_median")),
            "industry_median_pe": _num(val.get("industry_median")),
            "relative_score": _num(val.get("relative_valuation_score")),
            "prev_pe": _sane("pe", prev.get("pe")),
            "prev_pb": _sane("pb", prev.get("pb")),
            "pe_change_pct": _pct_change(prev.get("pe"), pe),
            "pb_change_pct": _pct_change(prev.get("pb"), pb),
            "consensus_target": _num(consensus.get("target_price")),
            "consensus_upside": _pct_change(val.get("cmp"), consensus.get("target_price")),
            "analyst_count": _num(consensus.get("analyst_count") or consensus.get("buy")),
            "valuation_date": val_date,
            "source": val.get("source") or "warehouse.historical_valuation",
        }
        row["primary_value"] = row.get(primary) if is_meaningful(primary, industry_dna) else pe
        rows.append(row)

    return {
        "ok": True,
        "valuation_date": val_date,
        "previous_date": prev_date,
        "count": len(rows),
        "rows": rows,
    }


def _pct_change(before: Any, after: Any) -> Optional[float]:
    try:
        start, end = float(before), float(after)
    except (TypeError, ValueError):
        return None
    if start == 0:
        return None
    return round(100.0 * (end - start) / abs(start), 2)
