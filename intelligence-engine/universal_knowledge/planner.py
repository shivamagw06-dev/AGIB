"""Universal Knowledge Planner — every question gets one execution plan.

The planner decides which providers to consult. It never hardcodes a route.
KUL's knowledge_planner owns menu selection by question family; this layer
adds expected-provider contracts so coverage can detect silence.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from universal_knowledge.registry import CAPABILITIES, DEPENDENCY_ORDER, capability


_EXPECTED: dict[str, tuple[str, ...]] = {
    "valuation": (
        "valuation_terminal",
        "valuation_consensus",
        "industry_intelligence",
        "capiq_ikt",
        "financial_statement_warehouse",
    ),
    "consensus": (
        "valuation_consensus",
        "capiq_ikt",
        "valuation_terminal",
    ),
    "business": (
        "business_intelligence",
        "industry_intelligence",
        "capiq_ikt",
        "company_memory",
    ),
    "investment": (
        "investment_intelligence",
        "business_intelligence",
        "industry_intelligence",
        "valuation_terminal",
        "valuation_consensus",
        "hedge_fund_screens",
    ),
    "portfolio": (
        "portfolio_intelligence",
        "investment_intelligence",
        "valuation_terminal",
    ),
    "research": (
        "research_intelligence",
        "cgl",
        "company_memory",
        "valuation_consensus",
    ),
    "financials": (
        "financial_statement_warehouse",
        "financial_statement_intelligence",
        "capiq_ikt",
        "valuation_terminal",
    ),
    "accounting": (
        "financial_foundations",
        "financial_statement_intelligence",
        "financial_concepts",
    ),
    "industry": (
        "industry_intelligence",
        "business_intelligence",
        "financial_concepts",
    ),
    "company": (
        "capiq_ikt",
        "company_memory",
        "business_intelligence",
        "industry_intelligence",
        "valuation_terminal",
        "valuation_consensus",
    ),
    "concept": (
        "financial_concepts",
        "financial_foundations",
        "academy",
    ),
    "screen": (
        "hedge_fund_screens",
        "valuation_terminal",
        "investment_intelligence",
    ),
}


_FAMILY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("screen", re.compile(
        r"\b(screen|scanner|hedge fund|long/?short|market neutral|pair trade|"
        r"value trap|momentum|quality screen)\b", re.I)),
    ("consensus", re.compile(
        r"\b(consensus|target price|price target|analysts? cover|coverage|"
        r"rating split|upside)\b", re.I)),
    ("valuation", re.compile(
        r"\b(expensive|cheap|overvalued|undervalued|valuation|multiple|"
        r"p/?e\b|p/?b\b|ev/?ebitda|price to (?:earnings|book|sales)|"
        r"trades? at|re-?rat(?:e|ing)|de-?rat(?:e|ing)|discount|premium)\b", re.I)),
    ("financials", re.compile(
        r"\b(revenue|eps|earnings|margin|debt|cash flow|fcf|capex|"
        r"balance sheet|income statement|working capital|historical)\b", re.I)),
    ("accounting", re.compile(
        r"\b(accrual|cash profit|journal|ledger|debit|credit|gaap|ind.?as|"
        r"depreciation|amortisation|amortization|impairment)\b", re.I)),
    ("investment", re.compile(
        r"\b(investment thesis|why (?:would|should).{0,20}own|thesis|catalysts?|"
        r"biggest risks?|business and financial quality)\b", re.I)),
    ("research", re.compile(
        r"\b(annual report|earnings call|transcript|guidance|"
        r"management (?:said|commentary)|what changed)\b", re.I)),
    ("portfolio", re.compile(
        r"\b(portfolio|position sizing|allocation|gross exposure|net exposure)\b", re.I)),
    ("business", re.compile(
        r"\b(business model|what does .+ do|explain .{0,40}do|moat|"
        r"competes?|unit economics)\b", re.I)),
    ("industry", re.compile(
        r"\b(industry|sector|how (?:are|is) .{0,30} valued|banking valuation|"
        r"valu(?:e|ing) (?:a |an )?(?:bank|saas|nbfc))\b", re.I)),
    ("concept", re.compile(
        r"\b(what is|define|difference between|explain the)\b", re.I)),
)


def detect_family(question: str, *, question_type: Optional[str] = None) -> str:
    q = str(question or "")
    for family, pattern in _FAMILY_PATTERNS:
        if pattern.search(q):
            return family
    if question_type in _EXPECTED:
        return question_type  # type: ignore[return-value]
    if question_type in {"business_model", "moat", "unit_economics"}:
        return "business"
    return "company"


def expected_providers(family: str) -> list[str]:
    return list(_EXPECTED.get(family, _EXPECTED["company"]))


def plan(
    question: str,
    *,
    ticker: Optional[str] = None,
    question_type: Optional[str] = None,
    max_providers: int = 10,
) -> dict[str, Any]:
    """Build the universal execution plan for one question."""
    from knowledge_unification.query_planner import plan_query
    from knowledge_unification.knowledge_planner import build_knowledge_plan

    family = detect_family(question, question_type=question_type)
    expected = expected_providers(family)

    query = plan_query(question)
    if ticker and not query.ticker_hint:
        query.ticker_hint = str(ticker).upper()
    if ticker and query.ticker_hint and "company" not in query.question_types:
        query.question_types = ["company", *list(query.question_types)]
    # Stamp the detected family onto question_types so KUL menus fire correctly
    # even when the query planner classified the question as pure industry pedagogy.
    family_type = {
        "valuation": "valuation",
        "consensus": "consensus",
        "business": "business_model",
        "investment": "investment",
        "portfolio": "portfolio",
        "research": "research",
        "financials": "financial_statement",
        "accounting": "accounting",
        "industry": "industry",
        "screen": "investment",
    }.get(family)
    if family_type and family_type not in query.question_types:
        query.question_types = [family_type, *list(query.question_types)]

    knowledge = build_knowledge_plan(query)
    menu = list(knowledge.provider_ids or [])

    # Expected providers are never truncated — coverage requires the attempt.
    locked = [pid for pid in expected if pid in CAPABILITIES]
    extras = [pid for pid in menu if pid not in locked]
    role_rank = {role: i for i, role in enumerate(DEPENDENCY_ORDER)}

    def sort_key(pid: str) -> tuple[int, int, str]:
        cap = capability(pid)
        if cap is None:
            return (99, 99, pid)
        return (role_rank.get(cap.role, 50), cap.priority, pid)

    budget = max(len(locked), int(max_providers))
    selected = sorted(set(locked + extras[: max(0, budget - len(locked))]), key=sort_key)
    knowledge.provider_ids = selected

    return {
        "ok": True,
        "engine": "universal_knowledge_planner",
        "version": "uko-6.0",
        "question": question,
        "ticker": query.ticker_hint,
        "family": family,
        "question_types": list(query.question_types),
        "selected_providers": selected,
        "expected_providers": expected,
        "query_plan": query,
        "knowledge_plan": knowledge,
        "max_providers": max_providers,
    }
