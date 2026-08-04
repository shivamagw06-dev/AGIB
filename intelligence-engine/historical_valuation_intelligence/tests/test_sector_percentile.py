"""Sector historical percentile — own-history rank, never mid-pack default."""

from __future__ import annotations

from historical_valuation_intelligence.sector_percentile import (
    MIN_SECTOR_HISTORY_OBS,
    sector_historical_percentile,
)
from historical_valuation_intelligence.statistics import _percentile_of
from market_intelligence_engine import aggregation


def test_percentile_of_formula():
    # Current 28.4 among [18,19,21,23,24,26,27,29,31] → 7 of 9 ≤ 28.4 → 77.8
    hist = [18, 19, 21, 23, 24, 26, 27, 29, 31]
    assert _percentile_of(28.4, hist + [28.4]) == round(100.0 * 8 / 10, 1)


def test_insufficient_history_never_defaults_to_50(monkeypatch):
    monkeypatch.setattr(
        "historical_valuation_intelligence.sector_percentile.load_sector_median_series",
        lambda sector, metric="pe", limit=5000: {
            "ok": True,
            "sector": sector,
            "values": [20.0, 21.0, 22.0],
            "points": [
                {"period": "2026-01-01", "value": 20.0},
                {"period": "2026-02-01", "value": 21.0},
                {"period": "2026-03-01", "value": 22.0},
            ],
            "first_observation": "2026-01-01",
            "last_observation": "2026-03-01",
            "source": "test",
        },
    )
    out = sector_historical_percentile("Information Technology", current_median=22.0)
    assert out["historical_percentile"] is None
    assert out["status"] == "INSUFFICIENT_HISTORY"
    assert out["observation_count"] == 3
    assert out["observation_count"] < MIN_SECTOR_HISTORY_OBS
    assert "50" not in (out.get("reason") or "")


def test_sufficient_history_ranks_current(monkeypatch):
    values = [18 + i * 0.5 for i in range(30)]  # 18 … 32.5
    points = [
        {"period": f"2024-{(i % 12) + 1:02d}-01", "value": v}
        for i, v in enumerate(values)
    ]
    monkeypatch.setattr(
        "historical_valuation_intelligence.sector_percentile.load_sector_median_series",
        lambda sector, metric="pe", limit=5000: {
            "ok": True,
            "sector": sector,
            "values": values,
            "points": points,
            "first_observation": points[0]["period"],
            "last_observation": points[-1]["period"],
            "source": "test",
        },
    )
    # Near the top of history → high percentile (expensive)
    expensive = sector_historical_percentile("IT", current_median=32.0)
    assert expensive["status"] == "OK"
    assert expensive["historical_percentile"] is not None
    assert expensive["historical_percentile"] >= 90

    cheap = sector_historical_percentile("IT", current_median=18.5)
    assert cheap["historical_percentile"] is not None
    assert cheap["historical_percentile"] <= 20


def test_sector_table_does_not_use_peer_median_as_historical(monkeypatch):
    """Peer percentiles at ~50 must not become heatmap historical_percentile."""

    def fake_hist(sector, current_median=None, metric="pe", min_obs=24):
        return {
            "ok": True,
            "historical_percentile": 78.0,
            "historical_median": 22.0,
            "status": "OK",
            "reason": None,
            "observation_count": 120,
            "first_observation": "2015-01-01",
            "last_observation": "2026-08-04",
            "source": "test",
        }

    monkeypatch.setattr(
        "historical_valuation_intelligence.sector_percentile.sector_historical_percentile",
        fake_hist,
    )
    uni = {
        "ok": True,
        "rows": [
            {
                "symbol": "AAA",
                "sector": "Information Technology",
                "industry_dna": "it_services",
                "pe": 28,
                "percentile": 51,  # peer rank mid-pack
                "provider_coverage": 3,
                "sector_median_pe": 24,
            },
            {
                "symbol": "BBB",
                "sector": "Information Technology",
                "industry_dna": "it_services",
                "pe": 30,
                "percentile": 49,
                "provider_coverage": 3,
                "sector_median_pe": 24,
            },
        ],
    }
    rows = aggregation.sector_table(uni)
    assert len(rows) == 1
    assert rows[0]["historical_percentile"] == 78.0
    assert rows[0]["peer_relative_percentile_median"] == 50.0
    assert rows[0]["historical_percentile_status"] == "OK"
    # Dispersion proof: heatmap KPI ≠ peer mid-pack
    assert rows[0]["historical_percentile"] != rows[0]["peer_relative_percentile_median"]
