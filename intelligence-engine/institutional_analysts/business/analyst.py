"""Business Analyst — Is this a good business?"""

from __future__ import annotations

from typing import Any

from institutional_analysts.base import as_list, company_name, opinion, pick_confidence, scrub_public


def analyse(ctx: dict[str, Any]) -> dict[str, Any]:
    ca = ctx.get("company_analysis") if isinstance(ctx.get("company_analysis"), dict) else {}
    cid = ctx.get("company_dossier") if isinstance(ctx.get("company_dossier"), dict) else {}
    academy = ctx.get("finance_academy") if isinstance(ctx.get("finance_academy"), dict) else {}
    leo = ctx.get("live_evidence") if isinstance(ctx.get("live_evidence"), dict) else {}
    name = company_name(ctx)

    bq = ca.get("business_quality") if isinstance(ca.get("business_quality"), dict) else {}
    identity = cid.get("identity") if isinstance(cid.get("identity"), dict) else {}
    profile = cid.get("business_profile") if isinstance(cid.get("business_profile"), dict) else {}
    thesis = ca.get("investment_thesis") if isinstance(ca.get("investment_thesis"), dict) else {}

    model = (
        scrub_public(profile.get("business_model") or thesis.get("business_overview") or bq.get("business_model"), limit=260)
        or f"{name} operates a deposit- and franchise-driven business model in its core market."
    )
    score = bq.get("business_quality_score")
    try:
        score_f = float(score) if score is not None else None
    except Exception:
        score_f = None

    evidence = []
    evidence.extend(as_list(leo.get("documents_used"), limit=4))
    evidence.extend(as_list((academy.get("applied_concepts") or [])[:3], limit=3))
    evidence.extend(as_list(bq.get("strengths") or thesis.get("competitive_advantages"), limit=3))

    return opinion(
        role="business",
        question="Is this a good business?",
        headline=f"{name}: franchise quality hinges on durable demand drivers and capital discipline.",
        sections={
            "business_model": model,
            "revenue_drivers": bq.get("revenue_drivers") or profile.get("revenue_drivers") or thesis.get("industry_drivers") or ["Core franchise demand", "Pricing / mix", "Scale efficiencies"],
            "competitive_position": bq.get("competitive_position") or profile.get("competitive_position") or identity.get("industry") or "Established franchise in its peer set",
            "competitive_advantages": bq.get("moat") or bq.get("advantages") or thesis.get("competitive_advantages") or ["Scale", "Distribution", "Brand / trust"],
            "pricing_power": bq.get("pricing_power") or "Mixed — depends on competitive intensity and product mix",
            "brand": bq.get("brand") or profile.get("brand") or f"{name} brand recognition supports customer retention",
            "management_quality": bq.get("management_quality") or "Assessed via capital allocation and execution consistency",
            "capital_allocation": bq.get("capital_allocation") or "Reinvestment versus shareholder returns must stay disciplined",
            "growth_opportunities": bq.get("growth_opportunities") or thesis.get("catalysts") or ["Share gains", "Adjacent products", "Operating leverage"],
            "business_risks": bq.get("risks") or thesis.get("risks") or ["Competition", "Execution", "Regulatory change"],
            "business_quality_score": score_f if score_f is not None else "n/a",
        },
        evidence=evidence or [f"Institutional business profile for {name}"],
        confidence=pick_confidence(bq.get("confidence"), ca.get("confidence"), default=0.58),
        score=score_f,
        word_limit=500,
    )
