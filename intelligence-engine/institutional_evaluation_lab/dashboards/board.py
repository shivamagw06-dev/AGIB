"""IEL Mission Control board."""

from __future__ import annotations

from typing import Any

from institutional_evaluation_lab.datasets.catalog import catalog_stats
from institutional_evaluation_lab.schema import IEL_VERSION, MODULE_CODE, QUALITY_TARGETS
from institutional_evaluation_lab import store


def build_board() -> dict[str, Any]:
    stats = catalog_stats()
    runs = store.list_runs(limit=10)
    baseline = store.load_baseline()
    latest = runs[0] if runs else None
    return {
        "module": MODULE_CODE,
        "version": IEL_VERSION,
        "catalogue": stats,
        "quality_targets": QUALITY_TARGETS,
        "baseline": baseline,
        "latest_run": {
            "run_id": (latest or {}).get("run_id"),
            "suite": (latest or {}).get("suite"),
            "pass_pct": ((latest or {}).get("aggregate") or {}).get("pass_pct"),
            "mean_score": ((latest or {}).get("aggregate") or {}).get("mean_score"),
            "n": ((latest or {}).get("aggregate") or {}).get("n"),
            "hypothesis_quality_score": (latest or {}).get("hypothesis_quality_score")
            or ((latest or {}).get("aggregate") or {}).get("hypothesis_quality"),
            "regression": (latest or {}).get("regression"),
            "top_root_causes": ((latest or {}).get("aggregate") or {}).get("top_root_causes"),
        }
        if latest
        else None,
        "recent_runs": [
            {
                "run_id": r.get("run_id"),
                "suite": r.get("suite"),
                "pass_pct": (r.get("aggregate") or {}).get("pass_pct"),
                "mean_score": (r.get("aggregate") or {}).get("mean_score"),
                "mean_hqs": (
                    ((r.get("hypothesis_quality_score") or {}).get("mean_hqs"))
                    or ((r.get("aggregate") or {}).get("hypothesis_quality") or {}).get("mean_hqs")
                ),
                "commit": r.get("commit"),
            }
            for r in runs[:8]
        ],
        "nightly_pipeline": [
            "GitHub Commit",
            "1000 Questions",
            "AGIB soft probe",
            "Deterministic Judge",
            "Score",
            "Hypothesis Quality Score",
            "Root Cause",
            "Dashboard",
        ],
        "freeze": {
            "reasoning_engine": "frozen",
            "knowledge_factory": "frozen",
            "iew_v1": "frozen",
            "ihg_v1": "frozen",
            "measurement_only": True,
        },
    }
