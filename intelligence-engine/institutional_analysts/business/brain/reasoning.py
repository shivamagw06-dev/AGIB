"""Institutional reasoning chain for the Business Analyst."""

from __future__ import annotations

from typing import Any


def reason(
    *,
    company: str,
    frameworks: dict[str, Any],
    evidence: dict[str, Any],
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Think like a senior strategy consultant — explain, assume, surface uncertainty."""
    moat = frameworks.get("moat") or {}
    outlook = frameworks.get("competitive_outlook") or {}
    value = frameworks.get("value_creation") or {}
    porter = frameworks.get("porter_five_forces") or {}

    durability = str(moat.get("durability") or "Moderate")
    improving = bool(outlook.get("improving"))

    steps = [
        {
            "question": "How does this business make money?",
            "answer": value.get("business_model")
            or f"{company} earns through its core franchise activities.",
        },
        {
            "question": "Why do customers stay?",
            "answer": value.get("customer_retention_hypothesis")
            or "Retention depends on trust, convenience and switching frictions.",
        },
        {
            "question": "Can competitors replicate the advantage?",
            "answer": moat.get("replicability")
            or "Replicability remains an open institutional question.",
        },
        {
            "question": "How durable is the moat?",
            "answer": moat.get("assessment")
            or f"Moat durability assessed as {durability.lower()}.",
        },
        {
            "question": "Is the business improving, and why?",
            "answer": (
                f"Yes — {outlook.get('why_improving_or_not')}"
                if improving
                else f"Not clearly — {outlook.get('why_improving_or_not')}"
            ),
        },
        {
            "question": "What creates long-term value?",
            "answer": (
                ", ".join(
                    value.get("long_term_value_creation")
                    or ["Disciplined reinvestment", "Franchise compounding"]
                )
                + f". Industry structure implication: {porter.get('implication', '')}"
            ).strip(),
        },
    ]

    assumptions = [
        "Available franchise and competitive signals are representative of the current operating reality.",
        "Advantage sources inferred from institutional research remain relevant over a multi-year horizon.",
        "No sudden regulatory or technological break that permanently resets industry structure.",
    ]

    uncertainty = [
        "Share / volume evidence versus industry growth may still be incomplete.",
        "Pricing power through the next competitive cycle is not fully observable from the current file.",
        "Capital allocation consistency across stress periods needs ongoing confirmation.",
    ]

    if durability == "High" and improving:
        quality_grade = "High"
        stance = "Bullish"
        opinion = (
            f"A long-term institutional investor would generally want to own {company} "
            "as a durable franchise, subject to entry discipline handled elsewhere."
        )
    elif durability == "Low":
        quality_grade = "Weak"
        stance = "Bearish"
        opinion = (
            f"On present evidence, {company} does not yet clear the bar as a high-quality "
            "long-term ownership candidate on business grounds alone."
        )
    else:
        quality_grade = "Adequate"
        stance = "Neutral"
        opinion = (
            f"{company} shows a credible franchise, but moat durability and improvement "
            "signals need fuller confirmation before raising business-quality conviction."
        )

    strengths = list(moat.get("sources") or [])[:4]
    for d in value.get("revenue_drivers") or []:
        if d not in strengths and len(strengths) < 5:
            strengths.append(d)

    weaknesses = list(outlook.get("disruption_watch") or [])[:3]
    for r in evidence.get("business_risks") or []:
        if r not in weaknesses and len(weaknesses) < 5:
            weaknesses.append(str(r))

    unanswered = [
        "Is market share actually increasing, or is industry growth lifting everyone?",
        "How durable is pricing power through the next competitive cycle?",
        "Which growth adjacencies truly expand the opportunity set versus diluting returns?",
    ]

    business_quality = {
        "grade": quality_grade,
        "summary": opinion,
        "improving": improving,
        "value_creation": ", ".join(
            value.get("long_term_value_creation") or ["Franchise compounding"]
        ),
    }

    moat_assessment = {
        "durability": durability,
        "sources": list(moat.get("sources") or [])[:5],
        "replicability": moat.get("replicability") or "",
        "summary": moat.get("assessment")
        or f"Moat durability assessed as {durability.lower()}.",
    }

    competitive_outlook = {
        "positioning": evidence.get("competitive_position")
        or "Established franchise in its peer set",
        "outlook": "Constructive" if improving and durability != "Low" else (
            "Challenged" if durability == "Low" else "Mixed"
        ),
        "summary": outlook.get("why_improving_or_not")
        or outlook.get("industry_phase_hypothesis")
        or "Competitive conditions require ongoing monitoring.",
        "disruption_watch": list(outlook.get("disruption_watch") or [])[:3],
        "industry_phase_hypothesis": outlook.get("industry_phase_hypothesis"),
    }

    change_notes = []
    if previous:
        prev_stance = previous.get("stance")
        if prev_stance and prev_stance != stance:
            change_notes.append(f"Business stance moved from {prev_stance} to {stance}.")
        prev_moat = None
        if isinstance(previous.get("moat_assessment"), dict):
            prev_moat = previous.get("moat_assessment", {}).get("durability")
        elif isinstance((previous.get("sections") or {}).get("moat_assessment"), dict):
            prev_moat = (previous.get("sections") or {}).get("moat_assessment", {}).get("durability")
        if prev_moat and prev_moat != durability:
            change_notes.append(f"Moat durability revised from {prev_moat} to {durability}.")

    return {
        "institutional_business_opinion": opinion,
        "business_quality": business_quality,
        "moat_assessment": moat_assessment,
        "competitive_outlook": competitive_outlook,
        "stance": stance,
        "strengths": strengths,
        "weaknesses": weaknesses or ["Competition", "Execution", "Regulatory change"],
        "reasoning_steps": steps,
        "assumptions": assumptions,
        "uncertainty": uncertainty,
        "unanswered_questions": unanswered,
        "view_changes": change_notes,
        "primary_question_answer": opinion,
    }
