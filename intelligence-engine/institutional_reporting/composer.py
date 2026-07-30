"""Report composer — Facts → Reasons → Report (IRE-02)."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Union

from institutional_reporting.flags import is_enabled
from institutional_reporting.models import InstitutionalReport, InstitutionalReportInput
from institutional_reporting.reason_composer import compose_reasons
from institutional_reporting.renderer import (
    render_diagnostics_text,
    render_reason_graph_text,
    render_sections_from_reasons,
    render_text,
)
from institutional_reporting.schema import (
    IRE_REPORT_TYPE,
    IRE_VERSION,
    IRE_WORKSTREAM_ID,
    REASON_COMPOSER_VERSION,
    REPORT_SECTIONS,
    VALIDATOR_VERSION,
)
from institutional_reporting.validator import validate_input, validate_reasons

try:
    from financial_statements_engine.util import now_iso
except Exception:  # noqa: BLE001
    from datetime import datetime, timezone

    def now_iso() -> str:  # type: ignore[misc]
        return datetime.now(timezone.utc).isoformat()


def _fingerprint(inp: InstitutionalReportInput) -> str:
    payload = json.dumps(inp.to_dict(), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def build_diagnostics(
    inp: InstitutionalReportInput,
    *,
    reason_count: int,
    gates: dict[str, bool],
) -> dict[str, Any]:
    evidence_count = len(inp.evidence or ())
    gate_pass = bool(gates) and all(gates.values())
    return {
        "generated_at": now_iso(),
        "report_version": IRE_REPORT_TYPE,
        "ire_version": IRE_VERSION,
        "reason_composer_version": REASON_COMPOSER_VERSION,
        "validator_version": VALIDATOR_VERSION,
        "reason_object_count": reason_count,
        "evidence_count": evidence_count,
        "quality_gate": "PASS" if gate_pass else "FAIL",
        "quality_gate_pass": gate_pass,
        "llm": False,
        "external_writer": False,
        "section_count": len(REPORT_SECTIONS),
    }


def quality_gates(
    inp: InstitutionalReportInput,
    *,
    validation_ok: bool,
    sections_ok: bool,
    evidence_ok: bool,
    reasons_ok: bool,
) -> dict[str, bool]:
    return {
        "recommendation_valid": validation_ok and bool(inp.recommendation),
        "confidence_present": isinstance(inp.confidence, int) and 0 <= inp.confidence <= 100,
        "evidence_exists": bool(inp.evidence) and evidence_ok,
        "thesis_exists": bool(inp.thesis),
        "valuation_exists": bool(str(inp.valuation or "").strip()),
        "risk_exists": bool(str(inp.overall_risk or "").strip()),
        "bottom_line_exists": sections_ok,
        "reasons_valid": reasons_ok,
        "section_reasons_complete": reasons_ok,
        "contradicting_evidence_present": reasons_ok,
        "unknowns_present": reasons_ok,
        "enabled": is_enabled(),
    }


def _rejected(
    inp: InstitutionalReportInput,
    errors: list[str],
    gates: dict[str, bool],
    *,
    reasons: list[Any] | None = None,
) -> InstitutionalReport:
    diagnostics = build_diagnostics(inp, reason_count=len(reasons or []), gates=gates)
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
        reasons=list(reasons or []),
        diagnostics=diagnostics,
        reason_graph_text="",
    )


def compose_report(
    report_input: Union[InstitutionalReportInput, dict[str, Any], None],
) -> InstitutionalReport:
    """Compose a deterministic InstitutionalReport from structured facts via Reasons.

    Pipeline: Evidence/facts → Reason Composer → Institutional Reporting render.
    No Gemini. No GPT. No external writer.
    """
    if isinstance(report_input, InstitutionalReportInput):
        inp = report_input
    else:
        inp = InstitutionalReportInput.from_dict(report_input or {})

    validation = validate_input(inp)
    if not validation.ok:
        gates = quality_gates(
            inp, validation_ok=False, sections_ok=False, evidence_ok=False, reasons_ok=False
        )
        return _rejected(inp, validation.errors, gates)

    graph = compose_reasons(inp)
    reason_validation = validate_reasons(graph)
    if not reason_validation.ok:
        gates = quality_gates(
            inp, validation_ok=True, sections_ok=False, evidence_ok=False, reasons_ok=False
        )
        return _rejected(inp, reason_validation.errors, gates, reasons=list(graph.reasons))

    # Evidence count zero already covered by input validator; double-check reasons.
    if len(inp.evidence) == 0:
        gates = quality_gates(
            inp, validation_ok=True, sections_ok=False, evidence_ok=False, reasons_ok=True
        )
        return _rejected(inp, ["evidence count zero"], gates, reasons=list(graph.reasons))

    sections = render_sections_from_reasons(graph, inp)
    section_keys = [s.key for s in sections]
    missing = [k for k in REPORT_SECTIONS if k not in section_keys]
    if missing or len(sections) != len(REPORT_SECTIONS):
        gates = quality_gates(
            inp, validation_ok=True, sections_ok=False, evidence_ok=True, reasons_ok=True
        )
        return _rejected(inp, [f"missing sections: {missing}"], gates, reasons=list(graph.reasons))

    # Every section must carry a reason in meta / object
    for section in sections:
        if section.reason is None:
            gates = quality_gates(
                inp, validation_ok=True, sections_ok=False, evidence_ok=True, reasons_ok=False
            )
            return _rejected(
                inp,
                [f"section missing reason: {section.key}"],
                gates,
                reasons=list(graph.reasons),
            )

    text = render_text(sections, ticker=inp.ticker, company_name=inp.company_name)
    if "Bottom Line" not in text:
        gates = quality_gates(
            inp, validation_ok=True, sections_ok=False, evidence_ok=True, reasons_ok=True
        )
        return _rejected(inp, ["bottom line missing from rendered text"], gates, reasons=list(graph.reasons))

    gates = quality_gates(
        inp, validation_ok=True, sections_ok=True, evidence_ok=True, reasons_ok=True
    )
    if not all(gates.values()):
        failed = [k for k, v in gates.items() if not v]
        return _rejected(inp, [f"quality gate failed: {failed}"], gates, reasons=list(graph.reasons))

    diagnostics = build_diagnostics(inp, reason_count=len(graph.reasons), gates=gates)
    reason_graph_text = render_reason_graph_text(graph)

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
        as_of=inp.as_of or diagnostics["generated_at"],
        input_fingerprint=_fingerprint(inp),
        reasons=list(graph.reasons),
        diagnostics=diagnostics,
        reason_graph_text=reason_graph_text,
    )
