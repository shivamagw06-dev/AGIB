"""Business Analyst — Is this a business we would like to own?"""

from __future__ import annotations

from typing import Any

from institutional_analysts.base import as_list, company_name, pick_confidence, structured_opinion
from institutional_analysts.flags import is_iai_business_enabled
from institutional_analysts.memory import get_previous_opinion


def _legacy_analyse(ctx: dict[str, Any]) -> dict[str, Any]:
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
        bq.get("strengths")
        or bq.get("advantages")
        or thesis.get("competitive_advantages")
        or ["Scale", "Distribution", "Customer trust"],
        limit=5,
    )
    weaknesses = as_list(
        bq.get("risks") or thesis.get("risks") or ["Competition", "Execution", "Regulatory change"],
        limit=4,
    )
    score = bq.get("business_quality_score")
    try:
        score_f = float(score) if score is not None else None
    except Exception:
        score_f = None

    stance = (
        "Bullish"
        if (score_f is not None and score_f >= 65)
        else "Neutral"
        if score_f is None or score_f >= 50
        else "Bearish"
    )
    evidence = []
    evidence.extend(as_list(leo.get("documents_used"), limit=3))
    evidence.extend(as_list((academy.get("applied_concepts") or [])[:2], limit=2))
    evidence.extend(strengths[:2])

    coverage = pick_confidence(bq.get("confidence"), ca.get("confidence"), default=0.55)
    return structured_opinion(
        role="business",
        summary=(
            f"{name}: franchise quality depends on durable demand drivers and capital discipline "
            "— not on the tape."
        ),
        strengths=strengths,
        weaknesses=weaknesses,
        evidence=evidence or [f"Institutional business profile for {name}"],
        unanswered_questions=[
            "How durable is pricing power through the next competitive cycle?",
            "Which growth adjacencies truly expand the opportunity set?",
        ],
        sections={
            "business_model": model,
            "revenue_drivers": bq.get("revenue_drivers")
            or profile.get("revenue_drivers")
            or ["Core franchise demand", "Mix", "Scale efficiencies"],
            "competitive_position": bq.get("competitive_position")
            or identity.get("industry")
            or "Established franchise in its peer set",
            "competitive_advantages": strengths,
            "pricing_power": bq.get("pricing_power")
            or "Mixed — depends on competitive intensity and product mix",
            "brand": bq.get("brand") or profile.get("brand") or f"{name} brand recognition supports retention",
            "capital_allocation": bq.get("capital_allocation")
            or "Reinvestment versus owner returns must stay disciplined",
            "growth_opportunities": bq.get("growth_opportunities")
            or thesis.get("catalysts")
            or ["Share gains", "Adjacent products"],
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


def _evidence_pack(ctx: dict[str, Any], name: str) -> dict[str, Any]:
    ca = ctx.get("company_analysis") if isinstance(ctx.get("company_analysis"), dict) else {}
    cid = ctx.get("company_dossier") if isinstance(ctx.get("company_dossier"), dict) else {}
    academy = ctx.get("finance_academy") if isinstance(ctx.get("finance_academy"), dict) else {}
    leo = ctx.get("live_evidence") if isinstance(ctx.get("live_evidence"), dict) else {}

    bq = ca.get("business_quality") if isinstance(ca.get("business_quality"), dict) else {}
    identity = cid.get("identity") if isinstance(cid.get("identity"), dict) else {}
    profile = cid.get("business_profile") if isinstance(cid.get("business_profile"), dict) else {}
    thesis = ca.get("investment_thesis") if isinstance(ca.get("investment_thesis"), dict) else {}

    advantages = as_list(
        bq.get("strengths")
        or bq.get("advantages")
        or thesis.get("competitive_advantages")
        or ["Scale", "Distribution", "Customer trust"],
        limit=5,
    )
    risks = as_list(
        bq.get("risks") or thesis.get("risks") or ["Competition", "Execution", "Regulatory change"],
        limit=5,
    )
    refs = []
    refs.extend(as_list(leo.get("documents_used"), limit=3))
    refs.extend(as_list((academy.get("applied_concepts") or [])[:2], limit=2))
    refs.extend(advantages[:2])

    score = bq.get("business_quality_score")
    try:
        score_f = float(score) if score is not None else None
    except Exception:
        score_f = None

    return {
        "company": name,
        "business_model": (
            profile.get("business_model")
            or thesis.get("business_overview")
            or bq.get("business_model")
            or identity.get("business_model")
            or f"{name} runs a franchise-driven operating model in its core market."
        ),
        "advantages": advantages,
        "revenue_drivers": as_list(
            bq.get("revenue_drivers")
            or profile.get("revenue_drivers")
            or ["Core franchise demand", "Mix", "Scale efficiencies"],
            limit=5,
        ),
        "competitive_position": bq.get("competitive_position")
        or identity.get("industry")
        or "Established franchise in its peer set",
        "pricing_power": bq.get("pricing_power")
        or "Mixed — depends on competitive intensity and product mix",
        "brand": bq.get("brand") or profile.get("brand") or f"{name} brand recognition supports retention",
        "capital_allocation": bq.get("capital_allocation")
        or "Reinvestment versus owner returns must stay disciplined",
        "growth_opportunities": as_list(
            bq.get("growth_opportunities") or thesis.get("catalysts") or ["Share gains", "Adjacent products"],
            limit=4,
        ),
        "business_risks": risks,
        "business_quality_score": score_f,
        "evidence_refs": [
            {"claim": r, "source_ref": "institutional research"} for r in refs
        ]
        or [{"claim": f"Institutional business profile for {name}", "source_ref": "institutional research"}],
    }


def analyse(ctx: dict[str, Any]) -> dict[str, Any]:
    if not is_iai_business_enabled():
        return _legacy_analyse(ctx)

    from institutional_analysts.business.brain import think
    from institutional_analysts.base import ticker_of

    name = company_name(ctx)
    ca = ctx.get("company_analysis") if isinstance(ctx.get("company_analysis"), dict) else {}
    leo = ctx.get("live_evidence") if isinstance(ctx.get("live_evidence"), dict) else {}
    bq = ca.get("business_quality") if isinstance(ca.get("business_quality"), dict) else {}
    evidence = _evidence_pack(ctx, name)

    coverage = pick_confidence(bq.get("confidence"), ca.get("confidence"), default=0.55)
    evidence_n = len(evidence.get("evidence_refs") or [])
    conf = {
        "evidence": pick_confidence(evidence_n / 6, default=0.5),
        "knowledge": coverage,
        "freshness": pick_confidence(leo.get("freshness_score"), default=0.55),
        "coverage": coverage,
    }
    conf["overall"] = round(
        (
            conf["evidence"] * 0.35
            + conf["knowledge"] * 0.25
            + conf["freshness"] * 0.2
            + conf["coverage"] * 0.2
        ),
        4,
    )

    previous = get_previous_opinion(ticker_of(ctx), "business")
    brain = think(
        company=name,
        evidence=evidence,
        previous=previous,
        confidence=conf,
    )

    score = evidence.get("business_quality_score")
    try:
        score_f = float(score) if score is not None else None
    except Exception:
        score_f = None

    base = structured_opinion(
        role="business",
        summary=str(brain.get("summary") or brain.get("institutional_business_opinion") or ""),
        strengths=list(brain.get("strengths") or []),
        weaknesses=list(brain.get("weaknesses") or []),
        evidence=[
            (e.get("claim") if isinstance(e, dict) else str(e))
            for e in (evidence.get("evidence_refs") or [])
        ],
        unanswered_questions=list(brain.get("unanswered_questions") or []),
        sections={
            "business_model": evidence.get("business_model"),
            "revenue_drivers": evidence.get("revenue_drivers"),
            "competitive_position": evidence.get("competitive_position"),
            "competitive_advantages": evidence.get("advantages"),
            "pricing_power": evidence.get("pricing_power"),
            "brand": evidence.get("brand"),
            "capital_allocation": evidence.get("capital_allocation"),
            "growth_opportunities": evidence.get("growth_opportunities"),
            "business_risks": evidence.get("business_risks"),
            "business_quality_score": score_f if score_f is not None else "n/a",
            # IAI enrichment — section-safe summaries (full objects attached top-level)
            "institutional_business_opinion": brain.get("institutional_business_opinion"),
            "business_quality_grade": (brain.get("business_quality") or {}).get("grade"),
            "moat_durability": (brain.get("moat_assessment") or {}).get("durability"),
            "moat_summary": (brain.get("moat_assessment") or {}).get("summary"),
            "competitive_outlook_summary": (brain.get("competitive_outlook") or {}).get("summary"),
            "assumptions": brain.get("assumptions"),
            "uncertainty": brain.get("uncertainty"),
            "frameworks_applied": brain.get("frameworks_applied"),
            "iai_version": brain.get("iai_version"),
        },
        stance=str(brain.get("stance") or "Neutral"),
        confidence=conf,
        score=score_f,
        ctx=ctx,
    )

    # Soft enrich top-level without breaking structured_opinion contract consumers.
    base["institutional_business_opinion"] = brain.get("institutional_business_opinion")
    base["business_quality"] = brain.get("business_quality")
    base["moat_assessment"] = brain.get("moat_assessment")
    base["competitive_outlook"] = brain.get("competitive_outlook")
    base["reasoning"] = brain.get("reasoning")
    base["assumptions"] = brain.get("assumptions")
    base["uncertainty"] = brain.get("uncertainty")
    base["quality_checks"] = brain.get("quality_checks")
    base["validation"] = brain.get("validation")
    base["analyst_memory"] = brain.get("memory")
    base["iai_version"] = brain.get("iai_version")
    base["iai_active"] = True
    base["ready_for_committee"] = brain.get("ready_for_committee")

    # Enrich change notes only when a prior opinion exists (preserve first-run None).
    if previous:
        brain_changed = list(brain.get("what_changed") or [])
        wc = base.get("what_changed") if isinstance(base.get("what_changed"), dict) else {}
        notes = list(wc.get("notes") or [])
        for note in brain_changed:
            if note and note not in notes:
                notes.append(note)
        if wc:
            wc["notes"] = notes[:6]
            base["what_changed"] = wc
        elif notes:
            base["what_changed"] = {
                "previous_stance": previous.get("stance"),
                "current_stance": base.get("stance"),
                "changed": True,
                "notes": notes[:6],
            }

    return base
