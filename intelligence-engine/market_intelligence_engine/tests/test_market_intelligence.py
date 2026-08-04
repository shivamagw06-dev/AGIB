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


def test_sector_table_no_fake_upstox_benchmark():
    """When Upstox coverage is 0%, Sector/Premium must stay empty (not peer median)."""
    uni = {
        "ok": True,
        "rows": [
            {
                "symbol": "AAA",
                "sector": "Industrials",
                "industry_dna": "industrials",
                "pe": 50,
                "sector_median_pe": 50,
                "percentile": 60,
                "provider_coverage": 0,
            },
            {
                "symbol": "BBB",
                "sector": "Industrials",
                "industry_dna": "industrials",
                "pe": 56,
                "sector_median_pe": 56,
                "percentile": 65,
                "provider_coverage": 0,
            },
        ],
    }
    rows = aggregation.sector_table(uni)
    assert len(rows) == 1
    assert rows[0]["current"] is not None
    assert rows[0]["sector_benchmark"] is None
    assert rows[0]["sector_benchmark_source"] is None
    assert rows[0]["premium_pct"] is None
    assert rows[0]["upstox_coverage_pct"] == 0


def test_isin_shape_helper():
    from valuation_ratios.isin_backfill import _valid_isin

    assert _valid_isin("INE002A01018") == "INE002A01018"
    assert _valid_isin("bad") is None


def test_text_confidence_does_not_crash_gateway():
    """valuation_ratios.confidence is TEXT ('high'); must not hit numeric bounds."""
    import os
    import tempfile

    from institutional_warehouse import db, gateway

    root = tempfile.mkdtemp(prefix="wh_conf_")
    os.environ["INSTITUTIONAL_WAREHOUSE_ROOT"] = root
    db.init(force=True)
    result = gateway.write(
        "valuation_ratios",
        [{
            "company_id": "AAA",
            "symbol": "AAA",
            "isin": "INE002A01018",
            "instrument_key": "NSE_EQ|INE002A01018",
            "ratio_name": "pe",
            "company_value": 20.0,
            "sector_value": 18.0,
            "reported_date": "2026-08-04",
            "snapshot_id": "t-conf-1",
            "confidence": "high",
            "dqiv_status": "passed",
            "source": "upstox",
        }],
        source="upstox",
        actor="test",
        detect_conflicts=False,
    )
    assert result.get("ok") is True
    assert result.get("written", 0) >= 1
