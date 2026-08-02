"""Module 3 — Knowledge Planner (ordered provider plan, never blind retrieval)."""

from __future__ import annotations

from knowledge_unification.registry import KnowledgeRegistry, get_registry
from knowledge_unification.schema import KnowledgePlan, QueryPlan

# Default ordered menus by question family. Priority numbers on ProviderSpec
# still decide final sort among the selected set.
_COMPANY_MENU = (
    "company_memory",
    "ikl",
    "capiq_ikt",
    "knowledge_factory",
    "cgl",
    "legacy_kip",
)
# Phase 3.0.5 — BI first for business-shaped questions, then CapIQ / memory / KF.
_BUSINESS_MENU = (
    "business_intelligence",
    "capiq_ikt",
    "company_memory",
    "ikl",
    "knowledge_factory",
    "cgl",
    "legacy_kip",
)
_INDUSTRY_CONCEPT_MENU = (
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
    "financial_concepts",
    "academy",
    "capiq_ikt",
    "company_memory",
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

    if business_shaped and (query.ticker_hint or query.company_hint or "comparison" in types):
        selected.extend(_BUSINESS_MENU)
        rationale.append(
            "Business-shaped question → BI → CapIQ → memory → KF → CGL → legacy fallback."
        )
    elif business_shaped:
        # Industry / unit-economics / moat pedagogy without a ticker bind.
        selected.extend(_INDUSTRY_CONCEPT_MENU)
        rationale.append(
            "Business/industry concept (no company bind) → BI → KF → concepts (no generic retrieval)."
        )
    elif types.intersection({"company", "market", "news"}) and (
        query.ticker_hint or query.company_hint
    ):
        selected.extend(_COMPANY_MENU)
        rationale.append("Company-shaped question → memory → CapIQ → KF → CGL → legacy fallback.")

    if types.intersection({"concept"}) and not query.ticker_hint and not business_shaped:
        selected.extend(_CONCEPT_MENU)
        rationale.append("Concept question → deterministic finance engines only (no retrieval default).")

    if types.intersection({"accounting", "financial_statement"}):
        selected.extend(_ACCOUNTING_MENU)
        rationale.append("Accounting/FSA → foundations + statement intelligence.")

    if types.intersection({"valuation"}) and not business_shaped:
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

    # Stable unique, then sort by registry priority
    seen = set()
    unique = []
    for pid in filtered:
        if pid not in seen:
            seen.add(pid)
            unique.append(pid)
    unique.sort(key=lambda pid: (reg.get(pid).spec.priority if reg.get(pid) else 999, pid))

    return KnowledgePlan(query=query, provider_ids=unique, rationale=rationale)
