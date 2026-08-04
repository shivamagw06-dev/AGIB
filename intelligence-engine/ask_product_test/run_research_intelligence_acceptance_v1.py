#!/usr/bin/env python3
"""Run Research Intelligence Acceptance Test v1.0 (engine in-process).

Does NOT call Ask / KUL. Exit 0 iff pass rate = 100%.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ask_product_test.research_intelligence_acceptance_v1 import (  # noqa: E402
    RI_ACCEPTANCE_400,
    evaluate_ri_case,
)
from research_intelligence.production import analyse, health  # noqa: E402


def main() -> int:
    h = health()
    print(
        f"[ri_acceptance_v1] version={h.get('version')} "
        f"entities={h.get('entity_count')} ask_wired={h.get('ask_wired')}",
        flush=True,
    )
    assert h.get("ask_wired") is False, "Ask must remain unwired until Acceptance = 100%"
    assert len(RI_ACCEPTANCE_400) == 400

    rows = []
    for i, case in enumerate(RI_ACCEPTANCE_400, 1):
        print(f"[{i}/400] {case['id']} — {case['prompt'][:72]}", flush=True)
        try:
            payload = analyse(case["prompt"], entity=case.get("entity"))
        except Exception as exc:
            payload = {
                "ok": False,
                "summary": "",
                "executive_summary": "",
                "modules_used": [],
                "fabricated": False,
                "recommendation": "BUY",
                "error": str(exc),
            }
        row = evaluate_ri_case(case, payload)
        rows.append(row)
        print(
            f"  pass={row['pass']} hits={row['topic_hits']} "
            f"failed={row['failed_assertions']}",
            flush=True,
        )

    passed = sum(1 for r in rows if r["pass"])
    by_cat: dict = {}
    for r in rows:
        by_cat.setdefault(r["category"], {"count": 0, "passed": 0})
        by_cat[r["category"]]["count"] += 1
        if r["pass"]:
            by_cat[r["category"]]["passed"] += 1

    rate = round(100.0 * passed / len(rows), 2) if rows else 0.0
    report = {
        "suite": "Research Intelligence Acceptance Test v1.0",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "version": h.get("version"),
        "ask_wired": bool(h.get("ask_wired")),
        "recommendation_policy": h.get("recommendation_policy"),
        "knowledge_authority": h.get("knowledge_authority"),
        "total": len(rows),
        "passed": passed,
        "pass_rate_pct": rate,
        "gate_pct": 100.0,
        "by_category": {
            k: {**v, "pass_rate_pct": round(100.0 * v["passed"] / v["count"], 2)}
            for k, v in by_cat.items()
        },
        "release_decision": "PASS" if rate >= 100.0 else "FAIL",
        "questions": rows,
    }
    out = Path("/workspace/artifacts")
    out.mkdir(parents=True, exist_ok=True)
    (out / "research_intelligence_acceptance_v1.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"\n[ri_acceptance_v1] {passed}/{len(rows)} ({rate}%) "
        f"decision={report['release_decision']}",
        flush=True,
    )
    for k, v in report["by_category"].items():
        print(f"  {k}: {v['passed']}/{v['count']} ({v['pass_rate_pct']}%)", flush=True)
    fails = [r for r in rows if not r["pass"]]
    if fails:
        print("\nFailures:", flush=True)
        for r in fails[:50]:
            print(
                f"  {r['id']} [{r['category']}] failed={r['failed_assertions']} "
                f":: {r['prompt'][:60]}",
                flush=True,
            )
            print(f"    summary={r['summary'][:160]}", flush=True)
    return 0 if report["release_decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
