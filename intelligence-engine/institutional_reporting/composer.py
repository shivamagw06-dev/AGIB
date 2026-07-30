"""Report composer — single public entrypoint compose_report()."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Union

from institutional_reporting.evidence import validate_section_evidence_coverage
from institutional_reporting.flags import is_enabled
from institutional_reporting.models import InstitutionalReport, InstitutionalReportInput
from institutional_reporting.renderer import render_sections, render_text
from institutional_reporting.schema import (
    IRE_REPORT_TYPE,
    IRE_VERSION,
    IRE_WORKSTREAM_ID,
    REPORT_SECTIONS,
)
from institutional_reporting.validator import validate_input


def _fingerprint(inp: InstitutionalReportInput) -> str:
    payload = json.dumps(inp.to_dict(), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _rejected(
    inp: InstitutionalReportInput,
    errors: list[str],
    gates: dict[str, bool],
) -> InstitutionalReport:
    return InstitutionalReport(
        ok=False,
        workstream_id=IRE_WORKSTREAM_ID,
        version=IRE_VERSION,
        report_type=IRE_REPORT_TYPE,
        ticker=inp.ticker,
        company_name=inp.company_name,
        recommendation=inp.recommendation,
        conviction=inp.conviction,
        confidence=inp.confidence if isinstance(inp.confidence, int) else -1,
        sections=[],
        text="",
        quality_gates=gates,
        validation_errors=list(errors),
        rejected=True,
        llm=False,
        as_of=inp.as_of,
        input_fingerprint=_fingerprint(inp) if inp.ticker else "",
    )


def quality_gates(
    inp: InstitutionalReportInput,
    *,
    validation_ok: bool,
    sections_ok: bool,
    evidence_ok: bool,
) -> dict[str, bool]:
    return {
        "recommendation_valid": validation_ok and bool(inp.recommendation),
        "confidence_present": isinstance(inp.confidence, int) and 0 <= inp.confidence <= 100,
        "evidence_exists": bool(inp.evidence) and evidence_ok,
        "thesis_exists": bool(inp.thesis),
        "valuation_exists": bool(str(inp.valuation or "").strip()),
        "risk_exists": bool(str(inp.overall_risk or "").strip()),
        "bottom_line_exists": sections_ok,
        "enabled": is_enabled(),
    }


def compose_report(
    report_input: Union[InstitutionalReportInput, dict[str, Any], None],
) -> InstitutionalReport:
    """Compose a deterministic InstitutionalReport from structured facts.

    No Gemini. No GPT. No external writer.
    """
    if isinstance(report_input, InstitutionalReportInput):
        inp = report_input
    else:
        inp = InstitutionalReportInput.from_dict(report_input or {})

    validation = validate_input(inp)
    if not validation.ok:
        gates = quality_gates(inp, validation_ok=False, sections_ok=False, evidence_ok=False)
        return _rejected(inp, validation.errors, gates)

    sections = render_sections(inp)
    section_keys = [s.key for s in sections]
    missing = [k for k in REPORT_SECTIONS if k not in section_keys]
    if missing or len(sections) != len(REPORT_SECTIONS):
        gates = quality_gates(inp, validation_ok=True, sections_ok=False, evidence_ok=False)
        return _rejected(inp, [f"missing sections: {missing}"], gates)

    section_evidence = {s.key: list(s.evidence_ids) for s in sections}
    evidence_errors = validate_section_evidence_coverage(inp, section_evidence)
    # Watch/meta sections may have empty mapping; paragraph sections must not.
    if evidence_errors:
        gates = quality_gates(inp, validation_ok=True, sections_ok=True, evidence_ok=False)
        return _rejected(inp, evidence_errors, gates)

    text = render_text(sections, ticker=inp.ticker, company_name=inp.company_name)
    if "Bottom Line" not in text:
        gates = quality_gates(inp, validation_ok=True, sections_ok=False, evidence_ok=True)
        return _rejected(inp, ["bottom line missing from rendered text"], gates)

    gates = quality_gates(inp, validation_ok=True, sections_ok=True, evidence_ok=True)
    if not all(gates.values()):
        failed = [k for k, v in gates.items() if not v]
        return _rejected(inp, [f"quality gate failed: {failed}"], gates)

    return InstitutionalReport(
        ok=True,
        workstream_id=IRE_WORKSTREAM_ID,
        version=IRE_VERSION,
        report_type=IRE_REPORT_TYPE,
        ticker=inp.ticker,
        company_name=inp.company_name,
        recommendation=inp.recommendation,
        conviction=inp.conviction,
        confidence=int(inp.confidence),
        sections=sections,
        text=text,
        quality_gates=gates,
        validation_errors=[],
        rejected=False,
        llm=False,
        as_of=inp.as_of,
        input_fingerprint=_fingerprint(inp),
    )
