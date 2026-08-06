from __future__ import annotations

from financial_warehouse_completion import capiq_workbook


def test_preview_reads_completed_capital_iq_sheets():
    result = capiq_workbook.preview()
    assert result["ok"] is True
    assert result["unit"] == "INR million"
    assert result["years"]["2016"] > 3000
    assert result["years"]["2024"] > 3000
    assert result["years"]["2026"] > 3000


def test_sheet_rows_normalise_ticker_and_stamp_identity():
    row = next(item for item in capiq_workbook._sheet_rows(2024, path=capiq_workbook.WORKBOOK_PATH)
               if item["symbol"] == "TCS")
    assert row["fiscal_year"] == "FY2024"
    assert row["statement_type"] == "CONSOLIDATED"
    assert row["statement_frequency"] == "ANNUAL"
    assert row["revenue"] == 2408930.0
    assert row["pat"] == 459080.0
