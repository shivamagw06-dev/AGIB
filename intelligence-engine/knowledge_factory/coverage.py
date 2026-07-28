"""Coverage KPI — North Star: Decision Coverage.

Reasoning Architecture Frozen v1.0. This module only measures and reports
investable-universe coverage. No new engines.
"""

from __future__ import annotations

from typing import Any

from institutional_reasoning.fundamentals.primitives import has_primitives
from institutional_reasoning.fundamentals.market_series import monthly_returns
from institutional_reasoning.fundamentals.universe import NIFTY_50, NIFTY_100_EXTRA, tier_report

COVERAGE_VERSION = "coverage-kpi-v1.0.0"

# Sprint 1 Target-20 — finish before Nifty 50.
TARGET_20: tuple[str, ...] = (
    "INFY",
    "TCS",
    "WIPRO",
    "HCLTECH",
    "TECHM",
    "HDFCBANK",
    "ICICIBANK",
    "SBIN",
    "RELIANCE",
    "ZOMATO",
    "SUNPHARMA",
    "DRREDDY",
    "CIPLA",
    "LT",
    "SIEMENS",
    "BEL",
    "MARUTI",
    "TATAMOTORS",
    "ASIANPAINT",
    "HINDUNILVR",
)

REQUIRED_FOR_DECISION = (
    "price_history",
    "financials",
    "historical_pe",
    "historical_pb",
    "ev",  # EV/EBITDA when applicable; banks skip
    "roic",
    "roe",
    "risk",
    "timeline",
    "sector_object",
    "evidence_pack",
)


def _company_checklist(entity: str) -> dict[str, Any]:
    from knowledge_factory.store import repository as store
    from institutional_reasoning.fundamentals.derivations import derive_series
    from institutional_reasoning.iki.applicability import infer_sector

    e = entity.upper()
    obj = store.get_object("company", e) or {}
    pack = store.get_pack(e) or {}
    sector = obj.get("sector") or infer_sector(e, None)
    sector_obj = store.get_object("sector", str(sector)) if sector else None
    bank = str(sector or "").lower() in {"bank", "banks"}

    pe = derive_series(e, "PE")
    pb = derive_series(e, "PB")
    ev = derive_series(e, "EV_EBITDA")
    roic = derive_series(e, "ROIC")
    roe = derive_series(e, "ROE")

    checks = {
        "price_history": bool(monthly_returns(e)),
        "financials": has_primitives(e),
        "historical_pe": bool(pe.get("found") and pe.get("points")),
        "historical_pb": bool(pb.get("found") and pb.get("points")),
        "ev": bool(ev.get("found") and ev.get("points")) or bank,  # banks: N/A counts as satisfied
        "roic": bool(roic.get("found") and roic.get("points")),
        "roe": bool(roe.get("found") and roe.get("points")),
        "risk": bool((obj.get("risk") or {}).get("found")) or bool(monthly_returns(e)),
        "timeline": int((obj.get("timeline") or {}).get("n") or 0) > 0,
        "sector_object": bool(sector_obj),
        "evidence_pack": bool(pack.get("historical_pe") is not None or pack.get("current_pe") is not None),
    }
    missing = [k for k, ok in checks.items() if not ok]
    decision_ready = len(missing) == 0
    return {
        "entity": e,
        "sector": sector,
        "checks": checks,
        "missing": missing,
        "decision_ready": decision_ready,
        "coverage_score": round(100.0 * (len(checks) - len(missing)) / len(checks), 1),
    }


def decision_coverage(universe: tuple[str, ...] | list[str] | None = None) -> dict[str, Any]:
    """North Star: % of universe that can complete evidence-backed research without data withhold."""
    universe = tuple(universe or TARGET_20)
    rows = [_company_checklist(e) for e in universe]
    ready = sum(1 for r in rows if r["decision_ready"])
    n = len(universe) or 1
    return {
        "coverage_version": COVERAGE_VERSION,
        "north_star": "decision_coverage",
        "definition": (
            "Percentage of the investable universe for which AGIB can produce a fully "
            "evidence-backed, policy-compliant research package without withholding due to missing data."
        ),
        "universe": "target_20" if tuple(universe) == TARGET_20 else "custom",
        "n": len(universe),
        "decision_ready": ready,
        "decision_coverage_pct": round(100.0 * ready / n, 2),
        "rows": rows,
        "gaps": [r["entity"] for r in rows if not r["decision_ready"]],
    }


def morning_coverage_dashboard() -> dict[str, Any]:
    """Homepage-ready coverage board — what AGIB knows this morning."""
    from knowledge_factory.store import repository as store

    # Ensure Target-20 objects exist for accurate board
    from knowledge_factory.production import run_daily_pipeline

    missing_objs = [e for e in TARGET_20 if not store.get_object("company", e)]
    if missing_objs:
        run_daily_pipeline(entities=list(TARGET_20))

    t20 = decision_coverage(TARGET_20)
    n50 = tier_report("nifty_50")
    n100 = tier_report("nifty_100")
    # Nifty 500 declared subset until full panel exists
    n500 = tier_report("nifty_500")

    packs = list((store.store_root() / "packs").glob("*.json"))
    report = store.get_report("coverage") or {}

    missing_pe = []
    missing_roic = []
    for e in TARGET_20:
        row = next((r for r in t20["rows"] if r["entity"] == e), None)
        if not row:
            continue
        if not row["checks"].get("historical_pe"):
            missing_pe.append(e)
        if not row["checks"].get("roic"):
            missing_roic.append(e)

    board = {
        "coverage_version": COVERAGE_VERSION,
        "north_star": {
            "name": "Decision Coverage",
            "value_pct": t20["decision_coverage_pct"],
            "ready": t20["decision_ready"],
            "universe_n": t20["n"],
            "gaps": t20["gaps"],
        },
        "tiers": {
            "target_20": {
                "covered": t20["decision_ready"],
                "declared": t20["n"],
                "coverage_pct": t20["decision_coverage_pct"],
            },
            "nifty_50": {
                "covered": n50.get("covered"),
                "declared": n50.get("declared"),
                "coverage_pct": n50.get("coverage_pct"),
                "by_level": n50.get("by_level"),
            },
            "nifty_100": {
                "covered": n100.get("covered"),
                "declared": n100.get("declared"),
                "coverage_pct": n100.get("coverage_pct"),
            },
            "nifty_500": {
                "covered": n500.get("covered"),
                "declared": n500.get("declared"),
                "coverage_pct": n500.get("coverage_pct"),
                "note": "Declared panel incomplete until Sprint 4 primitives land",
            },
        },
        "evidence_packs": len(packs),
        "missing_pe": missing_pe,
        "missing_roic": missing_roic,
        "stale": [],
        "validation_failures": len(report.get("validation_failures") or []),
        "collection_failures": len(report.get("collection_failures") or []),
        "architecture_frozen": "REASONING_V1",
        "kpi": "coverage_pct",
    }
    store.put_report("morning_coverage", board)
    return board
