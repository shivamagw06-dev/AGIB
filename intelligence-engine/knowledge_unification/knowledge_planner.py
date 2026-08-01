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


def build_knowledge_plan(
    query: QueryPlan,
    *,
    registry: KnowledgeRegistry | None = None,
) -> KnowledgePlan:
    reg = registry or get_registry()
    types = set(query.question_types)
    selected: list[str] = []
    rationale: list[str] = []

    if types.intersection({"company", "business_model", "industry", "market", "news"}) and (
        query.ticker_hint or query.company_hint
    ):
        selected.extend(_COMPANY_MENU)
        rationale.append("Company-shaped question → memory → CapIQ → KF → CGL → legacy fallback.")

    if types.intersection({"concept"}) and not query.ticker_hint:
        selected.extend(_CONCEPT_MENU)
        rationale.append("Concept question → deterministic finance engines only (no retrieval default).")

    if types.intersection({"accounting", "financial_statement"}):
        selected.extend(_ACCOUNTING_MENU)
        rationale.append("Accounting/FSA → foundations + statement intelligence.")

    if types.intersection({"valuation"}):
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
