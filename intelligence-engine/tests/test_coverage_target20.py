"""Sprint 1 — Target-20 coverage must hit 20/20 Decision Coverage."""

from __future__ import annotations

from knowledge_factory.coverage import TARGET_20, decision_coverage, morning_coverage_dashboard
from knowledge_factory.production import run_daily_pipeline
from knowledge_factory.store import repository as store
from institutional_reasoning.fundamentals.primitives import covered_entities, has_primitives
from institutional_reasoning.fundamentals.market_series import monthly_returns


def setup_function() -> None:
    store.reset_store()


def test_target_20_primitives_and_risk_series():
    assert len(TARGET_20) == 20
    for e in TARGET_20:
        assert has_primitives(e), e
        assert monthly_returns(e), e
    assert set(TARGET_20).issubset(set(covered_entities()))


def test_target_20_decision_coverage_100():
    run_daily_pipeline(entities=list(TARGET_20))
    dc = decision_coverage(TARGET_20)
    assert dc["decision_ready"] == 20, dc["gaps"]
    assert dc["decision_coverage_pct"] == 100.0
    for row in dc["rows"]:
        assert row["decision_ready"], (row["entity"], row["missing"])


def test_morning_board_shows_north_star():
    run_daily_pipeline(entities=list(TARGET_20))
    board = morning_coverage_dashboard()
    assert board["north_star"]["value_pct"] == 100.0
    assert board["tiers"]["target_20"]["covered"] == 20
    assert board["evidence_packs"] >= 20
    assert board["kpi"] == "coverage_pct"
