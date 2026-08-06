from institutional_warehouse.financials import canonical_statement_series


def test_annual_series_prefers_capiq_within_same_year():
    rows = [
        {"fiscal_year": "FY2024", "statement_type": "CONSOLIDATED", "source": "upstox", "pat": 10},
        {"fiscal_year": "FY2024", "statement_type": "CONSOLIDATED", "statement_version": "capiq_workbook_2024", "source": "capital_iq_workbook", "pat": 12},
        {"fiscal_year": "FY2025", "statement_type": "CONSOLIDATED", "source": "upstox", "pat": 15},
    ]
    selected = canonical_statement_series(rows, period_key="fiscal_year", annual=True)
    assert [row["pat"] for row in selected] == [12, 15]


def test_quarterly_series_does_not_apply_capiq_priority():
    rows = [
        {"fiscal_period": "FY2025Q1", "statement_type": "CONSOLIDATED", "source": "upstox", "pat": 10},
        {"fiscal_period": "FY2025Q1", "statement_type": "CONSOLIDATED", "statement_version": "capiq_workbook_2025", "source": "capital_iq_workbook", "pat": 12},
    ]
    selected = canonical_statement_series(rows, period_key="fiscal_period", annual=False)
    assert selected[0]["pat"] == 10
