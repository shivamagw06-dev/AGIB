"""Coverage KPI — North Star: Decision Coverage.

Reasoning Architecture Frozen v1.0. This module only measures and reports
investable-universe coverage. No new engines.
"""

from __future__ import annotations

from typing import Any

from institutional_reasoning.fundamentals.primitives import has_primitives
from institutional_reasoning.fundamentals.market_series import monthly_returns
from institutional_reasoning.fundamentals.universe import NIFTY_50, tier_report

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
    from knowledge_factory.fixtures.seed import sector_map
    from institutional_reasoning.fundamentals.derivations import derive_series
    from institutional_reasoning.iki.applicability import infer_sector

    e = entity.upper()
    obj = store.get_object("company", e) or {}
    pack = store.get_pack(e) or {}
    sector = obj.get("sector") or sector_map().get(e) or infer_sector(e, None)
    sector_obj = store.get_object("sector", str(sector)) if sector else None
    # Map KF sector labels onto derivation applicability keys.
    sector_key = str(sector or "").lower()
    if sector_key in {"banks", "bank"}:
        derive_sector = "bank"
    elif sector_key in {"insurance"}:
        derive_sector = "insurance"
    elif sector_key in {"nbfc"}:
        derive_sector = "nbfc"
    else:
        derive_sector = sector_key or None

    pe = derive_series(e, "PE", sector=derive_sector)
    pb = derive_series(e, "PB", sector=derive_sector)
    ev = derive_series(e, "EV_EBITDA", sector=derive_sector)
    roic = derive_series(e, "ROIC", sector=derive_sector)
    roe = derive_series(e, "ROE", sector=derive_sector)

    checks = {
        "price_history": bool(monthly_returns(e)),
        "financials": has_primitives(e),
        "historical_pe": bool(pe.get("found") and pe.get("points")),
        "historical_pb": bool(pb.get("found") and pb.get("points")),
        # FI: EV/EBITDA N/A is decision-ready (policy-compliant withhold avoided).
        "ev": bool(ev.get("found") and ev.get("points")) or bool(ev.get("not_applicable")),
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
    universe = tuple(universe or NIFTY_50)
    rows = [_company_checklist(e) for e in universe]
    ready = sum(1 for r in rows if r["decision_ready"])
    n = len(universe) or 1
    if tuple(universe) == TARGET_20:
        label = "target_20"
    elif tuple(universe) == NIFTY_50:
        label = "nifty_50"
    else:
        label = "custom"
    return {
        "coverage_version": COVERAGE_VERSION,
        "north_star": "decision_coverage",
        "definition": (
            "Percentage of the investable universe for which AGIB can produce a fully "
            "evidence-backed, policy-compliant research package without withholding due to missing data."
        ),
        "universe": label,
        "n": len(universe),
        "decision_ready": ready,
        "decision_coverage_pct": round(100.0 * ready / n, 2),
        "rows": rows,
        "gaps": [r["entity"] for r in rows if not r["decision_ready"]],
    }


def morning_coverage_dashboard() -> dict[str, Any]:
    """Homepage-ready coverage board — what AGIB knows this morning."""
    from knowledge_factory.store import repository as store

    # Ensure Target-20 + Nifty 50 objects exist for accurate Decision Coverage board
    from knowledge_factory.production import run_daily_pipeline

    board_universe = tuple(dict.fromkeys([*TARGET_20, *NIFTY_50]))
    missing_objs = [e for e in board_universe if not store.get_object("company", e)]
    if missing_objs:
        run_daily_pipeline(entities=list(board_universe))

    t20 = decision_coverage(TARGET_20)
    n50 = decision_coverage(NIFTY_50)
    n100_tier = tier_report("nifty_100")
    # Nifty 500 declared subset until full panel exists
    n500 = tier_report("nifty_500")

    packs = list((store.store_root() / "packs").glob("*.json"))
    report = store.get_report("coverage") or {}

    missing_pe = []
    missing_roic = []
    for row in n50["rows"]:
        if not row["checks"].get("historical_pe"):
            missing_pe.append(row["entity"])
        if not row["checks"].get("roic"):
            missing_roic.append(row["entity"])

    board = {
        "coverage_version": COVERAGE_VERSION,
        "north_star": {
            "name": "Decision Coverage",
            "value_pct": n50["decision_coverage_pct"],
            "ready": n50["decision_ready"],
            "universe_n": n50["n"],
            "universe": "nifty_50",
            "gaps": n50["gaps"],
        },
        "tiers": {
            "target_20": {
                "covered": t20["decision_ready"],
                "declared": t20["n"],
                "coverage_pct": t20["decision_coverage_pct"],
            },
            "nifty_50": {
                "covered": n50["decision_ready"],
                "declared": n50["n"],
                "coverage_pct": n50["decision_coverage_pct"],
            },
            "nifty_100": {
                "covered": n100_tier.get("covered"),
                "declared": n100_tier.get("declared"),
                "coverage_pct": n100_tier.get("coverage_pct"),
                "note": "Primitive/risk coverage until Sprint 3 Decision Coverage lands",
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
        "kpi": "decision_coverage_pct",
    }
    store.put_report("morning_coverage", board)
    return board
