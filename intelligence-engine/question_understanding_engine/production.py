"""Question Understanding Engine — production wiring."""

from __future__ import annotations

from typing import Any

from question_understanding_engine.resolver import understand_question
from question_understanding_engine.schema import (
    ARCHITECTURE_STATUS,
    LAYER,
    QUE_NAME,
    QUE_VERSION,
    TARGET_TAXONOMY_COUNT,
)
from question_understanding_engine.taxonomy import QUESTION_TAXONOMY
from question_understanding_engine.validation import validate_understanding


def apply_question_understanding_engine(out: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """First deterministic stage — every answer starts here."""
    if not isinstance(out, dict):
        out = {}

    query = str(kwargs.get("query") or out.get("query") or "")
    ticker = kwargs.get("ticker") or out.get("ticker")
    company = kwargs.get("company") or out.get("company")
    benchmark_id = kwargs.get("benchmark_id") or out.get("benchmark_id")

    # Enrich from benchmark if provided
    domain = kwargs.get("domain")
    if benchmark_id and not domain:
        try:
            from institutional_writing_benchmark.registry import get_benchmark

            bench = get_benchmark(benchmark_id)
            if bench:
                domain = bench.get("domain")
                ticker = ticker or bench.get("ticker")
                company = company or bench.get("company")
                if not query:
                    query = bench.get("question") or ""
        except ImportError:
            pass

    understanding = understand_question(
        query,
        ticker=ticker,
        company=company,
        benchmark_id=benchmark_id,
        domain=domain,
    )
    validation = validate_understanding(understanding)

    que = {
        "enabled": True,
        "version": QUE_VERSION,
        "engine": QUE_NAME,
        "layer": LAYER,
        "architecture_status": ARCHITECTURE_STATUS,
        "deterministic": True,
        "llm": False,
        "pipeline_position": "first",
        "pipeline": (
            "user_question → QUE → research_objective → research_workflow → "
            "knowledge_objects → evidence → response_planning → writing → editorial_review"
        ),
        "question_understanding": understanding,
        "validation": validation,
        "passed": validation["passed"],
    }

    out["question_understanding_engine"] = que
    out["question_understanding"] = understanding
    out["research_objective"] = understanding.get("research_objective")
    out["decision_type"] = understanding.get("decision_type")
    out["primary_investment_question"] = understanding.get("primary_investment_question")
    out["required_information"] = understanding.get("required_information")
    out["irrelevant_information"] = understanding.get("irrelevant_information")
    out["response_objective"] = understanding.get("response_objective")
    out["expected_deliverable"] = understanding.get("expected_deliverable")

    # Bridge to downstream intent_resolution consumers
    out["intent_resolution"] = {
        **(out.get("intent_resolution") or {}),
        "intent": understanding.get("decision_type"),
        "research_objective": understanding.get("research_objective"),
        "primary_investment_question": understanding.get("primary_investment_question"),
        "investor_meaning": understanding.get("investor_meaning"),
        "que_v1": True,
    }

    return out


def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "engine": QUE_NAME,
        "version": QUE_VERSION,
        "layer": LAYER,
        "taxonomy_entries": len(QUESTION_TAXONOMY),
        "taxonomy_target": TARGET_TAXONOMY_COUNT,
        "deterministic": True,
        "llm": False,
        "pipeline_position": "first",
    }
