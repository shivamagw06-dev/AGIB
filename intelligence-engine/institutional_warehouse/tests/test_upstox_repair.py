"""Safety checks for retiring legacy Upstox annual values labelled as Q4."""

from __future__ import annotations

from institutional_warehouse import store
from institutional_warehouse.upstox_repair import repair_annual_as_quarterly


def test_repair_only_selects_exact_annual_q4_duplicates(monkeypatch):
    annual = [{
        "symbol": "ABC", "fiscal_year": "FY2025", "statement_type": "CONSOLIDATED",
        "source": "upstox", "revenue": 100.0, "pbt": 20.0, "pat": 15.0, "eps": 10.0,
    }]
    quarterly = [
        {
            "row_id": "retire-me", "symbol": "ABC", "fiscal_year": "FY2025",
            "fiscal_period": "FY2025Q4", "statement_type": "CONSOLIDATED",
            "source": "upstox", "revenue": 100.0, "pbt": 20.0, "pat": 15.0, "eps": 10.0,
        },
        {
            "row_id": "keep-me", "symbol": "ABC", "fiscal_year": "FY2025",
            "fiscal_period": "FY2025Q3", "statement_type": "CONSOLIDATED",
            "source": "upstox", "revenue": 90.0, "pbt": 18.0, "pat": 13.0, "eps": 8.0,
        },
        {
            "row_id": "keep-different", "symbol": "ABC", "fiscal_year": "FY2025",
            "fiscal_period": "FY2025Q4", "statement_type": "CONSOLIDATED",
            "source": "upstox", "revenue": 99.0, "pbt": 20.0, "pat": 15.0, "eps": 10.0,
        },
    ]
    monkeypatch.setattr(store, "all_rows", lambda tab, **_: annual if tab == "financials_annual" else quarterly)

    result = repair_annual_as_quarterly()

    assert result["candidates"] == 1
    assert result["row_ids"] == ["retire-me"]
    assert not result["applied"]


def test_repair_apply_uses_retirement_not_deletion(monkeypatch):
    annual = [{
        "symbol": "ABC", "fiscal_year": "FY2025", "statement_type": "CONSOLIDATED",
        "source": "upstox", "revenue": 100.0,
    }]
    quarterly = [{
        "row_id": "retire-me", "symbol": "ABC", "fiscal_year": "FY2025",
        "fiscal_period": "FY2025Q4", "statement_type": "CONSOLIDATED",
        "source": "upstox", "revenue": 100.0,
    }]
    calls = []
    monkeypatch.setattr(store, "all_rows", lambda tab, **_: annual if tab == "financials_annual" else quarterly)
    monkeypatch.setattr(store, "retire_rows", lambda *args, **kwargs: calls.append((args, kwargs)) or {"ok": True, "retired": 1})

    result = repair_annual_as_quarterly(actor="admin", apply=True)

    assert result["applied"]
    assert calls[0][0] == ("financials_quarterly", ["retire-me"])
    assert "mislabelled as quarterly Q4" in calls[0][1]["reason"]
