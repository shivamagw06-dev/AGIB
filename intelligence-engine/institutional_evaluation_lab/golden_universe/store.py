"""Persist golden evaluation runs + recommendation baselines for drift."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

_LOCK = Lock()
_RUNS: list[dict[str, Any]] = []
_MAX = 50

_REPORTS = Path(__file__).resolve().parent.parent / "reports"
_BASELINE_PATH = _REPORTS / "phase1_golden_baseline.json"
_LATEST_PATH = _REPORTS / "phase1_golden_latest.json"


def _env_root() -> Path | None:
    raw = (os.environ.get("IEL_GOLDEN_STORE_ROOT") or "").strip()
    return Path(raw) if raw else None


def baseline_path() -> Path:
    root = _env_root()
    if root:
        root.mkdir(parents=True, exist_ok=True)
        return root / "phase1_golden_baseline.json"
    return _BASELINE_PATH


def latest_path() -> Path:
    root = _env_root()
    if root:
        root.mkdir(parents=True, exist_ok=True)
        return root / "phase1_golden_latest.json"
    return _LATEST_PATH


def record_run(summary: dict[str, Any]) -> dict[str, Any]:
    light = {
        "record_id": f"golden-{uuid4().hex[:12]}",
        **{k: v for k, v in summary.items() if k != "rows"},
        "n_rows": len(summary.get("rows") or []),
    }
    with _LOCK:
        _RUNS.append(light)
        if len(_RUNS) > _MAX:
            del _RUNS[: len(_RUNS) - _MAX]
    return deepcopy(light)


def list_runs(*, limit: int = 20) -> list[dict[str, Any]]:
    with _LOCK:
        rows = list(_RUNS)
    return deepcopy(list(reversed(rows[-max(1, min(int(limit), 50)) :])))


def save_latest(summary: dict[str, Any]) -> dict[str, Any]:
    path = latest_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": summary.get("run_id"),
        "release_id": summary.get("release_id"),
        "commit": summary.get("commit"),
        "suite": summary.get("suite"),
        "n": summary.get("n"),
        "coverage": summary.get("coverage"),
        "sector": summary.get("sector"),
        "qa": {k: v for k, v in (summary.get("qa") or {}).items() if k != "failures"},
        "scorecard": summary.get("scorecard"),
        "rows": summary.get("rows") or [],
    }
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return {"path": str(path), "n": len(payload["rows"])}


def load_latest() -> dict[str, Any] | None:
    path = latest_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_baseline(summary: dict[str, Any]) -> dict[str, Any]:
    path = baseline_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": summary.get("run_id"),
        "release_id": summary.get("release_id"),
        "commit": summary.get("commit"),
        "suite": summary.get("suite"),
        "n": summary.get("n"),
        "coverage": summary.get("coverage"),
        "scorecard": summary.get("scorecard"),
        "rows": [
            {
                "ticker": r.get("ticker"),
                "decision": r.get("decision"),
                "recommendation_readiness": r.get("recommendation_readiness"),
                "gate": r.get("gate"),
                "evidence_class": r.get("evidence_class"),
                "sector": r.get("sector"),
                "bucket": r.get("bucket"),
                "overall_score": r.get("overall_score"),
                "company_quality": r.get("company_quality"),
                "financial_quality": r.get("financial_quality"),
                "valuation": r.get("valuation"),
            }
            for r in (summary.get("rows") or [])
            if isinstance(r, dict)
        ],
    }
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return {"path": str(path), "n": len(payload["rows"]), "run_id": payload.get("run_id")}


def load_baseline() -> dict[str, Any] | None:
    path = baseline_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
