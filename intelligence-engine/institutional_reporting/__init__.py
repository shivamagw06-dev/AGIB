"""IRE-01 — Institutional Reporting Engine (deterministic, no LLM)."""

from institutional_reporting.composer import compose_report
from institutional_reporting.models import InstitutionalReport, InstitutionalReportInput
from institutional_reporting.schema import IRE_VERSION, IRE_WORKSTREAM_ID

__all__ = [
    "compose_report",
    "InstitutionalReport",
    "InstitutionalReportInput",
    "IRE_WORKSTREAM_ID",
    "IRE_VERSION",
]
