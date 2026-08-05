"""Question Understanding Engine v1.0 tests."""

from __future__ import annotations

from question_understanding_engine import (
    QUESTION_TAXONOMY,
    TARGET_TAXONOMY_COUNT,
    apply_question_understanding_engine,
    health,
    understand_question,
    validate_understanding,
)
from question_understanding_engine.schema import DECISION_TYPES


def test_health():
    h = health()
    assert h["status"] == "ok"
    assert h["pipeline_position"] == "first"
    assert h["taxonomy_entries"] == TARGET_TAXONOMY_COUNT


def test_taxonomy_has_500_labeled_questions():
    assert len(QUESTION_TAXONOMY) == 500
    sample = QUESTION_TAXONOMY[0]
    for field in ("literal_question", "decision_type", "research_objective", "expected_deliverable"):
        assert sample.get(field)


def test_acceptance_should_i_buy_tcs():
    qu = understand_question("Should I buy TCS?", ticker="TCS")
    assert qu["decision_type"] == "Capital Allocation"
    assert "allocate capital" in qu["investor_meaning"].lower()
    assert "justifies risk" in qu["research_objective"].lower() or "return" in qu["research_objective"].lower()
    v = validate_understanding(qu)
    assert v["passed"] is True


def test_acceptance_does_tcs_deserve_research():
    qu = understand_question("Does TCS deserve research?", ticker="TCS")
    assert qu["decision_type"] == "Research Priority"
    assert validate_understanding(qu)["passed"] is True


def test_acceptance_compare_infosys_tcs():
    qu = understand_question("Compare Infosys and TCS.")
    assert qu["decision_type"] == "Peer Selection"
    assert "differences" in qu["investor_meaning"].lower() or "one company" in qu["investor_meaning"].lower()


def test_acceptance_why_titan_expensive():
    qu = understand_question("Why is Titan expensive?")
    assert qu["decision_type"] == "Valuation Assessment"
    assert "expectations" in qu["investor_meaning"].lower()


def test_understanding_object_has_all_fields():
    qu = understand_question("Should I buy TCS?", ticker="TCS")
    for field in (
        "literal_question",
        "investor_meaning",
        "decision_type",
        "research_objective",
        "primary_investment_question",
        "required_information",
        "irrelevant_information",
        "response_objective",
        "expected_deliverable",
        "confidence",
    ):
        assert field in qu
    assert qu["decision_type"] in DECISION_TYPES


def test_apply_wires_first_in_pipeline():
    out = apply_question_understanding_engine(
        {},
        query="Does Tata Consultancy Services deserve research today?",
        ticker="TCS",
        benchmark_id="IIC_0001",
    )
    que = out["question_understanding_engine"]
    assert que["enabled"] is True
    assert que["pipeline_position"] == "first"
    assert out["research_objective"]
    assert out["intent_resolution"]["que_v1"] is True
    assert out["question_understanding"]["decision_type"] == "Research Priority"


def test_quality_gates_fail_on_empty():
    v = validate_understanding({})
    assert v["passed"] is False
    assert v["missing_fields"]
