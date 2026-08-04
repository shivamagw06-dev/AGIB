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

    # Latest Upstox valuation_ratios (long format) → per-symbol packs.
    provider_map: dict[str, dict[str, dict[str, Any]]] = {}
    try:
        for row in store.all_rows("valuation_ratios", limit=limit * 8):
            sym = str(row.get("symbol") or "").upper()
            name = str(row.get("ratio_name") or "")
            if not sym or not name:
                continue
            pack = provider_map.setdefault(sym, {})
            prev = pack.get(name)
            if prev and str(prev.get("reported_date") or "") >= str(row.get("reported_date") or ""):
                continue
            pack[name] = row
    except Exception:
        provider_map = {}

    rows: list[dict[str, Any]] = []
    for master in masters:
        sym = str(master.get("symbol") or "").upper()
        if not sym:
            continue
        val = valuations.get(sym) or {}
        prev = prev_vals.get(sym) or {}
        consensus = consensus_map.get(sym) or {}
        provider = provider_map.get(sym) or {}
        industry_dna = master.get("industry_dna") or master.get("industry")
        # VPAE gate — instrument / loss-making / DNA before any sector aggregate.
        try:
            from valuation_policy import evaluate as vpae_evaluate

            policy = vpae_evaluate(
                sym,
                record={
                    "ok": True,
                    "symbol": sym,
                    "master": master,
                    "provider_ratios": {"ratios": provider},
                    "latest_annual": {},
                    "latest_price": {},
                },
            )
        except Exception:
            policy = {}
        if policy.get("ok"):
            industry_dna = (policy.get("company") or {}).get("industry_dna") or industry_dna
            lens = {
                "primary_metric": policy.get("primary_metric"),
                "primary_metric_label": policy.get("primary_model"),
                "supporting_metrics": policy.get("supporting_metrics") or [],
                "suppressed_metrics": policy.get("hidden_metrics") or [],
                "rationale": policy.get("reason"),
                "status": policy.get("status"),
                "confidence": policy.get("confidence"),
            }
        else:
            lens = lens_for(industry_dna, master.get("sector")) or {}
        primary = lens.get("primary_metric") or "pe"

        # Prefer Upstox provider ratios over sparse computed warehouse multiples.
        def _provider_or_val(metric: str) -> Optional[float]:
            block = provider.get(metric) or {}
            return _sane(metric, block.get("company_value")) if block else _sane(metric, val.get(metric))

        pe = _provider_or_val("pe")
        pb = _provider_or_val("pb")
        ev = _provider_or_val("ev_ebitda")
        roe = _provider_or_val("roe")
        roa = _num((provider.get("roa") or {}).get("company_value"))
        roce = _num((provider.get("roce") or {}).get("company_value"))
        # Sector benchmarks are Upstox-owned only — never fall back to warehouse
        # sector_median (that often equals the peer median and falsely looks like
        # an Upstox sector print with 0% premium).
        sector_pe = _num((provider.get("pe") or {}).get("sector_value"))
        sector_pb = _num((provider.get("pb") or {}).get("sector_value"))
        sector_ev = _num((provider.get("ev_ebitda") or {}).get("sector_value"))
        sector_roe = _num((provider.get("roe") or {}).get("sector_value"))
        has_provider = bool(provider)

        source = "upstox" if has_provider else (val.get("source") or "warehouse.historical_valuation")
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
            "roe": roe,
            "roa": roa,
            "roce": roce,
            "dividend_yield": _sane("dividend_yield", val.get("dividend_yield")),
            "percentile": _num(val.get("percentile")),
            "sector_median_pe": sector_pe,
            "sector_median_pb": sector_pb,
            "sector_median_ev_ebitda": sector_ev,
            "sector_median_roe": sector_roe,
            "industry_median_pe": _num(val.get("industry_median")),
            "relative_score": _num(val.get("relative_valuation_score")),
            "prev_pe": _sane("pe", prev.get("pe")),
            "prev_pb": _sane("pb", prev.get("pb")),
            "pe_change_pct": _pct_change(prev.get("pe"), pe),
            "pb_change_pct": _pct_change(prev.get("pb"), pb),
            "consensus_target": _num(consensus.get("target_price")),
            "consensus_upside": _pct_change(val.get("cmp"), consensus.get("target_price")),
            "analyst_count": _num(consensus.get("analyst_count") or consensus.get("buy")),
            "valuation_date": val_date or (next(iter(provider.values()), {}) or {}).get("reported_date"),
            "source": source,
            "provider_coverage": len(provider) if has_provider else 0,
            "has_upstox_sector_benchmark": any(
                v is not None for v in (sector_pe, sector_pb, sector_ev, sector_roe)
            ),
        }
        primary_val = row.get(primary)
        if primary_val is None or not is_meaningful(primary, industry_dna):
            primary_val = pe if pe is not None else pb
        row["primary_value"] = primary_val
        # Premium vs Upstox sector benchmark for the primary metric.
        sector_bench = {
            "pe": sector_pe, "pb": sector_pb, "ev_ebitda": sector_ev, "roe": sector_roe,
        }.get(primary)
        if primary_val is not None and sector_bench:
            row["sector_premium_pct"] = round(100.0 * (primary_val - sector_bench) / sector_bench, 2)
        else:
            row["sector_premium_pct"] = None
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
