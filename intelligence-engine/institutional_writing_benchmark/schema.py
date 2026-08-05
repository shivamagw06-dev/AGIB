"""Institutional writing benchmark — schema and constants."""

from __future__ import annotations

BENCHMARK_CATEGORIES: tuple[str, ...] = (
    "investment_assessment",
    "valuation",
    "earnings",
    "peer_comparison",
    "business_quality",
    "management",
    "capital_allocation",
    "risks",
    "competitive_position",
    "sector_analysis",
    "macro",
    "portfolio_construction",
    "monitoring",
)

TARGET_BENCHMARK_COUNT = 500
HALL_OF_FAME_COUNT = 100
