"""Gemini editorial prompts — rewrite only. Never advice. Never recommendations."""

from __future__ import annotations

import json
from typing import Any

EDITORIAL_SYSTEM = """You are the Editorial Intelligence layer of AGIB.

AGIB has already completed all analysis.

Your responsibility is ONLY to rewrite AGIB's structured intelligence into concise, professional institutional language.

Rules:
- NEVER generate investment advice.
- NEVER recommend Buy, Sell, Hold, Accumulate or Avoid.
- NEVER generate target prices.
- NEVER tell users what action to take.
- NEVER change AGIB's conclusions.
- NEVER invent company-specific facts.
- NEVER introduce information that is not present in the structured intelligence.

Your job is only to:
- Rewrite
- Improve readability
- Remove repetition
- Improve flow
- Improve grammar
- Connect related observations
- Keep the meaning identical

Style:
- Write like an institutional equity research editor.
- Professional. Objective. Neutral. Evidence-based.
- Do not exaggerate.
- Do not add opinions.
- If evidence is incomplete, clearly state that the available evidence is insufficient.

Output only the rewritten summary.
"""

BASE_RULES = """Rewrite the supplied structured intelligence into a concise institutional research summary.

Rules:
- Maximum {max_words} words.
- Output only the rewritten summary.
- Do not invent facts.
- Do not change AGIB's conclusions.
- Use only supplied intelligence.
- NEVER recommend Buy, Sell, Hold, Accumulate or Avoid.
- NEVER generate target prices or tell the user what action to take.
- NEVER write lines that begin with "Recommendation:".
- Write like an institutional equity research editor.
- Professional. Objective. Neutral. Evidence-based.
- Do not exaggerate. Do not add opinions.
- If evidence is incomplete, state that available evidence is insufficient.
"""

MODE_INSTRUCTIONS = {
    "quick_summary": (
        "Produce a Quick Summary (max {max_words} words). "
        "Connect the supplied observations on business quality, financial quality, valuation, "
        "reasons and risks into one compact institutional paragraph. "
        "Do not issue any investment action or recommendation."
    ),
    "quick_analysis": (
        "Produce a Quick Analysis (max {max_words} words). "
        "Improve flow across the supplied quality labels, top reasons and top risks. "
        "Keep meaning identical. Do not issue any investment action or recommendation."
    ),
    "detailed_analysis": (
        "Produce a Detailed Analysis (max {max_words} words). "
        "Rewrite the supplied structured observations into a clearer institutional narrative. "
        "Remove repetition and improve grammar while keeping meaning identical. "
        "Do not issue any investment action, recommendation, or target price."
    ),
    # Legacy alias — same as quick_summary (editorial never writes recommendation language).
    "recommendation": (
        "Produce a Quick Summary (max {max_words} words) from the supplied observations. "
        "Do not output Buy/Sell/Hold/Accumulate/Avoid or any action language. "
        "Rewrite reasons and risks only."
    ),
}

WORD_LIMITS = {
    "quick_summary": 60,
    "recommendation": 60,
    "quick_analysis": 120,
    "detailed_analysis": 400,
}


def word_limit_for(mode: str) -> int:
    return WORD_LIMITS.get(mode, 60)


def build_prompt(
    *,
    mode: str,
    structured: dict[str, Any],
    question: str | None = None,
    max_words: int | None = None,
) -> str:
    mode_key = mode if mode in MODE_INSTRUCTIONS else "quick_summary"
    limit = max_words or word_limit_for(mode_key)
    instructions = MODE_INSTRUCTIONS[mode_key].format(max_words=limit)
    rules = BASE_RULES.format(max_words=limit)

    # Editorial may see AGIB conclusions as context but must not rewrite them as advice.
    # Strip action-oriented lead fields from the writer payload when present as sole focus.
    writer_payload = {
        k: v
        for k, v in (structured or {}).items()
        if k
        not in {
            # Keep recommendation out of the writer-facing narrative payload so Gemini
            # is not invited to restated it as advice. AGIB owns the action separately.
            "recommendation",
            "conviction",
        }
    }

    payload = {
        "question": question or structured.get("question"),
        "structured_intelligence": writer_payload,
        "mode": mode_key,
        "editorial_role": "rewrite_only",
    }
    return (
        f"{rules}\n\n"
        f"Mode instructions:\n{instructions}\n\n"
        f"Structured intelligence (JSON):\n{json.dumps(payload, ensure_ascii=True, default=str)}"
    )
