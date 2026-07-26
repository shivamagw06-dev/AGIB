"""Business Analyst knowledge catalog — institutional strategy frameworks (not engines)."""

from __future__ import annotations

from typing import Any

# Public institutional language only — never expose package/engine names.
KNOWLEDGE_DOMAINS: list[str] = [
    "Porter Five Forces",
    "Value Chain",
    "Competitive Advantage",
    "Blue Ocean Strategy",
    "Capital Cycle",
    "Network Effects",
    "Switching Costs",
    "Brand Strength",
    "Economies of Scale",
    "Pricing Power",
    "Customer Lifetime Value",
    "Customer Acquisition Cost",
    "Retention",
    "Operating Leverage",
    "Market Share",
    "Distribution",
    "Competitive Positioning",
    "Capital Allocation",
    "Innovation",
    "Technology Disruption",
]

MISSION = (
    "Determine whether this is a high-quality business capable of generating durable long-term value."
)

PRIMARY_QUESTION = "Would a long-term institutional investor want to own this business?"

CORE_QUESTIONS = [
    "Is this business improving?",
    "Why?",
    "Can competitors replicate it?",
    "How durable is its moat?",
    "Why do customers stay?",
    "How does it make money?",
    "What creates long-term value?",
]


def knowledge_pack() -> dict[str, Any]:
    pack: dict[str, Any] = {
        "analyst": "Business Analyst",
        "mission": MISSION,
        "primary_question": PRIMARY_QUESTION,
        "domains": list(KNOWLEDGE_DOMAINS),
        "core_questions": list(CORE_QUESTIONS),
        "never_answers": [
            "valuation attractiveness",
            "earnings multiple verdicts",
            "macro policy stance",
            "tape / momentum calls",
        ],
    }
    try:
        from academy.books.flags import flag_books_v3
        from academy.books.v3.production import analyst_base

        if flag_books_v3():
            pack["academy_institutional"] = analyst_base(
                "business",
                question="moat pricing power capital cycle network effects",
            )
    except Exception:
        pass
    try:
        from peer_intelligence.flags import is_enabled as pil_enabled

        if pil_enabled():
            pack["peer_intelligence"] = {
                "enabled": True,
                "rule": "Business conclusions must reference peer rank, history, or sector percentile before judgement",
                "soft_slice": "peer_intelligence.production.soft_slice_for_analyst(ticker, analyst='business')",
            }
    except Exception:
        pass
    try:
        from filing_intelligence.flags import is_enabled as fil_enabled

        if fil_enabled():
            pack["filing_intelligence"] = {
                "enabled": True,
                "rule": "Business-model evolution and management strategy must cite filing commentary when available",
                "soft_slice": "filing_intelligence.production.soft_slice_for_analyst(ticker, analyst='business')",
            }
    except Exception:
        pass
    return pack
