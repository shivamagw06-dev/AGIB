"""Institutional Intelligence Stack — soft integration schema (not a new engine)."""

from __future__ import annotations

STACK_VERSION = "1.0.0"
PROGRAMME = "AGIB_INSTITUTIONAL_INTELLIGENCE_STACK"
PROGRAMME_SHORT = "IIS"
ARCHITECTURE_STATUS = "v1.0.1 LOCKED"

PIPELINE = [
    "Official Filings",
    "FIL",
    "FDI",
    "MII",
    "ACI",
    "EIL",
    "PIL",
    "CAUSAL INTELLIGENCE GRAPH",
    "INSTITUTIONAL KNOWLEDGE GRAPH",
    "Institutional Analysts",
    "Investment Committee",
    "PORTFOLIO INTELLIGENCE OFFICE",
    "FORECAST INTELLIGENCE ENGINE",
    "CIO",
    "Research Writer",
    "ACS",
    "IRS",
    "Production",
]

LAYERS = (
    "filing_intelligence",
    "filing_diff",
    "management_intelligence",
    "accounting_intelligence",
    "portfolio_intelligence",
    "evidence_intelligence",
    "peer_intelligence",
    "causal_intelligence",
    "knowledge_graph",
    "forecast_intelligence",
)

DEFAULT_BOOTSTRAP_TICKERS = ("HDFCBANK", "NESTLEIND", "TCS")
