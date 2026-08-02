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
    if "business_intelligence" not in ids and any(
        r.provider_id == "business_intelligence" and r.empty for r in results
    ):
        missing.append("Business Intelligence foundation returned empty")
    if "industry_intelligence" not in ids and any(
        r.provider_id == "industry_intelligence" and r.empty for r in results
    ):
        missing.append("Industry Intelligence DNA returned empty")
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
    elif "research" in qtypes or any(
        r.provider_id == "research_intelligence" and not r.empty for r in used
    ) or any(
        k in ((getattr(plan.query, "question", None) or "").lower())
        for k in (
            "annual report",
            "earnings call",
            "transcript",
            "research memory",
            "deep research",
            "cross-document",
            "guidance history",
            "research timeline",
            "what changed since",
            "five years of",
            "from the annual report",
        )
    ):
        # Phase 3.4.5 — Research Intelligence leads research-shaped answers.
        preferred_order = (
            "research_intelligence",
            "investment_intelligence",
            "business_intelligence",
            "industry_intelligence",
            "capiq_ikt",
            "company_memory",
            "ikl",
            "knowledge_factory",
            "cgl",
            "financial_concepts",
            "academy",
            "legacy_kip",
        )
    elif "portfolio" in qtypes or any(
        r.provider_id == "portfolio_intelligence" and not r.empty for r in used
    ) or any(
        k in ((getattr(plan.query, "question", None) or "").lower())
        for k in (
            "portfolio construction",
            "portfolio quality",
            "risk budget",
            "factor exposure",
            "position sizing",
            "agib core",
            "concentrated growth",
        )
    ):
        preferred_order = (
            "portfolio_intelligence",
            "investment_intelligence",
            "business_intelligence",
            "industry_intelligence",
            "capiq_ikt",
            "company_memory",
            "ikl",
            "knowledge_factory",
            "cgl",
            "financial_concepts",
            "academy",
            "legacy_kip",
        )
    elif "investment" in qtypes or any(
        r.provider_id == "investment_intelligence" and not r.empty for r in used
    ) or any(
        k in ((getattr(plan.query, "question", None) or "").lower())
        for k in (
            "investment thesis",
            "catalyst",
            "scenario analysis",
            "bull and bear",
            "investors monitor",
            "for an investor",
            "monitoring priorit",
            "evidence strength",
            "from an investment",
            "investment quality",
            "investment committee",
            "what drives valuation",
            "valuation driver",
            "quality perspective",
            "business quality",
            "unknowns remain",
            "capital allocation",
        )
    ):
        # Phase 3.2.5 — Investment Intelligence leads investment-shaped answers.
        preferred_order = (
            "investment_intelligence",
            "business_intelligence",
            "industry_intelligence",
            "capiq_ikt",
            "company_memory",
            "ikl",
            "knowledge_factory",
            "cgl",
            "financial_concepts",
            "academy",
            "legacy_kip",
        )
    elif qtypes.intersection(
        {"business_model", "moat", "unit_economics", "comparison", "business_risk", "industry"}
    ):
        # Company-less moat pedagogy ("Explain network effects") should lead with
        # financial_concepts, not a synthetic company moat card from BI.
        company_bound = bool(
            getattr(plan.query, "ticker_hint", None)
            or getattr(plan.query, "company_hint", None)
            or "comparison" in qtypes
            or "company" in qtypes
        )
        qtext = (getattr(plan.query, "question", None) or "").lower()
        concept_moat_pedagogy = (not company_bound) and any(
            k in qtext
            for k in (
                "network effect",
                "pricing power",
                "competitive moat",
                "what is a moat",
                "explain moat",
                "what creates pricing",
            )
        )
        industry_lead = (not company_bound) and (
            "industry" in qtypes
            or "unit_economics" in qtypes
            or "business_risk" in qtypes
            or any(
                k in qtext
                for k in (
                    "nim",
                    "casa",
                    "arpob",
                    "load factor",
                    "ev/sales",
                    "p/b",
                    "embedded value",
                    "porter",
                    "oligopol",
                    "spectrum",
                    "industry economics",
                )
            )
        )
        if concept_moat_pedagogy:
            preferred_order = (
                "financial_concepts",
                "business_intelligence",
                "industry_intelligence",
                "capiq_ikt",
                "academy",
                "legacy_kip",
            )
        elif industry_lead:
            # Phase 3.1.5 — Industry DNA leads pure industry pedagogy.
            preferred_order = (
                "industry_intelligence",
                "business_intelligence",
                "financial_concepts",
                "knowledge_factory",
                "capiq_ikt",
                "academy",
                "legacy_kip",
            )
        else:
            preferred_order = (
                "business_intelligence",
                "industry_intelligence",
                "investment_intelligence",
                "capiq_ikt",
                "company_memory",
                "ikl",
                "knowledge_factory",
                "cgl",
                "financial_concepts",
                "academy",
                "legacy_kip",
            )
    elif qtypes.intersection({"valuation"}) and not (
        getattr(plan.query, "ticker_hint", None) or getattr(plan.query, "company_hint", None)
    ):
        preferred_order = (
            "industry_intelligence",
            "financial_concepts",
            "business_intelligence",
            "academy",
            "legacy_kip",
        )
    elif qtypes.intersection({"company", "market"}):
        preferred_order = (
            "capiq_ikt",
            "company_memory",
            "business_intelligence",
            "industry_intelligence",
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
            "industry_intelligence",
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
    hard_ids = {
        "financial_foundations",
        "financial_statement_intelligence",
        "financial_concepts",
        "research_intelligence",
        "portfolio_intelligence",
        "investment_intelligence",
        "industry_intelligence",
        "business_intelligence",
        "capiq_ikt",
    }
    soft_ids = {"academy", "legacy_kip", "cgl", "ikl", "knowledge_factory", "company_memory"}
    has_hard = any(r.provider_id in hard_ids for r in used)

    def _append_why(line: str, *, max_len: int = 280) -> None:
        norm = " ".join((line or "").split()).strip()
        if not norm or norm in seen_why:
            return
        if len(norm) > max_len:
            norm = norm[: max_len - 1].rstrip() + "…"
        seen_why.add(norm)
        why.append(norm)

    # Prefer hard-provider why; soft academy/book lines only fill gaps and stay short.
    for r in used:
        if r.provider_id in soft_ids and has_hard:
            continue
        for line in r.why:
            _append_why(line)
            if len(why) >= 6:
                break
        if len(why) >= 6:
            break
    if len(why) < 3:
        for r in used:
            if r.provider_id not in soft_ids:
                continue
            for line in r.why[:1]:
                _append_why(line, max_len=160)
            if len(why) >= 4:
                break
    for r in used:
        for ev in r.evidence:
            if ev and ev not in evidence:
                evidence.append(ev)

    # Compact multi-source annotation — do not dump provider dumps into the lead.
    if len(used) >= 2:
        why.insert(0, "Sources fused: " + ", ".join(r.provider_id for r in used) + ".")
        why = why[:7]

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
