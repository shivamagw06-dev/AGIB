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

    coverage = panel.get("coverage_pct")
    if coverage is None:
        coverage = readiness.get("overall")
    if coverage is None and company_dossier:
        coverage = company_dossier.get("coverage_score") or company_dossier.get("coverage_pct")

    name = company_name or (company_dossier or {}).get("ticker") or "this company"

    if blocked:
        status = "Withheld"
        summary = (
            f"Institutional recommendation status for {name}: current evidence is insufficient "
            "to support a Buy / Hold / Sell recommendation. The research briefing above remains "
            "valid institutional context — recommendation status is separate from company analysis."
        )
        detail = (
            "Several key valuation and financial datasets remain incomplete. AGI continues to "
            "enrich the living dossier; recommendation readiness will reopen when validated coverage "
            "crosses the institutional bar."
        )
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

    _ = (leo_gate, reco_gate)  # gate inputs used for blocked; names never exposed to clients
    return {
        "blocked": bool(blocked),
        "status": status,
        "summary": summary,
        "detail": detail,
        "coverage_pct": coverage,
        "readiness_label": "Open" if not blocked else "Deferred",
        "knowledge_gaps": gaps,
        "placement": "conclusion_only",
        "never_lead_answer": True,
        "not_a_trade_instruction": True,
    }
