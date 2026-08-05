"""Institutional Writing Constitution v1.0 tests."""

from __future__ import annotations

from institutional_writing_constitution import (
    BENCHMARK_QUESTIONS,
    apply_institutional_writing_constitution,
    assemble_writing_sections,
    health,
    infer_answer_length,
    list_benchmark_questions,
    score_writing_pack,
    validate_writing_response,
)
from institutional_writing_constitution.schema import CONSTITUTION_VERSION, RESPONSE_HIERARCHY
from institutional_writing_constitution.evaluation import TARGET_BENCHMARK_COUNT


def test_health():
    h = health()
    assert h["status"] == "ok"
    assert h["version"] == CONSTITUTION_VERSION
    assert h["benchmark_questions"] == len(BENCHMARK_QUESTIONS)
    assert h["benchmark_target"] == TARGET_BENCHMARK_COUNT


def test_benchmark_registry_has_100_questions():
    assert len(BENCHMARK_QUESTIONS) == 100
    ids = [q["id"] for q in BENCHMARK_QUESTIONS]
    assert len(set(ids)) == 100
    assert ids[0] == "WES_001"
    assert ids[-1] == "WES_100"


def test_list_benchmark_questions_by_category():
    valuation = list_benchmark_questions(category="valuation")
    assert valuation
    assert all(q["category"] == "valuation" for q in valuation)


def test_infer_answer_length():
    assert infer_answer_length("Should I invest in TCS?") == "research_request"
    assert infer_answer_length("Deep dive on Asian Paints business model") == "deep_research"
    assert infer_answer_length("What is TCS revenue?") == "simple_question"


def test_assemble_writing_sections_hierarchy():
    pack = {
        "response_constitution": {"direct_answer": "TCS remains a quality compounder with resilient demand."},
        "institutional_assertions": [
            {"statement": "Client retention remains strong.", "status": "SUPPORTED", "confidence": 82},
            {"statement": "Pricing power is intact.", "status": "SUPPORTED", "confidence": 75},
            {"statement": "Cash generation supports dividends.", "status": "PARTIAL", "confidence": 60},
        ],
        "investment_thesis": {
            "current_thesis": "TCS franchise durability",
            "invalidation_conditions": ["Margin collapse", "Client churn spike"],
        },
    }
    sections = assemble_writing_sections(pack, company="Tata Consultancy Services", ticker="TCS")
    assert list(sections.keys()) == list(RESPONSE_HIERARCHY)
    assert sections["executive_summary"]["word_count"] <= 150
    assert len(sections["what_evidence_suggests"]["observations"]) >= 3
    assert all(o.startswith("Evidence suggests") for o in sections["what_evidence_suggests"]["observations"])
    assert len(sections["questions_before_you_decide"]["questions"]) >= 3
    assert sections["research_conclusion"]["never_recommends"] is True


def test_apply_institutional_writing_constitution_wiring():
    out = apply_institutional_writing_constitution(
        {"ticker": "TCS", "company": "Tata Consultancy Services", "query": "Should I invest in TCS?"},
        query="Should I invest in TCS?",
        ticker="TCS",
        company="Tata Consultancy Services",
    )
    iwc = out["institutional_writing_constitution"]
    assert iwc["enabled"] is True
    assert iwc["version"] == "1.0"
    assert iwc["never_recommends"] is True
    assert out["writing_structure"] == "institutional_writing_constitution_v1"
    assert out.get("executive_summary")
    assert out.get("questions_before_you_decide")
    validation = out["writing_constitution_validation"]
    assert validation["checks_total"] >= 6


def test_validate_forbidden_language():
    pack = apply_institutional_writing_constitution({"ticker": "TCS", "company": "TCS"})
    validation = validate_writing_response(pack)
    assert validation["passed"] is True
    assert validation["forbidden_hits"] == []


def test_score_writing_pack():
    pack = apply_institutional_writing_constitution({"ticker": "INFY", "company": "Infosys"})
    scores = score_writing_pack(pack)
    assert "scores" in scores
    assert scores["average"] >= 0
    assert "passed_release_gate" in scores
