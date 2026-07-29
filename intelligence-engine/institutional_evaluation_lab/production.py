"""Production façade for Institutional Evaluation Lab (IEL)."""

from __future__ import annotations

from typing import Any

from institutional_evaluation_lab.benchmarks.runner import run_benchmark
from institutional_evaluation_lab.dashboards.board import build_board
from institutional_evaluation_lab.datasets.catalog import catalog_stats, get_question, load_suite
from institutional_evaluation_lab.reports.builder import build_markdown_report
from institutional_evaluation_lab.schema import FREEZE_LOCKS, IEL_VERSION, MODULE_CODE, PROGRAMME, QUALITY_TARGETS
from institutional_evaluation_lab import store


def status() -> dict[str, Any]:
    stats = catalog_stats()
    golden = None
    try:
        from institutional_evaluation_lab.golden_universe.runner import health as golden_health

        golden = golden_health()
    except Exception:
        golden = {"status": "unavailable"}
    return {
        "module": MODULE_CODE,
        "version": IEL_VERSION,
        "programme": PROGRAMME,
        "status": "ready",
        "catalogue": stats,
        "golden_universe_evaluation": golden,
        "quality_targets": QUALITY_TARGETS,
        "freeze_locks": dict(FREEZE_LOCKS),
        "nightly_default": {"suite": "institutional_1000", "mode": "soft"},
        "api_prefix": "/v1/institutional-evaluation-lab",
        "fabricated": False,
    }


def board() -> dict[str, Any]:
    return build_board()


def catalog(*, suite: str = "institutional_1000", limit: int = 50) -> dict[str, Any]:
    if suite in {"phase1_golden_200", "phase1_golden"}:
        from institutional_evaluation_lab.datasets.phase1_golden_universe import universe_board

        board = universe_board()
        rows = load_suite(suite)[: max(1, min(int(limit), 200))]
        return {
            "suite": "phase1_golden_200",
            "kind": "universe",
            "n": board.get("n"),
            "companies": rows,
            "board": board,
            "stats": catalog_stats(),
        }
    rows = load_suite(suite)[: max(1, min(int(limit), 200))]
    return {"suite": suite, "n": len(rows), "questions": rows, "stats": catalog_stats()}


def phase1_golden_universe() -> dict[str, Any]:
    from institutional_evaluation_lab.datasets.phase1_golden_universe import universe_board

    return universe_board()


def golden_evaluation_health() -> dict[str, Any]:
    from institutional_evaluation_lab.golden_universe.runner import health

    return health()


def run_golden_evaluation(
    *,
    limit: int | None = None,
    bucket: str | None = None,
    force_price_refresh: bool = False,
    persist: bool = True,
    persist_baseline: bool = False,
    compare_previous: bool = True,
    release_id: str | None = None,
) -> dict[str, Any]:
    """Evaluation Runner — full institutional pipeline over Phase 1 golden universe."""
    from institutional_evaluation_lab.golden_universe.runner import run_golden_evaluation as _run

    return _run(
        limit=limit,
        bucket=bucket,
        force_price_refresh=force_price_refresh,
        persist=persist,
        persist_baseline=persist_baseline,
        compare_previous=compare_previous,
        release_id=release_id,
    )


def golden_scorecard() -> dict[str, Any]:
    from institutional_evaluation_lab.golden_universe import store as golden_store

    latest = golden_store.load_latest()
    if not latest:
        return {"found": False, "note": "No golden evaluation run yet."}
    return {
        "found": True,
        "scorecard": latest.get("scorecard"),
        "coverage": latest.get("coverage"),
        "run_id": latest.get("run_id"),
        "release_id": latest.get("release_id"),
    }


def golden_drift_report() -> dict[str, Any]:
    from institutional_evaluation_lab.golden_universe import store as golden_store
    from institutional_evaluation_lab.golden_universe.recommendation_drift import (
        compare_recommendation_drift,
    )

    latest = golden_store.load_latest()
    baseline = golden_store.load_baseline()
    if not latest:
        return {"found": False, "note": "No latest golden run."}
    drift = compare_recommendation_drift(
        latest.get("rows") or [],
        (baseline or {}).get("rows") if baseline else None,
        previous_label=str((baseline or {}).get("release_id") or "previous"),
        current_label=str(latest.get("release_id") or "current"),
    )
    return {"found": True, "drift": drift, "baseline_run_id": (baseline or {}).get("run_id")}


def question(question_id: str) -> dict[str, Any] | None:
    return get_question(question_id)


def run(
    *,
    suite: str = "smoke",
    mode: str = "soft",
    limit: int | None = None,
    persist_baseline: bool = False,
) -> dict[str, Any]:
    return run_benchmark(
        suite=suite,
        mode=mode,
        limit=limit,
        persist_baseline=persist_baseline,
    )


def nightly() -> dict[str, Any]:
    """Nightly evaluation entry — soft probe over institutional_1000."""
    summary = run_benchmark(
        suite="institutional_1000",
        mode="soft",
        limit=None,
        persist_baseline=False,
        compare_baseline=True,
    )
    report_md = build_markdown_report(summary)
    # Persist report artifact next to baseline
    from pathlib import Path

    out = Path(__file__).resolve().parent / "reports" / "latest_nightly.md"
    out.write_text(report_md, encoding="utf-8")
    # Strip heavy rows for API response
    light = {k: v for k, v in summary.items() if k != "rows"}
    light["report_path"] = str(out)
    light["report_preview"] = report_md[:2000]
    return light


def history(*, limit: int = 20) -> dict[str, Any]:
    return {"n": limit, "rows": store.list_runs(limit=limit), "fabricated": False}


def report(run_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    if run_summary is None:
        runs = store.list_runs(limit=1)
        run_summary = runs[0] if runs else {"aggregate": {}, "suite": None}
    md = build_markdown_report(run_summary)
    return {"markdown": md, "run_id": run_summary.get("run_id"), "fabricated": False}
