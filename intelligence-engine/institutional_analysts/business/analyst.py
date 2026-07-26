"""Business Analyst — Is this a business we would like to own?"""

from __future__ import annotations

from typing import Any

from institutional_analysts.base import as_list, company_name, pick_confidence, structured_opinion


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
        profile.get("business_model")
        or thesis.get("business_overview")
        or bq.get("business_model")
        or identity.get("business_model")
        or f"{name} runs a deposit- and franchise-driven operating model in its core market."
    )
    strengths = as_list(
        bq.get("strengths") or bq.get("advantages") or thesis.get("competitive_advantages") or ["Scale", "Distribution", "Customer trust"],
        limit=5,
    )
    weaknesses = as_list(bq.get("risks") or thesis.get("risks") or ["Competition", "Execution", "Regulatory change"], limit=4)
    score = bq.get("business_quality_score")
    try:
        score_f = float(score) if score is not None else None
    except Exception:
        score_f = None

    stance = "Bullish" if (score_f is not None and score_f >= 65) else "Neutral" if score_f is None or score_f >= 50 else "Bearish"
    evidence = []
    evidence.extend(as_list(leo.get("documents_used"), limit=3))
    evidence.extend(as_list((academy.get("applied_concepts") or [])[:2], limit=2))
    evidence.extend(strengths[:2])

    coverage = pick_confidence(bq.get("confidence"), ca.get("confidence"), default=0.55)
    return structured_opinion(
        role="business",
        summary=f"{name}: franchise quality depends on durable demand drivers and capital discipline — not on the tape.",
        strengths=strengths,
        weaknesses=weaknesses,
        evidence=evidence or [f"Institutional business profile for {name}"],
        unanswered_questions=[
            "How durable is pricing power through the next competitive cycle?",
            "Which growth adjacencies truly expand the opportunity set?",
        ],
        sections={
            "business_model": model,
            "revenue_drivers": bq.get("revenue_drivers") or profile.get("revenue_drivers") or ["Core franchise demand", "Mix", "Scale efficiencies"],
            "competitive_position": bq.get("competitive_position") or identity.get("industry") or "Established franchise in its peer set",
            "competitive_advantages": strengths,
            "pricing_power": bq.get("pricing_power") or "Mixed — depends on competitive intensity and product mix",
            "brand": bq.get("brand") or profile.get("brand") or f"{name} brand recognition supports retention",
            "capital_allocation": bq.get("capital_allocation") or "Reinvestment versus owner returns must stay disciplined",
            "growth_opportunities": bq.get("growth_opportunities") or thesis.get("catalysts") or ["Share gains", "Adjacent products"],
            "business_risks": weaknesses,
            "business_quality_score": score_f if score_f is not None else "n/a",
        },
        stance=stance,
        confidence={
            "evidence": pick_confidence(len(evidence) / 6, default=0.5),
            "knowledge": coverage,
            "freshness": pick_confidence(leo.get("freshness_score"), default=0.55),
            "coverage": coverage,
        },
        score=score_f,
        ctx=ctx,
    )
