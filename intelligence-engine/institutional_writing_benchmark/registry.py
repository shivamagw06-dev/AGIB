"""Institutional writing benchmark — 500 investment questions."""

from __future__ import annotations

from typing import Any

from institutional_writing_benchmark.schema import BENCHMARK_CATEGORIES, TARGET_BENCHMARK_COUNT

# Category → expected response structure (template hint)
EXPECTED_STRUCTURES: dict[str, str] = {
    "investment_assessment": "executive_summary → investment_debate → evidence → uncertainties → conclusion → questions",
    "valuation": "executive_summary → current_expectations → historical_context → evidence → risks → conclusion",
    "earnings": "executive_summary → what_changed → what_didnt_change → market_implications → evidence → monitoring",
    "peer_comparison": "executive_summary → business_comparison → financial_comparison → competitive_position → evidence → conclusion",
    "business_quality": "executive_summary → what_matters_most → investment_debate → evidence → uncertainties → conclusion",
    "management": "executive_summary → management_quality → capital_allocation → evidence → uncertainties → conclusion",
    "capital_allocation": "executive_summary → allocation_track_record → evidence → uncertainties → conclusion",
    "risks": "executive_summary → primary_risks → evidence → probability → monitoring → conclusion",
    "competitive_position": "executive_summary → competitive_position → evidence → uncertainties → conclusion",
    "sector_analysis": "executive_summary → sector_context → evidence → implications → conclusion",
    "macro": "executive_summary → macro_drivers → company_implications → evidence → conclusion",
    "portfolio_construction": "executive_summary → role_in_portfolio → risks → evidence → conclusion",
    "monitoring": "executive_summary → monitoring_indicators → evidence → conclusion",
}

_CORE_EXEMPLARS: tuple[dict[str, Any], ...] = (
    {"id": "IWB_001", "question": "Should I invest in TCS?", "category": "investment_assessment", "ticker": "TCS", "editorial_notes": "Focus on franchise quality vs valuation debate."},
    {"id": "IWB_002", "question": "Why does Titan deserve a premium?", "category": "valuation", "ticker": "TITAN", "editorial_notes": "Explain premium drivers, not just multiples."},
    {"id": "IWB_003", "question": "Compare Infosys and TCS.", "category": "peer_comparison", "ticker": "INFY", "editorial_notes": "Business comparison before financial metrics."},
    {"id": "IWB_004", "question": "Is HDFC Bank losing competitive advantage?", "category": "competitive_position", "ticker": "HDFCBANK", "editorial_notes": "Identify what would prove advantage intact or lost."},
    {"id": "IWB_005", "question": "What changed after Reliance earnings?", "category": "earnings", "ticker": "RELIANCE", "editorial_notes": "Separate what changed from what did not."},
    {"id": "IWB_006", "question": "Explain Asian Paints pricing power.", "category": "business_quality", "ticker": "ASIANPAINT", "editorial_notes": "Explain mechanism, not just state pricing power exists."},
    {"id": "IWB_007", "question": "Why is HAL rerating?", "category": "valuation", "ticker": "HAL", "editorial_notes": "Connect rerating to expectations shift."},
    {"id": "IWB_008", "question": "Should I worry about Trent valuation?", "category": "valuation", "ticker": "TRENT", "editorial_notes": "Frame as uncertainty, not recommendation."},
    {"id": "IWB_009", "question": "How durable is Nestle India's pricing power?", "category": "business_quality", "ticker": "NESTLEIND", "editorial_notes": ""},
    {"id": "IWB_010", "question": "What are the key risks in Adani Enterprises?", "category": "risks", "ticker": "ADANIENT", "editorial_notes": ""},
)

_NIFTY50: tuple[tuple[str, str], ...] = (
    ("TCS", "Tata Consultancy Services"), ("INFY", "Infosys"), ("HDFCBANK", "HDFC Bank"),
    ("RELIANCE", "Reliance Industries"), ("ICICIBANK", "ICICI Bank"), ("HINDUNILVR", "Hindustan Unilever"),
    ("ITC", "ITC"), ("SBIN", "State Bank of India"), ("BHARTIARTL", "Bharti Airtel"),
    ("KOTAKBANK", "Kotak Mahindra Bank"), ("LT", "Larsen & Toubro"), ("AXISBANK", "Axis Bank"),
    ("ASIANPAINT", "Asian Paints"), ("MARUTI", "Maruti Suzuki"), ("TITAN", "Titan Company"),
    ("BAJFINANCE", "Bajaj Finance"), ("HCLTECH", "HCL Technologies"), ("WIPRO", "Wipro"),
    ("ULTRACEMCO", "UltraTech Cement"), ("NESTLEIND", "Nestle India"), ("SUNPHARMA", "Sun Pharmaceutical"),
    ("POWERGRID", "Power Grid"), ("NTPC", "NTPC"), ("M&M", "Mahindra & Mahindra"),
    ("TATAMOTORS", "Tata Motors"), ("TECHM", "Tech Mahindra"), ("ADANIENT", "Adani Enterprises"),
    ("JSWSTEEL", "JSW Steel"), ("TATASTEEL", "Tata Steel"), ("INDUSINDBK", "IndusInd Bank"),
    ("BAJAJFINSV", "Bajaj Finserv"), ("HINDALCO", "Hindalco"), ("GRASIM", "Grasim"),
    ("DIVISLAB", "Divi's Laboratories"), ("CIPLA", "Cipla"), ("DRREDDY", "Dr Reddy's"),
    ("EICHERMOT", "Eicher Motors"), ("HEROMOTOCO", "Hero MotoCorp"), ("BRITANNIA", "Britannia"),
    ("APOLLOHOSP", "Apollo Hospitals"), ("COALINDIA", "Coal India"), ("BPCL", "BPCL"),
    ("ONGC", "ONGC"), ("SBILIFE", "SBI Life"), ("HDFCLIFE", "HDFC Life"),
    ("TATACONSUM", "Tata Consumer"), ("ADANIPORTS", "Adani Ports"), ("UPL", "UPL"),
    ("SHREECEM", "Shree Cement"), ("LTIM", "LTIMindtree"),
)

_CATEGORY_TEMPLATES: dict[str, tuple[str, ...]] = {
    "investment_assessment": ("Should I invest in {name}?", "What is the investment case for {name}?"),
    "valuation": ("Is {name} fairly valued?", "Why is {name} trading at a premium?", "Should I worry about {name} valuation?"),
    "earnings": ("What changed after {name}'s latest earnings?", "What didn't change in {name}'s latest quarter?"),
    "peer_comparison": ("Compare {name} with its closest peer.", "How does {name} compare on margins?"),
    "business_quality": ("How durable is {name}'s competitive advantage?", "Explain {name}'s pricing power."),
    "management": ("How would you assess {name}'s management quality?", "Is {name}'s management executing well?"),
    "capital_allocation": ("How effective is {name}'s capital allocation?", "Does {name} allocate capital shareholder-friendly?"),
    "risks": ("What are the primary risks in {name}?", "What would invalidate the thesis on {name}?"),
    "competitive_position": ("Is {name} losing competitive advantage?", "How strong is {name}'s moat?"),
    "sector_analysis": ("What is the outlook for {name}'s sector?", "How does sector dynamics affect {name}?"),
    "macro": ("How do macro trends affect {name}?", "Explain RBI policy impact on {name}."),
    "portfolio_construction": ("What role would {name} play in a portfolio?", "Does {name} fit a concentrated portfolio?"),
    "monitoring": ("What should investors monitor on {name}?", "What are key triggers for {name}?"),
}


def _build_benchmarks() -> tuple[dict[str, Any], ...]:
    items: list[dict[str, Any]] = []
    for ex in _CORE_EXEMPLARS:
        items.append({
            **ex,
            "expected_structure": EXPECTED_STRUCTURES.get(ex["category"], "narrative_default"),
            "latest_score": None,
            "revision_history": [],
        })
    idx = len(items) + 1
    seen: set[tuple[str, str]] = {(i["ticker"] or "", i["category"]) for i in items if i.get("ticker")}

    for category in BENCHMARK_CATEGORIES:
        templates = _CATEGORY_TEMPLATES.get(category, ("Analyze {name}.",))
        for ticker, name in _NIFTY50:
            if idx > TARGET_BENCHMARK_COUNT:
                break
            for template in templates:
                if idx > TARGET_BENCHMARK_COUNT:
                    break
                key = (ticker, category)
                if key in seen:
                    continue
                seen.add(key)
                qid = f"IWB_{idx:03d}"
                items.append({
                    "id": qid,
                    "question": template.format(name=name),
                    "category": category,
                    "ticker": ticker,
                    "expected_structure": EXPECTED_STRUCTURES.get(category, "narrative_default"),
                    "editorial_notes": "",
                    "latest_score": None,
                    "revision_history": [],
                })
                idx += 1
        if idx > TARGET_BENCHMARK_COUNT:
            break
    return tuple(items[:TARGET_BENCHMARK_COUNT])


BENCHMARK_QUESTIONS: tuple[dict[str, Any], ...] = _build_benchmarks()


def list_benchmarks(*, category: str | None = None, limit: int = 500) -> list[dict[str, Any]]:
    items = list(BENCHMARK_QUESTIONS)
    if category:
        items = [q for q in items if q.get("category") == category]
    return items[:limit]


def get_benchmark(benchmark_id: str) -> dict[str, Any] | None:
    for q in BENCHMARK_QUESTIONS:
        if q.get("id") == benchmark_id:
            return dict(q)
    return None
