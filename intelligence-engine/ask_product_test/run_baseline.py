#!/usr/bin/env python3
"""Capture a live Ask product baseline report (always writes artifacts).

Usage:
  cd intelligence-engine
  ASK_TEST_MODE=live \\
  ASK_TEST_BASE=https://finance-news-backend-19i5.onrender.com \\
  ASK_TEST_LATENCY_MS=120000 \\
  ASK_TEST_BASELINE_NAME=ask_test_report_pre_ikl.json \\
    python3 -m ask_product_test.run_baseline

Optional:
  ASK_TEST_INCLUDE_REGRESSION=1   # include CIO sample (default limit 5)
  ASK_TEST_REGRESSION_LIMIT=5
  ASK_TEST_INCLUDE_IKL=1          # include Tier IKL soft prompts
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

from ask_product_test.harness import AskProductHarness, cio_cases_from_frozen, print_health_summary, write_report
from ask_product_test.prompts import CONTEXT_ISOLATION_SEQUENCE, IKL_PROMPTS, SMOKE_PROMPTS, UNKNOWN_COMPANY_PROMPT


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _limit(cases: List[dict]) -> List[dict]:
    raw = os.environ.get("ASK_TEST_REGRESSION_LIMIT", "5").strip()
    try:
        n = max(1, int(raw))
    except ValueError:
        n = 5
    return cases[:n]


def main() -> int:
    latency = int(os.environ.get("ASK_TEST_LATENCY_MS", "120000"))
    h = AskProductHarness(latency_budget_ms=latency)
    sections: Dict[str, Any] = {}
    questions: List[Dict[str, Any]] = []

    print(f"[baseline] mode={h.mode} base={h.base_url} latency_budget_ms={latency}", flush=True)

    smoke = h.run_cases(list(SMOKE_PROMPTS), suite="Tier A — Product Smoke")
    questions.extend(smoke.get("questions") or [])
    sections["tier_a"] = {
        "passed": smoke.get("passed"),
        "total": smoke.get("total"),
        "pass_rate": smoke.get("pass_rate"),
        "comparison_metrics": smoke.get("comparison_metrics"),
    }

    if str(os.environ.get("ASK_TEST_INCLUDE_REGRESSION", "1")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        cio = _limit(cio_cases_from_frozen())
        cio_report = h.run_cases(cio, suite="Tier B — CIO sample")
        questions.extend(cio_report.get("questions") or [])
        unknown_t = h.ask(UNKNOWN_COMPANY_PROMPT["prompt"], case=UNKNOWN_COMPANY_PROMPT)
        unknown_row = h.evaluate(UNKNOWN_COMPANY_PROMPT, unknown_t)
        questions.append(unknown_row)
        isolation = h.run_cases(
            CONTEXT_ISOLATION_SEQUENCE,
            suite="Tier B — Context Isolation",
            isolate_sequence=True,
        )
        questions.extend(isolation.get("questions") or [])
        sections["tier_b"] = {
            "cio": {
                "passed": cio_report.get("passed"),
                "total": cio_report.get("total"),
                "pass_rate": cio_report.get("pass_rate"),
            },
            "unknown_company": {"pass": unknown_row.get("pass")},
            "isolation": {
                "passed": isolation.get("passed"),
                "total": isolation.get("total"),
                "pass_rate": isolation.get("pass_rate"),
            },
        }

    if str(os.environ.get("ASK_TEST_INCLUDE_IKL", "1")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        # Soft IKL (no ASK_TEST_IKL_STRICT) — records memory misses for pre-deploy baseline
        os.environ.pop("ASK_TEST_IKL_STRICT", None)
        ikl = h.run_cases(list(IKL_PROMPTS), suite="Tier IKL — soft baseline")
        questions.extend(ikl.get("questions") or [])
        sections["tier_ikl"] = {
            "passed": ikl.get("passed"),
            "total": ikl.get("total"),
            "pass_rate": ikl.get("pass_rate"),
            "comparison_metrics": ikl.get("comparison_metrics"),
        }

    passed = sum(1 for q in questions if q.get("pass"))
    total = len(questions)
    latencies = [q.get("latency_ms") or 0 for q in questions]
    from ask_product_test.harness import _comparison_metrics

    report = {
        "suite": "Founder live baseline (pre/post IKL)",
        "timestamp": _ts(),
        "mode": h.mode,
        "base_url": h.base_url,
        "latency_budget_ms": latency,
        "pass_rate": (passed / total) if total else 0.0,
        "passed": passed,
        "total": total,
        "average_latency_ms": int(sum(latencies) / len(latencies)) if latencies else 0,
        "questions": questions,
        "sections": sections,
        "comparison_metrics": _comparison_metrics(questions),
        "note": "Baseline capture always writes; product gates are informational here.",
    }
    print_health_summary(report)
    primary = (os.environ.get("ASK_TEST_REPORT_NAME") or "ask_test_report.json").strip()
    path = write_report(report, filename=primary or "ask_test_report.json")
    baseline = (os.environ.get("ASK_TEST_BASELINE_NAME") or "ask_test_report_pre_ikl.json").strip()
    path_b = write_report(report, filename=baseline)
    # Durable copy under /opt/cursor/artifacts when available
    try:
        opt = "/opt/cursor/artifacts"
        if os.path.isdir(opt):
            import json
            from pathlib import Path

            Path(opt, baseline).write_text(
                json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8"
            )
    except Exception:
        pass
    print(f"[baseline] wrote {path}", flush=True)
    print(f"[baseline] wrote {path_b}", flush=True)
    print(
        f"[baseline] pass_rate={report['pass_rate']:.0%} "
        f"avg_latency_ms={report['average_latency_ms']} "
        f"fallback_rate={report['comparison_metrics'].get('fallback_rate')}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
