"""Business Analyst IAI V2 brain — institutional strategy partner for the IC."""

from __future__ import annotations

from typing import Any

from institutional_analysts.business.brain import knowledge as kn
from institutional_analysts.business.brain import validation as val
from institutional_analysts.business.brain.benchmarks import benchmark
from institutional_analysts.business.brain.frameworks import apply_all
from institutional_analysts.business.brain.memory import (
    build_memory_record,
    compare_views,
    extract_prior_view,
)
from institutional_analysts.business.brain.quality_checks import run_quality_checks
from institutional_analysts.business.brain.reasoning import synthesize
from institutional_analysts.business.brain.scoring import score_dimensions
from institutional_analysts.business.brain.templates import build_structured_opinion

IAI_BUSINESS_VERSION = "iai-business-v2.0.0"


def _confidence_block(raw: dict[str, float], *, reasoning_boost: float = 0.0) -> dict[str, float]:
    evidence = float(raw.get("evidence") or 0.0)
    knowledge = float(raw.get("knowledge") or 0.0)
    freshness = float(raw.get("freshness") or 0.0)
    coverage = float(raw.get("coverage") or knowledge)
    reasoning = float(raw.get("reasoning") or min(0.95, max(0.2, (evidence + knowledge) / 2 + reasoning_boost)))
    overall = float(
        raw.get("overall")
        or round(evidence * 0.3 + reasoning * 0.25 + knowledge * 0.2 + freshness * 0.15 + coverage * 0.1, 4)
    )
    return {
        "evidence": evidence,
        "reasoning": reasoning,
        "knowledge": knowledge,
        "freshness": freshness,
        "coverage": coverage,
        "overall": overall,
    }


def think(
    *,
    company: str,
    evidence: dict[str, Any],
    previous: dict[str, Any] | None = None,
    confidence: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Run Business Analyst V2 — answer whether this is an exceptional business."""
    conf_in = confidence if isinstance(confidence, dict) else {}
    frameworks = apply_all(evidence)
    scoring = score_dimensions(frameworks, evidence)
    # Strip internal numeric calculation from public scoring surface
    public_scoring = {
        k: v for k, v in scoring.items() if not str(k).startswith("_")
    }
    benches = benchmark(evidence, frameworks)
    reasoned = synthesize(
        company=company,
        frameworks=frameworks,
        scoring=public_scoring,
        benchmarks=benches,
        previous=previous,
    )

    conf = _confidence_block(
        conf_in,
        reasoning_boost=0.08 if public_scoring.get("grade") in {"High", "Exceptional"} else 0.0,
    )

    business_quality = {
        "grade": public_scoring.get("grade"),
        "summary": reasoned.get("executive_opinion"),
        "dimensions": public_scoring.get("dimensions"),
        "exceptional_business": public_scoring.get("exceptional_business"),
        "ownership_bar": public_scoring.get("ownership_bar"),
        "improving": (frameworks.get("moat") or {}).get("trajectory") == "Improving",
        "value_creation": reasoned.get("capital_allocation_summary"),
    }
    moat = frameworks.get("moat") or {}
    stance = str(reasoned.get("stance") or "Neutral")
    strengths = list(reasoned.get("strengths") or [])
    weaknesses = list(reasoned.get("weaknesses") or [])
    assumptions = list(reasoned.get("assumptions") or [])
    uncertainties = list(reasoned.get("uncertainties") or [])
    missing = list(reasoned.get("missing_evidence") or [])
    reasoning_steps = list(reasoned.get("reasoning_steps") or [])
    executive = str(reasoned.get("executive_opinion") or "")

    prior = extract_prior_view(previous)
    comparison = compare_views(
        current_stance=stance,
        current_quality_grade=str(business_quality.get("grade") or ""),
        current_moat_durability=str(moat.get("durability") or ""),
        current_growth_view=str(reasoned.get("growth_runway_summary") or ""),
        current_risks=list(reasoned.get("risks_list") or []),
        current_confidence=float(conf.get("overall") or 0.0),
        prior=prior,
    )
    memory_record = build_memory_record(
        company=company,
        stance=stance,
        quality_grade=str(business_quality.get("grade") or ""),
        moat_durability=str(moat.get("durability") or ""),
        growth_view=str(reasoned.get("growth_runway_summary") or ""),
        risks=list(reasoned.get("risks_list") or []),
        confidence=float(conf.get("overall") or 0.0),
        opinion_summary=executive,
        comparison=comparison,
        prior=prior,
    )

    evidence_items = []
    for item in evidence.get("evidence_refs") or []:
        if isinstance(item, dict):
            evidence_items.append(item)
        elif item:
            evidence_items.append({"claim": str(item), "source_ref": "institutional research"})

    claims = [str(s.get("answer")) for s in reasoning_steps if isinstance(s, dict) and s.get("answer")][:8]

    quality = run_quality_checks(
        strengths=strengths,
        weaknesses=weaknesses,
        claims=claims,
        evidence=evidence_items,
        assumptions=assumptions,
        freshness=float(conf.get("freshness") or 0.0),
        overall_confidence=float(conf.get("overall") or 0.0),
        moat_assessment=moat,
        competitive_outlook=frameworks.get("competitive_outlook") or {},
        business_quality=business_quality,
        frameworks=frameworks,
        scoring=public_scoring,
    )

    validation = val.run_validation(
        answer=executive,
        claims=claims,
        evidence=evidence_items,
        opinion={
            "business_quality": business_quality,
            "moat_assessment": moat,
            "competitive_outlook": frameworks.get("competitive_outlook") or {},
            "reasoning": reasoning_steps,
            "assumptions": assumptions,
            "uncertainty": uncertainties,
            "unanswered_questions": missing
            or [
                "Is market share actually increasing, or is industry growth lifting everyone?",
                "How durable is pricing power through the next competitive cycle?",
            ],
            "confidence": {
                "evidence": conf["evidence"],
                "knowledge": conf["knowledge"],
                "freshness": conf["freshness"],
                "overall": conf["overall"],
            },
        },
        forbidden_tokens=[
            "P/E",
            "intrinsic value",
            "margin of safety",
            "overvalued",
            "undervalued",
            "momentum",
            "good company",
            "strong company",
            "nice moat",
        ],
    )

    structured = build_structured_opinion(
        executive_opinion=(
            quality.get("explanation")
            if quality.get("incomplete")
            else executive
        ),
        business_quality=business_quality,
        moat=moat,
        competitive_position=str(reasoned.get("competitive_position_summary") or ""),
        business_model=frameworks.get("business_model") or {},
        revenue_drivers=list(reasoned.get("revenue_drivers") or []),
        customer_economics=frameworks.get("customer_economics") or {},
        pricing_power=frameworks.get("pricing_power") or {},
        capital_allocation=frameworks.get("capital_allocation") or {},
        innovation=str(reasoned.get("innovation_summary") or ""),
        industry_position=str(reasoned.get("industry_position_summary") or ""),
        growth_runway=str(reasoned.get("growth_runway_summary") or ""),
        risks=list(reasoned.get("risks_list") or []),
        opportunities=list(reasoned.get("opportunities") or []),
        assumptions=assumptions,
        uncertainties=uncertainties,
        missing_evidence=missing,
        confidence=conf,
        quality_checks=quality,
    )

    what_changed = list(comparison.get("what_changed") or [])
    what_changed.extend(list(reasoned.get("view_changes") or []))

    # If incomplete, force cautious stance messaging for committee
    if quality.get("incomplete"):
        structured["executive_opinion"] = quality.get("explanation") or "Incomplete Business Assessment"
        stance_out = "Neutral"
        summary = structured["executive_opinion"]
    else:
        stance_out = stance
        summary = executive

    return {
        "iai_version": IAI_BUSINESS_VERSION,
        "knowledge": kn.knowledge_pack(),
        "frameworks_applied": list(frameworks.get("applied") or []),
        "framework_detail": frameworks,
        "benchmarks": benches,
        "scoring": public_scoring,
        # V2 structured object (canonical)
        "structured_business_opinion": structured,
        "executive_opinion": structured["executive_opinion"],
        "business_quality": business_quality,
        "moat": moat,
        "moat_assessment": moat,  # V1 alias
        "competitive_position": structured["competitive_position"],
        "business_model": structured["business_model"],
        "revenue_drivers": structured["revenue_drivers"],
        "customer_economics": structured["customer_economics"],
        "pricing_power": structured["pricing_power"],
        "capital_allocation": structured["capital_allocation"],
        "innovation": structured["innovation"],
        "industry_position": structured["industry_position"],
        "growth_runway": structured["growth_runway"],
        "risks": structured["risks"],
        "opportunities": structured["opportunities"],
        "assumptions": assumptions,
        "uncertainties": uncertainties,
        "uncertainty": uncertainties,  # V1 alias
        "missing_evidence": missing,
        "unanswered_questions": missing
        or [
            "Is market share actually increasing, or is industry growth lifting everyone?",
            "How durable is pricing power through the next competitive cycle?",
            "Which growth adjacencies truly expand the opportunity set versus diluting returns?",
        ],
        "confidence": conf,
        "quality_checks": quality,
        "validation": validation,
        # Compatibility surface for IAF/ICI/IRW
        "institutional_business_opinion": summary,
        "summary": summary,
        "stance": stance_out,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "competitive_outlook": frameworks.get("competitive_outlook") or {},
        "reasoning": reasoning_steps,
        "memory": memory_record,
        "what_changed": what_changed,
        "trajectory": comparison.get("trajectory") or "Stable",
        "ready_for_committee": bool(quality.get("ready_for_committee", True)),
        "primary_question_answer": reasoned.get("primary_question_answer"),
    }


__all__ = ["think", "IAI_BUSINESS_VERSION"]
