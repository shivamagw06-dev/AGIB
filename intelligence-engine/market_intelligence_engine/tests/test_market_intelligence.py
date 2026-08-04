"""Market Intelligence Engine tests."""

from market_intelligence_engine import aggregation, ingest_flows, opportunities, summary


def test_opportunity_label_bands():
    assert aggregation._opportunity_label(20) == "Attractive"
    assert aggregation._opportunity_label(50) == "Fair"
    assert aggregation._opportunity_label(80) == "Premium"


def test_normalise_upstox_flow():
    rows = ingest_flows.normalise_upstox_flow({
        "date": "2026-08-01",
        "fii": {"buy": 1000, "sell": 800},
        "dii": {"buy": 500, "sell": 600},
    })
    assert len(rows) == 1
    assert rows[0]["fii_net"] == 200.0
    assert rows[0]["dii_net"] == -100.0


def test_detect_opportunities_empty():
    out = opportunities.detect_opportunities({"ok": True, "rows": []})
    assert out["ok"] is False


def test_detect_historical_discount():
    uni = {
        "ok": True,
        "rows": [
            {"symbol": "AAA", "company_name": "A", "sector": "IT", "industry": "Software",
             "pe": 15, "percentile": 8, "source": "warehouse"},
            {"symbol": "BBB", "company_name": "B", "sector": "IT", "industry": "Software",
             "pe": 30, "percentile": 90, "source": "warehouse"},
        ],
    }
    out = opportunities.detect_opportunities(uni, limit_per_kind=2)
    kinds = {c["kind"] for c in out["cards"]}
    assert "historical_discount" in kinds


def test_market_summary_not_empty():
    text = summary.market_summary(
        {"averages": {"pe": 22.5}},
        [{"sector": "IT", "opportunity": "Attractive", "historical_percentile": 25}],
        {"ok": True, "heatmap": "Bullish", "advancing": 800, "declining": 400},
        {"available": False},
    )
    assert "median P/E" in text
    assert "investment advice" in text.lower() or "not investment advice" in text.lower()
