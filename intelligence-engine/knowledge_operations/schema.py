"""KOC-01 — Institutional Knowledge Operations Center constants."""

from __future__ import annotations

KOC_WORKSTREAM_ID = "KOC-01"
KOC_PRODUCT = "Institutional Knowledge Operations Center"
KOC_VERSION = "koc-01-v1.0.0"
KOC_SPEC = "docs/AGI_KOC_01_KNOWLEDGE_OPERATIONS_CENTER.md"

MISSION = (
    "Monitor, validate and improve institutional knowledge across the entire AGI universe."
)

DOCUMENT_UPLOAD_TYPES = (
    "annual_report",
    "quarterly_results",
    "investor_presentation",
    "transcript",
    "shareholding",
    "corporate_action",
    "management_guidance",
    "segment_data",
    "credit_rating",
    "investor_day",
    "other",
)

UPLOAD_EXTENSIONS = (".pdf", ".ppt", ".pptx", ".doc", ".docx", ".xls", ".xlsx", ".zip")

# Missing-inbox priority by evidence class
MISSING_PRIORITY = {
    "financial_statements": "Critical",
    "annual_reports": "Critical",
    "quarterly_results": "Critical",
    "earnings_presentations": "Critical",
    "earnings_call_transcripts": "High",
    "shareholding": "High",
    "segment_kpis": "High",
    "corporate_actions": "Medium",
    "management_guidance": "Medium",
    "company_memory": "Medium",
    "knowledge_graph": "Low",
}

PRIORITY_RANK = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}

CLASS_LABELS = {
    "annual_reports": "Annual Report",
    "quarterly_results": "Quarterly Results",
    "financial_statements": "Financial Statements",
    "earnings_presentations": "Investor Presentation",
    "earnings_call_transcripts": "Earnings Call Transcript",
    "shareholding": "Shareholding Pattern",
    "corporate_actions": "Corporate Action",
    "management_guidance": "Management Guidance",
    "segment_kpis": "Segment KPIs",
    "company_memory": "Company Memory",
    "knowledge_graph": "Knowledge Graph",
}

QUEUE_STAGES = (
    "Waiting for Parsing",
    "Waiting for Validation",
    "Waiting for OCR",
    "Waiting for Embedding",
    "Waiting for Company Memory",
    "Waiting for Knowledge Graph",
    "Waiting for Research Refresh",
    "Retry Failed",
)

COLLECTOR_NAMES = (
    "Annual Reports",
    "Quarterly Results",
    "Presentations",
    "Transcripts",
    "Shareholding",
    "Corporate Actions",
    "IR Websites",
    "NSE",
    "BSE",
    "Yahoo",
    "Groww",
)
