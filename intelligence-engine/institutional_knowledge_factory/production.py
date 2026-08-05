"""Institutional Knowledge Factory v1.0 — public API."""

from __future__ import annotations

from typing import Any

from institutional_knowledge_factory.decision_memory import get_decision_memory, record_decision_memory
from institutional_knowledge_factory.dna_update import update_company_dna
from institutional_knowledge_factory.extract import extract_claims
from institutional_knowledge_factory.pipeline import process_evidence
from institutional_knowledge_factory.quality import compute_knowledge_quality
from institutional_knowledge_factory.review import institutional_review
from institutional_knowledge_factory.schema import IKF_VERSION, PROGRAMME
from institutional_knowledge_factory.sources import normalize_source
from institutional_knowledge_factory.thesis import evaluate_thesis
from institutional_knowledge_runtime.store import load_or_create_company


def apply_ikf(out: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Soft-wire IKF into answer pipeline — runs before IKR when evidence is present."""
    if not isinstance(out, dict):
        return out

    ticker = kwargs.get("ticker") or out.get("ticker")
    company = kwargs.get("company") or out.get("company")
    entity_id = str(ticker or company or "").strip()

    evidence_items = kwargs.get("evidence_items") or out.get("evidence_items") or []

    if not entity_id:
        out["institutional_knowledge_factory"] = {
            "enabled": False,
            "bypassed": True,
            "reason": "no_entity_id",
        }
        return out

    factory_result: dict[str, Any] | None = None
    if evidence_items:
        factory_result = process_evidence(
            entity_id,
            evidence_items,
            company=company,
            reason=str(kwargs.get("reason") or "Ask evidence ingestion"),
        )
        out["iko"] = factory_result.get("iko")
        out["evidence_graph_delta"] = factory_result.get("evidence_graph_delta")

    # Always compute quality/review from current IKO state
    iko = factory_result.get("iko") if factory_result else load_or_create_company(entity_id, company=company)
    quality = compute_knowledge_quality(iko)
    thesis = factory_result.get("thesis") if factory_result else evaluate_thesis(iko)
    review = institutional_review(
        iko,
        (factory_result or {}).get("changes"),
        quality,
    )

    result = {
        "enabled": True,
        "version": IKF_VERSION,
        "programme": PROGRAMME,
        "entity_id": entity_id.upper(),
        "entity_type": "company",
        "evidence_processed": bool(evidence_items),
        "sources_processed": (factory_result or {}).get("sources_processed", 0),
        "claims_updated": (factory_result or {}).get("claims_updated", 0),
        "thesis": thesis,
        "quality": quality,
        "review": review,
        "notifications": (factory_result or {}).get("notifications") or [],
        "pipeline_steps": (factory_result or {}).get("pipeline_steps"),
        "steps_completed": (factory_result or {}).get("steps_completed"),
        "deterministic": True,
        "llm": False,
    }

    out["institutional_knowledge_factory"] = result
    out["knowledge_quality"] = quality
    out["investment_thesis"] = thesis
    out["institutional_review"] = review
    out["research_notifications"] = result["notifications"]

    if factory_result:
        out["ikf_pack"] = factory_result

    return out


def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "programme": PROGRAMME,
        "version": IKF_VERSION,
        "deterministic": True,
        "llm": False,
        "writers_llm_allowed": False,
        "pipeline_steps": 11,
    }


__all__ = [
    "apply_ikf",
    "compute_knowledge_quality",
    "evaluate_thesis",
    "extract_claims",
    "get_decision_memory",
    "health",
    "institutional_review",
    "normalize_source",
    "process_evidence",
    "record_decision_memory",
    "update_company_dna",
]
