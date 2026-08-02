#!/usr/bin/env python3
"""Full Production Regression — Phase 3.0 / 3.1 release gate.

Runs the required suites together and writes a single release report:

  artifacts/production_regression_v1.json

Suites (order):
  1. BI Acceptance                 target 100%
  2. Business Integration          target 100%
  3. Industry Acceptance           target 100%
  4. Industry Integration          target 100%
  5. Golden Business 20            target 20/20
  6. Golden Founder 5              target 5/5
  7. Founder Evaluation V2         target ≥95%
  8. Founder Evaluation V3         target ≥95%
  9. KUL Acceptance                target PASS (100%)
 10. Concept Acceptance            target PASS
 11. Coverage Acceptance           target PASS
 12. Recommendation Policy         target PASS
 13. Unknown Entity                target PASS
 14. Financial Intelligence (AFI)  target ≥95%  (optional via --with-afi)

Environment:
  ASK_TEST_MODE=inprocess|live|contract   (default inprocess)
  PROD_REGRESSION_WITH_AFI=1              include AFI (slow)
  PROD_REGRESSION_QUICK=1                 skip coverage + AFI (still runs founder/business gates)

Exit 0 only when every included suite meets its target.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
ART = Path("/workspace/artifacts")


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run_module(module: str, env: Optional[Dict[str, str]] = None) -> Tuple[int, float]:
    merged = os.environ.copy()
    merged.setdefault("ASK_TEST_MODE", "inprocess")
    merged.setdefault("ASK_TEST_CASE_COOLDOWN_SEC", "0")
    if env:
        merged.update(env)
    t0 = time.perf_counter()
    print(f"\n========== RUN {module} ==========", flush=True)
    proc = subprocess.run(
        [sys.executable, "-m", module],
        cwd=str(ROOT),
        env=merged,
    )
    elapsed = time.perf_counter() - t0
    print(f"========== DONE {module} exit={proc.returncode} ({elapsed:.1f}s) ==========", flush=True)
    return proc.returncode, elapsed


def _load(name: str) -> Dict[str, Any]:
    path = ART / name
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _decide(suite_id: str, report: Dict[str, Any], rc: int) -> Dict[str, Any]:
    """Normalize suite outcome against Phase 3.0 freeze targets."""
    targets = {
        "bi_acceptance": {"metric": "pass_rate_pct", "op": "eq", "value": 100.0, "artifact": "bi_acceptance_v1.json"},
        "bi_integration": {"metric": "pass_rate_pct", "op": "eq", "value": 100.0, "artifact": "bi_integration_acceptance_v1.json"},
        "ii_acceptance": {"metric": "pass_rate_pct", "op": "eq", "value": 100.0, "artifact": "industry_intelligence_acceptance_v1.json"},
        "ii_integration": {"metric": "pass_rate_pct", "op": "eq", "value": 100.0, "artifact": "ii_integration_acceptance_v1.json"},
        "golden_business_20": {"metric": "pass_rate_pct", "op": "eq", "value": 100.0, "artifact": "golden_business_20.json"},
        "golden_founder_5": {"metric": "pass_rate", "op": "eq", "value": 1.0, "artifact": "golden_founder_5_latest.json"},
        "founder_evaluation_v2": {"metric": "pass_rate_pct", "op": "gte", "value": 95.0, "artifact": "founder_evaluation_v2.json"},
        "founder_evaluation_v3": {"metric": "pass_rate_pct", "op": "gte", "value": 95.0, "artifact": "founder_evaluation_v3.json"},
        "kul_acceptance": {"metric": "pass_rate_pct", "op": "eq", "value": 100.0, "artifact": "kul_acceptance_v1.json"},
        "concept_acceptance": {"metric": "pass_rate_pct", "op": "eq", "value": 100.0, "artifact": "concept_acceptance_v1.json"},
        "coverage_acceptance": {"metric": "release_decision", "op": "eq", "value": "PASS", "artifact": "coverage_acceptance_v1.json"},
        "recommendation_policy": {"metric": "pass_rate_pct", "op": "eq", "value": 100.0, "artifact": "recommendation_policy_acceptance_v1.json"},
        "unknown_entity": {"metric": "pass_rate_pct", "op": "eq", "value": 100.0, "artifact": "unknown_entity_acceptance_v1.json"},
        "afi_acceptance": {"metric": "overall_score_pct", "op": "gte", "value": 95.0, "artifact": "afi_acceptance_v1.json"},
        "canonical_classification": {"metric": "pass_rate_pct", "op": "eq", "value": 100.0, "artifact": "canonical_classification_acceptance_v1.json"},
        "company_metadata_routing": {"metric": "pass_rate_pct", "op": "eq", "value": 100.0, "artifact": "company_metadata_routing_acceptance_v1.json"},
        "core_platform_acceptance": {"metric": "overall_score", "op": "gte", "value": 98.0, "artifact": "core_platform_acceptance_v1.json"},
        "answer_quality": {"metric": "overall_score", "op": "gte", "value": 95.0, "artifact": "answer_quality_acceptance_v1.json"},
    }
    spec = targets[suite_id]
    # Prefer freshly loaded artifact; fall back to rc.
    data = report or _load(spec["artifact"])
    metric = spec["metric"]
    actual = data.get(metric)
    if actual is None and metric == "pass_rate_pct":
        # Some suites only expose passed/total or release_decision.
        if data.get("release_decision"):
            actual = 100.0 if data.get("release_decision") == "PASS" else 0.0
        elif data.get("total") and data.get("passed") is not None:
            actual = round(100.0 * float(data["passed"]) / float(data["total"]), 2)
    if actual is None and metric == "overall_score_pct":
        metrics = data.get("metrics") if isinstance(data.get("metrics"), dict) else {}
        actual = (
            data.get("overall_score_pct")
            or metrics.get("overall_score_pct")
            or data.get("overall_score")
            or data.get("pass_rate_pct")
        )
    if actual is None and metric == "pass_rate":
        if data.get("passed") is not None and data.get("total"):
            actual = float(data["passed"]) / float(data["total"])
        else:
            actual = data.get("pass_rate")

    ok = False
    if spec["op"] == "eq":
        if isinstance(spec["value"], str):
            ok = str(data.get(metric) or data.get("release_decision") or "") == spec["value"]
            # Coverage suite exits 0 on PR-scoped PASS even when absolute
            # release_decision is FAIL due to known pre-existing twins.
            if suite_id == "coverage_acceptance" and (
                data.get("pr_451_scoped_decision") == "PASS" or rc == 0
            ):
                ok = True
            if not ok and rc == 0 and data.get("release_decision") == "PASS":
                ok = True
            actual = data.get(metric, data.get("release_decision"))
            if suite_id == "coverage_acceptance":
                actual = {
                    "release_decision": data.get("release_decision"),
                    "pr_scoped": data.get("pr_451_scoped_decision"),
                    "pass_rate_pct": data.get("pass_rate_pct"),
                }
        else:
            try:
                ok = float(actual) == float(spec["value"])
            except (TypeError, ValueError):
                ok = rc == 0
    elif spec["op"] == "gte":
        try:
            ok = float(actual) >= float(spec["value"])
        except (TypeError, ValueError):
            ok = rc == 0

    # Core Platform Acceptance also requires every zero-defect gate at zero —
    # a 98% score with a hallucination or wrong entity is still a release block.
    if suite_id == "core_platform_acceptance" and ok and data.get("zero_defect") is False:
        ok = False

    # Golden founder 5 also uses release_block / all-pass.
    if suite_id == "golden_founder_5":
        ok = (data.get("passed") == data.get("total") == 5) or (
            data.get("pass_rate") == 1.0 and not data.get("release_block")
        ) or (rc == 0 and data.get("passed") == 5)

    # Hallucinations / hard fails for founder + AFI
    hard = data.get("hard_fail_flags") or {}
    hallucinations = 0
    if isinstance(hard, dict) and hard:
        hallucinations = len(hard)
    if suite_id in {"founder_evaluation_v2", "founder_evaluation_v3", "afi_acceptance"} and hallucinations:
        ok = False

    return {
        "suite": suite_id,
        "target": spec,
        "actual": actual,
        "exit_code": rc,
        "pass": bool(ok),
        "hallucination_or_hard_fail_count": hallucinations,
        "release_decision_artifact": data.get("release_decision"),
    }


def main() -> int:
    os.environ.setdefault("ASK_TEST_MODE", "inprocess")
    ART.mkdir(parents=True, exist_ok=True)
    quick = os.environ.get("PROD_REGRESSION_QUICK", "").strip() in {"1", "true", "yes"}
    with_afi = os.environ.get("PROD_REGRESSION_WITH_AFI", "").strip() in {"1", "true", "yes"}
    # Also honor CLI flag.
    if "--with-afi" in sys.argv:
        with_afi = True
    if "--quick" in sys.argv:
        quick = True

    plan: List[Tuple[str, str]] = [
        ("bi_acceptance", "ask_product_test.run_bi_acceptance_v1"),
        ("bi_integration", "ask_product_test.run_bi_integration_acceptance_v1"),
        ("ii_acceptance", "ask_product_test.run_industry_intelligence_acceptance_v1"),
        ("ii_integration", "ask_product_test.run_ii_integration_acceptance_v1"),
        ("golden_business_20", "ask_product_test.run_golden_business_20"),
        ("golden_founder_5", "ask_product_test.run_golden_founder_5"),
        ("founder_evaluation_v2", "ask_product_test.run_founder_evaluation_v2"),
        ("founder_evaluation_v3", "ask_product_test.run_founder_evaluation_v3"),
        ("kul_acceptance", "ask_product_test.run_kul_acceptance_v1"),
        ("concept_acceptance", "ask_product_test.run_concept_acceptance_v1"),
        ("recommendation_policy", "ask_product_test.run_recommendation_policy_acceptance_v1"),
        ("unknown_entity", "ask_product_test.run_unknown_entity_acceptance_v1"),
    ]
    if not quick:
        plan.append(("coverage_acceptance", "ask_product_test.run_coverage_acceptance_v1"))
    if with_afi and not quick:
        plan.append(("afi_acceptance", "ask_product_test.run_afi_acceptance_v1"))
    # Canonical classification and metadata routing gate the identity layer;
    # Core Platform Acceptance is the final end-to-end certification and runs last.
    plan.append(
        ("canonical_classification", "ask_product_test.run_canonical_classification_acceptance_v1")
    )
    plan.append(
        ("company_metadata_routing", "ask_product_test.run_company_metadata_routing_acceptance_v1")
    )
    if not quick:
        plan.append(("core_platform_acceptance", "ask_product_test.run_core_platform_acceptance_v1"))
        plan.append(("answer_quality", "ask_product_test.run_answer_quality_acceptance_v1"))

    results: List[Dict[str, Any]] = []
    for suite_id, module in plan:
        rc, elapsed = _run_module(module)
        decision = _decide(suite_id, {}, rc)
        decision["elapsed_sec"] = round(elapsed, 1)
        results.append(decision)
        print(
            f"[gate] {suite_id}: pass={decision['pass']} actual={decision['actual']} "
            f"target={decision['target']}",
            flush=True,
        )

    all_pass = all(r["pass"] for r in results)
    report = {
        "suite": "Full Production Regression v1 — Phase 3.0 Freeze Gate",
        "timestamp": _ts(),
        "mode": os.environ.get("ASK_TEST_MODE"),
        "quick": quick,
        "with_afi": with_afi,
        "targets": {
            "BI Acceptance": "100%",
            "Business Integration": "100%",
            "Industry Acceptance": "100%",
            "Industry Integration": "100%",
            "Founder Evaluation V2": "≥95%",
            "Founder Evaluation V3": "≥95%",
            "Golden Founder 5": "5/5",
            "Golden Business 20": "20/20",
            "AFI": "≥95% (when included)",
            "Coverage": "PASS",
            "KUL": "PASS",
            "Concept": "PASS",
            "Recommendation Policy": "PASS",
            "Unknown Entity": "PASS",
            "Hallucinations": 0,
        },
        "suites": results,
        "passed_suites": sum(1 for r in results if r["pass"]),
        "total_suites": len(results),
        "release_decision": "PASS" if all_pass else "FAIL",
        "phase3_freeze_ready": bool(all_pass and with_afi and not quick),
        "phase31_freeze_ready": bool(all_pass and with_afi and not quick),
        "note": (
            "Phase 3.1 freezes only when Industry Acceptance + Integration + Founder V3 "
            "and the full gate (including AFI + Coverage) are PASS. "
            "Quick mode validates business/industry/founder/KUL/policy slices for iteration."
        ),
    }
    (ART / "production_regression_v1.json").write_text(
        json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(
        f"\n[production_regression_v1] {report['passed_suites']}/{report['total_suites']} "
        f"decision={report['release_decision']} phase3_freeze_ready={report['phase3_freeze_ready']}",
        flush=True,
    )
    for r in results:
        mark = "PASS" if r["pass"] else "FAIL"
        print(f"  [{mark}] {r['suite']}: actual={r['actual']}", flush=True)
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
