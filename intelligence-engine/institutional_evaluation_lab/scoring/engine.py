"""Aggregate judge dimensions into per-question and suite scores."""

from __future__ import annotations

from typing import Any

from institutional_evaluation_lab.schema import DIMENSION_WEIGHTS


def score_question(
    question: dict[str, Any],
    judgments: list[dict[str, Any]],
) -> dict[str, Any]:
    by_dim = {j["dimension"]: j for j in judgments}
    weighted = 0.0
    weight_sum = 0.0
    failures: list[str] = []
    for dim, w in DIMENSION_WEIGHTS.items():
        j = by_dim.get(dim) or {}
        s = float(j.get("score") or 0.0)
        weighted += w * s
        weight_sum += w
        if j.get("passed") is False and j.get("root_cause"):
            failures.append(str(j["root_cause"]))
    overall = round(weighted / weight_sum if weight_sum else 0.0, 2)
    passed = overall >= 70.0 and not any(
        f in failures for f in ("fabricated_or_invented", "future_leakage", "quality_gate_fail")
    )
    return {
        "question_id": question.get("question_id"),
        "category": question.get("category"),
        "difficulty": question.get("difficulty"),
        "suite": question.get("suite"),
        "overall": overall,
        "passed": passed,
        "dimensions": {d: by_dim.get(d, {}) for d in DIMENSION_WEIGHTS},
        "root_causes": failures,
        "verdict": "PASS" if passed else ("PARTIAL" if overall >= 55 else "FAIL"),
    }


def aggregate_suite(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "n": 0,
            "pass_pct": 0.0,
            "mean_score": 0.0,
            "by_category": {},
            "by_verdict": {},
            "top_root_causes": [],
        }
    n = len(rows)
    passes = sum(1 for r in rows if r.get("passed"))
    mean_score = round(sum(float(r.get("overall") or 0) for r in rows) / n, 2)
    by_cat: dict[str, list[float]] = {}
    by_verdict: dict[str, int] = {}
    causes: dict[str, int] = {}
    for r in rows:
        cat = str(r.get("category") or "unknown")
        by_cat.setdefault(cat, []).append(float(r.get("overall") or 0))
        v = str(r.get("verdict") or "?")
        by_verdict[v] = by_verdict.get(v, 0) + 1
        for c in r.get("root_causes") or []:
            causes[str(c)] = causes.get(str(c), 0) + 1
    top_causes = sorted(causes.items(), key=lambda x: (-x[1], x[0]))[:20]
    return {
        "n": n,
        "pass_pct": round(100.0 * passes / n, 2),
        "mean_score": mean_score,
        "by_category": {
            k: {"n": len(v), "mean_score": round(sum(v) / len(v), 2)} for k, v in sorted(by_cat.items())
        },
        "by_verdict": by_verdict,
        "top_root_causes": [{"cause": c, "count": n_} for c, n_ in top_causes],
        "passed": passes,
        "failed": n - passes,
    }
