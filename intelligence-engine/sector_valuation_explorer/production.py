"""Sector Valuation Explorer production surface.

Composes Market Intelligence universe + sector_lens + HVIE sector medians.
No vendor calls. No UI-side calculations required.
"""

from __future__ import annotations

import statistics as stats
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import unquote

from sector_valuation_explorer.status import (
    market_cap_bucket,
    opportunity_label,
    outcome_label,
    valuation_status,
)
from valuation_terminal.production import PRIMARY_SECTORS
from valuation_terminal.sector_lens import METRIC_LABELS, explain, lens_for

ENGINE_CODE = "sector_valuation_explorer"
VERSION = "1.0.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _num(value: Any) -> Optional[float]:
    try:
        if value is None or isinstance(value, bool):
            return None
        out = float(value)
        return None if out != out else out
    except (TypeError, ValueError):
        return None


def _median(values: list[Any]) -> Optional[float]:
    clean = [_num(v) for v in values]
    clean = [v for v in clean if v is not None]
    return round(stats.median(clean), 4) if clean else None


def _canonical_sector(name: str) -> Optional[str]:
    text = unquote(str(name or "")).strip()
    if not text:
        return None
    for s in PRIMARY_SECTORS:
        if s.lower() == text.lower():
            return s
    # Soft alias: Health Care / Healthcare, IT / Information Technology
    aliases = {
        "healthcare": "Health Care",
        "health care": "Health Care",
        "it": "Information Technology",
        "information technology": "Information Technology",
        "tech": "Information Technology",
        "financial": "Financials",
        "finance": "Financials",
        "consumer discretionary": "Consumer Discretionary",
        "consumer staples": "Consumer Staples",
        "communication": "Communication Services",
        "communication services": "Communication Services",
        "realestate": "Real Estate",
        "real estate": "Real Estate",
    }
    hit = aliases.get(text.lower())
    return hit if hit in PRIMARY_SECTORS else None


def _load_universe(limit: int = 5000) -> dict[str, Any]:
    from market_intelligence_engine import universe

    return universe.load_universe(limit=limit)


def _sector_history_medians(sector: str, metric: str) -> dict[str, Any]:
    """Latest historical sector median from HVIE weekly persist, when present."""
    from institutional_warehouse import store

    try:
        rows = store.fetch(
            "historical_sector_medians",
            filters={"sector": sector, "metric": metric},
            limit=40,
        ).get("rows") or []
    except Exception:
        rows = []
    if not rows:
        return {}
    rows = sorted(rows, key=lambda r: str(r.get("as_of") or ""), reverse=True)
    top = rows[0]
    return {
        "historical_median": _num(top.get("median_value")),
        "as_of": top.get("as_of"),
        "company_count": top.get("company_count"),
        "source": "warehouse.historical_sector_medians",
    }


def _enrich_company(row: dict[str, Any], sector_medians: dict[str, Any]) -> dict[str, Any]:
    primary = row.get("primary_metric") or "pe"
    primary_value = row.get("primary_value")
    sector_pe = sector_medians.get("median_pe") or row.get("sector_median_pe")
    sector_pb = sector_medians.get("median_pb") or row.get("sector_median_pb")
    sector_bench = {
        "pe": sector_pe,
        "pb": sector_pb,
        "ev_ebitda": sector_medians.get("median_ev_ebitda") or row.get("sector_median_ev_ebitda"),
        "roe": sector_medians.get("median_roe") or row.get("sector_median_roe"),
    }.get(primary)
    premium = row.get("sector_premium_pct")
    if premium is None and primary_value is not None and sector_bench:
        premium = round(100.0 * (primary_value - sector_bench) / sector_bench, 2)
    percentile = _num(row.get("percentile"))
    status = valuation_status(
        percentile=percentile,
        premium_pct=_num(premium),
        primary_value=_num(primary_value),
        provider_coverage=int(row.get("provider_coverage") or 0),
    )
    return {
        "symbol": row.get("symbol"),
        "company_name": row.get("company_name"),
        "cmp": row.get("cmp"),
        "market_cap": row.get("market_cap"),
        "market_cap_bucket": market_cap_bucket(_num(row.get("market_cap"))),
        "sector": row.get("sector"),
        "industry": row.get("industry"),
        "industry_dna": row.get("industry_dna"),
        "pe": row.get("pe"),
        "sector_pe": sector_pe,
        "premium_pct": premium,
        "historical_percentile": percentile,
        "pb": row.get("pb"),
        "sector_pb": sector_pb,
        "roe": row.get("roe"),
        "roce": row.get("roce"),
        "ev_ebitda": row.get("ev_ebitda"),
        "primary_metric": primary,
        "primary_value": primary_value,
        "valuation_status": status,
        "coverage": {
            "provider": int(row.get("provider_coverage") or 0),
            "has_percentile": percentile is not None,
            "source": row.get("source"),
        },
        "confidence": 0.9 if row.get("provider_coverage") else 0.6,
        "valuation_date": row.get("valuation_date"),
    }


def _distribution(values: list[Any], *, bins: int = 8) -> dict[str, Any]:
    clean = sorted(v for v in (_num(x) for x in values) if v is not None)
    if not clean:
        return {"count": 0, "bins": []}
    low, high = clean[0], clean[-1]
    if low == high:
        return {
            "count": len(clean),
            "low": low,
            "high": high,
            "median": low,
            "bins": [{"start": low, "end": high, "count": len(clean)}],
        }
    width = (high - low) / bins
    hist = [0] * bins
    for v in clean:
        idx = min(bins - 1, int((v - low) / width))
        hist[idx] += 1
    return {
        "count": len(clean),
        "low": low,
        "high": high,
        "median": clean[len(clean) // 2],
        "bins": [
            {
                "start": round(low + i * width, 4),
                "end": round(low + (i + 1) * width, 4),
                "count": hist[i],
            }
            for i in range(bins)
        ],
    }


def _sector_explanation(lens: dict[str, Any], sector: str) -> dict[str, Any]:
    primary = lens.get("primary_metric") or "pe"
    pedagogy = explain(primary)
    supporting = [
        {"metric": m, "label": METRIC_LABELS.get(m, m), **(explain(m) if explain(m).get("ok") else {})}
        for m in (lens.get("supporting_metrics") or [])[:6]
    ]
    hidden = [
        {"metric": m, "label": METRIC_LABELS.get(m, m), "why": "Not meaningful for this sector DNA."}
        for m in (lens.get("suppressed_metrics") or [])
    ]
    return {
        "sector": sector,
        "primary_metric": primary,
        "primary_metric_label": lens.get("primary_metric_label") or METRIC_LABELS.get(primary, primary),
        "rationale": lens.get("rationale"),
        "why": pedagogy.get("why") if pedagogy.get("ok") else lens.get("rationale"),
        "what": pedagogy.get("what") if pedagogy.get("ok") else None,
        "interpret": pedagogy.get("interpret") if pedagogy.get("ok") else None,
        "supporting": supporting,
        "hidden": hidden,
        "source": "valuation_terminal.sector_lens",
    }


def _sector_outcome(sector: str, valuation: dict[str, Any], companies: list[dict[str, Any]]) -> dict[str, Any]:
    current = _num(valuation.get("current"))
    hist = _num(valuation.get("historical_median"))
    # Prefer HVIE sector median when available for own-history premium.
    hist_pack = _sector_history_medians(sector, valuation.get("primary_metric") or "pe")
    if hist_pack.get("historical_median") is not None:
        hist = hist_pack["historical_median"]
    premium = None
    if current is not None and hist:
        premium = round(100.0 * (current - hist) / hist, 1)
    elif valuation.get("premium_pct") is not None:
        premium = _num(valuation.get("premium_pct"))
    pct = _num(valuation.get("historical_percentile"))
    label = outcome_label(pct, premium)
    evidence: list[str] = []
    if premium is not None:
        direction = "premium" if premium > 0 else "discount"
        evidence.append(f"Sector median sits at a {abs(premium):.1f}% {direction} to its reference median.")
    if pct is not None:
        evidence.append(f"Median company historical percentile is {pct:.0f}.")
    roe = _median([c.get("roe") for c in companies])
    if roe is not None:
        evidence.append(f"Median ROE across covered names is {roe:.1f}%.")
    covered = sum(1 for c in companies if (c.get("coverage") or {}).get("provider"))
    if companies:
        evidence.append(f"Provider coverage on {covered}/{len(companies)} companies.")
    confidence = 0.5
    if pct is not None:
        confidence += 0.25
    if covered >= max(5, len(companies) * 0.4):
        confidence += 0.2
    if hist is not None:
        confidence += 0.05
    return {
        "title": "Sector Valuation Conclusion",
        "sector": sector,
        "current_median": current,
        "historical_median": hist,
        "premium_pct": premium,
        "historical_percentile": pct,
        "conclusion": (
            f"{sector} is trading at a {'premium' if (premium or 0) > 0 else 'discount' if (premium or 0) < 0 else 'level near'} "
            f"to its reference history."
            if premium is not None else
            f"{sector} valuation context is available with limited historical reference."
        ),
        "overall": label,
        "opportunity": opportunity_label(pct),
        "evidence": evidence,
        "confidence": round(min(0.98, confidence) * 100, 0),
        "history_source": hist_pack.get("source") or valuation.get("sector_benchmark_source"),
        "language": "analysis_only",
    }


def health() -> dict[str, Any]:
    return {
        "ok": True,
        "engine": ENGINE_CODE,
        "version": VERSION,
        "role": "sector_first_valuation_workspace",
        "sectors": list(PRIMARY_SECTORS),
        "reads": [
            "market_intelligence_engine.universe",
            "valuation_terminal.sector_lens",
            "warehouse.historical_sector_medians",
            "warehouse.valuation_ratios",
            "historical_valuation_intelligence",
        ],
        "rule": "no_ui_calculations_no_buy_sell",
        "endpoints": [
            "/v1/valuation/sectors",
            "/v1/valuation/sector/{sector}",
            "/v1/valuation/sector/{sector}/companies",
            "/v1/valuation/sector/{sector}/summary",
            "/v1/valuation/sector/{sector}/leaders",
            "/v1/valuation/sector/{sector}/heatmap",
            "/v1/valuation/sector/{sector}/research",
            "/v1/valuation/company/{symbol}",
            "/v1/valuation/company/{symbol}/history",
        ],
    }


def sectors(*, universe_limit: int = 5000) -> dict[str, Any]:
    from market_intelligence_engine import aggregation

    uni = _load_universe(universe_limit)
    if not uni.get("ok"):
        return {"ok": False, "error": uni.get("error"), "engine": ENGINE_CODE}
    table = aggregation.sector_table(uni)
    # Ensure every PRIMARY_SECTOR appears even if empty.
    by_name = {r["sector"]: r for r in table}
    cards = []
    for name in PRIMARY_SECTORS:
        row = by_name.get(name) or {
            "sector": name,
            "companies": 0,
            "primary_metric": "pe",
            "primary_metric_label": "P/E",
            "current": None,
            "historical_percentile": None,
            "opportunity": "Unknown",
            "median_pe": None,
            "median_pb": None,
        }
        cards.append({
            **row,
            "opportunity": row.get("opportunity") or opportunity_label(_num(row.get("historical_percentile"))),
            "heatmap_band": aggregation.sector_heatmap([row])[0].get("heatmap_band") if row.get("companies") else "grey",
        })
    return {
        "ok": True,
        "engine": ENGINE_CODE,
        "version": VERSION,
        "as_of": uni.get("valuation_date"),
        "sectors": cards,
        "count": len(cards),
        "provenance": {
            "base": "market_intelligence_engine.sector_table",
            "lens": "valuation_terminal.sector_lens",
        },
        "checked_at": _now(),
    }


def sector_pack(sector: str, *, universe_limit: int = 5000) -> dict[str, Any]:
    canonical = _canonical_sector(sector)
    if not canonical:
        return {"ok": False, "error": "unknown_sector", "sector": sector}
    from market_intelligence_engine import aggregation

    uni = _load_universe(universe_limit)
    members = [r for r in (uni.get("rows") or []) if str(r.get("sector") or "") == canonical]
    table = aggregation.sector_table(uni)
    valuation = next((s for s in table if s["sector"] == canonical), {})
    dna_counts: dict[str, int] = {}
    for m in members:
        d = m.get("industry_dna") or "general"
        dna_counts[d] = dna_counts.get(d, 0) + 1
    dominant = max(dna_counts, key=dna_counts.get) if dna_counts else None
    lens = lens_for(dominant, canonical) or {}
    companies = [_enrich_company(m, valuation) for m in members]
    market_cap = sum(_num(c.get("market_cap")) or 0 for c in companies)
    covered = sum(1 for c in companies if (c.get("coverage") or {}).get("provider"))
    explanation = _sector_explanation(lens, canonical)
    outcome = _sector_outcome(canonical, valuation, companies)
    return {
        "ok": True,
        "engine": ENGINE_CODE,
        "version": VERSION,
        "sector": canonical,
        "as_of": uni.get("valuation_date"),
        "companies": len(companies),
        "lens": lens,
        "explanation": explanation,
        "outcome": outcome,
        "valuation": {
            **valuation,
            "market_cap": market_cap or None,
            "coverage_pct": round(100.0 * covered / len(companies), 1) if companies else 0,
            "last_updated": uni.get("valuation_date") or _now()[:10],
        },
        "summary": {
            "sector": canonical,
            "companies": len(companies),
            "current_median": valuation.get("current"),
            "primary_metric": valuation.get("primary_metric") or lens.get("primary_metric"),
            "primary_metric_label": valuation.get("primary_metric_label") or lens.get("primary_metric_label"),
            "historical_percentile": valuation.get("historical_percentile"),
            "premium_pct": outcome.get("premium_pct"),
            "historical_median": outcome.get("historical_median"),
            "market_cap": market_cap or None,
            "coverage_pct": round(100.0 * covered / len(companies), 1) if companies else 0,
            "opportunity": outcome.get("opportunity"),
            "overall": outcome.get("overall"),
        },
        "company_rows": companies,
        "distributions": {
            "pe": _distribution([c.get("pe") for c in companies]),
            "pb": _distribution([c.get("pb") for c in companies]),
            "historical_percentile": _distribution([c.get("historical_percentile") for c in companies]),
            "premium_pct": _distribution([c.get("premium_pct") for c in companies]),
            "roe": _distribution([c.get("roe") for c in companies]),
        },
        "industries": sorted({c.get("industry") for c in companies if c.get("industry")}),
        "provenance": {
            "universe": "market_intelligence_engine.universe",
            "lens": "valuation_terminal.sector_lens",
            "provider_ratios": "warehouse.valuation_ratios",
            "historical_valuation": "warehouse.historical_valuation",
            "sector_history": "warehouse.historical_sector_medians",
        },
        "checked_at": _now(),
    }


def summary(sector: str, *, universe_limit: int = 5000) -> dict[str, Any]:
    pack = sector_pack(sector, universe_limit=universe_limit)
    if not pack.get("ok"):
        return pack
    return {
        "ok": True,
        "engine": ENGINE_CODE,
        "sector": pack["sector"],
        "summary": pack["summary"],
        "explanation": pack["explanation"],
        "outcome": pack["outcome"],
        "valuation": pack["valuation"],
        "provenance": pack["provenance"],
    }


def sector_companies(
    sector: str,
    *,
    universe_limit: int = 5000,
    industry: Optional[str] = None,
    status: Optional[str] = None,
    market_cap: Optional[str] = None,
    sort: str = "market_cap",
    order: str = "desc",
    limit: int = 500,
) -> dict[str, Any]:
    pack = sector_pack(sector, universe_limit=universe_limit)
    if not pack.get("ok"):
        return pack
    rows = list(pack.get("company_rows") or [])
    if industry:
        rows = [r for r in rows if str(r.get("industry") or "").lower() == industry.lower()]
    if status:
        rows = [r for r in rows if str(r.get("valuation_status") or "").lower() == status.lower()]
    if market_cap:
        rows = [r for r in rows if r.get("market_cap_bucket") == market_cap.lower()]
    reverse = str(order).lower() != "asc"
    key = sort if sort in {
        "market_cap", "pe", "pb", "roe", "roce", "ev_ebitda", "premium_pct",
        "historical_percentile", "cmp", "company_name", "symbol",
    } else "market_cap"

    def sort_key(row: dict[str, Any]):
        val = row.get(key)
        if val is None:
            return (1, 0 if isinstance(val, (int, float)) else "")
        if isinstance(val, (int, float)):
            return (0, -val if reverse else val)
        return (0, str(val).lower())

    if key in {"company_name", "symbol"}:
        rows.sort(key=lambda r: str(r.get(key) or "").lower(), reverse=reverse)
    else:
        rows.sort(key=lambda r: (_num(r.get(key)) is None, -(_num(r.get(key)) or 0) if reverse else (_num(r.get(key)) or 0)))
    return {
        "ok": True,
        "engine": ENGINE_CODE,
        "sector": pack["sector"],
        "count": len(rows),
        "companies": rows[: max(1, min(limit, 2000))],
        "filters": {
            "industry": industry,
            "status": status,
            "market_cap": market_cap,
            "sort": sort,
            "order": order,
        },
        "as_of": pack.get("as_of"),
    }


def leaders(sector: str, *, universe_limit: int = 5000, top: int = 10) -> dict[str, Any]:
    pack = sector_pack(sector, universe_limit=universe_limit)
    if not pack.get("ok"):
        return pack
    rows = [r for r in pack.get("company_rows") or [] if r.get("symbol")]
    n = max(1, min(int(top or 10), 25))

    def top_by(field: str, *, reverse: bool = True, require=True):
        pool = [r for r in rows if r.get(field) is not None] if require else rows
        pool = sorted(pool, key=lambda r: _num(r.get(field)) or 0, reverse=reverse)
        return [
            {
                "symbol": r["symbol"],
                "company_name": r.get("company_name"),
                "value": r.get(field),
                "valuation_status": r.get("valuation_status"),
                "primary_metric": r.get("primary_metric"),
            }
            for r in pool[:n]
        ]

    return {
        "ok": True,
        "engine": ENGINE_CODE,
        "sector": pack["sector"],
        "leaders": {
            "cheapest": top_by("historical_percentile", reverse=False),
            "most_expensive": top_by("historical_percentile", reverse=True),
            "highest_roe": top_by("roe", reverse=True),
            "highest_roce": top_by("roce", reverse=True),
            "largest_premium": top_by("premium_pct", reverse=True),
            "largest_discount": top_by("premium_pct", reverse=False),
            "highest_quality": top_by("roe", reverse=True),
            "most_attractive_historical": top_by("historical_percentile", reverse=False),
        },
    }


def heatmap(sector: str, *, universe_limit: int = 5000) -> dict[str, Any]:
    pack = sector_pack(sector, universe_limit=universe_limit)
    if not pack.get("ok"):
        return pack
    metrics = ("pe", "pb", "roe", "roce", "ev_ebitda", "historical_percentile")
    cells = []
    for c in pack.get("company_rows") or []:
        cell = {"symbol": c.get("symbol"), "company_name": c.get("company_name")}
        for m in metrics:
            val = _num(c.get(m))
            # Color by historical percentile when available; else by metric rank proxy.
            pct = _num(c.get("historical_percentile")) if m != "historical_percentile" else val
            band = "grey"
            if pct is not None:
                if pct <= 20:
                    band = "dark_green"
                elif pct <= 45:
                    band = "light_green"
                elif pct <= 55:
                    band = "grey"
                elif pct <= 75:
                    band = "orange"
                else:
                    band = "dark_red"
            cell[m] = {"value": val, "band": band}
        cells.append(cell)
    return {
        "ok": True,
        "engine": ENGINE_CODE,
        "sector": pack["sector"],
        "metrics": list(metrics),
        "cells": cells[:400],
        "legend": {
            "dark_green": "≤20th percentile (cheap)",
            "light_green": "20–45",
            "grey": "45–55 (fair)",
            "orange": "55–75",
            "dark_red": "≥75th percentile (expensive)",
        },
    }


def research(sector: str, *, universe_limit: int = 5000) -> dict[str, Any]:
    pack = sector_pack(sector, universe_limit=universe_limit)
    if not pack.get("ok"):
        return pack
    priorities = []
    for c in pack.get("company_rows") or []:
        pct = _num(c.get("historical_percentile"))
        premium = _num(c.get("premium_pct"))
        roe = _num(c.get("roe"))
        reason = None
        action = None
        if pct is not None and pct >= 85:
            reason = "Premium expanded / historically expensive"
            action = "Study earnings quality and durability of the premium"
        elif pct is not None and pct <= 15:
            reason = "Historical low percentile"
            action = "Review re-rating drivers and balance-sheet quality"
        elif premium is not None and premium >= 35:
            reason = "Large premium vs sector median"
            action = "Compare growth and ROE versus peers"
        elif roe is not None and roe >= 25:
            reason = "Highest-quartile ROE"
            action = "Capital allocation review"
        if reason:
            priorities.append({
                "symbol": c.get("symbol"),
                "company_name": c.get("company_name"),
                "reason": reason,
                "action": action,
                "historical_percentile": pct,
                "premium_pct": premium,
                "roe": roe,
                "valuation_status": c.get("valuation_status"),
            })
    priorities = sorted(
        priorities,
        key=lambda r: abs((_num(r.get("historical_percentile")) or 50) - 50),
        reverse=True,
    )[:20]
    return {
        "ok": True,
        "engine": ENGINE_CODE,
        "sector": pack["sector"],
        "priorities": priorities,
        "note": "Research priorities for investigation — not recommendations.",
        "feeds": "research_intelligence",
    }


def company_history(symbol: str, *, metric: str = "pe", window: str = "MAX") -> dict[str, Any]:
    """Proxy HVIE history — warehouse only."""
    try:
        from historical_valuation_intelligence.production import history as hvie_history

        return hvie_history(symbol, metric=metric, window=str(window or "max").lower())
    except Exception as exc:
        return {"ok": False, "symbol": str(symbol).upper(), "error": str(exc)[:200]}
