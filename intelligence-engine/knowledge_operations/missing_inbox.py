"""Missing Knowledge Inbox — prioritized gaps to clear, not search."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from knowledge_operations.schema import (
    CLASS_LABELS,
    MISSING_PRIORITY,
    PRIORITY_RANK,
)


def _company_name(ticker: str) -> str:
    try:
        from institutional_evidence.schema import PHASE1_TOP20

        for row in PHASE1_TOP20:
            if row["ticker"] == ticker:
                return str(row["company"])
    except Exception:
        pass
    return ticker


def build_missing_inbox(*, scope: str = "TOP20", limit: int = 50) -> Dict[str, Any]:
    """
    Today's highest-impact missing knowledge.

    One row per (company, missing class) ranked Critical → Low, then by tier.
    """
    from institutional_coverage_factory.universe import top20_tickers, tier_for_ticker
    from institutional_coverage_factory.scorer.score import score_evidence_classes

    scope_u = str(scope or "TOP20").upper()
    if scope_u == "TOP20":
        tickers = top20_tickers()
    else:
        try:
            from institutional_coverage_factory.universe import ordered_universe

            tickers = [c["ticker"] for c in ordered_universe()]
            if scope_u == "NIFTY50":
                tickers = [t for t in tickers if tier_for_ticker(t) in {"TOP20", "NIFTY50"}]
            elif scope_u == "NIFTY100":
                tickers = [
                    t
                    for t in tickers
                    if tier_for_ticker(t) in {"TOP20", "NIFTY50", "NIFTY100"}
                ]
        except Exception:
            tickers = top20_tickers()

    items: List[Dict[str, Any]] = []
    for t in tickers:
        try:
            score = score_evidence_classes(t)
        except Exception:
            continue
        missing = list(score.get("missing_classes") or [])
        tier = tier_for_ticker(t)
        for class_id in missing:
            # Skip non-uploadable structural classes from upload CTA prominence
            priority = MISSING_PRIORITY.get(class_id, "Medium")
            label = CLASS_LABELS.get(class_id, class_id.replace("_", " ").title())
            uploadable = class_id not in {"company_memory", "knowledge_graph"}
            items.append(
                {
                    "ticker": t,
                    "company": _company_name(t),
                    "missing": label,
                    "missing_class": class_id,
                    "priority": priority,
                    "priority_rank": PRIORITY_RANK.get(priority, 9),
                    "tier": tier,
                    "coverage_pct": score.get("coverage_pct"),
                    "uploadable": uploadable,
                    "impact_note": f"Clears {label} gap for {t}",
                }
            )

    items.sort(
        key=lambda r: (
            r.get("priority_rank", 9),
            0 if r.get("tier") == "TOP20" else 1,
            -(float(r.get("coverage_pct") or 0)),
            r.get("ticker") or "",
        )
    )
    capped = items[: max(1, min(int(limit), 200))]
    by_priority: Dict[str, int] = {}
    for r in capped:
        p = r["priority"]
        by_priority[p] = by_priority.get(p, 0) + 1

    return {
        "ok": True,
        "title": "Today's Highest-Impact Missing Knowledge",
        "scope": scope_u,
        "count": len(capped),
        "total_gaps": len(items),
        "by_priority": by_priority,
        "items": capped,
        "workflow": "Clear the inbox — do not search for gaps.",
    }


def missing_for_ticker(ticker: str) -> Dict[str, Any]:
    from institutional_coverage_factory.scorer.score import score_evidence_classes

    t = str(ticker or "").upper().strip()
    score = score_evidence_classes(t)
    missing = list(score.get("missing_classes") or [])
    return {
        "ok": True,
        "ticker": t,
        "coverage_pct": score.get("coverage_pct"),
        "missing": [
            {
                "class_id": c,
                "label": CLASS_LABELS.get(c, c),
                "priority": MISSING_PRIORITY.get(c, "Medium"),
                "uploadable": c not in {"company_memory", "knowledge_graph"},
            }
            for c in missing
        ],
        "classes": score.get("classes"),
    }
