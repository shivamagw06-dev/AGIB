"""Golden-universe Evaluation Runner — statistical evaluation over Phase 1 200."""

from __future__ import annotations

import os
import subprocess
import time
from typing import Any
from uuid import uuid4

from institutional_evaluation_lab.golden_universe.dashboards import (
    bucket_dashboard,
    coverage_dashboard,
    sector_dashboard,
)
from institutional_evaluation_lab.golden_universe.per_ticker import evaluate_ticker
from institutional_evaluation_lab.golden_universe.performance import attach_performance_stubs
from institutional_evaluation_lab.golden_universe.qa_governance import suite_qa_summary
from institutional_evaluation_lab.golden_universe.recommendation_drift import (
    compare_recommendation_drift,
)
from institutional_evaluation_lab.golden_universe.schema import GOLDEN_EVAL_VERSION, PROGRAMME, SUITE_ID
from institutional_evaluation_lab.golden_universe.scorecard import release_scorecard
from institutional_evaluation_lab.golden_universe import store as golden_store


def _git_commit() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=os.environ.get("IEL_GIT_ROOT", "/workspace"),
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except Exception:
        return None


def _universe_rows(*, bucket: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    from knowledge_factory.phase1_golden_test_set import PHASE1_GOLDEN_ROWS, by_bucket

    if bucket:
        rows = list(by_bucket().get(bucket) or [])
    else:
        rows = [dict(r) for r in PHASE1_GOLDEN_ROWS]
    if limit is not None:
        rows = rows[: max(1, int(limit))]
    return rows


def run_golden_evaluation(
    *,
    limit: int | None = None,
    bucket: str | None = None,
    force_price_refresh: bool = False,
    persist: bool = True,
    persist_baseline: bool = False,
    compare_previous: bool = True,
    release_id: str | None = None,
    previous_label: str | None = None,
    current_label: str | None = None,
    include_performance_stubs: bool = True,
    ide_runner=None,
    price_runner=None,
) -> dict[str, Any]:
    """
    Run the institutional pipeline across the Phase 1 golden universe.

    Pipeline per ticker:
      Load Company Pack → Fetch Live Price (Groww) → Freshness Validation
      → Decision Engine → Evaluation Report (+ QA)
    """
    t0 = time.time()
    universe = _universe_rows(bucket=bucket, limit=limit)
    run_id = f"IEL-GOLDEN-{uuid4().hex[:10].upper()}"
    release = release_id or os.environ.get("IEL_RELEASE_ID") or _git_commit() or run_id
    cur_label = current_label or (release if release_id else "current")
    prev_label = previous_label or "previous"

    rows: list[dict[str, Any]] = []
    for meta in universe:
        row = evaluate_ticker(
            meta,
            force_price_refresh=force_price_refresh,
            ide_runner=ide_runner,
            price_runner=price_runner,
        )
        rows.append(row)

    if include_performance_stubs:
        rows = attach_performance_stubs(rows)

    coverage = coverage_dashboard(rows)
    sector = sector_dashboard(rows)
    buckets = bucket_dashboard(rows)
    qa = suite_qa_summary(rows)

    baseline = golden_store.load_baseline() if compare_previous else None
    prev_rows = (baseline or {}).get("rows") if baseline else None
    if baseline and not previous_label:
        prev_label = str(baseline.get("release_id") or baseline.get("commit") or "previous")
    drift = compare_recommendation_drift(
        rows,
        prev_rows if isinstance(prev_rows, list) else None,
        previous_label=prev_label,
        current_label=cur_label,
    )

    summary: dict[str, Any] = {
        "run_id": run_id,
        "release_id": release,
        "commit": _git_commit(),
        "programme": PROGRAMME,
        "suite": SUITE_ID,
        "version": GOLDEN_EVAL_VERSION,
        "kind": "golden_universe_evaluation",
        "n": len(rows),
        "bucket_filter": bucket,
        "elapsed_ms": int((time.time() - t0) * 1000),
        "coverage": coverage,
        "sector": sector,
        "buckets": buckets,
        "qa": qa,
        "drift": {
            **{k: v for k, v in drift.items() if k != "rows"},
            "rows_sample": (drift.get("rows") or [])[:30],
        },
        "rows": rows,
        "pipeline": [
            "golden_universe",
            "load_company_pack",
            "fetch_live_price_groww",
            "freshness_validation",
            "decision_engine",
            "generate_evaluation_report",
        ],
        "fabricated": False,
    }
    summary["scorecard"] = release_scorecard(summary)
    # Attach full drift table under a separate key for consumers that want it
    summary["drift_table"] = drift.get("rows") or []

    if persist:
        golden_store.record_run(summary)
        golden_store.save_latest(summary)
    if persist_baseline:
        golden_store.save_baseline(summary)

    return summary


def health() -> dict[str, Any]:
    from knowledge_factory.phase1_golden_test_set import summary as universe_summary

    return {
        "status": "ok",
        "programme": PROGRAMME,
        "version": GOLDEN_EVAL_VERSION,
        "suite": SUITE_ID,
        "universe": universe_summary(),
        "baseline_present": golden_store.load_baseline() is not None,
        "latest_present": golden_store.load_latest() is not None,
    }
