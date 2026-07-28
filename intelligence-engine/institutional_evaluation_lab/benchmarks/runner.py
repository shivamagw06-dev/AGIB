"""IEL benchmark runner — GitHub commit → questions → AGIB → judge → score."""

from __future__ import annotations

import os
import subprocess
import time
from typing import Any
from uuid import uuid4

from institutional_evaluation_lab.analytics.root_cause import cluster_failures
from institutional_evaluation_lab.benchmarks.probe import probe_question
from institutional_evaluation_lab.datasets.catalog import load_suite
from institutional_evaluation_lab.judges.structural import judge_all
from institutional_evaluation_lab.regression.compare import compare_to_baseline
from institutional_evaluation_lab.schema import IEL_VERSION, MODULE_CODE, QUALITY_TARGETS
from institutional_evaluation_lab.scoring.engine import aggregate_suite, score_question
from institutional_evaluation_lab import store


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


def run_benchmark(
    *,
    suite: str = "smoke",
    mode: str = "soft",
    limit: int | None = None,
    persist_baseline: bool = False,
    compare_baseline: bool = True,
) -> dict[str, Any]:
    """
    Run IEL suite.

    suite: cio_frozen_25 | institutional_1000 | smoke | all
    mode: soft (nightly default) | full (sample)
    """
    t0 = time.time()
    questions = load_suite(suite)
    if limit is not None:
        questions = questions[: max(1, int(limit))]

    scored: list[dict[str, Any]] = []
    for q in questions:
        try:
            probe = probe_question(q, mode=mode)
            judgments = judge_all(q, probe)
            row = score_question(q, judgments)
            row["probe_mode"] = probe.get("mode")
            row["intent_observed"] = (probe.get("intent_resolution") or {}).get("intent")
            row["playbook_id"] = (probe.get("playbook_selection") or {}).get("playbook_id")
            row["framework_ids"] = (probe.get("framework_selection") or {}).get("framework_ids")
            row["imai_hit"] = (probe.get("institutional_memory") or {}).get("have_we_seen_this_before")
            row["ieg_nodes"] = (probe.get("evidence_graph") or {}).get("n_nodes")
            scored.append(row)
        except Exception as exc:
            scored.append(
                {
                    "question_id": q.get("question_id"),
                    "category": q.get("category"),
                    "difficulty": q.get("difficulty"),
                    "suite": q.get("suite"),
                    "overall": 0.0,
                    "passed": False,
                    "verdict": "FAIL",
                    "root_causes": [f"probe_error:{str(exc)[:120]}"],
                    "dimensions": {},
                    "error": str(exc)[:240],
                }
            )

    agg = aggregate_suite(scored)
    clusters = cluster_failures(scored)
    run_id = f"iel-run-{uuid4().hex[:10]}"
    commit = _git_commit()
    baseline = store.load_baseline() if compare_baseline else None
    regression = compare_to_baseline(agg, baseline)

    # Distance to quality targets
    targets = {
        "benchmark_1000_pass_pct": {
            "target": QUALITY_TARGETS["benchmark_1000_pass_pct"],
            "observed": agg["pass_pct"] if suite in {"institutional_1000", "all", "smoke"} else None,
            "gap": (
                round(QUALITY_TARGETS["benchmark_1000_pass_pct"] - agg["pass_pct"], 2)
                if suite in {"institutional_1000", "all", "smoke"}
                else None
            ),
        },
        "framework_selection_proxy": {
            "target": QUALITY_TARGETS["framework_selection_pct"],
            "note": "Proxy = share of questions with framework dimension passed",
        },
    }
    fw_pass = sum(
        1
        for r in scored
        if ((r.get("dimensions") or {}).get("framework") or {}).get("passed")
    )
    targets["framework_selection_proxy"]["observed"] = round(100.0 * fw_pass / max(1, len(scored)), 2)

    summary = {
        "run_id": run_id,
        "module": MODULE_CODE,
        "iel_version": IEL_VERSION,
        "suite": suite,
        "mode": mode,
        "commit": commit,
        "n_questions": len(questions),
        "aggregate": agg,
        "failure_clusters": clusters,
        "regression": regression,
        "targets": targets,
        "latency_ms": int((time.time() - t0) * 1000),
        "reasoning_changed": False,
        "fabricated": False,
        "rows": scored,
    }
    store.record_run(summary)
    if persist_baseline or (baseline is None and suite in {"institutional_1000", "cio_frozen_25", "smoke"}):
        # Auto-establish baseline on first meaningful run; explicit flag overwrites
        if persist_baseline or baseline is None:
            store.save_baseline(summary)
            summary["baseline_saved"] = True
    return summary
