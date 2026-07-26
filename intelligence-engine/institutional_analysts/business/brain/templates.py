"""Business Analyst output templates — institutional opinion shape."""

from __future__ import annotations

from typing import Any, Dict, List


def institutional_business_opinion_template() -> Dict[str, Any]:
    return {
        "institutional_business_opinion": "",
        "strengths": [],
        "weaknesses": [],
        "business_quality": {
            "grade": "",
            "summary": "",
            "improving": None,
            "value_creation": "",
        },
        "moat_assessment": {
            "durability": "",
            "sources": [],
            "replicability": "",
            "summary": "",
        },
        "competitive_outlook": {
            "positioning": "",
            "outlook": "",
            "summary": "",
        },
        "reasoning": [],
        "assumptions": [],
        "uncertainty": [],
        "unanswered_questions": [],
        "confidence": {
            "evidence": 0.0,
            "knowledge": 0.0,
            "freshness": 0.0,
            "overall": 0.0,
        },
        "quality_checks": {
            "passed": False,
            "issues": [],
        },
        "what_changed": [],
    }


def render_opinion_prose(
    *,
    company: str,
    stance: str,
    business_quality: Dict[str, Any],
    moat_assessment: Dict[str, Any],
    competitive_outlook: Dict[str, Any],
    strengths: List[str],
    weaknesses: List[str],
) -> str:
    subject = company or "The business"
    grade = (business_quality or {}).get("grade") or "mixed"
    moat = (moat_assessment or {}).get("durability") or "unclear"
    outlook = (competitive_outlook or {}).get("outlook") or "uncertain"
    strength_bit = strengths[0] if strengths else "durable customer demand"
    weakness_bit = weaknesses[0] if weaknesses else "limited visibility on competitive intensity"

    stance_phrase = {
        "Bullish": "merits long-term institutional ownership consideration",
        "Bearish": "does not yet clear the bar for long-term ownership on business grounds alone",
        "Neutral": "presents a balanced ownership case pending clearer evidence",
        "constructive": "merits long-term institutional ownership consideration",
        "cautious": "requires selectivity before committing long-term capital",
        "neutral": "presents a balanced ownership case pending clearer evidence",
    }.get(stance, "presents a balanced ownership case pending clearer evidence")

    return (
        f"{subject} {stance_phrase}. "
        f"Business quality is assessed as {grade}, with moat durability {moat}. "
        f"Competitive outlook is {outlook}. "
        f"Supporting case: {strength_bit}. "
        f"Primary caution: {weakness_bit}."
    )
