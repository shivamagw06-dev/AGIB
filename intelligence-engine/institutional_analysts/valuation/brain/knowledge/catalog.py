"""Valuation Analyst knowledge catalog."""

from __future__ import annotations

from typing import Any

KNOWLEDGE_DOMAINS = [
    "DCF",
    "Reverse DCF",
    "Residual Income",
    "Economic Value Added",
    "SOTP",
    "Comparable Companies",
    "Comparable Transactions",
    "Historical Multiples",
    "Margin of Safety",
    "Expected Return",
    "Monte Carlo",
    "Scenario Valuation",
]

MISSION = (
    "Determine whether the current market price is justified by expected future cash flows, "
    "growth, profitability and risk."
)

PRIMARY_QUESTION = (
    "Does today's valuation appropriately reflect the company's long-term intrinsic value and future expectations?"
)

CORE_QUESTIONS = [
    "Is current valuation justified?",
    "What assumptions are priced in?",
    "What must happen to support current valuation?",
    "How much margin of safety remains if execution undershoots?",
]


def knowledge_pack() -> dict[str, Any]:
    return {
        "analyst": "Valuation Analyst",
        "mission": MISSION,
        "primary_question": PRIMARY_QUESTION,
        "domains": list(KNOWLEDGE_DOMAINS),
        "core_questions": list(CORE_QUESTIONS),
        "never_answers": [
            "business-model storytelling",
            "management character judgements",
            "technical momentum calls",
        ],
    }
