"""Language analysis — surface cues for intent resolution (deterministic)."""

from __future__ import annotations

import re
from typing import Any


_EXPLAIN = re.compile(
    r"\b(why|explain|how (?:does|do|would|should|can)|what (?:makes|causes)|reason|because)\b",
    re.I,
)
_COMPARE = re.compile(r"\b(compare|comparison|versus|\bvs\.?\b|relative to|difference between|which of)\b", re.I)
_ANALYSE = re.compile(
    r"\b(analyse|analyze|assess|evaluate|investigate|determine whether|how would you|what evidence|"
    r"list at least|construct|identify|which (?:additional )?evidence)\b",
    re.I,
)
_EDUCATION = re.compile(
    r"^(what is|what's|define|meaning of)\b|\bwhat is a\b|\bwhat does .+ mean\b",
    re.I,
)
_VALUATION = re.compile(
    r"\b(valu(?:e|ation)|fair value|dcf|ev/?ebitda|p/?e\b|price[- ]to[- ]book|p/?b\b|"
    r"residual income|sotp|sum[- ]of[- ]the[- ]parts|multiple|overvalued|undervalued|expensive|cheap)\b",
    re.I,
)
_PORTFOLIO = re.compile(
    r"\b(should i invest|should we invest|portfolio|position size|allocation|buy |sell |recommend)\b",
    re.I,
)
_RISK = re.compile(r"\b(risk|drawdown|downside|volatility|var\b|tail risk)\b", re.I)
_ACCOUNTING = re.compile(
    r"\b(accounting|cash flow|operating cash|accrual|earnings quality|working capital|"
    r"revenue growth|cash conversion|balance sheet)\b",
    re.I,
)
_INDUSTRY = re.compile(
    r"\b(industry|sector|cement|steel|software|fmcg|hospitals?|pharmaceutical|"
    r"it services|psu banks?|value chain|peers?)\b",
    re.I,
)
_MACRO = re.compile(
    r"\b(macro|inflation|gdp|repo|interest rate|crude|oil prices?|rupee|fx|currency|"
    r"stagflation|transmission)\b",
    re.I,
)
_GOVERNMENT = re.compile(
    r"\b(government|rbi|sebi|gst|budget|pli|import dut(?:y|ies)|policy|regulation|duty)\b",
    re.I,
)
_EVENTS = re.compile(
    r"\b(dividend|buyback|merger|announcement|board meeting|earnings|quarterly result)\b",
    re.I,
)
_DOCUMENTS = re.compile(
    r"\b(annual report|investor presentation|transcript|filing|md&a|risk factors?|"
    r"notes to|audited|institutional documents?|document)\b",
    re.I,
)
_REPLAY = re.compile(
    r"\b(replay|point[- ]in[- ]time|as of|available on that date|future (?:information )?leakage|"
    r"before covid|fy\s?\d{2,4})\b",
    re.I,
)
_CROSS = re.compile(
    r"\b(simultaneously|cross[- ]domain|using evidence from|macro,? government,? alternative|"
    r"investment committee|evidence package|evidence pack)\b",
    re.I,
)


def analyse_language(question: str) -> dict[str, Any]:
    q = str(question or "").strip()
    ql = q.lower()
    cues = {
        "explain": bool(_EXPLAIN.search(ql)),
        "compare": bool(_COMPARE.search(ql)),
        "analyse": bool(_ANALYSE.search(ql)),
        "education": bool(_EDUCATION.search(ql)),
        "valuation_lexicon": bool(_VALUATION.search(ql)),
        "portfolio": bool(_PORTFOLIO.search(ql)),
        "risk": bool(_RISK.search(ql)),
        "accounting": bool(_ACCOUNTING.search(ql)),
        "industry": bool(_INDUSTRY.search(ql)),
        "macro": bool(_MACRO.search(ql)),
        "government": bool(_GOVERNMENT.search(ql)),
        "corporate_events": bool(_EVENTS.search(ql)),
        "documents": bool(_DOCUMENTS.search(ql)),
        "historical_replay": bool(_REPLAY.search(ql)),
        "cross_domain": bool(_CROSS.search(ql)),
        "why_question": ql.strip().startswith("why") or " why " in f" {ql}",
        "how_would_you": "how would you" in ql or "how should" in ql,
        "list_request": bool(re.search(r"\b(list|enumerate|name every|every evidence)\b", ql)),
    }
    cue_count = sum(1 for v in cues.values() if v)
    return {
        "question": q,
        "normalized": ql,
        "cues": cues,
        "cue_count": cue_count,
        "word_count": len(ql.split()),
        "fabricated": False,
    }
