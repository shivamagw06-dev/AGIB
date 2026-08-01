#!/usr/bin/env python3
"""Run Tier A (SMOKE-01..08) only — founder gate before full 42-case suite.

Usage:
  cd intelligence-engine
  ASK_TEST_MODE=inprocess python3 -m ask_product_test.run_tier_a
  ASK_TEST_MODE=live ASK_TEST_BASE=https://... python3 -m ask_product_test.run_tier_a

Writes:
  artifacts/tier_a_fix_report.json
  artifacts/tier_a_fix_report_<UTC>.json  (stamped, never overwritten)
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ask_product_test.harness import AskProductHarness, _artifacts_dir, print_health_summary
from ask_product_test.prompts import SMOKE_PROMPTS
from ask_product_test.run_baseline import _enrich_row, _print_execution_trace, _ts, _write_atomic


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _row_summary(row: Dict[str, Any]) -> Dict[str, Any]:
    orch_lat = row.get("orchestration_latency") or {}
    funnel = row.get("funnel") or {}
    return {
        "id": row.get("id"),
        "prompt": row.get("prompt"),
        "pass": bool(row.get("pass")),
        "completed": bool(row.get("completed")),
        "latency_ms": row.get("latency_ms"),
        "entity": row.get("entity"),
        "entity_confidence": row.get("entity_confidence"),
        "reasoning_ms": orch_lat.get("reasoning_ms") or row.get("reasoning_ms"),
        "assembly_ms": orch_lat.get("assembly_ms") or row.get("assembly_ms"),
        "retrieved": funnel.get("retrieved"),
        "ranked": funnel.get("ranked"),
        "passed": funnel.get("passed"),
        "referenced": funnel.get("referenced"),
        "fallback": bool(row.get("fallback_used") or row.get("fallback")),
        "timeout": bool(row.get("timeout")),
        "ask_trace_id": row.get("ask_trace_id"),
        "last_completed_stage": row.get("last_completed_stage"),
        "short_circuit": (row.get("degradation") or {}).get("short_circuit")
        if isinstance(row.get("degradation"), dict)
        else None,
        "failures": row.get("failures") or [],
    }


def _load_previous_baseline() -> Optional[Dict[str, Any]]:
    root = _artifacts_dir()
    # Prefer paused pre-IKL baseline from the aborted 42-case run
    candidates = [
        root / "ask_test_report_pre_ikl_20260801T064555Z_paused.json",
        root / "ask_test_report_pre_ikl_20260801T064555Z_preserved.json",
        root / "ask_test_report_pre_ikl_20260801T064555Z.json",
        root / "ask_test_report_pre_ikl.json",
    ]
    # Also check repo-root artifacts/
    for extra in (
        Path("/workspace/artifacts"),
        Path(__file__).resolve().parents[2] / "artifacts",
    ):
        if extra.is_dir():
            candidates.extend(
                [
                    extra / "ask_test_report_pre_ikl_20260801T064555Z_paused.json",
                    extra / "ask_test_report_pre_ikl_20260801T064555Z_preserved.json",
                    extra / "ask_test_report_pre_ikl_20260801T064555Z.json",
                ]
            )
    for path in candidates:
        try:
            if path.is_file():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
    return None


def _compare(tier_rows: List[Dict[str, Any]], previous: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    prev_by_id: Dict[str, Any] = {}
    if isinstance(previous, dict):
        for q in previous.get("questions") or []:
            if isinstance(q, dict) and str(q.get("id") or "").startswith("SMOKE-"):
                prev_by_id[str(q["id"])] = q
    deltas = []
    for row in tier_rows:
        pid = str(row.get("id") or "")
        prev = prev_by_id.get(pid) or {}
        deltas.append(
            {
                "id": pid,
                "prev_pass": prev.get("pass"),
                "now_pass": row.get("pass"),
                "prev_latency_ms": prev.get("latency_ms"),
                "now_latency_ms": row.get("latency_ms"),
                "prev_timeout": prev.get("timeout"),
                "now_timeout": row.get("timeout"),
                "prev_fallback": prev.get("fallback_used") or prev.get("fallback"),
                "now_fallback": row.get("fallback"),
                "prev_reasoning_ms": (prev.get("orchestration_latency") or {}).get("reasoning_ms"),
                "now_reasoning_ms": row.get("reasoning_ms"),
            }
        )
    tier_pass = sum(1 for r in tier_rows if r.get("pass"))
    return {
        "previous_artifact_note": "compared against paused/preserved pre-IKL baseline when available",
        "tier_a_passed": tier_pass,
        "tier_a_total": len(tier_rows),
        "tier_a_gate": "PASS" if tier_pass == 8 else "FAIL",
        "deltas": deltas,
        "recommend_full_suite": tier_pass == 8,
        "recommend_ikl_merge": False,  # never until Tier A green + post-IKL baseline
    }


def main() -> int:
    latency = int(
        os.environ.get("ASK_TEST_LATENCY_MS")
        or os.environ.get("ASK_ENGINE_TIMEOUT_MS")
        or "120000"
    )
    # Default inprocess so local fixes are verified before deploy.
    os.environ.setdefault("ASK_TEST_MODE", "inprocess")
    h = AskProductHarness(latency_budget_ms=latency)
    stamp = _stamp()
    out_dir = _artifacts_dir()
    stamped = out_dir / f"tier_a_fix_report_{stamp}.json"
    stable = out_dir / "tier_a_fix_report.json"
    # Also write under /workspace/artifacts when that is the repo root artifacts dir
    workspace_arts = Path("/workspace/artifacts")

    cases = list(SMOKE_PROMPTS)
    print(
        f"[tier-a] mode={h.mode} base={h.base_url} "
        f"latency_budget_ms={latency} cases={len(cases)}",
        flush=True,
    )

    questions: List[Dict[str, Any]] = []
    for idx, case in enumerate(cases, 1):
        print(
            f"\n[tier-a] ({idx}/{len(cases)}) {case.get('id')} — {case.get('prompt')[:100]}",
            flush=True,
        )
        t0 = time.perf_counter()
        try:
            transport = h.ask(case["prompt"], ticker=case.get("ticker"), case=case)
        except Exception as exc:  # noqa: BLE001
            transport = {
                "http_status": 0,
                "latency_ms": int((time.perf_counter() - t0) * 1000),
                "payload": {
                    "error": "research_desk_unavailable",
                    "retryable": True,
                    "detail": str(exc)[:240],
                },
                "error": str(exc),
                "timeout": "timeout" in str(exc).lower(),
                "raw_is_html": False,
                "transport": h.mode,
            }
        row = h.evaluate(case, transport, previous_entities=None)
        row = _enrich_row(row, transport)
        # Attach degradation for short_circuit reporting
        payload = transport.get("payload") if isinstance(transport.get("payload"), dict) else {}
        if isinstance(payload, dict):
            row["degradation"] = payload.get("degradation") or {}
        questions.append(row)
        orch = (payload.get("ask_orchestration") or {}) if isinstance(payload, dict) else {}
        _print_execution_trace(row, orch if isinstance(orch, dict) else {})
        print(
            f"[tier-a] pass={row.get('pass')} timeout={row.get('timeout')} "
            f"fallback={row.get('fallback_used')} ms={row.get('latency_ms')}",
            flush=True,
        )

    summaries = [_row_summary(q) for q in questions]
    previous = _load_previous_baseline()
    comparison = _compare(summaries, previous)
    passed = sum(1 for s in summaries if s.get("pass"))
    report = {
        "suite": "Tier A founder acceptance (SMOKE-01..08)",
        "timestamp": _ts(),
        "mode": h.mode,
        "base_url": h.base_url,
        "latency_budget_ms": latency,
        "partial": False,
        "completed": True,
        "pass_rate": (passed / len(summaries)) if summaries else 0.0,
        "passed": passed,
        "total": len(summaries),
        "tier_a_gate": "PASS" if passed == 8 else "FAIL",
        "questions": summaries,
        "full_questions": questions,
        "comparison": comparison,
        "artifact": str(stable),
        "stamped_artifact": str(stamped),
        "note": (
            "Tier A only — do not run full 42-case suite until 8/8. "
            "Do not merge IKL until Tier A is green."
        ),
    }
    _write_atomic(stamped, report)
    _write_atomic(stable, report)
    if workspace_arts.is_dir():
        _write_atomic(workspace_arts / "tier_a_fix_report.json", report)
        _write_atomic(workspace_arts / stamped.name, report)
    try:
        opt = Path("/opt/cursor/artifacts")
        if opt.is_dir():
            _write_atomic(opt / "tier_a_fix_report.json", report)
            _write_atomic(opt / stamped.name, report)
    except Exception:
        pass

    print_health_summary(
        {
            "pass_rate": report["pass_rate"],
            "passed": passed,
            "total": len(summaries),
            "average_latency_ms": int(
                sum(s.get("latency_ms") or 0 for s in summaries) / max(1, len(summaries))
            ),
            "questions": questions,
            "comparison_metrics": {
                "fallback_rate": sum(1 for s in summaries if s.get("fallback")) / max(1, len(summaries)),
            },
        }
    )
    print(
        f"[tier-a] GATE={report['tier_a_gate']} {passed}/8 "
        f"recommend_full_suite={comparison['recommend_full_suite']} "
        f"artifact={stable}",
        flush=True,
    )
    return 0 if passed == 8 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("[tier-a] interrupted", flush=True)
        raise SystemExit(130)
