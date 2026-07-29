"""Trailing Institutional Recommendation Status — never the first screen."""

from __future__ import annotations

from typing import Any

from answer_construction.knowledge_gaps import knowledge_gaps_from_sources
from answer_construction.schema import AC_VERSION, ARCHITECTURE_STATUS, PROGRAMME


def build_recommendation_status(
    *,
    blocked: bool,
    evidence_completion: dict[str, Any] | None = None,
    company_dossier: dict[str, Any] | None = None,
    live_evidence: dict[str, Any] | None = None,
    company_analysis: dict[str, Any] | None = None,
    sector_intelligence: dict[str, Any] | None = None,
    company_name: str | None = None,
    decision_engine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gaps = knowledge_gaps_from_sources(
        evidence_completion=evidence_completion,
        company_dossier=company_dossier,
        live_evidence=live_evidence,
        company_analysis=company_analysis,
        limit=8,
    )
    ecp = evidence_completion if isinstance(evidence_completion, dict) else {}
    panel = ecp.get("quality_panel") or {}
    readiness = (company_analysis or {}).get("recommendation_readiness") or {}
    leo_gate = ((live_evidence or {}).get("quality_gate") or {}) if isinstance(live_evidence, dict) else {}
    reco_gate = ((sector_intelligence or {}).get("recommendation_gate") or {}) if isinstance(sector_intelligence, dict) else {}
    ide = decision_engine if isinstance(decision_engine, dict) else {}
    gate = ide.get("institutional_readiness_gate") or {}

    coverage = gate.get("overall_coverage_pct")
    if coverage is None:
        coverage = panel.get("coverage_pct")
    if coverage is None:
        coverage = readiness.get("overall")
    if coverage is None and company_dossier:
        coverage = company_dossier.get("coverage_score") or company_dossier.get("coverage_pct")

    name = company_name or (company_dossier or {}).get("ticker") or "this company"
    evidence_conf = gate.get("evidence_confidence_pct")
    required = gate.get("required_confidence_pct") or 80
    missing = gate.get("additional_evidence_required") or gate.get("missing") or gaps

    if blocked or gate.get("hard_fail") or gate.get("band") in {"deferred", "watchlist"}:
        status = "Withheld"
        summary = (
            f"Investment thesis for {name}: INCONCLUSIVE. "
            "Current evidence is insufficient for an institutional-level recommendation. "
            "This should not be interpreted as a negative view of the company."
        )
        detail = (
            f"Evidence confidence {evidence_conf if evidence_conf is not None else 'n/a'}% "
            f"(required {required}% for high conviction). "
            "Additional evidence required: "
            + (
                "; ".join(str(m) for m in list(missing)[:5])
                if missing
                else "updated valuation, ownership, and latest earnings/filings"
            )
            + ". The research briefing above remains valid institutional context."
        )
        readiness_label = gate.get("band_label") or "Deferred"
        thesis_status = "INCONCLUSIVE"
        not_negative = True
    else:
        status = "Open for institutional assessment"
        summary = (
            f"Institutional recommendation status for {name}: evidence coverage supports analysis. "
            "This is not an automatic Buy / Hold / Sell instruction."
        )
        detail = (
            "Use the house view, financial intelligence, valuation discussion and risks above as "
            "the decision frame. Position sizing remains discretionary."
        )
        readiness_label = gate.get("band_label") or "Open"
        thesis_status = "FORMED"
        not_negative = False

    _ = (leo_gate, reco_gate)  # gate inputs used for blocked; names never exposed to clients
    return {
        "blocked": bool(blocked or gate.get("hard_fail")),
        "status": status,
        "summary": summary,
        "detail": detail,
        "coverage_pct": coverage,
        "evidence_confidence_pct": evidence_conf,
        "required_confidence_pct": required,
        "company_quality_10": gate.get("company_quality_10"),
        "market_opportunity_10": gate.get("market_opportunity_10"),
        "coverage": gate.get("coverage"),
        "checklist": gate.get("checklist") or [],
        "additional_evidence_required": list(missing)[:8] if isinstance(missing, list) else [],
        "investment_thesis_status": thesis_status,
        "not_a_negative_view": not_negative,
        "readiness_label": readiness_label,
        "readiness_band": gate.get("band"),
        "gate_summary": gate.get("summary_for_user") or {},
        "knowledge_gaps": gaps,
        "placement": "conclusion_only",
        "never_lead_answer": True,
        "not_a_trade_instruction": True,
        "never_conflate_data_with_quality": True,
    }
