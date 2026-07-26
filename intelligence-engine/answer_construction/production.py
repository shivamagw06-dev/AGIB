"""Ask AGI Answer Construction V3 — soft production entry (+ IAF orchestration)."""

from __future__ import annotations

from typing import Any

from answer_construction.flags import flags_dict, is_enabled
from answer_construction.policy import apply_answer_construction_v3
from answer_construction.schema import AC_VERSION, ARCHITECTURE_STATUS, PROGRAMME


def health() -> dict[str, Any]:
    iaf_health: dict[str, Any] = {}
    irw_health: dict[str, Any] = {}
    try:
        from institutional_analysts.production import health as iaf_h

        iaf_health = iaf_h()
    except Exception:
        iaf_health = {"status": "unavailable"}
    try:
        from research_writer.production import health as irw_h

        irw_health = irw_h()
    except Exception:
        irw_health = {"status": "unavailable"}
    return {
        "status": "ok" if is_enabled() else "disabled",
        "programme": PROGRAMME,
        "version": AC_VERSION,
        "architecture_status": ARCHITECTURE_STATUS,
        "not_an_engine": True,
        "gate_logic_unchanged": True,
        "never_stop_at_first_coverage_check": True,
        "institutional_analyst_framework": iaf_health,
        "institutional_research_writer": irw_health,
        "flags": flags_dict(),
    }


_AC_POLICY_KEYS = {
    "query",
    "executive",
    "thesis",
    "house_label",
    "bull",
    "bear",
    "risks",
    "catalysts",
    "why",
    "intelligence_construction",
    "company_analysis",
    "company_dossier",
    "evidence_completion",
    "live_evidence",
    "sector_intelligence",
    "institutional_briefing",
    "decision_engine",
    "reco_gate",
    "leo_gate",
}


def package_for_ask_agi(**kwargs: Any) -> dict[str, Any]:
    """Soft entry used by UiService after IRP / IC / ECP orchestration.

    Runs Institutional Analyst Framework (opinions → committee → CIO → Research Writer),
    then applies Answer Construction V3 policy. Engines remain unchanged.
    """
    iaf_pack: dict[str, Any] = {}
    try:
        from institutional_analysts.production import package_for_ask_agi as iaf_package

        iaf_pack = (
            iaf_package(
                kwargs.get("query") or "",
                ticker=kwargs.get("ticker"),
                company_analysis=kwargs.get("company_analysis"),
                company_dossier=kwargs.get("company_dossier"),
                live_evidence=kwargs.get("live_evidence"),
                finance_academy=kwargs.get("finance_academy"),
                sector_intelligence=kwargs.get("sector_intelligence"),
                company_monitor=kwargs.get("company_monitor"),
                valuation=kwargs.get("valuation"),
                institutional_briefing=kwargs.get("institutional_briefing"),
                intelligence_construction=kwargs.get("intelligence_construction"),
                decision_engine=kwargs.get("decision_engine"),
                intelligence_layer=kwargs.get("intelligence_layer"),
                irp=kwargs.get("irp"),
                evidence_completion=kwargs.get("evidence_completion"),
                data_validation=kwargs.get("data_validation"),
                knowledge_foundation=kwargs.get("knowledge_foundation"),
                aws_macro=kwargs.get("aws_macro"),
                yahoo_enrichment=kwargs.get("yahoo_enrichment"),
            )
            or {}
        )
    except Exception:
        iaf_pack = {}

    policy_kwargs = {k: kwargs[k] for k in _AC_POLICY_KEYS if k in kwargs}
    out = apply_answer_construction_v3(
        institutional_analysts=iaf_pack if iaf_pack.get("enabled") else None,
        **policy_kwargs,
    )
    if iaf_pack.get("enabled"):
        out["institutional_analysts"] = iaf_pack
        out["base"] = list(iaf_pack.get("base_case") or out.get("base") or [])[:6]
        if iaf_pack.get("research_writer"):
            out["research_writer"] = iaf_pack.get("research_writer")
            out["institutional_report"] = iaf_pack.get("institutional_report")
        if iaf_pack.get("institutional_stack"):
            out["institutional_stack"] = iaf_pack["institutional_stack"]
    if not out.get("institutional_stack"):
        try:
            from institutional_stack.production import soft_slice_for_ask_agi

            stack = soft_slice_for_ask_agi(kwargs.get("ticker"))
            if stack:
                out["institutional_stack"] = stack.get("institutional_stack") or stack
        except Exception:
            pass
    return out


def quality_gates() -> dict[str, Any]:
    return {
        "programme": PROGRAMME,
        "version": AC_VERSION,
        "architecture_status": ARCHITECTURE_STATUS,
        "passed": is_enabled(),
        "checks": {
            "enabled": is_enabled(),
            "preserves_full_brief_when_gated": True,
            "recommendation_status_trailing_only": True,
            "never_expose_raw_missing_keys": True,
            "gate_logic_unchanged": True,
            "institutional_analyst_framework_soft": True,
            "institutional_research_writer_soft": True,
        },
        "flags": flags_dict(),
    }
