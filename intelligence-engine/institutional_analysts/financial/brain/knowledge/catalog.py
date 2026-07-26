"""Financial Analyst knowledge catalog — institutional finance frameworks."""

from __future__ import annotations

from typing import Any

KNOWLEDGE_DOMAINS = [
    "ROIC Tree",
    "DuPont Analysis",
    "Cash Conversion Cycle",
    "Working Capital",
    "Sloan Accrual Ratio",
    "Piotroski F Score",
    "Altman Z Score",
    "Beneish M Score",
    "Economic Profit",
    "Free Cash Flow",
    "Capital Allocation",
    "Earnings Quality",
    "Margin Expansion",
]

MISSION = (
    "Determine whether reported financial performance represents durable economic value creation."
)

PRIMARY_QUESTION = "Do the financial statements support the investment thesis?"

CORE_QUESTIONS = [
    "Is growth sustainable?",
    "Are profits high quality?",
    "Is cash flow improving?",
    "Can returns remain high?",
    "How resilient is the balance sheet?",
    "Has capital allocation created shareholder value?",
]


def knowledge_pack() -> dict[str, Any]:
    pack: dict[str, Any] = {
        "analyst": "Financial Analyst",
        "mission": MISSION,
        "primary_question": PRIMARY_QUESTION,
        "domains": list(KNOWLEDGE_DOMAINS),
        "core_questions": list(CORE_QUESTIONS),
        "never_answers": [
            "brand / moat commentary",
            "valuation attractiveness",
            "macro policy outlook",
            "tape / momentum calls",
        ],
    }
    try:
        from academy.books.flags import flag_books_v3
        from academy.books.v3.production import analyst_base

        if flag_books_v3():
            pack["academy_institutional"] = analyst_base(
                "financial",
                question="ROIC cash conversion earnings quality capital allocation",
            )
    except Exception:
        pass
    return pack
