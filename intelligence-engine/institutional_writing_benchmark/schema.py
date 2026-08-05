"""Institutional writing benchmark — schema and constants."""

from __future__ import annotations

# 20 lifecycle playbooks × 5 questions = 100 curated benchmark questions (Phase 1: TCS)
PLAYBOOK_COUNT = 20
QUESTIONS_PER_PLAYBOOK = 5
TARGET_BENCHMARK_COUNT = 100
HALL_OF_FAME_COUNT = 100

# Phase 2 — replicate curriculum for each company → 1,000 total
PHASE2_COMPANIES: tuple[tuple[str, str], ...] = (
    ("INFY", "Infosys"),
    ("HDFCBANK", "HDFC Bank"),
    ("RELIANCE", "Reliance Industries"),
    ("ICICIBANK", "ICICI Bank"),
    ("BHARTIARTL", "Bharti Airtel"),
    ("TITAN", "Titan"),
    ("ASIANPAINT", "Asian Paints"),
    ("LT", "Larsen & Toubro"),
    ("MARUTI", "Maruti Suzuki"),
    ("HAL", "HAL"),
)

PHASE2_TARGET_BENCHMARK_COUNT = 1000  # TCS 100 + 10 companies × 100

LIFECYCLE_PLAYBOOKS: tuple[str, ...] = (
    "investment_assessment",
    "business_quality",
    "management_quality",
    "financial_quality",
    "valuation",
    "growth",
    "risks",
    "investment_debate",
    "earnings",
    "competitive_position",
    "industry",
    "portfolio_fit",
    "macro_impact",
    "monitoring",
    "historical_perspective",
    "scenario_analysis",
    "decision_support",
    "explainability",
    "communication",
    "institutional_thinking",
)

# Back-compat alias for category filters
BENCHMARK_CATEGORIES: tuple[str, ...] = LIFECYCLE_PLAYBOOKS

PLAYBOOK_TITLES: dict[str, str] = {
    "investment_assessment": "Investment Assessment",
    "business_quality": "Business Quality",
    "management_quality": "Management Quality",
    "financial_quality": "Financial Quality",
    "valuation": "Valuation",
    "growth": "Growth",
    "risks": "Risks",
    "investment_debate": "Investment Debate",
    "earnings": "Earnings",
    "competitive_position": "Competitive Position",
    "industry": "Industry",
    "portfolio_fit": "Portfolio Fit",
    "macro_impact": "Macro Impact",
    "monitoring": "Monitoring",
    "historical_perspective": "Historical Perspective",
    "scenario_analysis": "Scenario Analysis",
    "decision_support": "Decision Support",
    "explainability": "Explainability",
    "communication": "Communication",
    "institutional_thinking": "Institutional Thinking",
}
