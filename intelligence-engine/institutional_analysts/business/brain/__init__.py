"""Business Analyst IAI brain — frameworks, reasoning, validation, memory, quality."""

from __future__ import annotations

from typing import Any

from institutional_analysts.business.brain import frameworks as fw
from institutional_analysts.business.brain import knowledge as kn
from institutional_analysts.business.brain import memory as mem
from institutional_analysts.business.brain import quality_checks as qc
from institutional_analysts.business.brain import reasoning as rz
from institutional_analysts.business.brain import templates as tmpl
from institutional_analysts.business.brain import validation as val

IAI_BUSINESS_VERSION = "iai-business-v1.0.0"


def think(
    *,
    company: str,
    evidence: dict[str, Any],
    previous: dict[str, Any] | None = None,
    confidence: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Run the Business Analyst institutional reasoning loop.

    Consumes already-assembled evidence only. No provider or engine calls.
    """
    conf = confidence if isinstance(confidence, dict) else {}
    applied = fw.apply_frameworks(evidence)
    reasoned = rz.reason(
        company=company,
        frameworks=applied,
        evidence=evidence,
        previous=previous,
    )

    strengths = list(reasoned.get("strengths") or [])
    weaknesses = list(reasoned.get("weaknesses") or [])
    business_quality = reasoned.get("business_quality") or {}
    moat_assessment = reasoned.get("moat_assessment") or {}
    competitive_outlook = reasoned.get("competitive_outlook") or {}
    assumptions = list(reasoned.get("assumptions") or [])
    uncertainty = list(reasoned.get("uncertainty") or [])
    unanswered = list(reasoned.get("unanswered_questions") or [])
    reasoning_steps = list(reasoned.get("reasoning_steps") or [])
    stance = str(reasoned.get("stance") or "Neutral")

    prose = tmpl.render_opinion_prose(
        company=company,
        stance=stance,
        business_quality=business_quality,
        moat_assessment=moat_assessment,
        competitive_outlook=competitive_outlook,
        strengths=strengths,
        weaknesses=weaknesses,
    )
    opinion_text = reasoned.get("institutional_business_opinion") or prose

    prior = mem.extract_prior_view(previous)
    comparison = mem.compare_views(
        current_stance=stance,
        current_quality_grade=str(business_quality.get("grade") or ""),
        current_moat_durability=str(moat_assessment.get("durability") or ""),
        current_confidence=float(conf.get("overall") or 0.0),
        prior=prior,
    )
    memory_record = mem.build_memory_record(
        company=company,
        stance=stance,
        quality_grade=str(business_quality.get("grade") or ""),
        moat_durability=str(moat_assessment.get("durability") or ""),
        confidence=float(conf.get("overall") or 0.0),
        opinion_summary=str(opinion_text),
        comparison=comparison,
        prior=prior,
    )

    evidence_items = []
    for item in evidence.get("evidence_refs") or []:
        if isinstance(item, dict):
            evidence_items.append(item)
        elif item:
            evidence_items.append({"claim": str(item), "source_ref": "institutional research"})

    claims = [s.get("answer") for s in reasoning_steps if isinstance(s, dict) and s.get("answer")]
    claims = [str(c) for c in claims if c][:6]

    opinion_for_validation = {
        "business_quality": business_quality,
        "moat_assessment": moat_assessment,
        "competitive_outlook": competitive_outlook,
        "reasoning": reasoning_steps,
        "assumptions": assumptions,
        "uncertainty": uncertainty,
        "unanswered_questions": unanswered,
        "confidence": {
            "evidence": float(conf.get("evidence") or 0.0),
            "knowledge": float(conf.get("knowledge") or 0.0),
            "freshness": float(conf.get("freshness") or 0.0),
            "overall": float(conf.get("overall") or 0.0),
        },
    }

    validation = val.run_validation(
        answer=str(opinion_text),
        claims=claims,
        evidence=evidence_items,
        opinion=opinion_for_validation,
        forbidden_tokens=[
            "P/E",
            "intrinsic value",
            "margin of safety",
            "overvalued",
            "undervalued",
            "momentum",
        ],
    )

    quality = qc.run_quality_checks(
        strengths=strengths,
        weaknesses=weaknesses,
        claims=claims,
        evidence=evidence_items,
        assumptions=assumptions,
        freshness=float(conf.get("freshness") or 0.0),
        overall_confidence=float(conf.get("overall") or 0.0),
        moat_assessment=moat_assessment,
        competitive_outlook=competitive_outlook,
        business_quality=business_quality,
    )

    what_changed = list(comparison.get("what_changed") or [])
    what_changed.extend(list(reasoned.get("view_changes") or []))

    return {
        "iai_version": IAI_BUSINESS_VERSION,
        "knowledge": kn.knowledge_pack(),
        "frameworks_applied": list(applied.get("applied") or []),
        "framework_detail": {
            "porter_five_forces": applied.get("porter_five_forces"),
            "moat": applied.get("moat"),
            "value_creation": applied.get("value_creation"),
            "competitive_outlook": applied.get("competitive_outlook"),
            "knowledge_hits": applied.get("knowledge_hits"),
        },
        "institutional_business_opinion": opinion_text,
        "summary": opinion_text,
        "stance": stance,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "business_quality": business_quality,
        "moat_assessment": moat_assessment,
        "competitive_outlook": competitive_outlook,
        "reasoning": reasoning_steps,
        "assumptions": assumptions,
        "uncertainty": uncertainty,
        "unanswered_questions": unanswered,
        "validation": validation,
        "quality_checks": quality,
        "memory": memory_record,
        "what_changed": what_changed,
        "ready_for_committee": bool(quality.get("ready_for_committee", True)),
    }


__all__ = ["think", "IAI_BUSINESS_VERSION"]
