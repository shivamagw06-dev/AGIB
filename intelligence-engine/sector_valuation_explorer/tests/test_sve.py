"""Sector Valuation Explorer contract tests."""

from __future__ import annotations

from sector_valuation_explorer import health
from sector_valuation_explorer.production import _canonical_sector, _enrich_company, _sector_explanation
from sector_valuation_explorer.status import opportunity_label, outcome_label, valuation_status
from valuation_terminal.sector_lens import lens_for


def test_health_contract():
    h = health()
    assert h["ok"] is True
    assert h["engine"] == "sector_valuation_explorer"
    assert "Financials" in h["sectors"]
    assert h["rule"] == "no_ui_calculations_no_buy_sell"


def test_canonical_sector_aliases():
    assert _canonical_sector("information technology") == "Information Technology"
    assert _canonical_sector("Healthcare") == "Health Care"
    assert _canonical_sector("nope") is None


def test_valuation_status_labels():
    assert valuation_status(percentile=10, premium_pct=None, primary_value=12) == "Historically Cheap"
    assert valuation_status(percentile=90, premium_pct=None, primary_value=40) == "Historically Expensive"
    assert valuation_status(percentile=50, premium_pct=0, primary_value=20) == "Fairly Valued"
    assert valuation_status(percentile=None, premium_pct=None, primary_value=None) == "Data Insufficient"
    assert valuation_status(
        percentile=50, premium_pct=0, primary_value=1, policy_status="METRIC_NOT_APPLICABLE",
    ) == "Metric Not Applicable"


def test_opportunity_and_outcome():
    assert opportunity_label(20) == "Attractive"
    assert opportunity_label(80) == "Premium"
    assert "Expensive" in outcome_label(85, 20) or "Premium" in outcome_label(85, 20)


def test_sector_explanation_reuses_lens():
    lens = lens_for("it_services", "Information Technology")
    expl = _sector_explanation(lens, "Information Technology")
    assert expl["primary_metric"] == "pe"
    assert expl["source"] == "valuation_terminal.sector_lens"
    assert any(h["metric"] == "pb" for h in expl["hidden"])


def test_enrich_company_status():
    row = _enrich_company(
        {
            "symbol": "INFY",
            "company_name": "Infosys",
            "sector": "Information Technology",
            "industry": "IT Services",
            "primary_metric": "pe",
            "primary_value": 28,
            "pe": 28,
            "pb": 8,
            "roe": 30,
            "percentile": 82,
            "sector_premium_pct": 18,
            "provider_coverage": 5,
            "market_cap": 5e12,
            "source": "upstox",
        },
        {"median_pe": 24, "median_pb": 6},
    )
    assert row["valuation_status"] == "Premium"
    assert row["market_cap_bucket"] == "large"
    assert row["sector_pe"] == 24
