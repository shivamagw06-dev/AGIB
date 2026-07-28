"""Coverage KPI — North Star: Decision Coverage.

Reasoning Architecture Frozen v1.0. This module only measures and reports
investable-universe coverage. No new engines.

Four operational dimensions:
  1. Entity Coverage     — can AGIB answer for the name?
  2. Evidence Coverage   — does every company have required evidence fields?
  3. Decision Coverage   — end-to-end research package without data withhold
  4. Confidence Coverage — evidence/research/portfolio quality thresholds
"""

from __future__ import annotations

import time
from typing import Any

from institutional_reasoning.fundamentals.primitives import has_primitives
from institutional_reasoning.fundamentals.market_series import monthly_returns
from institutional_reasoning.fundamentals.universe import NIFTY_50, NIFTY_100_EXTRA

COVERAGE_VERSION = "coverage-kpi-v1.1.0"

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

NIFTY_100: tuple[str, ...] = tuple(dict.fromkeys([*NIFTY_50, *NIFTY_100_EXTRA]))

REQUIRED_FOR_DECISION = (
    "price_history",
    "financials",
    "historical_pe",
    "historical_pb",
    "ev",  # EV/EBITDA when applicable; FI N/A counts
    "roic",
    "roe",
    "risk",
    "timeline",
    "sector_object",
    "evidence_pack",
)

EVIDENCE_FIELDS = (
    "historical_pe",
    "historical_pb",
    "ev",
    "roic",
    "roe",
    "risk",
    "timeline",
    "corporate_actions",
)

CONFIDENCE_THRESHOLD = 90.0


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

    timeline_n = int((obj.get("timeline") or {}).get("n") or 0)
    # Filings fixture supplies corporate-action-like events (dividends etc.).
    corporate_actions = timeline_n > 0

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
        "timeline": timeline_n > 0,
        "corporate_actions": corporate_actions,
        "sector_object": bool(sector_obj),
        "evidence_pack": bool(pack.get("historical_pe") is not None or pack.get("current_pe") is not None),
    }
    decision_keys = [k for k in REQUIRED_FOR_DECISION]
    missing = [k for k in decision_keys if not checks.get(k)]
    decision_ready = len(missing) == 0

    evidence_quality = float(pack.get("quality") or obj.get("quality_score") or 0.0)
    # Soft proxies until research/portfolio engines expose per-entity confidence.
    research_confidence = evidence_quality if decision_ready else min(evidence_quality, 50.0)
    portfolio_confidence = evidence_quality if decision_ready and checks.get("risk") else min(evidence_quality, 40.0)

    return {
        "entity": e,
        "sector": sector,
        "checks": checks,
        "missing": missing,
        "decision_ready": decision_ready,
        "entity_ready": bool(checks["financials"] and checks["price_history"]),
        "coverage_score": round(100.0 * (len(decision_keys) - len(missing)) / len(decision_keys), 1),
        "evidence_quality": evidence_quality,
        "research_confidence": research_confidence,
        "portfolio_confidence": portfolio_confidence,
        "confidence_ready": (
            evidence_quality >= CONFIDENCE_THRESHOLD
            and research_confidence >= CONFIDENCE_THRESHOLD
            and portfolio_confidence >= CONFIDENCE_THRESHOLD
        ),
    }


def _universe_label(universe: tuple[str, ...]) -> str:
    if universe == TARGET_20:
        return "target_20"
    if universe == NIFTY_50:
        return "nifty_50"
    if universe == NIFTY_100:
        return "nifty_100"
    return "custom"


def decision_coverage(universe: tuple[str, ...] | list[str] | None = None) -> dict[str, Any]:
    """North Star: % of universe that can complete evidence-backed research without data withhold."""
    universe = tuple(universe or NIFTY_100)
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
        "universe": _universe_label(universe),
        "n": len(universe),
        "decision_ready": ready,
        "decision_coverage_pct": round(100.0 * ready / n, 2),
        "rows": rows,
        "gaps": [r["entity"] for r in rows if not r["decision_ready"]],
    }


def entity_coverage(universe: tuple[str, ...] | list[str] | None = None) -> dict[str, Any]:
    """Dimension 1 — can AGIB answer (primitives + price history)?"""
    universe = tuple(universe or NIFTY_100)
    rows = [_company_checklist(e) for e in universe]
    ready = sum(1 for r in rows if r["entity_ready"])
    n = len(universe) or 1
    return {
        "dimension": "entity_coverage",
        "universe": _universe_label(universe),
        "n": n,
        "ready": ready,
        "coverage_pct": round(100.0 * ready / n, 2),
        "gaps": [r["entity"] for r in rows if not r["entity_ready"]],
    }


def evidence_coverage(universe: tuple[str, ...] | list[str] | None = None) -> dict[str, Any]:
    """Dimension 2 — field-level evidence completeness across the universe."""
    universe = tuple(universe or NIFTY_100)
    rows = [_company_checklist(e) for e in universe]
    n = len(universe) or 1
    by_field: dict[str, dict[str, Any]] = {}
    for field in EVIDENCE_FIELDS:
        ok = sum(1 for r in rows if r["checks"].get(field))
        by_field[field] = {
            "ready": ok,
            "declared": n,
            "coverage_pct": round(100.0 * ok / n, 2),
            "gaps": [r["entity"] for r in rows if not r["checks"].get(field)],
        }
    # Average field coverage as the headline evidence %.
    avg = round(sum(v["coverage_pct"] for v in by_field.values()) / len(by_field), 2)
    return {
        "dimension": "evidence_coverage",
        "universe": _universe_label(universe),
        "n": n,
        "coverage_pct": avg,
        "by_field": by_field,
    }


def confidence_coverage(universe: tuple[str, ...] | list[str] | None = None) -> dict[str, Any]:
    """Dimension 4 — share of names above quality/confidence thresholds."""
    universe = tuple(universe or NIFTY_100)
    rows = [_company_checklist(e) for e in universe]
    n = len(universe) or 1
    eq = sum(1 for r in rows if r["evidence_quality"] >= CONFIDENCE_THRESHOLD)
    rc = sum(1 for r in rows if r["research_confidence"] >= CONFIDENCE_THRESHOLD)
    pc = sum(1 for r in rows if r["portfolio_confidence"] >= CONFIDENCE_THRESHOLD)
    ready = sum(1 for r in rows if r["confidence_ready"])
    return {
        "dimension": "confidence_coverage",
        "universe": _universe_label(universe),
        "threshold": CONFIDENCE_THRESHOLD,
        "n": n,
        "ready": ready,
        "coverage_pct": round(100.0 * ready / n, 2),
        "evidence_quality_gt_threshold": {"ready": eq, "coverage_pct": round(100.0 * eq / n, 2)},
        "research_confidence_gt_threshold": {"ready": rc, "coverage_pct": round(100.0 * rc / n, 2)},
        "portfolio_confidence_gt_threshold": {"ready": pc, "coverage_pct": round(100.0 * pc / n, 2)},
        "gaps": [r["entity"] for r in rows if not r["confidence_ready"]],
        "avg_evidence_quality": round(sum(r["evidence_quality"] for r in rows) / n, 2) if n else 0.0,
    }


def coverage_dimensions(universe: tuple[str, ...] | list[str] | None = None) -> dict[str, Any]:
    """All four coverage dimensions for one universe."""
    universe = tuple(universe or NIFTY_100)
    dc = decision_coverage(universe)
    return {
        "coverage_version": COVERAGE_VERSION,
        "universe": _universe_label(universe),
        "entity_coverage": entity_coverage(universe),
        "evidence_coverage": evidence_coverage(universe),
        "decision_coverage": {
            "dimension": "decision_coverage",
            "universe": dc["universe"],
            "n": dc["n"],
            "ready": dc["decision_ready"],
            "coverage_pct": dc["decision_coverage_pct"],
            "gaps": dc["gaps"],
            "north_star": True,
        },
        "confidence_coverage": confidence_coverage(universe),
    }


def _learning_stats() -> dict[str, int]:
    """Soft CAL learning counters when available; zeros otherwise."""
    try:
        from institutional_reasoning.cal import production as cal  # type: ignore

        if hasattr(cal, "learning_stats"):
            stats = cal.learning_stats() or {}
            return {
                "proposals": int(stats.get("proposals") or 0),
                "approved": int(stats.get("approved") or 0),
                "rejected": int(stats.get("rejected") or 0),
            }
    except Exception:
        pass
    report = {}
    try:
        from knowledge_factory.store import repository as store

        report = store.get_report("learning") or {}
    except Exception:
        report = {}
    return {
        "proposals": int(report.get("proposals") or 0),
        "approved": int(report.get("approved") or 0),
        "rejected": int(report.get("rejected") or 0),
    }


def daily_health_scorecard(*, ensure_pipeline: bool = True) -> dict[str, Any]:
    """Nightly / morning AGIB Daily Health — one operational screen."""
    from knowledge_factory.store import repository as store
    from knowledge_factory.production import run_daily_pipeline

    t0 = time.perf_counter()
    board_universe = tuple(dict.fromkeys([*TARGET_20, *NIFTY_100]))
    if ensure_pipeline:
        missing_objs = [e for e in board_universe if not store.get_object("company", e)]
        if missing_objs:
            run_daily_pipeline(entities=list(board_universe))

    t20 = decision_coverage(TARGET_20)
    n50 = decision_coverage(NIFTY_50)
    n100 = decision_coverage(NIFTY_100)
    dims = coverage_dimensions(NIFTY_100)
    conf = dims["confidence_coverage"]
    evid = dims["evidence_coverage"]
    # Honest denominators — do not inflate Nifty 500 / Global via covered-entity union.
    nifty_500_declared = 500
    global_declared = 1000  # placeholder investable-global denominator until Sprint 8
    nifty_500_pct = round(100.0 * n100["decision_ready"] / nifty_500_declared, 2)
    global_pct = 0.0

    report = store.get_report("coverage") or {}
    daily = store.get_report("daily") or {}
    packs = list((store.store_root() / "packs").glob("*.json"))

    missing_metrics = 0
    for row in n100["rows"]:
        missing_metrics += len(row["missing"])

    # Stale: packs with no freshness, or company objects without risk/timeline.
    stale = [
        r["entity"]
        for r in n100["rows"]
        if not r["checks"].get("timeline") or not r["checks"].get("risk")
    ]

    learning = _learning_stats()
    runtime_s = round(time.perf_counter() - t0, 2)
    # Prefer recorded nightly runtime when present.
    recorded = daily.get("runtime_seconds") or daily.get("duration_seconds")
    if recorded is not None:
        try:
            runtime_s = round(float(recorded), 2)
        except (TypeError, ValueError):
            pass

    scorecard = {
        "coverage_version": COVERAGE_VERSION,
        "title": "AGIB Daily Health",
        "architecture_frozen": "REASONING_V1",
        "operating_mode": True,
        "kpi_rule": "Every PR must improve at least one measurable operational KPI.",
        "north_star": {
            "name": "Decision Coverage",
            "universe": "nifty_100",
            "value_pct": n100["decision_coverage_pct"],
            "ready": n100["decision_ready"],
            "universe_n": n100["n"],
            "gaps": n100["gaps"],
        },
        "decision_coverage": {
            "target_20": t20["decision_coverage_pct"],
            "nifty_50": n50["decision_coverage_pct"],
            "nifty_100": n100["decision_coverage_pct"],
            "nifty_500": nifty_500_pct,
            "nifty_500_note": f"{n100['decision_ready']}/{nifty_500_declared} (deferred)",
            "global": global_pct,
            "global_note": f"0/{global_declared} (deferred until Sprint 8)",
        },
        "dimensions": {
            "entity_coverage": dims["entity_coverage"]["coverage_pct"],
            "evidence_coverage": evid["coverage_pct"],
            "decision_coverage": n100["decision_coverage_pct"],
            "confidence_coverage": conf["coverage_pct"],
        },
        "evidence_quality": conf.get("avg_evidence_quality"),
        "framework_accuracy": None,  # filled when acceptance suites publish nightly
        "missing_metrics": missing_metrics,
        "validation_failures": len(report.get("validation_failures") or []),
        "stale_companies": len(stale),
        "stale": stale,
        "collector_failures": len(report.get("collection_failures") or []),
        "nightly_runtime_seconds": runtime_s,
        "evidence_packs": len(packs),
        "learning": learning,
        "evidence_by_field": {
            k: v["coverage_pct"] for k, v in evid.get("by_field", {}).items()
        },
        "roadmap_next": "historical_depth",
        "roadmap_note": (
            "After Nifty 100 Decision Coverage = 100%: Historical Depth → "
            "Sector Intelligence → Macro Intelligence → Nifty 500 → Global. "
            "IMI is Knowledge Factory only; Phases 1–7 frozen."
        ),
    }
    # Surface Historical Depth Coverage when the HD store is populated.
    try:
        from knowledge_factory.historical_depth.dashboard import historical_depth_dashboard

        hd = historical_depth_dashboard()
        scorecard["historical_depth"] = {
            "average_history_years": hd.get("average_history_years"),
            "companies_gt_10y_pct": hd.get("companies_gt_10y_pct"),
            "companies_gt_20y_pct": hd.get("companies_gt_20y_pct"),
            "historical_completeness_pct": hd.get("historical_completeness_pct"),
            "historical_evidence_quality": hd.get("historical_evidence_quality"),
            "point_in_time_integrity": hd.get("point_in_time_integrity"),
        }
        if (hd.get("companies_gt_20y_pct") or 0) >= 100:
            scorecard["roadmap_next"] = "sector_intelligence"
    except Exception:
        scorecard["historical_depth"] = None
    try:
        from knowledge_factory.sector_intelligence.dashboard import sector_intelligence_dashboard

        isi = sector_intelligence_dashboard()
        scorecard["sector_intelligence"] = {
            "sector_coverage_pct": isi.get("sector_coverage_pct"),
            "sector_dna_completeness": isi.get("sector_dna_completeness"),
            "playbook_coverage_pct": isi.get("playbook_coverage_pct"),
            "framework_coverage_pct": isi.get("framework_coverage_pct"),
            "average_evidence_quality": isi.get("average_evidence_quality"),
        }
        if (isi.get("sector_coverage_pct") or 0) >= 100 and (isi.get("playbook_coverage_pct") or 0) >= 100:
            scorecard["roadmap_next"] = "macro_intelligence"
    except Exception:
        scorecard["sector_intelligence"] = None
    try:
        from knowledge_factory.macro_intelligence.dashboard import macro_intelligence_dashboard

        imi = macro_intelligence_dashboard()
        kpi = imi.get("kpi") or {}
        scorecard["macro_intelligence"] = {
            "coverage": kpi.get("coverage"),
            "macro_objects": (kpi.get("counts") or {}).get("macro_objects"),
            "regime_coverage": kpi.get("regime_coverage"),
            "decision_matrix_coverage": kpi.get("decision_matrix_coverage"),
            "evidence_quality": kpi.get("evidence_quality"),
            "status": imi.get("status"),
        }
        if float(kpi.get("coverage") or 0) >= 0.7 and imi.get("status") == "operational":
            scorecard["roadmap_next"] = "nifty_500"
    except Exception:
        scorecard["macro_intelligence"] = None
    store.put_report("daily_health", scorecard)
    return scorecard


def morning_coverage_dashboard() -> dict[str, Any]:
    """Homepage-ready coverage board — what AGIB knows this morning."""
    from knowledge_factory.store import repository as store
    from knowledge_factory.production import run_daily_pipeline

    board_universe = tuple(dict.fromkeys([*TARGET_20, *NIFTY_100]))
    missing_objs = [e for e in board_universe if not store.get_object("company", e)]
    if missing_objs:
        run_daily_pipeline(entities=list(board_universe))

    t20 = decision_coverage(TARGET_20)
    n50 = decision_coverage(NIFTY_50)
    n100 = decision_coverage(NIFTY_100)
    dims = coverage_dimensions(NIFTY_100)
    health = daily_health_scorecard(ensure_pipeline=False)

    packs = list((store.store_root() / "packs").glob("*.json"))
    report = store.get_report("coverage") or {}

    missing_pe = []
    missing_roic = []
    for row in n100["rows"]:
        if not row["checks"].get("historical_pe"):
            missing_pe.append(row["entity"])
        if not row["checks"].get("roic"):
            missing_roic.append(row["entity"])

    board = {
        "coverage_version": COVERAGE_VERSION,
        "north_star": {
            "name": "Decision Coverage",
            "value_pct": n100["decision_coverage_pct"],
            "ready": n100["decision_ready"],
            "universe_n": n100["n"],
            "universe": "nifty_100",
            "gaps": n100["gaps"],
        },
        "dimensions": dims,
        "daily_health": health,
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
                "covered": n100["decision_ready"],
                "declared": n100["n"],
                "coverage_pct": n100["decision_coverage_pct"],
            },
            "nifty_500": {
                "covered": n100["decision_ready"],
                "declared": 500,
                "coverage_pct": round(100.0 * n100["decision_ready"] / 500, 2),
                "note": "Deferred until Historical Depth + Sector + Macro (post Nifty 100)",
            },
        },
        "evidence_packs": len(packs),
        "missing_pe": missing_pe,
        "missing_roic": missing_roic,
        "stale": health.get("stale") or [],
        "validation_failures": len(report.get("validation_failures") or []),
        "collection_failures": len(report.get("collection_failures") or []),
        "architecture_frozen": "REASONING_V1",
        "kpi": "decision_coverage_pct",
        "kpi_rule": "Every PR must improve at least one measurable operational KPI.",
        "roadmap_next": "historical_depth",
    }
    store.put_report("morning_coverage", board)
    return board
