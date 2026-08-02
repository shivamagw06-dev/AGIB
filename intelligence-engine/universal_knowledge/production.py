"""UKO production surface — the only knowledge entry Ask should call."""

from __future__ import annotations

from typing import Any, Optional

from universal_knowledge.gather import gather as _gather
from universal_knowledge.registry import registered_providers


UKO_VERSION = "uko-6.0"
PROGRAMME = "Phase 6.0 Universal Knowledge Orchestration"


def gather(question: str, *, ticker: Optional[str] = None, max_providers: int = 10) -> dict[str, Any]:
    return _gather(question, ticker=ticker, max_providers=max_providers)


def orchestrate(question: str, *, ticker: Optional[str] = None, max_providers: int = 10) -> dict[str, Any]:
    """Alias kept for API clarity — plan, gather, graph, coverage in one call."""
    return gather(question, ticker=ticker, max_providers=max_providers)


def for_ask(question: str, *, ticker: Optional[str] = None) -> Optional[dict[str, Any]]:
    """Compact Ask payload. Returns None when UKO has nothing answerable."""
    out = gather(question, ticker=ticker)
    if not out.get("answerable"):
        return None
    used = list((out.get("coverage") or {}).get("knowledge_sources_used") or [])
    if not used:
        return None
    return {
        "summary": out.get("summary") or "",
        "why": list(out.get("why") or []),
        "evidence": list(out.get("evidence") or []),
        "engine": "universal_knowledge",
        "version": UKO_VERSION,
        "programme": PROGRAMME,
        "key": ((out.get("company_intelligence") or {}).get("identity") or {}).get("ticker"),
        "company_name": ((out.get("company_intelligence") or {}).get("identity") or {}).get("name"),
        "coverage": out.get("coverage") or {},
        "company_intelligence": out.get("company_intelligence") or {},
        "concept_intelligence": out.get("concept_intelligence") or {},
        "diagnostics": out.get("diagnostics") or {},
        "providers_used": used,
        "evidence_graph": out.get("evidence_graph") or {},
        "attributions": out.get("attributions") or [],
    }


def for_ask_pipeline(question: str, *, ticker: Optional[str] = None) -> dict[str, Any]:
    """Full UKO bag for the desk path — always returns a dict, even when empty."""
    out = gather(question, ticker=ticker)
    graph = out.get("evidence_graph") or {}
    return {
        "ok": True,
        "engine": "universal_knowledge",
        "version": UKO_VERSION,
        "answerable": bool(out.get("answerable")),
        "summary": out.get("summary") or "",
        "why": list(out.get("why") or []),
        "evidence": list(out.get("evidence") or []),
        "facts": list(graph.get("facts") or []),
        "nodes": list(graph.get("nodes") or []),
        "by_role": graph.get("by_role") or {},
        "coverage": out.get("coverage") or {},
        "attributions": out.get("attributions") or [],
        "providers_used": list((out.get("coverage") or {}).get("knowledge_sources_used") or []),
        "providers_missing": list((out.get("coverage") or {}).get("providers_missing") or []),
        "latency_ms": out.get("latency_ms"),
        "diagnostics": out.get("diagnostics") or {},
        "company_intelligence": out.get("company_intelligence") or {},
        "concept_intelligence": out.get("concept_intelligence") or {},
    }


def health() -> dict[str, Any]:
    providers = registered_providers()
    ok = sum(1 for p in providers if p.get("health") == "ok")
    return {
        "ok": True,
        "engine": "universal_knowledge",
        "version": UKO_VERSION,
        "programme": PROGRAMME,
        "provider_count": len(providers),
        "healthy": ok,
        "providers": providers,
    }
