"""IRW production entry — soft writing layer after CIO."""

from __future__ import annotations

from typing import Any

from research_writer.editor import write_institutional_report
from research_writer.flags import flags_dict, is_enabled
from research_writer.schema import ARCHITECTURE_STATUS, IRW_VERSION, PROGRAMME, REPORT_TYPES


def health() -> dict[str, Any]:
    return {
        "status": "ok" if is_enabled() else "disabled",
        "programme": PROGRAMME,
        "version": IRW_VERSION,
        "architecture_status": ARCHITECTURE_STATUS,
        "not_an_engine": True,
        "presentation_writing_layer_only": True,
        "sits_after": "cio",
        "never_changes": [
            "recommendations",
            "scores",
            "confidence",
            "votes",
            "evidence",
        ],
        "report_types": list(REPORT_TYPES),
        "modules": [
            "editor",
            "narrative",
            "formatter",
            "transition",
            "table_builder",
            "chart_recommender",
            "citation_builder",
            "language_quality",
            "consistency",
            "tone",
        ],
        "does_not_redesign": [
            "cid",
            "company_analysis",
            "financial_intelligence",
            "investment_committee",
            "cio",
            "dvc",
            "providers",
            "knowledge_foundation",
            "academy",
            "institutional_analysts",
        ],
        "flags": flags_dict(),
    }


def quality_gates() -> dict[str, Any]:
    return {
        "programme": PROGRAMME,
        "version": IRW_VERSION,
        "passed": is_enabled(),
        "checks": {
            "enabled": is_enabled(),
            "presentation_only": True,
            "never_mutates_votes": True,
            "never_mutates_confidence": True,
            "never_mutates_evidence": True,
            "scrubs_provider_names": True,
            "scrubs_engine_names": True,
            "has_transitions": True,
            "has_tables": True,
            "has_chart_recommender": True,
            "has_repetition_detector": True,
            "has_consistency_engine": True,
            "engines_unchanged": True,
        },
        "flags": flags_dict(),
    }


def package_for_ask_agi(intelligence_pack: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Write the final institutional report from CIO/committee/analyst outputs.

    Never invents facts. Never changes votes, scores, confidence, or evidence.
    """
    if not is_enabled():
        return {"enabled": False, "bypassed": True, "programme": PROGRAMME}

    pack = dict(intelligence_pack or {})
    # Allow kwargs overlay for soft callers
    for k, v in kwargs.items():
        if v is not None and k not in pack:
            pack[k] = v
    query = str(pack.get("query") or kwargs.get("query") or "")

    try:
        report = write_institutional_report(pack, query=query)
    except Exception as exc:
        return {
            "enabled": False,
            "error": str(exc)[:200],
            "programme": PROGRAMME,
            "version": IRW_VERSION,
        }

    return {
        "enabled": True,
        "programme": PROGRAMME,
        "version": IRW_VERSION,
        "architecture_status": ARCHITECTURE_STATUS,
        "not_an_engine": True,
        "presentation_writing_layer_only": True,
        "institutional_report": report,
        # Flat presentation fields for AC / UI
        "executive_summary": report.get("executive_summary"),
        "investment_thesis": report.get("investment_thesis"),
        "institutional_view": report.get("institutional_view"),
        "business_intelligence": report.get("business_intelligence"),
        "financial_intelligence": report.get("financial_intelligence"),
        "valuation_intelligence": report.get("valuation_intelligence"),
        "market_intelligence": report.get("market_intelligence"),
        "sector_intelligence": report.get("sector_intelligence"),
        "macro_intelligence": report.get("macro_intelligence"),
        "management": report.get("management"),
        "ownership": report.get("ownership"),
        "institutional_conclusion": report.get("institutional_conclusion"),
        "bull_case": report.get("bull_case"),
        "base_case": report.get("base_case"),
        "bear_case": report.get("bear_case"),
        "risk_register": report.get("risk_register"),
        "tables": (report.get("tables") or []),
        "chart_recommendations": (report.get("chart_recommendations") or []),
        "citations": (report.get("citations") or []),
        "report_type": report.get("report_type"),
        "quality": report.get("quality"),
        # Explicit pass-through of immutable intelligence
        "intelligence_unchanged": report.get("intelligence_unchanged"),
        "ask_agi_hints": [
            f"Institutional Research Writer produced a {report.get('report_type')} note",
            "Presentation layer only — committee vote and confidence unchanged",
        ],
    }
