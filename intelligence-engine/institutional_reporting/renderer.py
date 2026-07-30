"""Render fixed institutional report sections to text."""

from __future__ import annotations

from institutional_reporting.confidence import explain_confidence
from institutional_reporting.evidence import evidence_ids_for_section, format_supported_by
from institutional_reporting.models import InstitutionalReportInput, ReportSection
from institutional_reporting.schema import REPORT_SECTIONS, SECTION_TITLES
from institutional_reporting import templates


def _attach_evidence(body: str, evidence_block: str) -> str:
    text = body.rstrip() + "\n\n" + evidence_block.rstrip() + "\n"
    return text


def render_sections(inp: InstitutionalReportInput) -> list[ReportSection]:
    conf = explain_confidence(inp)
    builders = {
        "institutional_view": lambda: templates.institutional_view_body(inp),
        "investment_horizon": lambda: templates.investment_horizon_body(inp),
        "confidence": lambda: conf["body"],
        "investment_thesis": lambda: templates.investment_thesis_body(inp),
        "business_quality": lambda: templates.business_quality_body(inp),
        "financial_quality": lambda: templates.financial_quality_body(inp),
        "valuation": lambda: templates.valuation_body(inp),
        "risk_assessment": lambda: templates.risk_assessment_body(inp),
        "bull_case": lambda: templates.bull_case_body(inp),
        "bear_case": lambda: templates.bear_case_body(inp),
        "watch_items": lambda: templates.watch_items_body(inp),
        "evidence": lambda: templates.evidence_section_body(inp),
        "bottom_line": lambda: templates.bottom_line_body(inp),
    }

    sections: list[ReportSection] = []
    for key in REPORT_SECTIONS:
        body = builders[key]()
        eids = evidence_ids_for_section(inp, key)
        meta = {}
        if key == "confidence":
            meta = {
                "score": conf["score"],
                "positive_drivers": conf["positive_drivers"],
                "negative_drivers": conf["negative_drivers"],
                "unknowns": conf["unknowns"],
            }
            # Confidence section is explanatory; still bind catalog evidence for audit.
        elif key not in {"institutional_view", "investment_horizon", "watch_items", "evidence", "confidence"}:
            body = _attach_evidence(body, format_supported_by(eids, list(inp.evidence)))
        elif key == "confidence" and eids:
            body = _attach_evidence(body, format_supported_by(eids, list(inp.evidence)))

        sections.append(
            ReportSection(
                key=key,
                title=SECTION_TITLES[key],
                body=body if body.endswith("\n") else body + "\n",
                evidence_ids=list(eids),
                meta=meta,
            )
        )
    return sections


def render_text(sections: list[ReportSection], *, ticker: str, company_name: str) -> str:
    parts = [
        "Institutional Report",
        "",
        f"{company_name} ({ticker})",
        "",
    ]
    for section in sections:
        parts.append(section.body.rstrip())
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"
