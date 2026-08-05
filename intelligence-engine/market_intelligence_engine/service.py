"""Market Intelligence Engine service — single dashboard contract."""

from __future__ import annotations

from typing import Any

from market_intelligence_engine import aggregation, breadth, flows, opportunities, rotation, summary, universe
from market_intelligence_engine.constitution import CONFIDENCE_METHODOLOGY, CONSTITUTION_VERSION, widget_provenance
from market_intelligence_engine.drivers import market_drivers
from market_intelligence_engine.health import market_health_score
from market_intelligence_engine.regime import classify_market_regime
from market_intelligence_engine.validation import validate_dashboard

ENGINE_CODE = "market_intelligence_engine"
VERSION = "2.0"


def health() -> dict[str, Any]:
    wh: dict[str, Any] = {}
    flow: dict[str, Any] = {}
    try:
        from institutional_warehouse.production import coverage as wh_coverage

        wh = wh_coverage() or {}
    except Exception as exc:
        wh = {"error": str(exc)[:200]}
    try:
        flow = flows.institutional_flows() or {}
    except Exception as exc:
        flow = {"coverage": {"error": str(exc)[:200]}}
    return {
        "ok": "error" not in wh,
        "engine": ENGINE_CODE,
        "version": VERSION,
        "constitution": CONSTITUTION_VERSION,
        "data_path": "warehouse → unified_valuation_engine → market_intelligence_engine",
        "companies": wh.get("companies"),
        "warehouse_rows": wh.get("total_rows"),
        "institutional_flow": flow.get("coverage"),
        "warehouse_error": wh.get("error"),
        "reads": ["institutional_warehouse", "valuation_engine", "valuation_terminal.sector_lens"],
    }


def dashboard(*, universe_limit: int = 5000) -> dict[str, Any]:
    """Full market & sector intelligence pack — constitution v2.0."""
    uni = universe.load_universe(limit=universe_limit)
    if not uni.get("ok"):
        return {"ok": False, "error": uni.get("error"), "engine": ENGINE_CODE, "version": VERSION}

    overview = aggregation.market_overview(uni)
    sectors = aggregation.sector_table(uni)
    heatmap = aggregation.sector_heatmap(sectors)
    industries = aggregation.industry_table(uni)
    breadth_pack = breadth.market_breadth()
    if overview.get("companies"):
        breadth_pack["universe_total"] = overview["companies"]
        breadth_pack["not_tracked"] = max(
            0, overview["companies"] - breadth_pack.get("sample_size", 0)
        )
        if overview["companies"]:
            breadth_pack["coverage_pct"] = round(
                100.0 * breadth_pack.get("sample_size", 0) / overview["companies"], 1
            )
    breadth_pack["provenance"] = widget_provenance(
        source="warehouse.daily_market_history",
        table="daily_market_history",
        coverage=breadth_pack.get("coverage"),
        snapshot_date=breadth_pack.get("date"),
    )

    flow_pack = flows.institutional_flows()
    flow_pack["provenance"] = widget_provenance(
        source="warehouse.institutional_flow",
        table="institutional_flow",
        coverage=flow_pack.get("coverage"),
        snapshot_date=flow_pack.get("latest_date"),
    )

    opps = opportunities.detect_opportunities(uni)
    priorities = opportunities.research_priorities(uni, opps)
    rotate = rotation.market_rotation(sectors, uni)
    rotate["provenance"] = widget_provenance(source="market_intelligence_engine.rotation", table="derived")
    explain = rotation.market_explainability(uni)

    regime_pack = classify_market_regime(
        breadth=breadth_pack, flows=flow_pack, sectors=sectors, overview=overview
    )
    health_pack = market_health_score(
        breadth=breadth_pack, flows=flow_pack, overview=overview, sectors=sectors
    )
    drivers_pack = market_drivers(
        sectors=sectors, rotation=rotate, flows=flow_pack, breadth=breadth_pack
    )

    agi_summary = summary.market_summary(
        overview, sectors, breadth_pack, flow_pack, regime=regime_pack, health=health_pack
    )

    pack: dict[str, Any] = {
        "ok": True,
        "engine": ENGINE_CODE,
        "version": VERSION,
        "constitution": CONSTITUTION_VERSION,
        "overview": overview,
        "market_regime": regime_pack,
        "market_health": health_pack,
        "market_drivers": drivers_pack,
        "breadth": breadth_pack,
        "flows": flow_pack,
        "sectors": sectors,
        "sector_heatmap": heatmap,
        "industries": industries,
        "opportunities": opps,
        "rotation": rotate,
        "research_priorities": priorities,
        "explainability": explain,
        "summary": agi_summary,
        "confidence": {
            "methodology": CONFIDENCE_METHODOLOGY,
            "research_priority_note": "Per-company confidence reflects evidence completeness, not return expectation.",
        },
        "provenance": {
            "valuation": "warehouse.historical_valuation",
            "provider_ratios": "warehouse.valuation_ratios (upstox)",
            "price": "warehouse.daily_market_history",
            "consensus": "warehouse.consensus",
            "flows": flow_pack.get("provenance") or {},
            "formula": ENGINE_CODE,
            "formula_version": VERSION,
            "constitution": CONSTITUTION_VERSION,
        },
        "coverage": {
            "companies": uni.get("count"),
            "valuation_date": uni.get("valuation_date"),
            "breadth_sample": breadth_pack.get("sample_size"),
            "breadth_coverage_pct": breadth_pack.get("coverage_pct"),
            "flow_history": (flow_pack.get("coverage") or {}).get("history"),
            "upstox_ratio_companies": sum(1 for r in (uni.get("rows") or []) if r.get("provider_coverage")),
        },
    }
    pack["validation"] = validate_dashboard(pack)
    return pack


def sector_detail(sector: str, *, universe_limit: int = 5000) -> dict[str, Any]:
    uni = universe.load_universe(limit=universe_limit)
    name = str(sector or "").strip()
    members = [r for r in (uni.get("rows") or []) if str(r.get("sector") or "") == name]
    if not members:
        return {"ok": False, "error": "sector_not_found", "sector": name}

    from valuation_terminal.sector_lens import lens_for

    dna_counts: dict[str, int] = {}
    for m in members:
        d = m.get("industry_dna") or "general"
        dna_counts[d] = dna_counts.get(d, 0) + 1
    dominant = max(dna_counts, key=dna_counts.get) if dna_counts else None
    lens = lens_for(dominant, name) or {}

    leaders = sorted(members, key=lambda r: -(r.get("market_cap") or 0))[:8]
    laggards = sorted(
        [m for m in members if m.get("percentile") is not None],
        key=lambda m: m["percentile"],
    )[:8]

    sector_row = next((s for s in aggregation.sector_table(uni) if s["sector"] == name), {})

    return {
        "ok": True,
        "sector": name,
        "companies": len(members),
        "lens": lens,
        "valuation": sector_row,
        "leaders": leaders,
        "laggards": laggards,
        "distribution": {
            "pe": _distribution([m.get("pe") for m in members]),
            "pb": _distribution([m.get("pb") for m in members]),
        },
        "agi_sector_intelligence": _sector_narrative(name, sector_row, lens),
    }


def _distribution(values: list[Any]) -> dict[str, Any]:
    clean = sorted(float(v) for v in values if v is not None)
    if not clean:
        return {"count": 0}
    return {"count": len(clean), "low": clean[0], "high": clean[-1], "median": clean[len(clean) // 2]}


def _sector_narrative(sector: str, row: dict[str, Any], lens: dict[str, Any]) -> str:
    primary = lens.get("primary_metric_label") or row.get("primary_metric_label") or "P/E"
    status = row.get("historical_range_status") or row.get("opportunity") or "mixed"
    pct = row.get("historical_percentile")
    return (
        f"{sector} is led by {primary}. Historical valuation sits "
        f"{status.lower()} (approx. {pct:.0f}th percentile vs sector history). "
        f"This is sector context for research prioritisation, not a recommendation."
        if pct is not None else
        f"{sector} sector intelligence is available with limited historical percentile coverage."
    )
