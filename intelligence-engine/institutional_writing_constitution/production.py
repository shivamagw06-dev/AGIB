"""Apply Institutional Writing Constitution v1.0 — IRE communication layer."""

from __future__ import annotations

from typing import Any

from institutional_writing_constitution.assembler import assemble_writing_sections, infer_answer_length
from institutional_writing_constitution.evaluation import evaluation_rubric
from institutional_writing_constitution.schema import (
    CONSTITUTION_VERSION,
    LAYER,
    PROGRAMME,
    RESPONSE_HIERARCHY,
    WRITING_PHILOSOPHY,
)
from institutional_writing_constitution.validation import validate_writing_response


def apply_institutional_writing_constitution(out: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Enforce institutional writing hierarchy on every user-facing response."""
    if not isinstance(out, dict):
        return out

    query = str(kwargs.get("query") or out.get("query") or "")
    ticker = kwargs.get("ticker") or out.get("ticker")
    company = kwargs.get("company") or out.get("company") or ticker or "This company"

    sections = assemble_writing_sections(out, company=str(company), ticker=ticker)
    length_class = infer_answer_length(query)

    constitution = {
        "enabled": True,
        "version": CONSTITUTION_VERSION,
        "programme": PROGRAMME,
        "layer": LAYER,
        "purpose": "Defines how AGI explains — not how AGI thinks",
        "sections": sections,
        "section_order": list(RESPONSE_HIERARCHY),
        "writing_philosophy": list(WRITING_PHILOSOPHY),
        "answer_length_class": length_class,
        "primary_objective": "Improve the user's investment understanding",
        "never_recommends": True,
        "user_decides": True,
        "evaluation_rubric": evaluation_rubric(),
    }

    out["institutional_writing_constitution"] = constitution
    out["writing_structure"] = "institutional_writing_constitution_v1"
    out["writing_sections"] = sections
    out["executive_summary"] = sections.get("executive_summary")
    out["investment_meaning"] = sections.get("investment_meaning")
    out["what_evidence_suggests"] = sections.get("what_evidence_suggests")
    out["what_could_change_view"] = sections.get("what_could_change_view")

    # Align with AIC outputs where present
    if sections.get("research_conclusion"):
        out["research_conclusion"] = sections["research_conclusion"]
    qsec = sections.get("questions_before_you_decide") or {}
    if qsec.get("questions"):
        out["questions_before_you_decide"] = qsec["questions"]

    out["writing_constitution_validation"] = validate_writing_response(out)
    return out


def health() -> dict[str, Any]:
    from institutional_writing_constitution.evaluation import BENCHMARK_QUESTIONS, TARGET_BENCHMARK_COUNT

    return {
        "status": "ok",
        "programme": PROGRAMME,
        "version": CONSTITUTION_VERSION,
        "layer": LAYER,
        "section_count": len(RESPONSE_HIERARCHY),
        "benchmark_questions": len(BENCHMARK_QUESTIONS),
        "benchmark_target": TARGET_BENCHMARK_COUNT,
        "deterministic": True,
        "llm": False,
    }
