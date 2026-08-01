"""Module 5 + 11 — Evidence Fusion and Unified Coverage Object."""

from __future__ import annotations

from typing import Any

from knowledge_unification.company_object import build_company_intelligence
from knowledge_unification.schema import (
    CoverageObject,
    FusedEvidence,
    KnowledgePlan,
    ProviderResult,
)


def _concept_intelligence(
    results: list[ProviderResult],
    *,
    question_types: list[str] | None = None,
) -> dict[str, Any]:
    qtypes = set(question_types or [])
    if qtypes.intersection({"accounting", "financial_statement"}):
        order = (
            "financial_statement_intelligence",
            "financial_foundations",
            "financial_concepts",
        )
    else:
        order = (
            "financial_concepts",
            "financial_foundations",
            "financial_statement_intelligence",
        )
    by_id = {r.provider_id: r for r in results if not r.empty}
    for pid in order:
        r = by_id.get(pid)
        if not r:
            continue
        key = next(
            (f.get("value") for f in r.facts if f.get("field") in {"concept_key", "key"}),
            None,
        )
        return {
            "provider": r.provider_id,
            "summary": r.summary,
            "why": r.why,
            "key": key,
            "raw_keys": list((r.raw or {}).keys())[:20],
        }
    return {}


def _coverage(results: list[ProviderResult], used: list[ProviderResult]) -> CoverageObject:
    sources = [r.provider_id for r in used]
    conf = max((r.confidence for r in used), default=0.0)
    if len(used) >= 3 and conf >= 0.75:
        level, strength = "high", "strong"
    elif len(used) >= 1 and conf >= 0.6:
        level, strength = "medium", "moderate"
    elif used:
        level, strength = "low", "weak"
    else:
        level, strength = "none", "none"

    missing = []
    ids = set(sources)
    if "capiq_ikt" not in ids and any(r.provider_id == "capiq_ikt" and r.empty for r in results):
        missing.append("CapIQ company profile unavailable for this entity")
    if "company_memory" not in ids and any(r.provider_id == "company_memory" for r in results):
        missing.append("Company memory not populated")
    if "ikl" not in ids and any(r.provider_id == "ikl" for r in results):
        missing.append("IKL memory miss")
    if "cgl" not in ids and any(r.provider_id == "cgl" for r in results):
        missing.append("No Continuous Gather extracts matched")

    return CoverageObject(
        coverage_level=level,
        knowledge_sources_used=sources,
        confidence=round(conf * 100.0, 1),
        evidence_strength=strength,
        missing_information=missing,
    )


def fuse(
    plan: KnowledgePlan,
    ranked: list[ProviderResult],
    all_results: list[ProviderResult],
) -> FusedEvidence:
    used = ranked
    company = build_company_intelligence(plan.query, used)
    concept = _concept_intelligence(used, question_types=plan.query.question_types)
    coverage = _coverage(all_results, used)

    # Lead summary: company → FSA/foundations → concepts → soft sources.
    # Prefer statement/foundations over concepts when both contributed so
    # interpretive accounting answers aren't overwritten by a concept card.
    qtypes = set(plan.query.question_types or [])
    if qtypes.intersection({"financial_statement", "accounting"}):
        preferred_order = (
            "financial_statement_intelligence",
            "financial_foundations",
            "financial_concepts",
            "capiq_ikt",
            "academy",
            "legacy_kip",
        )
    elif qtypes.intersection({"company", "business_model", "industry", "market"}):
        preferred_order = (
            "capiq_ikt",
            "company_memory",
            "ikl",
            "knowledge_factory",
            "cgl",
            "financial_concepts",
            "academy",
            "legacy_kip",
        )
    else:
        preferred_order = (
            "financial_concepts",
            "financial_foundations",
            "financial_statement_intelligence",
            "capiq_ikt",
            "academy",
            "knowledge_factory",
            "company_memory",
            "ikl",
            "cgl",
            "legacy_kip",
        )
    summary = ""
    for preferred in preferred_order:
        for r in used:
            if r.provider_id == preferred and r.summary:
                summary = r.summary
                break
        if summary:
            break
    if not summary and used:
        summary = used[0].summary

    why: list[str] = []
    evidence: list[dict[str, Any]] = []
    seen_why: set[str] = set()
    for r in used:
        for line in r.why:
            norm = line.strip()
            if not norm or norm in seen_why:
                continue
            seen_why.add(norm)
            why.append(norm)
        for ev in r.evidence:
            if ev and ev not in evidence:
                evidence.append(ev)

    # Annotate multi-source fusion in why when more than one provider contributed.
    if len(used) >= 2:
        why.insert(0, "Sources fused: " + ", ".join(r.provider_id for r in used) + ".")

    diagnostics = {
        "plan": plan.to_dict(),
        "providers_consulted": [r.provider_id for r in all_results],
        "providers_used": [r.provider_id for r in used],
        "providers_rejected": [
            {"id": r.provider_id, "reason": r.rejected_reason or ("error" if not r.ok else "unused")}
            for r in all_results
            if r.empty or not r.ok or r.rejected_reason
        ],
        "provider_latency_ms": {r.provider_id: r.latency_ms for r in all_results},
        "provider_contribution": {
            r.provider_id: {
                "confidence": r.confidence,
                "fact_count": len(r.facts),
                "why_count": len(r.why),
            }
            for r in used
        },
    }

    return FusedEvidence(
        summary=summary or "Insufficient unified knowledge for this question.",
        why=why,
        evidence=evidence,
        company_intelligence=company,
        concept_intelligence=concept,
        coverage=coverage,
        provider_results=all_results,
        diagnostics=diagnostics,
    )
