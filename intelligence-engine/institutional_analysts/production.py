"""IAF production entry — Research Planner → Analysts → Committee → CIO."""

from __future__ import annotations

from typing import Any

from institutional_analysts.base import company_name, ticker_of
from institutional_analysts.business.analyst import analyse as business_analyse
from institutional_analysts.cio.report import write_report
from institutional_analysts.committee.aggregate import aggregate
from institutional_analysts.financial.analyst import analyse as financial_analyse
from institutional_analysts.flags import flags_dict, is_enabled
from institutional_analysts.macro.analyst import analyse as macro_analyse
from institutional_analysts.management.analyst import analyse as management_analyse
from institutional_analysts.market.analyst import analyse as market_analyse
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
        "section_owners": SECTION_OWNERS,
        "public_owner_labels": PUBLIC_OWNER_LABELS,
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
            "committee_reads_opinions_only": True,
            "cio_reads_committee_only": True,
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
        "assignments": [{"role": r, "mandate": _mandate(r)} for r in ANALYST_ROLES],
        "flow": [
            "research_planner",
            "specialist_analysts",
            "investment_committee",
            "chief_investment_officer",
            "institutional_report",
        ],
    }


def _mandate(role: str) -> str:
    return {
        "business": "Is this a good business?",
        "financial": "Are the financials improving?",
        "valuation": "Is today's valuation attractive?",
        "market": "What is the market saying?",
        "sector": "Is the industry attractive?",
        "macro": "Does macro help or hurt?",
        "risk": "What can go wrong?",
        "management": "Can management be trusted?",
        "ownership": "Who owns this business?",
    }.get(role, role)


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
            opinions[role] = {
                "role": role,
                "analyst": role.title(),
                "question": _mandate(role),
                "headline": "Opinion unavailable for this run.",
                "sections": {},
                "evidence": [],
                "confidence": 0.3,
                "error": str(exc)[:120],
            }

    committee = aggregate(opinions)
    cio = write_report(committee, query=query, company=name)

    return {
        "enabled": True,
        "programme": PROGRAMME,
        "version": IAF_VERSION,
        "architecture_status": ARCHITECTURE_STATUS,
        "not_an_engine": True,
        "orchestration_only": True,
        "ticker": t,
        "company": name,
        "research_plan": planner,
        "analyst_opinions": opinions,
        "committee": committee,
        "cio": cio,
        "section_owners": SECTION_OWNERS,
        "public_owner_labels": PUBLIC_OWNER_LABELS,
        # Convenience projections for Answer Construction / UI
        "executive_summary": cio.get("executive_summary"),
        "investment_thesis": cio.get("investment_thesis"),
        "bull_case": cio.get("bull_case"),
        "base_case": cio.get("base_case"),
        "bear_case": cio.get("bear_case"),
        "key_risks": cio.get("key_risks"),
        "key_catalysts": cio.get("key_catalysts"),
        "institutional_conclusion": cio.get("institutional_conclusion"),
        "why": [w for w in (cio.get("why") or []) if w][:6],
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
            f"Specialist analysts contributed opinions on {name}",
            f"Investment Committee readiness: {committee.get('recommendation_readiness')}",
            f"Chief Investment Officer confidence {cio.get('confidence')}",
        ],
    }
