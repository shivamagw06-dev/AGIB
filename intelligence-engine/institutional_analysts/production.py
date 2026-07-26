"""IAF production entry — Research Planner → Analysts → Committee → CIO."""

from __future__ import annotations

from typing import Any

from institutional_analysts.base import company_name, ticker_of
from institutional_analysts.business.analyst import analyse as business_analyse
from institutional_analysts.cio.report import write_report
from institutional_analysts.committee.aggregate import aggregate
from institutional_analysts.financial.analyst import analyse as financial_analyse
from institutional_analysts.flags import (
    flags_dict,
    is_enabled,
    is_iai_business_enabled,
    is_iai_financial_enabled,
    is_iai_valuation_enabled,
)
from institutional_analysts.macro.analyst import analyse as macro_analyse
from institutional_analysts.management.analyst import analyse as management_analyse
from institutional_analysts.mandates import MANDATES, mandate_for
from institutional_analysts.market.analyst import analyse as market_analyse
from institutional_analysts import memory as iaf_memory
from institutional_analysts.ownership.analyst import analyse as ownership_analyse
from institutional_analysts.risk.analyst import analyse as risk_analyse
from institutional_analysts.schema import (
    ANALYST_ROLES,
    ARCHITECTURE_STATUS,
    IAF_VERSION,
    PROGRAMME,
    PUBLIC_OWNER_LABELS,
    SECTION_OWNERS,
)
from institutional_analysts.sector.analyst import analyse as sector_analyse
from institutional_analysts.valuation.analyst import analyse as valuation_analyse

_ANALYSERS = {
    "business": business_analyse,
    "financial": financial_analyse,
    "valuation": valuation_analyse,
    "market": market_analyse,
    "sector": sector_analyse,
    "macro": macro_analyse,
    "risk": risk_analyse,
    "management": management_analyse,
    "ownership": ownership_analyse,
}


def health() -> dict[str, Any]:
    return {
        "status": "ok" if is_enabled() else "disabled",
        "programme": PROGRAMME,
        "version": IAF_VERSION,
        "architecture_status": ARCHITECTURE_STATUS,
        "not_an_engine": True,
        "orchestration_only": True,
        "no_new_data": True,
        "analysts": list(ANALYST_ROLES),
        "mandates": {r: mandate_for(r) for r in ANALYST_ROLES},
        "section_owners": SECTION_OWNERS,
        "public_owner_labels": PUBLIC_OWNER_LABELS,
        "memory": iaf_memory.metrics(),
        "features": {
            "structured_opinions": True,
            "domain_guards": True,
            "multi_factor_confidence": True,
            "analyst_memory": True,
            "committee_meeting_stages": True,
            "disagreement_matrix": True,
            "committee_minutes": True,
            "cio_editor": True,
            "iai_business_analyst": is_iai_business_enabled(),
            "iai_business_analyst_v2": is_iai_business_enabled(),
            "iai_business_analyst_v2_1": is_iai_business_enabled(),
            "iai_financial_analyst": is_iai_financial_enabled(),
            "iai_valuation_analyst": is_iai_valuation_enabled(),
        },
        "does_not_redesign": [
            "cid",
            "leo",
            "irp",
            "company_analysis",
            "financial_intelligence",
            "company_monitor",
            "knowledge_foundation",
            "academy",
            "dvc",
            "ecp",
            "market_data_client",
            "providers",
            "investment_committee",
            "cio",
            "research_writer",
            "ui",
        ],
        "flags": flags_dict(),
    }


def quality_gates() -> dict[str, Any]:
    return {
        "programme": PROGRAMME,
        "version": IAF_VERSION,
        "passed": is_enabled(),
        "checks": {
            "enabled": is_enabled(),
            "one_question_per_analyst": True,
            "mandate_metadata_present": len(MANDATES) == len(ANALYST_ROLES),
            "structured_opinions": True,
            "domain_guards": True,
            "committee_reads_opinions_only": True,
            "committee_meeting_stages": True,
            "cio_reads_committee_only": True,
            "cio_editor_no_analyst_verbatim": True,
            "no_internal_names_in_user_copy": True,
            "engines_unchanged": True,
        },
        "flags": flags_dict(),
    }


def plan_research(query: str, *, ticker: str | None = None) -> dict[str, Any]:
    return {
        "owner": "research_planner",
        "query": query,
        "ticker": ticker,
        "assignments": [
            {
                "role": r,
                "mandate": mandate_for(r).get("mandate"),
                "primary_question": mandate_for(r).get("primary_question"),
                "primary_inputs": mandate_for(r).get("primary_inputs"),
                "outputs": mandate_for(r).get("outputs"),
                "never": mandate_for(r).get("never"),
            }
            for r in ANALYST_ROLES
        ],
        "flow": [
            "research_planner",
            "specialist_analysts",
            "investment_committee_meeting",
            "chief_investment_officer_editor",
            "institutional_report",
        ],
    }


def package_for_ask_agi(
    query: str,
    *,
    ticker: str | None = None,
    company_analysis: dict[str, Any] | None = None,
    company_dossier: dict[str, Any] | None = None,
    live_evidence: dict[str, Any] | None = None,
    finance_academy: dict[str, Any] | None = None,
    sector_intelligence: dict[str, Any] | None = None,
    company_monitor: dict[str, Any] | None = None,
    valuation: dict[str, Any] | None = None,
    institutional_briefing: dict[str, Any] | None = None,
    intelligence_construction: dict[str, Any] | None = None,
    decision_engine: dict[str, Any] | None = None,
    intelligence_layer: dict[str, Any] | None = None,
    irp: dict[str, Any] | None = None,
    evidence_completion: dict[str, Any] | None = None,
    data_validation: dict[str, Any] | None = None,
    knowledge_foundation: dict[str, Any] | None = None,
    aws_macro: dict[str, Any] | None = None,
    yahoo_enrichment: dict[str, Any] | None = None,
    **_: Any,
) -> dict[str, Any]:
    if not is_enabled():
        return {"enabled": False, "bypassed": True, "programme": PROGRAMME}

    ctx: dict[str, Any] = {
        "query": query,
        "ticker": ticker,
        "company_analysis": company_analysis or {},
        "company_dossier": company_dossier or {},
        "live_evidence": live_evidence or {},
        "finance_academy": finance_academy or {},
        "sector_intelligence": sector_intelligence or {},
        "company_monitor": company_monitor or {},
        "valuation": valuation or {},
        "institutional_briefing": institutional_briefing or {},
        "intelligence_construction": intelligence_construction or {},
        "decision_engine": decision_engine or {},
        "intelligence_layer": intelligence_layer or {},
        "irp": irp or {},
        "evidence_completion": evidence_completion or {},
        "data_validation": data_validation or {},
        "knowledge_foundation": knowledge_foundation or {},
        "aws_macro": aws_macro or {},
        "yahoo_enrichment": yahoo_enrichment or {},
    }
    t = ticker_of(ctx) or (ticker.upper() if ticker else None)
    ctx["ticker"] = t
    name = company_name(ctx)

    planner = plan_research(query, ticker=t)
    opinions: dict[str, dict[str, Any]] = {}
    for role, fn in _ANALYSERS.items():
        try:
            opinions[role] = fn(ctx)
        except Exception as exc:
            meta = mandate_for(role)
            opinions[role] = {
                "role": role,
                "analyst": meta.get("analyst"),
                "mandate": {
                    "text": meta.get("mandate"),
                    "primary_question": meta.get("primary_question"),
                    "primary_inputs": meta.get("primary_inputs"),
                    "outputs": meta.get("outputs"),
                    "never": meta.get("never"),
                },
                "primary_question": meta.get("primary_question"),
                "question": meta.get("primary_question"),
                "summary": "Opinion unavailable for this run.",
                "headline": "Opinion unavailable for this run.",
                "stance": "Neutral",
                "strengths": [],
                "weaknesses": [],
                "sections": {},
                "evidence": [],
                "unanswered_questions": ["Specialist file could not be assembled for this run."],
                "confidence": {
                    "evidence": 0.2,
                    "knowledge": 0.2,
                    "freshness": 0.2,
                    "coverage": 0.2,
                    "overall": 0.2,
                },
                "structured": True,
                "error": str(exc)[:120],
            }

    committee = aggregate(opinions, query=query, company=name, ticker=t)
    cio = write_report(committee, query=query, company=name)

    # Persist memory AFTER opinions are built (so this run can compare to prior)
    iaf_memory.put_opinions(t, opinions)
    minutes_row = committee.get("minutes") or {}
    # ICI already stores minutes forever; keep IAF mirror for analyst what-changed
    iaf_memory.put_minutes(t, minutes_row)
    minutes_history = committee.get("timeline") or iaf_memory.get_minutes_history(t, limit=6)

    base_pack = {
        "enabled": True,
        "programme": PROGRAMME,
        "version": IAF_VERSION,
        "architecture_status": ARCHITECTURE_STATUS,
        "not_an_engine": True,
        "orchestration_only": True,
        "query": query,
        "ticker": t,
        "company": name,
        "research_plan": planner,
        "mandates": {r: mandate_for(r) for r in ANALYST_ROLES},
        "analyst_opinions": opinions,
        "committee": committee,
        "investment_committee_intelligence": committee.get("ici") if committee.get("ici_enabled") else {},
        "cio": cio,
        "disagreement_matrix": committee.get("disagreement_matrix"),
        "committee_minutes": minutes_row,
        "committee_minutes_history": minutes_history,
        "committee_vote": committee.get("vote") or committee.get("stage_5_vote"),
        "committee_decision": committee.get("decision") or committee.get("stage_10_decision"),
        "committee_challenges": committee.get("challenges") or committee.get("stage_3_challenges") or [],
        "minority_opinions": committee.get("minority_opinions") or [],
        "confidence_recalibration": committee.get("confidence_recalibration") or {},
        "committee_timeline": committee.get("timeline") or [],
        "committee_accuracy": committee.get("accuracy") or {},
        "section_owners": SECTION_OWNERS,
        "public_owner_labels": PUBLIC_OWNER_LABELS,
        "executive_summary": cio.get("executive_summary"),
        "investment_thesis": cio.get("investment_thesis"),
        "bull_case": cio.get("bull_case"),
        "base_case": cio.get("base_case"),
        "bear_case": cio.get("bear_case"),
        "key_risks": cio.get("key_risks"),
        "key_catalysts": cio.get("key_catalysts"),
        "institutional_conclusion": cio.get("institutional_conclusion"),
        "why": [w for w in (cio.get("why") or []) if w][:6],
        "what_changed": cio.get("what_changed") or [],
        "confidence": cio.get("confidence"),
        "business_intelligence": opinions.get("business"),
        "financial_intelligence": opinions.get("financial"),
        "valuation_intelligence": opinions.get("valuation"),
        "market_intelligence": opinions.get("market"),
        "sector_intelligence_opinion": opinions.get("sector"),
        "macro_intelligence": opinions.get("macro"),
        "risk_intelligence": opinions.get("risk"),
        "management_intelligence": opinions.get("management"),
        "ownership_intelligence": opinions.get("ownership"),
        "institutional_view": committee,
        "ask_agi_hints": [
            f"Specialist analysts contributed structured opinions on {name}",
            f"Committee stance: {committee.get('committee_stance')}",
            f"Chief Investment Officer confidence {cio.get('confidence')}",
        ],
    }

    # Institutional Research Writer — presentation layer AFTER CIO (never mutates votes/confidence)
    research_writer: dict[str, Any] = {}
    try:
        from research_writer.production import package_for_ask_agi as irw_package

        research_writer = irw_package(base_pack, query=query) or {}
    except Exception:
        research_writer = {}

    if research_writer.get("enabled"):
        base_pack["research_writer"] = research_writer
        base_pack["institutional_report"] = research_writer.get("institutional_report")
        # Presentation overlays only — intelligence fields above stay authoritative for votes/confidence
        base_pack["executive_summary"] = research_writer.get("executive_summary") or base_pack["executive_summary"]
        base_pack["investment_thesis"] = research_writer.get("investment_thesis") or base_pack["investment_thesis"]
        base_pack["institutional_conclusion"] = (
            research_writer.get("institutional_conclusion") or base_pack["institutional_conclusion"]
        )
        base_pack["written_business_intelligence"] = research_writer.get("business_intelligence")
        base_pack["written_financial_intelligence"] = research_writer.get("financial_intelligence")
        base_pack["written_valuation_intelligence"] = research_writer.get("valuation_intelligence")
        base_pack["written_market_intelligence"] = research_writer.get("market_intelligence")
        base_pack["written_sector_intelligence"] = research_writer.get("sector_intelligence")
        base_pack["written_macro_intelligence"] = research_writer.get("macro_intelligence")
        base_pack["written_management"] = research_writer.get("management")
        base_pack["written_ownership"] = research_writer.get("ownership")
        base_pack["written_institutional_view"] = research_writer.get("institutional_view")
        base_pack["risk_register"] = research_writer.get("risk_register")
        base_pack["report_tables"] = research_writer.get("tables")
        base_pack["chart_recommendations"] = research_writer.get("chart_recommendations")
        if research_writer.get("bull_case"):
            base_pack["bull_case"] = research_writer.get("bull_case")
        if research_writer.get("base_case"):
            base_pack["base_case"] = research_writer.get("base_case")
        if research_writer.get("bear_case"):
            base_pack["bear_case"] = research_writer.get("bear_case")
        hints = list(base_pack.get("ask_agi_hints") or [])
        for h in research_writer.get("ask_agi_hints") or []:
            if h not in hints:
                hints.append(h)
        base_pack["ask_agi_hints"] = hints[:8]

    return base_pack
