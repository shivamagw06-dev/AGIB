"""Editorial Excellence Program v1.0 tests."""

from __future__ import annotations

from editorial_excellence import (
    apply_editorial_excellence,
    health,
    list_rules,
    quality_gates,
    rule_count,
    score_editorial,
)
from editorial_excellence.schema import PROGRAM_VERSION, TARGET_BENCHMARK_COUNT
from editorial_excellence.reports import monthly_report, weekly_review
from institutional_writing_benchmark import (
    get_benchmark,
    get_playbook,
    hall_of_fame_ids,
    list_benchmarks,
    list_playbooks,
    load_hall_of_fame,
    phase2_expansion_plan,
)
from institutional_writing_benchmark.registry import BENCHMARK_QUESTIONS
from institutional_writing_benchmark.schema import PLAYBOOK_COUNT, QUESTIONS_PER_PLAYBOOK
from institutional_writing_constitution import apply_institutional_writing_constitution


def test_health():
    h = health()
    assert h["status"] == "ok"
    assert h["version"] == PROGRAM_VERSION
    assert h["benchmark_questions"] == TARGET_BENCHMARK_COUNT
    assert h["editorial_rules"] == rule_count()


def test_benchmark_curriculum_has_100_lifecycle_questions():
    assert len(BENCHMARK_QUESTIONS) == 100
    ids = [q["id"] for q in BENCHMARK_QUESTIONS]
    assert len(set(ids)) == 100
    assert ids[0] == "IWB_001"
    assert ids[-1] == "IWB_100"
    assert all(q["ticker"] == "TCS" for q in BENCHMARK_QUESTIONS)


def test_twenty_playbooks_five_questions_each():
    playbooks = list_playbooks()
    assert len(playbooks) == PLAYBOOK_COUNT
    assert PLAYBOOK_COUNT == 20
    assert QUESTIONS_PER_PLAYBOOK == 5
    for pb in playbooks:
        assert len(pb["question_ids"]) == 5


def test_benchmark_categories():
    valuation = list_benchmarks(playbook="valuation", limit=10)
    assert len(valuation) == 5
    assert all(q["playbook"] == "valuation" for q in valuation)
    assert get_benchmark("IWB_001")["question"] == "Should I invest in TCS today?"
    debate = get_playbook("investment_debate")
    assert len(debate["questions"]) == 5


def test_phase2_expansion_plan():
    plan = phase2_expansion_plan()
    assert plan["target_total"] == 1000
    assert len(plan["companies_pending"]) == 10


def test_hall_of_fame_ids():
    ids = hall_of_fame_ids()
    assert len(ids) == 100
    assert ids[0] == "IWB_001"
    assert ids[-1] == "IWB_100"


def test_editorial_rules_append_only():
    rules = list_rules()
    assert len(rules) >= 15
    assert rules[0]["id"] == "ER-001"
    assert any(r["id"] == "ER-034" for r in rules)


def test_score_editorial_on_iwc_pack():
    pack = apply_institutional_writing_constitution(
        {"ticker": "TCS", "company": "Tata Consultancy Services", "query": "Should I invest in TCS today?"},
        query="Should I invest in TCS today?",
    )
    editorial = score_editorial(pack)
    assert "overall_editorial_score" in editorial
    assert editorial["forward_without_editing"] in ("YES", "MINOR_EDITS", "MAJOR_EDITS", "REWRITE")
    assert len(editorial["scorecard"]) >= 11


def test_quality_gates():
    pack = apply_institutional_writing_constitution({"ticker": "INFY", "company": "Infosys"})
    gates = quality_gates(pack)
    assert "checks" in gates
    assert gates["checks"]["executive_summary_exists"] is True
    assert gates["checks"]["questions_before_you_decide_included"] is True


def test_apply_editorial_excellence_wiring():
    base = apply_institutional_writing_constitution(
        {"ticker": "TCS", "company": "TCS", "query": "Should I invest in TCS today?"},
        query="Should I invest in TCS today?",
    )
    out = apply_editorial_excellence(base, query="Should I invest in TCS today?", benchmark_id="IWB_001")
    ee = out["editorial_excellence"]
    assert ee["enabled"] is True
    assert ee["version"] == "1.0"
    assert ee["constitution_stable"] is True
    assert out.get("editorial_score") is not None
    assert out.get("editorial_review_workspace")
    assert out["editorial_excellence"]["hall_of_fame_update"]["benchmark_id"] == "IWB_001"


def test_hall_of_fame_keeps_better_version():
    from institutional_writing_benchmark.hall_of_fame import compare_and_maybe_update

    bench_id = "IWB_HOF_TEST"
    compare_and_maybe_update(
        bench_id,
        question="Test question",
        response_text="The central investment debate centers on durability.",
        editorial_score=85.0,
        forward_rating="MINOR_EDITS",
    )
    result = compare_and_maybe_update(
        bench_id,
        question="Test question",
        response_text="Improved response with because and depends on clarity.",
        editorial_score=92.0,
        forward_rating="YES",
    )
    assert result["improved"] is True
    assert result["kept"] is True
    hof = load_hall_of_fame()
    assert hof["entries"][bench_id]["editorial_score"] == 92.0


def test_weekly_and_monthly_reports():
    sample = [
        {"overall_editorial_score": 88, "forward_without_editing": "MINOR_EDITS", "writing_problems": ["weak_conclusion"]},
        {"overall_editorial_score": 95, "forward_without_editing": "YES", "writing_problems": []},
    ]
    weekly = weekly_review(sample)
    assert weekly["sample_size"] == 2
    assert "average_editorial_score" in weekly
    monthly = monthly_report(sample)
    assert monthly["forward_without_editing_yes_pct"] == 50.0
