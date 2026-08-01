"""KUL production facade — single gateway for Ask and diagnostics."""

from __future__ import annotations

from typing import Any, Optional

from knowledge_unification.fusion import fuse
from knowledge_unification.knowledge_planner import build_knowledge_plan
from knowledge_unification.query_planner import plan_query
from knowledge_unification.ranking import rank_and_filter
from knowledge_unification.registry import get_registry
from knowledge_unification.schema import FusedEvidence, ProviderResult

KUL_VERSION = "1.0.0"
PROGRAMME = "Phase X — Knowledge Unification Layer"


def health() -> dict[str, Any]:
    reg = get_registry()
    dash = reg.dashboard()
    ok_n = sum(1 for p in dash["providers"] if p.get("health") == "ok")
    return {
        "ok": True,
        "programme": PROGRAMME,
        "version": KUL_VERSION,
        "providers_ok": ok_n,
        "providers_total": dash["provider_count"],
        "dashboard": dash,
        "fabricated": False,
    }


def plan_and_gather(
    question: str,
    *,
    ticker: Optional[str] = None,
    max_providers: int = 8,
) -> dict[str, Any]:
    """Full KUL path: query plan → knowledge plan → consult → rank → fuse."""
    query = plan_query(question)
    if ticker and not query.ticker_hint:
        query.ticker_hint = str(ticker).upper()
        if "company" not in query.question_types:
            query.question_types = ["company", *query.question_types]

    reg = get_registry()
    kplan = build_knowledge_plan(query, registry=reg)

    results: list[ProviderResult] = []
    for pid in kplan.provider_ids[:max_providers]:
        provider = reg.get(pid)
        if not provider:
            continue
        try:
            results.append(provider.consult(query))
        except Exception as exc:  # pragma: no cover — provider wrappers already catch
            from knowledge_unification.providers.base import error_result
            import time

            results.append(error_result(pid, time.perf_counter(), exc))

    ranked = rank_and_filter(results)
    fused: FusedEvidence = fuse(kplan, ranked, results)
    payload = fused.to_dict()
    payload.update(
        {
            "ok": bool(ranked),
            "version": KUL_VERSION,
            "programme": PROGRAMME,
            "engine": "knowledge_unification",
            "answerable": bool(ranked) and bool(fused.summary),
            "fabricated": False,
        }
    )
    return payload


def soft_slice_for_ask_agi(
    question: str = "",
    *_args: Any,
    ticker: Optional[str] = None,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Ask-facing soft slice — runs KUL and returns fusion + coverage."""
    return plan_and_gather(question, ticker=ticker)


_HARD_PROVIDERS = frozenset(
    {
        "capiq_ikt",
        "company_memory",
        "ikl",
        "knowledge_factory",
        "cgl",
        "financial_concepts",
        "financial_foundations",
        "financial_statement_intelligence",
    }
)


def answer_for_ask(question: str, *, ticker: Optional[str] = None) -> Optional[dict[str, Any]]:
    """Compact Ask short-circuit payload. Returns None when KUL has nothing."""
    out = plan_and_gather(question, ticker=ticker)
    if not out.get("answerable"):
        return None
    coverage = out.get("coverage") or {}
    sources = list(coverage.get("knowledge_sources_used") or [])
    # Require at least one real provider contribution.
    if not sources:
        return None
    # Soft-only academy/legacy hits must not short-circuit Ask — that blocks
    # CapIQ company_router fallback and unknown-entity / recommendation
    # policies for names KUL couldn't bind.
    if not any(s in _HARD_PROVIDERS for s in sources):
        return None
    return {
        "summary": out.get("summary") or "",
        "why": list(out.get("why") or []),
        "evidence": list(out.get("evidence") or []),
        "engine": "knowledge_unification",
        "key": ((out.get("company_intelligence") or {}).get("identity") or {}).get("ticker"),
        "company_name": ((out.get("company_intelligence") or {}).get("identity") or {}).get("name"),
        "coverage": coverage,
        "company_intelligence": out.get("company_intelligence") or {},
        "concept_intelligence": out.get("concept_intelligence") or {},
        "diagnostics": out.get("diagnostics") or {},
        "providers_used": coverage.get("knowledge_sources_used") or [],
    }
