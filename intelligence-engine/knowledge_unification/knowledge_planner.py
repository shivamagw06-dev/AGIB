"""Module 3 — Knowledge Planner (ordered provider plan, never blind retrieval)."""

from __future__ import annotations

from knowledge_unification.registry import KnowledgeRegistry, get_registry
from knowledge_unification.schema import KnowledgePlan, QueryPlan

# Default ordered menus by question family. Priority numbers on ProviderSpec
# still decide final sort among the selected set.
_COMPANY_MENU = (
    "company_memory",
    "ikl",
    "valuation_consensus",
    "capiq_ikt",
    "knowledge_factory",
    "cgl",
    "legacy_kip",
)
# Phase 3.0.5 — BI first for company business questions, then CapIQ / memory / KF.
# Phase 3.1.5 — Industry Intelligence consulted so BI can fuse Industry DNA.
_BUSINESS_MENU = (
    "business_intelligence",
    "industry_intelligence",
    "valuation_consensus",
    "capiq_ikt",
    "company_memory",
    "ikl",
    "knowledge_factory",
    "cgl",
    "legacy_kip",
)
# Phase 3.2.5 — Investment Intelligence first for investment-shaped questions.
# INV consumes BI + Industry DNA conceptually; planner still consults BI/II.
_INVESTMENT_MENU = (
    "investment_intelligence",
    "business_intelligence",
    "industry_intelligence",
    "valuation_consensus",
    "capiq_ikt",
    "company_memory",
    "ikl",
    "knowledge_factory",
    "cgl",
    "legacy_kip",
)
# Phase 3.3.5 — Portfolio Intelligence for portfolio-shaped questions.
_PORTFOLIO_MENU = (
    "portfolio_intelligence",
    "investment_intelligence",
    "business_intelligence",
    "industry_intelligence",
    "valuation_consensus",
    "capiq_ikt",
    "company_memory",
    "ikl",
    "knowledge_factory",
    "cgl",
    "legacy_kip",
)
# Phase 3.4.5 — Research Intelligence for institutional research / document memory.
_RESEARCH_MENU = (
    "research_intelligence",
    "investment_intelligence",
    "business_intelligence",
    "industry_intelligence",
    "valuation_consensus",
    "capiq_ikt",
    "company_memory",
    "ikl",
    "knowledge_factory",
    "cgl",
    "legacy_kip",
)
# Pure industry / KPI / valuation pedagogy — II first (canonical Industry DNA).
_INDUSTRY_CONCEPT_MENU = (
    "industry_intelligence",
    "business_intelligence",
    "knowledge_factory",
    "financial_concepts",
    "cgl",
    "legacy_kip",
)
_CONCEPT_MENU = (
    "financial_concepts",
    "financial_foundations",
    "financial_statement_intelligence",
    "academy",
)
_ACCOUNTING_MENU = (
    "financial_foundations",
    "financial_statement_intelligence",
    "financial_concepts",
    "academy",
)
_VALUATION_MENU = (
    "valuation_consensus",
    "financial_concepts",
    "academy",
    "capiq_ikt",
    "company_memory",
)
# Industry-specific valuation pedagogy (P/B for banks, EV/Sales for SaaS, …).
_VALUATION_INDUSTRY_MENU = (
    "industry_intelligence",
    "financial_concepts",
    "business_intelligence",
    "academy",
)
_MACRO_MENU = (
    "academy",
    "ikl",
    "cgl",
    "legacy_kip",
)

_BUSINESS_TYPES = frozenset(
    {
        "business_model",
        "moat",
        "unit_economics",
        "comparison",
        "business_risk",
        "industry",
    }
)


def build_knowledge_plan(
    query: QueryPlan,
    *,
    registry: KnowledgeRegistry | None = None,
) -> KnowledgePlan:
    reg = registry or get_registry()
    types = set(query.question_types)
    selected: list[str] = []
    rationale: list[str] = []

    business_shaped = bool(types.intersection(_BUSINESS_TYPES))
    company_bound = bool(query.ticker_hint or query.company_hint or "comparison" in types)
    qlow = (query.question or "").lower()
    research_shaped = "research" in types or any(
        k in qlow
        for k in (
            "annual report",
            "earnings call",
            "earnings transcript",
            "conference call",
            "transcript",
            "management commentary",
            "management intelligence",
            "guidance history",
            "guidance evolved",
            "guidance intelligence",
            "research memory",
            "deep research",
            "cross-document",
            "cross document",
            "investor day",
            "research timeline",
            "timeline intelligence",
            "what changed since",
            "last quarter",
            "five years of",
            "5 years of",
            "from the annual report",
            "capital allocation evolution",
            "management philosophy",
            "estimate intelligence",
            "estimate changes",
            "event intelligence",
            "event research",
        )
    )
    portfolio_shaped = "portfolio" in types or any(
        k in qlow
        for k in (
            "portfolio construction",
            "portfolio quality",
            "portfolio scenario",
            "risk budget",
            "factor exposure",
            "position sizing",
            "rebalanc",
            "agib core",
            "concentrated growth",
            "watchlist",
        )
    )
    investment_shaped = "investment" in types or any(
        k in qlow
        for k in (
            "investment thesis",
            "catalyst",
            "scenario analysis",
            "bull and bear",
            "bear case",
            "base scenario",
            "scenario",
            "downside",
            "investors monitor",
            "for an investor",
            "monitoring priorit",
            "monitoring point",
            "evidence strength",
            "from an investment",
            "investment quality",
            "investment risk",
            "investment case",
            "committee",
            "what drives valuation",
            "valuation driver",
            "quality perspective",
            "business quality",
            "unknowns remain",
            "allocate capital",
            "capital allocation",
            "roic improve",
            "why might roic",
        )
    )
    industry_pedagogy = bool(
        types.intersection({"industry", "unit_economics", "business_risk"})
        or (
            "valuation" in types
            and not company_bound
            and any(
                tok in (query.question or "").lower()
                for tok in (
                    "bank",
                    "saas",
                    "software",
                    "airline",
                    "fmcg",
                    "utilit",
                    "hospital",
                    "telecom",
                    "insurance",
                    "insurer",
                    "cement",
                    "real estate",
                    "commodity",
                    "p/b",
                    "ev/sales",
                    "embedded value",
                    "nav",
                )
            )
        )
    )

    if research_shaped and (company_bound or "research" in types or "comparison" in types):
        selected.extend(_RESEARCH_MENU)
        rationale.append(
            "Research-shaped → Research Intelligence → INV → BI → Industry DNA → CapIQ → memory → KF."
        )
    elif portfolio_shaped:
        selected.extend(_PORTFOLIO_MENU)
        rationale.append(
            "Portfolio-shaped → Portfolio Intelligence → INV → BI → Industry DNA → CapIQ → memory → KF."
        )
    elif investment_shaped and (company_bound or "comparison" in types or "investment" in types):
        selected.extend(_INVESTMENT_MENU)
        rationale.append(
            "Investment-shaped → Investment Intelligence → BI → Industry DNA → CapIQ → memory → KF."
        )
    elif business_shaped and company_bound:
        selected.extend(_BUSINESS_MENU)
        rationale.append(
            "Business-shaped + company → BI → Industry DNA → CapIQ → memory → KF → CGL → legacy."
        )
    elif business_shaped or (industry_pedagogy and not company_bound):
        # Industry / unit-economics / KPI / valuation pedagogy without a ticker bind.
        selected.extend(_INDUSTRY_CONCEPT_MENU)
        rationale.append(
            "Industry pedagogy (no company bind) → Industry Intelligence → BI → KF → concepts."
        )
    elif types.intersection({"company", "market", "news"}) and (
        query.ticker_hint or query.company_hint
    ):
        selected.extend(_COMPANY_MENU)
        rationale.append("Company-shaped question → memory → CapIQ → KF → CGL → legacy fallback.")

    if types.intersection({"concept"}) and not query.ticker_hint and not business_shaped and not industry_pedagogy:
        selected.extend(_CONCEPT_MENU)
        rationale.append("Concept question → deterministic finance engines only (no retrieval default).")

    if types.intersection({"accounting", "financial_statement"}):
        selected.extend(_ACCOUNTING_MENU)
        rationale.append("Accounting/FSA → foundations + statement intelligence.")

    if types.intersection({"valuation"}) and not business_shaped:
        if industry_pedagogy and not company_bound:
            selected.extend(_VALUATION_INDUSTRY_MENU)
            rationale.append("Industry valuation pedagogy → Industry Intelligence → concepts.")
        else:
            selected.extend(_VALUATION_MENU)
            rationale.append("Valuation → concepts + academy + CapIQ snapshot when company-bound.")

    if types.intersection({"macro"}):
        selected.extend(_MACRO_MENU)
        rationale.append("Macro → academy datasets + IKL/CGL.")

    if not selected:
        # Unknown: try concepts then soft company detection leftovers, then legacy.
        selected = ["financial_concepts", "financial_foundations", "capiq_ikt", "legacy_kip"]
        rationale.append("Unknown intent → conservative deterministic-first menu.")

    # Drop providers that are hard-empty/error when health is known, but keep
    # them if health is unknown (lazy). Refresh lightly.
    health = reg.refresh_health()
    filtered = []
    for pid in selected:
        if pid not in {p.spec.id for p in reg.all()}:
            continue
        status = health.get(pid, "unknown")
        if status == "error":
            rationale.append(f"Skipped {pid}: health=error.")
            continue
        # Keep "empty" providers in the plan so diagnostics show they were
        # considered; ranking will reject empty results after consult.
        filtered.append(pid)

    # Preserve menu order — menus encode the Knowledge Dependency Map
    # (Industry DNA → BI → CapIQ → …). Re-sorting by ProviderSpec.priority
    # would incorrectly put Industry Intelligence ahead of BI on company
    # business questions.
    seen = set()
    unique = []
    for pid in filtered:
        if pid not in seen:
            seen.add(pid)
            unique.append(pid)

    return KnowledgePlan(query=query, provider_ids=unique, rationale=rationale)
