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
    "Institutional Analysts",
    "Investment Committee",
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
    "evidence_intelligence",
    "peer_intelligence",
)

DEFAULT_BOOTSTRAP_TICKERS = ("HDFCBANK", "NESTLEIND", "TCS")
