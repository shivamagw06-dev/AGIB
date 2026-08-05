"""Institutional Writing Constitution v1.0 — IRE writing layer schema."""

from __future__ import annotations

CONSTITUTION_VERSION = "1.0"
PROGRAMME = "AGI Institutional Writing Constitution — How AGI Explains"
LAYER = "Institutional Research Engine (IRE)"
SCOPE = "Every user-facing research response"

# Fixed response hierarchy — never reorder
RESPONSE_HIERARCHY: tuple[str, ...] = (
    "executive_summary",
    "investment_meaning",
    "what_evidence_suggests",
    "what_could_change_view",
    "research_conclusion",
    "questions_before_you_decide",
)

SECTION_LABELS: dict[str, str] = {
    "executive_summary": "Executive Summary",
    "investment_meaning": "Investment Meaning",
    "what_evidence_suggests": "What Current Evidence Suggests",
    "what_could_change_view": "What Could Change This View",
    "research_conclusion": "Research Conclusion",
    "questions_before_you_decide": "Questions Before You Decide",
}

EXECUTIVE_SUMMARY_MAX_WORDS = 150
EVIDENCE_OBSERVATIONS_MIN = 3
EVIDENCE_OBSERVATIONS_MAX = 6
QUESTIONS_MIN = 3
QUESTIONS_MAX = 5

# Answer length guidance (words)
LENGTH_SIMPLE = (300, 500)
LENGTH_RESEARCH = (700, 1200)
LENGTH_DEEP = (2000, 4000)

FORBIDDEN_PHRASES: tuple[str, ...] = (
    "must buy",
    "must sell",
    "strong buy",
    "strong sell",
    "huge upside",
    "amazing",
    "excellent stock",
    "great company",
    "bullish",
    "bearish",
    "undervalued",
    "overvalued",
    "cheap",
    "expensive stock",
    "guaranteed",
    "multi-bagger",
    "target price",
    "entry price",
    "exit price",
)

PREFERRED_PHRASES: tuple[str, ...] = (
    "current evidence suggests",
    "the central investment debate",
    "market expectations imply",
    "the business appears",
    "the primary uncertainty",
    "future value creation depends on",
    "historical evidence indicates",
    "the thesis remains intact because",
    "evidence does not currently suggest",
    "institutional investors would likely focus on",
    "evidence suggests",
)

FORBIDDEN_CLASSIFICATIONS: tuple[str, ...] = (
    "business quality: supportive",
    "risk: high",
    "growth: positive",
    "valuation: fair",
)

EVALUATION_DIMENSIONS: tuple[str, ...] = (
    "executive_summary_quality",
    "institutional_tone",
    "clarity",
    "evidence_usage",
    "prioritization",
    "implication_explanation",
    "uncertainty_handling",
    "readability",
)

QUALITY_TEST_QUESTIONS: tuple[str, ...] = (
    "Does this improve understanding?",
    "Does this explain why?",
    "Does this connect evidence?",
    "Does this expose uncertainty?",
    "Does this avoid unnecessary facts?",
    "Would a portfolio manager consider this useful?",
)

WRITING_PHILOSOPHY: tuple[str, ...] = (
    "Never summarize information — explain meaning",
    "Never list facts — connect facts",
    "Never report numbers — explain implications",
    "Never say what happened — explain why it matters",
    "Never tell users what to buy — help them understand what they are buying",
)
