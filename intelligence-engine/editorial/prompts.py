"""Gemini editorial prompts — writer only, never analyst."""

from __future__ import annotations

import json
from typing import Any

BASE_RULES = """Convert the supplied structured intelligence into a concise institutional investment answer.

Rules:
- Maximum {max_words} words unless mode is detailed_analysis (then maximum 180 words).
- Do not invent facts.
- Do not change the recommendation.
- Use only supplied intelligence.
- Write like an institutional equity research analyst.
- Professional. Objective. Evidence based.
- Never claim you analysed filings, PDFs, news, or financial statements.
- Never override AGIB's recommendation, conviction, or horizon.
"""

MODE_INSTRUCTIONS = {
    "recommendation": (
        "Produce a stock recommendation answer with this structure:\n"
        "Recommendation: <exact recommendation from JSON, keep conviction if supplied>\n"
        "Then 1–2 sentences covering reason and the single biggest risk, ending with horizon.\n"
        "Use only top_reasons and top_risks from the JSON."
    ),
    "quick_analysis": (
        "Produce a quick institutional analysis (max {max_words} words) covering the supplied "
        "business_quality, financial_quality, valuation, top reasons and top risks. "
        "Lead with the recommendation exactly as supplied."
    ),
    "detailed_analysis": (
        "Produce a detailed but still institutional analysis (max 180 words). "
        "Keep the recommendation unchanged. Expand only on supplied reasons, risks, quality labels, "
        "valuation and horizon. Do not add external facts."
    ),
}


def build_prompt(
    *,
    mode: str,
    structured: dict[str, Any],
    question: str | None = None,
    max_words: int = 60,
) -> str:
    mode_key = mode if mode in MODE_INSTRUCTIONS else "recommendation"
    instructions = MODE_INSTRUCTIONS[mode_key].format(max_words=max_words)
    rules = BASE_RULES.format(max_words=max_words)
    payload = {
        "question": question or structured.get("question"),
        "structured_intelligence": structured,
        "mode": mode_key,
    }
    return (
        f"{rules}\n\n"
        f"Mode instructions:\n{instructions}\n\n"
        f"Structured intelligence (JSON):\n{json.dumps(payload, ensure_ascii=True, default=str)}"
    )
