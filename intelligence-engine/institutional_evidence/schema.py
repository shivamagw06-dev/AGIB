"""IEP-01 — Institutional Evidence Platform constants.

AGI v1.1 highest priority: evidence-first research.
Intelligence consumes evidence — it does not substitute for it.
"""

from __future__ import annotations

IEP_WORKSTREAM_ID = "IEP-01"
IEP_PRODUCT = "Institutional Evidence Platform"
IEP_VERSION = "iep-01-v1.0.0"
IEP_SPEC = "docs/AGI_IEP_01_INSTITUTIONAL_EVIDENCE_PLATFORM.md"
IEP_ROLE = "evidence_foundation"

ADDS_INTELLIGENCE_ENGINES = False
ARCHITECTURE_FROZEN = True  # engines frozen; evidence plane is the v1.1 expansion
AGI_PLATFORM_VERSION = "1.1.0-iep"
GUIDING_PRINCIPLE = (
    "No research without evidence. No recommendation without canonical financial "
    "statements. No narrative without lineage. Intelligence is a consumer of "
    "evidence — not a substitute for it."
)

# Phase 1 — Top 20 Indian companies (cross-sector). Do not scale before quality.
PHASE1_UNIVERSE = (
    "RELIANCE",
    "TCS",
    "HDFCBANK",
    "INFY",
    "ICICIBANK",
    "HINDUNILVR",
    "ITC",
    "SBIN",
    "BHARTIARTL",
    "KOTAKBANK",
    "LT",
    "AXISBANK",
    "ASIANPAINT",
    "MARUTI",
    "SUNPHARMA",
    "TITAN",
    "ULTRACEMCO",
    "NTPC",
    "POWERGRID",
    "NESTLEIND",
)

PHASE1_TOP20 = (
    {"ticker": "RELIANCE", "company": "Reliance Industries", "sector": "Energy / Conglomerate"},
    {"ticker": "TCS", "company": "Tata Consultancy Services", "sector": "IT Services"},
    {"ticker": "HDFCBANK", "company": "HDFC Bank", "sector": "Banks"},
    {"ticker": "INFY", "company": "Infosys", "sector": "IT Services"},
    {"ticker": "ICICIBANK", "company": "ICICI Bank", "sector": "Banks"},
    {"ticker": "HINDUNILVR", "company": "Hindustan Unilever", "sector": "FMCG"},
    {"ticker": "ITC", "company": "ITC", "sector": "FMCG"},
    {"ticker": "SBIN", "company": "State Bank of India", "sector": "Banks"},
    {"ticker": "BHARTIARTL", "company": "Bharti Airtel", "sector": "Telecom"},
    {"ticker": "KOTAKBANK", "company": "Kotak Mahindra Bank", "sector": "Banks"},
    {"ticker": "LT", "company": "Larsen & Toubro", "sector": "Industrials"},
    {"ticker": "AXISBANK", "company": "Axis Bank", "sector": "Banks"},
    {"ticker": "ASIANPAINT", "company": "Asian Paints", "sector": "Materials"},
    {"ticker": "MARUTI", "company": "Maruti Suzuki", "sector": "Auto"},
    {"ticker": "SUNPHARMA", "company": "Sun Pharmaceutical", "sector": "Pharma"},
    {"ticker": "TITAN", "company": "Titan Company", "sector": "Consumer Discretionary"},
    {"ticker": "ULTRACEMCO", "company": "UltraTech Cement", "sector": "Materials"},
    {"ticker": "NTPC", "company": "NTPC", "sector": "Utilities"},
    {"ticker": "POWERGRID", "company": "Power Grid Corporation", "sector": "Utilities"},
    {"ticker": "NESTLEIND", "company": "Nestlé India", "sector": "FMCG"},
)

PRIMARY_DOCUMENT_TYPES = (
    "annual_report",
    "quarterly_results",
    "earnings_presentation",
    "earnings_transcript",
    "nse_xbrl",
    "xbrl_filing",
    "shareholding",
    "corporate_action",
    "exchange_announcement",
    "ir_document",
)

AUTHORITY_SCORES = {
    "nse": 0.95,
    "bse": 0.95,
    "company_ir": 0.9,
    "annual_report": 0.95,
    "quarterly_results": 0.9,
    "earnings_intelligence": 0.85,
    "financial_statements_engine": 0.9,
    "nse_xbrl": 0.95,
    "yahoo": 0.45,
    "groww": 0.4,
    "finnhub": 0.45,
    "news": 0.35,
    "macro": 0.5,
    "live_institutional_data": 0.55,
    "market_secondary": 0.4,
}

FRESHNESS_SLA_DAYS = {
    "annual_report": 400,
    "quarterly_results": 120,
    "earnings_presentation": 120,
    "earnings_transcript": 120,
    "nse_xbrl": 120,
    "xbrl_filing": 120,
    "shareholding": 120,
    "corporate_action": 30,
    "market_secondary": 7,
    "news": 14,
    "macro": 60,
}

DOCUMENT_TYPES = (
    "annual_report",
    "quarterly_results",
    "earnings_presentation",
    "earnings_transcript",
    "shareholding",
    "corporate_action",
    "exchange_announcement",
    "xbrl_filing",
    "nse_xbrl",
    "ir_document",
    "news",
    "macro",
    "market_quote",
    "market_secondary",
    "other",
)

PRIMARY_SOURCES = (
    "nse",
    "bse",
    "company_ir",
    "annual_report",
    "quarterly_results",
    "earnings_presentation",
    "earnings_transcript",
    "shareholding",
    "corporate_actions",
)

SECONDARY_SOURCES = (
    "yahoo",
    "groww",
    "finnhub",
    "news",
    "macro",
    "fred",
    "rbi",
    "firecrawl",
    "exa",
)

MANDATORY_PACK_COMPONENTS = (
    "financials",
    "evidence",
    "company_memory",
    "research_readiness",
)

# Readiness weights (sum = 100)
READINESS_WEIGHTS = {
    "primary_filings": 15,
    "financial_statements": 25,
    "segment_coverage": 10,
    "valuation_inputs": 10,
    "evidence_completeness": 15,
    "freshness": 10,
    "knowledge_graph": 5,
    "financial_intelligence": 5,
    "decision_consistency": 5,
}

RESEARCH_READY_THRESHOLD = 70.0
FRESHNESS_MAX_DAYS = 120

FORBIDDEN_INVENTED_FIELDS = (
    "revenue",
    "eps",
    "ebitda",
    "debt",
    "margins",
    "arpu",
    "grm",
    "capex",
    "valuation",
    "pat",
    "roe",
    "roce",
)

BLOCKED_RECOMMENDATIONS = (
    "BUY",
    "SELL",
    "OVERWEIGHT",
    "UNDERWEIGHT",
    "STRONG BUY",
    "STRONG SELL",
)

ALLOWED_WHEN_BLOCKED = (
    "NO RECOMMENDATION",
    "MONITOR",
    "NEUTRAL",
)
