#!/usr/bin/env python3
"""AGI Financial Intelligence Acceptance Test v1.0 — live release gate.

Runs all 40 questions against LIVE Ask (POST /api/ui/search), scores each
against the 6-dimension rubric, computes the required suite metrics, and
writes:

    artifacts/afi_acceptance_v1.json          full report (partial written
                                               after every question so a hang
                                               doesn't lose progress)

Release PASS requires (per spec):
    Overall Score >= 95%, Financial Routing Accuracy = 100%,
    Financial Engine Utilization >= 95%, Generic Retrieval Pollution = 0%,
    Hallucinations = 0, Recommendation Policy = 100%,
    Unknown Entity Handling = 100%, executive answers first every time.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from ask_product_test import checks
from ask_product_test.afi_acceptance_v1 import AFI_ACCEPTANCE_40, SECTIONS, score_afi_answer
from ask_product_test.harness import AskProductHarness, _artifacts_dir


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _evaluate_one(case: Dict[str, Any], payload: Dict[str, Any], *, latency_ms: int, http_status: int) -> Dict[str, Any]:
    text = checks.extract_answer_text(payload) if isinstance(payload, dict) else ""
    evidence_n = checks.evidence_count(payload) if isinstance(payload, dict) else 0
    entities_blob = checks.flatten_text(checks.extract_entities(payload)) + " " + checks.flatten_text(payload.get("related_companies")) if isinstance(payload, dict) else ""
    engine_blob = checks.flatten_text(payload) if isinstance(payload, dict) else ""
    orch = checks.extract_orchestration(payload) if isinstance(payload, dict) else {}
    degraded = checks.is_degraded(payload) if isinstance(payload, dict) else True
    return score_afi_answer(
        case,
        text=text,
        evidence_count=evidence_n,
        entities_blob=entities_blob,
        engine_blob=engine_blob,
        orch=orch,
        latency_ms=latency_ms,
        http_status=http_status,
        degraded=degraded,
    )


def _percentile(values: List[int], pct: float) -> int:
    if not values:
        return 0
    s = sorted(values)
    k = (len(s) - 1) * pct
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return int(s[f] + (s[c] - s[f]) * (k - f))


def _compute_metrics(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(rows) or 1
    engine_required = [r for r in rows if r.get("requires_engine")]
    engine_hit = [r for r in engine_required if r.get("engine_signal_found")]
    financial_routing_accuracy = round(100.0 * len(engine_hit) / len(engine_required), 2) if engine_required else 100.0
    generic_pollution = round(100.0 * (len(engine_required) - len(engine_hit)) / len(engine_required), 2) if engine_required else 0.0

    policy_rows = [r for r in rows if r["id"] in ("E37", "E38")]
    policy_ok = sum(1 for r in policy_rows if not r["auto_fail_flags"].get("recommendation_policy_regression"))
    recommendation_policy_accuracy = round(100.0 * policy_ok / len(policy_rows), 2) if policy_rows else 100.0

    unknown_rows = [r for r in rows if r["id"] == "E39"]
    unknown_ok = sum(1 for r in unknown_rows if not r["auto_fail_flags"].get("hallucinated_entity"))
    unknown_entity_accuracy = round(100.0 * unknown_ok / len(unknown_rows), 2) if unknown_rows else 100.0

    hallucination_count = sum(
        1 for r in rows if r["auto_fail_flags"].get("hallucinated_entity") or r["auto_fail_flags"].get("wrong_company_injected")
    )
    exec_first_count = sum(1 for r in rows if not r["auto_fail_flags"].get("executive_did_not_answer_first"))
    exec_first_pct = round(100.0 * exec_first_count / total, 2)

    latencies = [r["latency_ms"] for r in rows if isinstance(r.get("latency_ms"), (int, float))]
    total_score = sum(r["final_score"] for r in rows)
    max_score = sum(r["max_score"] for r in rows)
    overall_pct = round(100.0 * total_score / max_score, 2) if max_score else 0.0

    exec_quality_avg = round(sum(r["dimension_scores"]["executive_quality"] for r in rows) / total, 2)

    by_section: Dict[str, Any] = {}
    for section in SECTIONS:
        srows = [r for r in rows if r["section"] == section]
        if not srows:
            continue
        by_section[section] = {
            "count": len(srows),
            "avg_score": round(sum(r["final_score"] for r in srows) / len(srows), 2),
            "avg_pct": round(100.0 * sum(r["final_score"] for r in srows) / (30 * len(srows)), 2),
        }

    return {
        "overall_score_pct": overall_pct,
        "total_score": total_score,
        "max_score": max_score,
        "financial_routing_accuracy_pct": financial_routing_accuracy,
        "financial_engine_utilization_pct": financial_routing_accuracy,
        "generic_retrieval_pollution_pct": generic_pollution,
        "executive_composer_quality_avg": exec_quality_avg,
        "hallucination_count": hallucination_count,
        "recommendation_policy_accuracy_pct": recommendation_policy_accuracy,
        "unknown_entity_accuracy_pct": unknown_entity_accuracy,
        "executive_answers_first_pct": exec_first_pct,
        "latency_ms_p50": _percentile(latencies, 0.50),
        "latency_ms_p95": _percentile(latencies, 0.95),
        "by_section": by_section,
        "engine_required_questions": len(engine_required),
        "engine_signal_found_count": len(engine_hit),
    }


def _release_decision(metrics: Dict[str, Any], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    criteria = {
        "overall_score_pct >= 95": metrics["overall_score_pct"] >= 95.0,
        "financial_routing_accuracy_pct == 100": metrics["financial_routing_accuracy_pct"] == 100.0,
        "financial_engine_utilization_pct >= 95": metrics["financial_engine_utilization_pct"] >= 95.0,
        "generic_retrieval_pollution_pct == 0": metrics["generic_retrieval_pollution_pct"] == 0.0,
        "hallucination_count == 0": metrics["hallucination_count"] == 0,
        "recommendation_policy_accuracy_pct == 100": metrics["recommendation_policy_accuracy_pct"] == 100.0,
        "unknown_entity_accuracy_pct == 100": metrics["unknown_entity_accuracy_pct"] == 100.0,
        "executive_answers_first_pct == 100": metrics["executive_answers_first_pct"] == 100.0,
    }
    passed = all(criteria.values())
    return {"pass": passed, "criteria": criteria}


def _top_failures(rows: List[Dict[str, Any]], n: int = 5) -> List[Dict[str, Any]]:
    ranked = sorted(rows, key=lambda r: r["final_score"])[:n]
    out = []
    for r in ranked:
        flags = list(r["auto_fail_flags"])
        root_cause = "; ".join(flags) if flags else "low topical/reasoning coverage in the visible answer"
        out.append(
            {
                "id": r["id"],
                "section": r["section"],
                "question": r["question"],
                "final_score": r["final_score"],
                "auto_fail_flags": flags,
                "root_cause": root_cause,
                "answer_excerpt": (r.get("answer") or "")[:300],
            }
        )
    return out


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")


def main() -> int:
    latency = int(os.environ.get("ASK_TEST_LATENCY_MS") or "120000")
    cooldown = float(os.environ.get("ASK_TEST_CASE_COOLDOWN_SEC", "6") or "6")
    h = AskProductHarness(latency_budget_ms=latency)
    out_dir = _artifacts_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    ws = Path("/workspace/artifacts")
    ws.mkdir(parents=True, exist_ok=True)

    print(
        f"[afi_acceptance_v1] mode={h.mode} base={h.base_url} cases={len(AFI_ACCEPTANCE_40)} cooldown={cooldown}s",
        flush=True,
    )

    rows: List[Dict[str, Any]] = []
    for i, case in enumerate(AFI_ACCEPTANCE_40, 1):
        if i > 1 and cooldown > 0 and h.mode == "live":
            time.sleep(cooldown)
        print(f"\n[{i}/40] {case['id']} ({case['section']}) — {case['prompt'][:90]}", flush=True)
        transport = h.ask(case["prompt"])
        payload = transport.get("payload") if isinstance(transport.get("payload"), dict) else {}
        row = _evaluate_one(
            case, payload, latency_ms=transport.get("latency_ms") or 0, http_status=transport.get("http_status") or 0
        )
        row["raw_payload_excerpt"] = {
            "ask_trace_id": (payload.get("ask_orchestration") or {}).get("ask_trace_id") if isinstance(payload, dict) else None,
            "intent": payload.get("intent") if isinstance(payload, dict) else None,
        }
        rows.append(row)
        print(
            f"  score={row['final_score']}/30 auto_fail={list(row['auto_fail_flags'])} "
            f"engine_hit={row['engine_signal_found']} ms={row.get('latency_ms')}",
            flush=True,
        )
        print(f"  answer: {(row.get('answer') or '')[:220]}", flush=True)

        # Partial write after every case.
        partial = {
            "suite": "AGI Financial Intelligence Acceptance Test v1.0",
            "timestamp": _ts(),
            "mode": h.mode,
            "base_url": h.base_url,
            "partial": True,
            "completed_so_far": len(rows),
            "planned_total": len(AFI_ACCEPTANCE_40),
            "questions": rows,
        }
        _write_json(ws / "afi_acceptance_v1.json", partial)
        _write_json(out_dir / "afi_acceptance_v1.json", partial)

    metrics = _compute_metrics(rows)
    decision = _release_decision(metrics, rows)
    top_failures = _top_failures(rows, 5)

    report = {
        "suite": "AGI Financial Intelligence Acceptance Test v1.0",
        "timestamp": _ts(),
        "mode": h.mode,
        "base_url": h.base_url,
        "total_questions": len(rows),
        "pass_mark_pct": 95,
        "metrics": metrics,
        "release_gate": decision,
        "top_5_failures": top_failures,
        "questions": rows,
    }
    _write_json(ws / "afi_acceptance_v1.json", report)
    _write_json(out_dir / "afi_acceptance_v1.json", report)

    print(
        f"\n[afi_acceptance_v1] overall={metrics['overall_score_pct']}% "
        f"routing={metrics['financial_routing_accuracy_pct']}% "
        f"engine_util={metrics['financial_engine_utilization_pct']}% "
        f"pollution={metrics['generic_retrieval_pollution_pct']}% "
        f"decision={'PASS' if decision['pass'] else 'FAIL'}",
        flush=True,
    )
    return 0 if decision["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
