"""Persist golden evaluation runs — per-ticker JSON under results/{release}/."""

from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

_LOCK = Lock()
_RUNS: list[dict[str, Any]] = []
_MAX = 50

_IEL_ROOT = Path(__file__).resolve().parent.parent
_REPORTS = _IEL_ROOT / "reports"
_RESULTS = _IEL_ROOT / "results"
_BASELINE_PATH = _REPORTS / "phase1_golden_baseline.json"
_LATEST_PATH = _REPORTS / "phase1_golden_latest.json"

_RELEASE_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _env_root() -> Path | None:
    raw = (os.environ.get("IEL_GOLDEN_STORE_ROOT") or "").strip()
    return Path(raw) if raw else None


def results_root() -> Path:
    """Root for release result trees: results/{release_id}/{TICKER}.json"""
    override = (os.environ.get("IEL_GOLDEN_RESULTS_ROOT") or "").strip()
    if override:
        path = Path(override)
        path.mkdir(parents=True, exist_ok=True)
        return path
    root = _env_root()
    if root:
        path = root / "results"
        path.mkdir(parents=True, exist_ok=True)
        return path
    _RESULTS.mkdir(parents=True, exist_ok=True)
    return _RESULTS


def sanitize_release_id(release_id: str | None) -> str:
    raw = (release_id or "run").strip() or "run"
    safe = _RELEASE_SAFE.sub("_", raw)
    return safe[:80] or "run"


def release_dir(release_id: str | None) -> Path:
    return results_root() / sanitize_release_id(release_id)


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


def ticker_result_payload(row: dict[str, Any], *, release_id: str, run_id: str | None = None) -> dict[str, Any]:
    """Canonical per-ticker JSON written to results/{release}/{TICKER}.json."""
    return {
        "ticker": row.get("ticker"),
        "company_name": row.get("company_name"),
        "sector": row.get("sector"),
        "bucket": row.get("bucket"),
        "release_id": release_id,
        "run_id": run_id,
        "company_quality": row.get("company_quality"),
        "financial_quality": row.get("financial_quality"),
        "valuation": row.get("valuation"),
        "macro": row.get("macro"),
        "technical": row.get("technical"),
        "risk": row.get("risk"),
        "overall_score": row.get("overall_score"),
        "recommendation_readiness": row.get("recommendation_readiness"),
        "institutional_readiness": row.get("institutional_readiness"),
        "decision": row.get("decision"),
        "action": row.get("action"),
        "readiness_band": row.get("readiness_band"),
        "investment_thesis_status": row.get("investment_thesis_status"),
        "gate": row.get("gate"),
        "gate_status": row.get("gate_status"),
        "evidence_class": row.get("evidence_class"),
        "runtime_ms": row.get("runtime_ms"),
        "live_price": row.get("live_price"),
        "price_available": row.get("price_available"),
        "price_ltp": row.get("price_ltp"),
        "price_source": row.get("price_source"),
        "price_stale": row.get("price_stale"),
        "pack_present": row.get("pack_present"),
        "qa_passed": row.get("qa_passed"),
        "qa": row.get("qa"),
        "pipeline": row.get("pipeline"),
        "errors": row.get("errors") or [],
        "ok": row.get("ok"),
    }


def save_release_results(summary: dict[str, Any]) -> dict[str, Any]:
    """
    Write the durable Evaluation Lab artifact tree:

        results/
          PR306/
            HDFCBANK.json
            RELIANCE.json
            ...
            _summary.json
            _manifest.json
    """
    release = sanitize_release_id(str(summary.get("release_id") or summary.get("run_id") or "run"))
    out_dir = release_dir(release)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    rows = [r for r in (summary.get("rows") or []) if isinstance(r, dict) and r.get("ticker")]
    for row in rows:
        ticker = str(row["ticker"]).upper()
        path = out_dir / f"{ticker}.json"
        payload = ticker_result_payload(
            row,
            release_id=release,
            run_id=summary.get("run_id"),
        )
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        written.append(ticker)

    manifest = {
        "release_id": release,
        "run_id": summary.get("run_id"),
        "commit": summary.get("commit"),
        "suite": summary.get("suite"),
        "version": summary.get("version"),
        "n": len(written),
        "tickers": written,
        "results_dir": str(out_dir),
        "layout": "results/{release_id}/{TICKER}.json",
    }
    (out_dir / "_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    light_summary = {
        k: v
        for k, v in summary.items()
        if k not in {"rows", "drift_table"}
    }
    light_summary["results_dir"] = str(out_dir)
    light_summary["ticker_files"] = len(written)
    (out_dir / "_summary.json").write_text(
        json.dumps(light_summary, indent=2, default=str), encoding="utf-8"
    )

    return {
        "release_id": release,
        "results_dir": str(out_dir),
        "n": len(written),
        "tickers": written,
        "manifest_path": str(out_dir / "_manifest.json"),
        "summary_path": str(out_dir / "_summary.json"),
    }


def load_release_results(release_id: str) -> dict[str, Any] | None:
    """Load a prior release tree for Phase 6+ governance tests / drift."""
    out_dir = release_dir(release_id)
    manifest_path = out_dir / "_manifest.json"
    if not manifest_path.exists():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    rows: list[dict[str, Any]] = []
    for ticker in manifest.get("tickers") or []:
        path = out_dir / f"{str(ticker).upper()}.json"
        if not path.exists():
            continue
        try:
            rows.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    summary = None
    summary_path = out_dir / "_summary.json"
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            summary = None
    return {
        "release_id": sanitize_release_id(release_id),
        "results_dir": str(out_dir),
        "manifest": manifest,
        "summary": summary,
        "rows": rows,
        "n": len(rows),
    }


def list_releases() -> list[dict[str, Any]]:
    root = results_root()
    if not root.exists():
        return []
    out: list[dict[str, Any]] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        man = child / "_manifest.json"
        if not man.exists():
            continue
        try:
            meta = json.loads(man.read_text(encoding="utf-8"))
        except Exception:
            meta = {"release_id": child.name, "n": None}
        out.append(
            {
                "release_id": meta.get("release_id") or child.name,
                "n": meta.get("n"),
                "results_dir": str(child),
                "commit": meta.get("commit"),
            }
        )
    return out


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
