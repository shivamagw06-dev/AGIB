"""FDI analyse pipeline — compare periods, emit material change intelligence."""

from __future__ import annotations

from typing import Any

from filing_diff.capital_allocation_diff.diff import capital_allocation_diff
from filing_diff.comparator.periods import load_comparison_context
from filing_diff.confidence.score import score_diff
from filing_diff.evidence.attach import evidence_for_changes
from filing_diff.governance_diff.diff import governance_diff
from filing_diff.guidance_diff.diff import guidance_diff
from filing_diff.management_diff.diff import management_diff
from filing_diff.notes_diff.diff import notes_diff
from filing_diff.ownership_diff.diff import ownership_diff
from filing_diff.reports.build import build_report
from filing_diff.risks_diff.diff import risks_diff
from filing_diff.schema import FDI_VERSION
from filing_diff.segment_diff.diff import segment_diff
from filing_diff.statement_diff.diff import statement_diff
from filing_diff.timeline.build import build_change_timeline


def analyse_diff(ticker: str) -> dict[str, Any]:
    ctx = load_comparison_context(ticker)
    if not ctx.get("found"):
        return {"ticker": ticker.upper(), "found": False, "fdi_version": FDI_VERSION}

    records = []
    records += statement_diff(ctx)
    note_rows = notes_diff(ctx)
    for r in note_rows:
        if "Impairment" in r.metric or "Revenue_Recognition" in r.metric or "Accounting_Policy" in r.metric:
            r.domain = "accounting"
    records += note_rows
    records += guidance_diff(ctx)
    records += management_diff(ctx)
    records += risks_diff(ctx)
    records += segment_diff(ctx)
    records += capital_allocation_diff(ctx)
    records += governance_diff(ctx)
    records += ownership_diff(ctx)

    changes = [r.to_dict() for r in records]
    # drop ignores / cosmetics from primary list but keep audit
    material = [c for c in changes if not c.get("cosmetic") and c.get("materiality") != "ignore"]
    confidence = score_diff(changes)
    evidence = evidence_for_changes(material, ctx.get("documents") or [])
    # attach prior doc stub into evidence docs list for linkage display
    docs = list(ctx.get("documents") or [])
    prev_docs = ((ctx.get("qual_by_period") or {}).get(ctx.get("previous_period") or "") or {}).get("docs") or []
    for d in prev_docs:
        if d and not any(x.get("doc_id") == d for x in docs):
            docs.append({"doc_id": d, "title": d, "as_of": "", "evidence_tier": 2})
    evidence = evidence_for_changes(material, docs)
    timeline = build_change_timeline(material, ctx)
    report = build_report(
        ticker=ctx["ticker"],
        ctx=ctx,
        changes=changes,
        confidence=confidence,
        evidence=evidence,
    )

    return {
        "ticker": ctx["ticker"],
        "found": True,
        "fdi_version": FDI_VERSION,
        "primary_question": "What materially changed since the previous filing?",
        "comparison": ctx.get("comparison_pair"),
        "current_period": ctx.get("current_period"),
        "previous_period": ctx.get("previous_period"),
        "changes": material,
        "all_detected": changes,
        "timeline": timeline,
        "evidence": evidence,
        "confidence": confidence,
        "report": report,
        "origin": "filing_diff_engine",
    }
