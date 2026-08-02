"""Universal gather — plan once, consult every selected provider, build the graph.

This is the only retrieval entry point Ask is allowed to use for institutional
knowledge. Both the KUL short-circuit and the full desk path call here.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from universal_knowledge.coverage import measure_coverage
from universal_knowledge.evidence_graph import build_evidence_graph
from universal_knowledge.planner import plan as plan_question
from universal_knowledge.registry import kul_registry


def gather(
    question: str,
    *,
    ticker: Optional[str] = None,
    max_providers: int = 10,
) -> dict[str, Any]:
    """Plan → consult → evidence graph → coverage. Never short-circuits by route."""
    t0 = time.perf_counter()

    # Entity Intelligence remains authoritative for clarification / refusal.
    ei_contract: dict[str, Any] = {}
    try:
        from entity_intelligence.production import analyse as ei_analyse
        from entity_intelligence.production import should_short_circuit

        ei_contract = ei_analyse(question) or {}
        if should_short_circuit(ei_contract):
            summary = str(ei_contract.get("summary") or "").strip()
            return {
                "ok": True,
                "version": "uko-6.0",
                "engine": "universal_knowledge",
                "programme": "Phase 6.0 Universal Knowledge Orchestration",
                "answerable": bool(summary),
                "fabricated": False,
                "summary": summary,
                "why": list(ei_contract.get("why") or []),
                "evidence": [],
                "company_intelligence": {
                    "identity": {
                        "ticker": None,
                        "name": ei_contract.get("canonical_name"),
                    }
                },
                "concept_intelligence": {},
                "evidence_graph": {"ok": True, "nodes": [], "by_role": {}, "facts": [], "evidence": [], "why": [], "attributions": [], "node_count": 0, "fact_count": 0, "evidence_count": 0},
                "coverage": {
                    "providers_selected": [],
                    "providers_expected": [],
                    "providers_used": ["entity_intelligence"],
                    "providers_available": [],
                    "providers_missing": [],
                    "providers_unused": [],
                    "providers_surprise": [],
                    "coverage_pct": 0.0,
                    "expected_hit": 0,
                    "expected_total": 0,
                    "average_confidence": None,
                    "complete": False,
                    "knowledge_sources_used": ["entity_intelligence"],
                },
                "attributions": [],
                "provider_results": [],
                "diagnostics": {
                    "planner": {"family": "entity_gate", "selected": [], "expected": [], "ticker": None},
                    "errors": [],
                    "latency_ms": round((time.perf_counter() - t0) * 1000.0, 1),
                    "entity_intelligence": {
                        "state": ei_contract.get("state"),
                        "confidence": ei_contract.get("confidence"),
                    },
                },
                "latency_ms": round((time.perf_counter() - t0) * 1000.0, 1),
            }
    except Exception:
        ei_contract = {}

    # Prefer an explicit caller ticker, then a verified Entity Intelligence bind.
    # The query planner deliberately drops CapIQ binds on industry-pedagogy
    # phrasing ("…compared with its industry"); UKO must not lose the company.
    bound = ticker
    if not bound and ei_contract.get("allow_planner") and ei_contract.get("ticker"):
        bound = str(ei_contract.get("ticker") or "").upper() or None
    if bound:
        try:
            from entity_intelligence.production import validate_bound_ticker

            if ei_contract and not validate_bound_ticker(ei_contract, bound):
                bound = None
        except Exception:
            pass

    execution = plan_question(question, ticker=bound, max_providers=max_providers)
    selected = list(execution["selected_providers"])
    expected = list(execution["expected_providers"])
    knowledge_plan = execution["knowledge_plan"]
    query = execution["query_plan"]

    registry = kul_registry()
    results = []
    used: list[str] = []
    confidences: list[float] = []
    errors: list[dict[str, str]] = []

    for pid in selected:
        provider = registry.get(pid)
        if provider is None:
            errors.append({"provider": pid, "error": "unregistered"})
            continue
        try:
            result = provider.consult(query)
            results.append(result)
            if bool(getattr(result, "ok", False)) and not bool(getattr(result, "empty", True)):
                used.append(pid)
                conf = getattr(result, "confidence", None)
                if isinstance(conf, (int, float)):
                    confidences.append(float(conf))
        except Exception as exc:
            errors.append({"provider": pid, "error": f"{type(exc).__name__}: {exc}"})

    bound_ticker = execution.get("ticker") or getattr(query, "ticker_hint", None)
    graph = build_evidence_graph(results, ticker=bound_ticker, family=execution["family"])
    coverage = measure_coverage(
        selected=selected,
        expected=expected,
        used=used,
        available=[p.spec.id for p in registry.all()],
        confidences=confidences,
    )

    fused_dict: dict[str, Any] = {}
    try:
        from knowledge_unification.fusion import fuse
        from knowledge_unification.ranking import rank_and_filter

        ranked = rank_and_filter(results)
        fused = fuse(knowledge_plan, ranked, results)
        fused_dict = fused.to_dict() if hasattr(fused, "to_dict") else dict(fused or {})
    except Exception as exc:
        fused_dict = {"summary": "", "why": [], "error": f"fusion_failed:{type(exc).__name__}:{exc}"}

    summary = str(fused_dict.get("summary") or "").strip()
    if not summary and graph["nodes"]:
        summary = graph["nodes"][0].get("summary") or ""

    why = list(fused_dict.get("why") or []) or list(graph.get("why") or [])
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 1)
    answerable = bool(summary) and bool(used)

    return {
        "ok": True,
        "version": "uko-6.0",
        "engine": "universal_knowledge",
        "programme": "Phase 6.0 Universal Knowledge Orchestration",
        "answerable": answerable,
        "fabricated": False,
        "summary": summary,
        "why": why,
        "evidence": list(fused_dict.get("evidence") or graph.get("evidence") or []),
        "company_intelligence": fused_dict.get("company_intelligence") or {},
        "concept_intelligence": fused_dict.get("concept_intelligence") or {},
        "evidence_graph": graph,
        "coverage": {
            **coverage,
            "knowledge_sources_used": used,
        },
        "attributions": graph.get("attributions") or [],
        "provider_results": [
            {
                "provider_id": getattr(r, "provider_id", None),
                "ok": getattr(r, "ok", False),
                "empty": getattr(r, "empty", True),
                "confidence": getattr(r, "confidence", None),
                "summary": (getattr(r, "summary", None) or "")[:240],
            }
            for r in results
        ],
        "diagnostics": {
            "planner": {
                "family": execution["family"],
                "selected": selected,
                "expected": expected,
                "ticker": bound_ticker,
            },
            "errors": errors,
            "latency_ms": elapsed_ms,
            "fusion_engine": "knowledge_unification.fusion",
            "entity_intelligence": {
                "state": ei_contract.get("state") if ei_contract else None,
            },
        },
        "latency_ms": elapsed_ms,
    }
