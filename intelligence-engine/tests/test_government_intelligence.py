"""AGIB v2.0 Sprint 3 — Institutional Government & Regulatory Intelligence acceptance.

Soft Knowledge Factory enrichment only.
Never political opinion. Never forecast policy. Never fabricate.
Company Intelligence / Corporate Events / Decision Quality / Phases 1–7 frozen.
"""

from __future__ import annotations

from knowledge_factory.government_intelligence import store as igri_store
from knowledge_factory.government_intelligence.objects.compile import compile_government_intelligence
from knowledge_factory.government_intelligence.pipeline import run_government_intelligence_pipeline
from knowledge_factory.government_intelligence.production import (
    dashboard,
    domain_view,
    get_policy,
    health,
    list_policies,
    search,
    timeline,
)
from knowledge_factory.government_intelligence.schema import (
    FREEZE_LOCKS,
    IGRI_VERSION,
    INSTITUTIONAL_COMPLETE_LEVEL,
)
from knowledge_factory.government_intelligence.timeline.build import replay_as_of
from knowledge_factory.government_intelligence.validators.gates import (
    detect_duplicate_policies,
    validate_pack,
    validate_policy,
)


def setup_function() -> None:
    igri_store.reset()


def test_freeze_locks_and_health():
    h = health()
    assert h["version"] == IGRI_VERSION
    assert h["not_a_reasoning_engine"] is True
    assert h["never_political_opinion"] is True
    assert h["never_forecast_policy"] is True
    assert h["freeze_locks"]["phases_1_7"] is True
    assert h["freeze_locks"]["company_intelligence_architecture"] is True
    assert h["freeze_locks"]["corporate_event_intelligence_architecture"] is True
    assert h["freeze_locks"]["decision_quality_architecture"] is True
    assert FREEZE_LOCKS["never_fabricate"] is True


def test_registry_and_modules_operational():
    pack = compile_government_intelligence()
    assert pack["registry"]["body_count"] >= 10
    domains = set(pack["domains"])
    for d in ("rbi", "budget", "sebi", "gst", "pli", "trade", "mca", "industry", "state"):
        assert d in domains, d
    assert pack["coverage_level"] == INSTITUTIONAL_COMPLETE_LEVEL
    assert pack["institutional_ready"] is True
    assert pack["political_opinion"] is False
    assert pack["policy_forecast"] is False


def test_rbi_budget_sebi_gst_pli_trade_views():
    compile_government_intelligence()
    assert domain_view("rbi")["n"] >= 3
    assert domain_view("budget")["n"] >= 2
    assert domain_view("sebi")["n"] >= 3
    assert domain_view("gst")["n"] >= 1
    assert domain_view("pli")["n"] >= 4
    assert domain_view("trade")["n"] >= 1


def test_policy_object_fields_and_provenance():
    pack = compile_government_intelligence()
    for p in pack["policies"]:
        assert p["policy_id"]
        assert p["name"]
        assert p["government_body"]
        assert p["announcement_date"]
        assert p["effective_date"]
        assert p["available_from"]
        assert p["source"]
        assert p["provenance"]
        assert p["provenance"]["fabricated"] is False
        assert p["immutable"] is True
        assert p["relationships"]["portfolio"]
        assert "sector" in p["relationships"]
        assert "company" in p["relationships"]
        assert p["transmission"]["speculative_forecast"] is False
        q = validate_policy(p)
        assert q["gate_pass"] is True


def test_transmission_knowledge_not_forecast():
    p = get_policy("RBI-REPO-2020-03")
    assert p["found"] is True
    tx = p["transmission"]
    assert "Bank NIM" in str(tx["primary"]) or "liquidity" in str(tx["primary"]).lower() or tx["primary"]
    assert tx["secondary"]
    assert tx["speculative_forecast"] is False
    assert p["policy_forecast"] is False


def test_point_in_time_replay_no_future_leak():
    pack = compile_government_intelligence()
    tl = pack["timeline"]
    replay = replay_as_of(tl, "2018-01-01")
    assert replay["future_leakage"] is False
    for p in replay["policies"]:
        assert p["available_from"] <= "2018-01-01"
    assert replay["excluded_future_count"] > 0
    api = timeline(as_of="2015-01-01")
    assert api["policy_count"] < tl["policy_count"]


def test_pli_timeline_sequence():
    compile_government_intelligence()
    pli = list_policies(domain="pli")["policies"]
    ids = [p["policy_id"] for p in pli]
    assert "PLI-ELECTRONICS-2020" in ids
    assert "SEMICONDUCTOR-MISSION-2022" in ids
    assert "PLI-BUDGET-EXTENSION-2024" in ids
    dates = [p["announcement_date"] for p in pli]
    assert dates == sorted(dates)


def test_duplicate_detection_and_pack_gates():
    pack = compile_government_intelligence()
    dups = detect_duplicate_policies(pack["policies"])
    assert dups == []
    q = validate_pack(
        bodies=pack["registry"]["bodies"],
        policies=pack["policies"],
        timeline=pack["timeline"],
    )
    assert q["gate_pass"] is True
    assert q["institutional_ready"] is True


def test_sector_company_portfolio_mapping():
    p = get_policy("GST-LAUNCH-2017")
    assert "fmcg" in p["affected_sectors"] or "all" in p["affected_sectors"]
    assert p["affected_companies"]
    assert p["relationships"]["portfolio"] == "institutional_reasoning.ipi"
    assert p["relationships"]["decision_quality"] == "decision_quality"
    assert p["relationships"]["corporate_events"] == "knowledge_factory.corporate_events"


def test_pipeline_dashboard_search():
    report = run_government_intelligence_pipeline()
    assert report["status"] == "ok"
    assert report["reasoning_changed"] is False
    assert report["governance_changed"] is False
    assert report["political_opinion"] is False
    dash = dashboard(ensure=False)
    assert dash["policy_count"] > 0
    assert dash["replay_status"] == "operational"
    assert dash["coverage_pct"] == 100.0
    hits = search("PLI")
    assert hits["n"] >= 1


def test_soft_wire_does_not_break_prior_sprints():
    from knowledge_factory.company_intelligence.schema import ICI_VERSION
    from knowledge_factory.corporate_events.schema import ICEI_VERSION

    assert ICI_VERSION
    assert ICEI_VERSION
    assert FREEZE_LOCKS["knowledge_factory_architecture"] is True
