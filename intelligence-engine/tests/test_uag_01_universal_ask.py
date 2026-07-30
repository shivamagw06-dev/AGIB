"""UAG-01 — Universal Ask AGI Orchestrator tests."""

from __future__ import annotations

from institutional_orchestrator.intent_classifier import classify_intent, extract_entities
from institutional_orchestrator.object_registry import catalog, get, match_routes, register
from institutional_orchestrator.planner import plan_query
from institutional_orchestrator.production import (
    ask,
    get_query,
    health,
    reset_for_tests,
    soft_slice_mission_control,
)
from institutional_orchestrator.router import resolve_provider, route_plan
from institutional_orchestrator.schema import UAG_WORKSTREAM_ID
from institutional_orchestrator.validator import validate_response
from institutional_orchestrator.response_builder import build_response
from institutional_orchestrator.retrieval import execute_plan
from dataclasses import replace


def setup_function():
    reset_for_tests()


def test_health_and_registry():
    h = health()
    assert h["workstream_id"] == UAG_WORKSTREAM_ID
    assert h["stateless"] is True
    assert h["generates_recommendations"] is False
    assert h["owns_business_state"] is False
    types = {r["object_type"] for r in h["registered_objects"]}
    assert "PortfolioRisk" in types
    assert "CommitteeResolution" in types
    assert "PolicyAssessment" in types


def test_intent_committee_and_policy():
    assert classify_intent("Why was this deferred by the committee?")["intent"] == "Committee"
    assert classify_intent("Which policy violations are active?")["intent"] == "Policy"
    assert classify_intent("What is portfolio concentration risk?")["intent"] == "Risk"


def test_entity_extraction():
    ents = extract_entities("Why reduce HDFCBANK in the book?")
    assert "HDFCBANK" in ents


def test_registry_route_discovery():
    hits = match_routes("Show committee deferred decisions and policy violations")
    types = {h.object_type for h in hits}
    assert "CommitteeResolution" in types
    assert "PolicyAssessment" in types


def test_planner_committee_lineage_order():
    q = plan_query(
        query_id="t1",
        question="Why did the committee reduce HDFCBANK?",
        intent="Committee",
        entities=("HDFCBANK",),
    )
    assert q.execution_plan
    types = [s.object_type for s in q.execution_plan]
    assert types[0] == "CommitteeResolution"
    assert "PortfolioDecision" in types
    assert "PolicyAssessment" in types
    assert "PortfolioRisk" in types


def test_router_resolves_registered_providers():
    q = plan_query(
        query_id="t2",
        question="Which holdings should I reduce?",
        intent="Portfolio Analysis",
        entities=(),
    )
    routed = route_plan(q)
    assert routed
    assert all("provider" in r for r in routed)
    assert resolve_provider("PortfolioDecision")["ok"] is True


def test_response_builder_no_recommendation_generation():
    q = plan_query(
        query_id="t3",
        question="Why reduce HDFCBANK?",
        intent="Committee",
        entities=("HDFCBANK",),
    )
    steps, payloads = execute_plan(q)
    resp = build_response(q, steps=steps, payloads=payloads, generated_at="now")
    assert resp.generates_recommendations is False
    assert resp.direct_answer
    assert "orchestrator" in " ".join(resp.warnings).lower() or resp.llm is False


def test_validator_requires_plan_and_objects():
    q = plan_query(
        query_id="t4",
        question="Portfolio risk overview",
        intent="Risk",
        entities=(),
    )
    steps, payloads = execute_plan(q)
    resp = build_response(q, steps=steps, payloads=payloads)
    # missing diagnostics → fail
    v = validate_response(q, resp)
    assert not v.ok
    assert "missing diagnostics" in v.errors

    resp2 = replace(resp, diagnostics={"ok": True})
    v2 = validate_response(q, resp2)
    assert v2.ok


def test_ask_portfolio_integration():
    result = ask({"question": "Which holdings should I reduce?", "portfolio_id": "default"})
    assert result["ok"] is True
    assert result["generates_recommendations"] is False
    assert result["owns_business_state"] is False
    r = result["response"]
    assert r["intent"] in {"Portfolio Analysis", "Risk", "Policy", "Committee"}
    assert r["execution_plan"]
    assert r["objects_consulted"]
    assert r["evidence_lineage"]
    cached = get_query(r["query_id"])
    assert cached["ok"] is True


def test_ask_committee_integration():
    result = ask({"question": "Why did the committee reduce HDFCBANK?", "portfolio_id": "default"})
    assert result["ok"] is True
    r = result["response"]
    assert r["intent"] == "Committee"
    consulted = set(r["objects_consulted"])
    # At least committee stack objects when providers available
    assert "CommitteeResolution" in consulted or "PortfolioDecision" in consulted
    board = soft_slice_mission_control()
    assert board["orchestration_center"] is True


def test_ask_cross_object_policy_observations():
    result = ask(
        {
            "question": "Which policy violations came from today's observations?",
            "portfolio_id": "default",
        }
    )
    assert result["ok"] is True
    types = [s["object_type"] for s in result["query"]["execution_plan"]]
    assert "PolicyAssessment" in types
    assert "Observation" in types or "CommitteeResolution" in types


def test_custom_registration():
    register(
        "CustomProbe",
        routes=["custom probe xyz"],
        provider="test",
        planner="company",
        retrieve=lambda ctx: {"ok": True, "object_type": "CustomProbe", "payload": {"hit": True}},
    )
    assert get("CustomProbe") is not None
    assert any(r["object_type"] == "CustomProbe" for r in catalog())
    hits = match_routes("run custom probe xyz now")
    assert any(h.object_type == "CustomProbe" for h in hits)
