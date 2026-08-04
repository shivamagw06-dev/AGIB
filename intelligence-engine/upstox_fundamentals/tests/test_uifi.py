"""UIFI normaliser + ingest contract tests."""

from __future__ import annotations

from upstox_fundamentals import health
from upstox_fundamentals.normalize import (
    merge_statement_rows,
    normalise_competitors,
    normalise_corporate_actions,
    normalise_profile,
    normalise_shareholding,
    normalise_statements,
)


def test_health_contract():
    h = health()
    assert h["ok"] is True
    assert h["engine"] == "UIFI"
    assert "profile" in h["datasets"]
    assert h["rule"] == "products_read_warehouse_only"


def test_normalise_profile():
    row = normalise_profile({
        "symbol": "INFY",
        "isin": "INE009A01021",
        "data": {
            "company_name": "Infosys Ltd",
            "sector": "Information Technology",
            "industry": "IT Services",
            "website": "https://www.infosys.com",
            "business_description": "IT services",
            "employee_count": 250000,
        },
    })
    assert row["symbol"] == "INFY"
    assert row["instrument_key"] == "NSE_EQ|INE009A01021"
    assert row["sector"] == "Information Technology"
    assert row["dqiv_status"] == "passed"


def test_normalise_income_statement_periods():
    rows = normalise_statements({
        "symbol": "INFY",
        "data": {
            "units_in": "crore",
            "statement_type": "Consolidated",
            "Revenue": {"FY2024": 150000, "FY2023": 140000},
            "PAT": {"FY2024": 25000, "FY2023": 23000},
            "EPS": {"FY2024": 60.5, "FY2023": 55.1},
        },
    }, kind="income-statement")
    assert len(rows) >= 2
    assert {r["fiscal_year"] for r in rows} >= {"FY2024", "FY2023"}
    assert all(r["statement_type"] == "CONSOLIDATED" for r in rows)
    assert any(r.get("revenue") == 150000 for r in rows)


def test_merge_statements():
    income = normalise_statements({
        "symbol": "TCS",
        "data": {"units_in": "crore", "Revenue": {"FY2024": 200000}, "PAT": {"FY2024": 40000}},
    }, kind="income-statement")
    balance = normalise_statements({
        "symbol": "TCS",
        "data": {
            "units_in": "crore",
            "Total Assets": {"FY2024": 180000},
            "Shareholders Equity": {"FY2024": 120000},
        },
    }, kind="balance-sheet")
    cash = normalise_statements({
        "symbol": "TCS",
        "data": {
            "units_in": "crore",
            "Operating Cash Flow": {"FY2024": 45000},
            "Capex": {"FY2024": 5000},
        },
    }, kind="cash-flow")
    merged = merge_statement_rows(income + balance + cash)
    assert len(merged) == 1
    row = merged[0]
    assert row.get("revenue") == 200000
    assert row.get("assets") == 180000
    assert row.get("cfo") == 45000


def test_shareholding_dqiv():
    rows = normalise_shareholding({
        "symbol": "INFY",
        "data": [{
            "date": "2026-03-31",
            "promoter": 14.5,
            "fii": 33.0,
            "dii": 28.0,
            "public": 24.5,
        }],
    })
    assert len(rows) == 1
    assert rows[0]["promoter_holding"] == 14.5
    assert rows[0]["institutional_holding"] == 61.0


def test_corporate_actions_secondary_confidence():
    rows = normalise_corporate_actions({
        "symbol": "INFY",
        "data": [{
            "name": "Dividend",
            "amount": 20,
            "expiry_date": "2026-06-01",
            "event_details": [
                {"name": "Announcement date", "value": "2026-04-15"},
                {"name": "Ex dividend date", "value": "2026-06-01"},
            ],
        }],
    })
    assert rows
    assert rows[0]["confidence"] == 0.55
    assert rows[0]["action_type"] == "dividend"
    assert rows[0]["source"] == "upstox"


def test_competitors_no_self():
    rows = normalise_competitors({
        "symbol": "INFY",
        "isin_map": {"INE467B01029": "TCS", "INE009A01021": "INFY"},
        "data": ["NSE_EQ|INE467B01029", "NSE_EQ|INE009A01021"],
    })
    assert len(rows) == 1
    assert rows[0]["peer_symbol"] == "TCS"
    assert rows[0]["relationship"] == "competitor"


def test_ingest_bundle_profile(monkeypatch):
    from upstox_fundamentals import ingest

    writes = []

    class GW:
        def write(self, tab, rows, **kwargs):
            writes.append({"tab": tab, "rows": rows, **kwargs})
            return {"ok": True, "written": len(rows)}

    import institutional_warehouse.gateway as gateway_mod
    monkeypatch.setattr(gateway_mod, "write", GW().write)

    out = ingest.ingest_bundle({
        "dataset": "profile",
        "companies": [{
            "symbol": "INFY",
            "isin": "INE009A01021",
            "data": {"company_name": "Infosys", "sector": "IT", "industry": "Services"},
        }],
    })
    assert out["ok"] is True
    tabs = {w["tab"] for w in writes}
    assert "company_master" in tabs
    assert "profile_history" in tabs
