"""RQ2 Sprint 7 — Institutional Thesis Construction Engine regression tests."""

from thesis_engine.conviction_engine import thesis_state
from thesis_engine.production import (
    build_thesis,
    generate_for_question,
    quality_gates,
    soft_slice_for_ask_agi,
)
from thesis_engine.schema import (
    MIN_CATALYSTS,
    MIN_MAJOR_CONTRADICTIONS,
    MIN_SUPPORTING_PILLARS,
    PILLARS,
    THESIS_STATES,
)


def test_hdfc_thesis_construction():
    row = generate_for_question("Should I buy HDFC Bank?", {})
    assert row["ok"] is True
    t = row["thesis"]
    assert t["core_thesis"]["statement"]
    assert len(t["supporting_pillars"]) == len(PILLARS)
    assert t["status"] in THESIS_STATES
    assert t["conviction"]["overall"] is not None
    assert t["audit"]["passed"] is True
    counts = t["audit"]["counts"]
    assert counts["supporting_pillars"] >= MIN_SUPPORTING_PILLARS
    assert counts["major_contradictions"] >= MIN_MAJOR_CONTRADICTIONS
    assert counts["catalysts"] >= MIN_CATALYSTS
    assert counts["thesis_breaking_conditions"] >= 1


def test_output_contract_fields():
    row = generate_for_question("Is Nifty IT expensive versus history?", {})
    t = row["thesis"]
    for key in (
        "core_thesis",
        "supporting_pillars",
        "contradictions",
        "catalysts",
        "timeline",
        "confidence",
        "conviction",
        "missing_evidence",
        "status",
    ):
        assert key in t


def test_catalysts_have_polarity_timing_probability():
    row = generate_for_question("Should I buy HDFC Bank?", {})
    catalysts = row["thesis"]["catalysts"]
    polarities = {c["polarity"] for c in catalysts}
    assert polarities & {"Positive", "Negative"}
    for c in catalysts:
        assert c["expected_timing"] in ("Near Term", "Medium Term", "Long Term")
        assert 0 < float(c["probability"]) < 1
        assert c["evidence_required"]


def test_pillar_dependency_chain_present():
    row = generate_for_question("Should I buy HDFC Bank?", {})
    graph = row["thesis"]["dependency_graph"]
    edges = {(e["from"], e["to"]) for e in graph["edges"]}
    assert ("Business Quality", "Financial Quality") in edges
    assert ("Financial Quality", "Valuation") in edges
    assert ("Valuation", "Portfolio Fit") in edges


def test_weak_pillars_produce_weaker_thesis():
    weak_beliefs = [
        {
            "hypothesis_id": f"W{i}",
            "hypothesis": f"Weak hypothesis {i}",
            "type": t,
            "posterior_belief": 0.2,
            "confidence": 0.4,
            "supporting_evidence": [{"text": "thin support", "support_score": 40}],
            "contradicting_evidence": [
                {"text": "strong challenge", "contradiction_score": 88},
                {"text": "second challenge", "contradiction_score": 80},
            ],
            "missing_evidence": ["large gap"],
            "uncertainty": {"known_unknowns": ["unknown"], "missing_evidence": ["large gap"]},
        }
        for i, t in enumerate(["Business", "Financial", "Valuation", "Macro", "Portfolio"])
    ]
    thesis = build_thesis(weak_beliefs, question="Should I buy X?", payload={})
    assert thesis["conviction"]["overall"] < 0.55
    assert thesis["status"] in ("Emerging", "Developing", "Weakening", "Broken", "Rejected")


def test_thesis_state_bands():
    assert thesis_state(0.8, supported_pillars=6, major_contradictions=1) == "Very Strong"
    assert thesis_state(0.2, supported_pillars=1, major_contradictions=5) == "Rejected"


def test_soft_slice_ask_agi():
    wrap = soft_slice_for_ask_agi("Should I buy HDFC Bank?", {})
    body = wrap["thesis_engine"]
    assert body["enabled"] is True
    assert body["not_a_top_level_intelligence_layer"] is True
    assert body["executes_after"] == "Bayesian Belief & Confidence Engine"
    assert body["executes_before"] == "Investment Committee"
    assert body["core_thesis"]["statement"]
    assert body["committee_handoff"]["debate_this"]


def test_quality_gates_meet_sprint_bar():
    gates = quality_gates()
    assert gates["total"] >= 2000
    assert gates["thesis_construction"] >= 1.0
    assert gates["logical_consistency"] >= 1.0
    assert gates["pillar_completeness"] >= 1.0
    assert gates["contradiction_handling"] >= 1.0
    assert gates["catalyst_quality"] >= 1.0
    assert gates["conviction_calibration"] >= 1.0
    assert gates["avg_build_ms"] < 60
    assert len(gates["state_counts"]) >= 2
    assert gates["ok"] is True
