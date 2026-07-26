"""Management Analyst — Can management be trusted?"""

from __future__ import annotations

from typing import Any

from institutional_analysts.base import as_list, company_name, opinion, pick_confidence, scrub_public


def analyse(ctx: dict[str, Any]) -> dict[str, Any]:
    cid = ctx.get("company_dossier") if isinstance(ctx.get("company_dossier"), dict) else {}
    ca = ctx.get("company_analysis") if isinstance(ctx.get("company_analysis"), dict) else {}
    leo = ctx.get("live_evidence") if isinstance(ctx.get("live_evidence"), dict) else {}
    de = ctx.get("decision_engine") if isinstance(ctx.get("decision_engine"), dict) else {}
    layers = {str(l.get("id")): l for l in (de.get("layers") or []) if isinstance(l, dict)}
    mgmt_layer = layers.get("management") or {}
    mgmt = cid.get("management") if isinstance(cid.get("management"), dict) else {}
    bq = ca.get("business_quality") if isinstance(ca.get("business_quality"), dict) else {}
    name = company_name(ctx)

    docs = as_list(leo.get("documents_used") or leo.get("announcements_used"), limit=6)
    evidence = docs or ["Annual disclosures and management commentary", "Capital allocation track record"]

    score = mgmt_layer.get("score") or bq.get("management_quality_score")
    try:
        score_f = float(score) if score is not None else None
    except Exception:
        score_f = None

    return opinion(
        role="management",
        question="Can management be trusted?",
        headline=f"{name}: trust rests on governance, capital allocation, and communication consistency.",
        sections={
            "governance": mgmt.get("governance") or "Board oversight and related-party discipline are central",
            "capital_allocation": mgmt.get("capital_allocation") or bq.get("capital_allocation") or "Allocation across growth, buffers, and owner returns",
            "execution": mgmt.get("execution") or mgmt_layer.get("reasoning") or "Delivery versus prior guidance is the practical test",
            "communication": mgmt.get("communication") or "Clarity in results commentary and forward indicators",
            "promoter": mgmt.get("promoter") or cid.get("promoter") or "Promoter alignment and pledge risk deserve watch",
            "board": mgmt.get("board") or "Independent challenge quality matters in stress periods",
            "management_score": score_f if score_f is not None else scrub_public(bq.get("management_quality") or "n/a", limit=80),
        },
        evidence=evidence,
        confidence=pick_confidence(mgmt.get("confidence"), mgmt_layer.get("score"), default=0.52),
        score=score_f,
        word_limit=400,
    )
