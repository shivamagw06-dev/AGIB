"""IRE-01 constants — Company Recommendation Reports only."""

from __future__ import annotations

IRE_WORKSTREAM_ID = "IRE-01"
IRE_PRODUCT = "Institutional Reporting Engine"
IRE_VERSION = "ire-01-v1.0.0"
IRE_SPEC = "docs/AGI_IRE_01_INSTITUTIONAL_REPORTING.md"
IRE_ROLE = "deterministic_company_recommendation_reporting"
IRE_REPORT_TYPE = "CompanyRecommendationReport"

# Fixed section order — never omit, never reorder.
REPORT_SECTIONS = (
    "institutional_view",
    "investment_horizon",
    "confidence",
    "investment_thesis",
    "business_quality",
    "financial_quality",
    "valuation",
    "risk_assessment",
    "bull_case",
    "bear_case",
    "watch_items",
    "evidence",
    "bottom_line",
)

SECTION_TITLES = {
    "institutional_view": "Institutional View",
    "investment_horizon": "Investment Horizon",
    "confidence": "Confidence",
    "investment_thesis": "Investment Thesis",
    "business_quality": "Business Quality",
    "financial_quality": "Financial Quality",
    "valuation": "Valuation",
    "risk_assessment": "Risk Assessment",
    "bull_case": "Bull Case",
    "bear_case": "Bear Case",
    "watch_items": "Watch Items",
    "evidence": "Evidence",
    "bottom_line": "Bottom Line",
}

RECOMMENDATIONS = ("BUY", "HOLD", "SELL", "AVOID", "WATCH")
CONVICTIONS = ("LOW", "MEDIUM", "HIGH")
HORIZONS = ("Short", "Medium", "Long")
VALUATION_LABELS = ("Cheap", "Fair", "Expensive", "Unclear")
RISK_LABELS = ("Low", "Moderate", "High", "Severe")
FINANCIAL_QUALITY_LABELS = ("Weak", "Stable", "Strong", "Excellent")
