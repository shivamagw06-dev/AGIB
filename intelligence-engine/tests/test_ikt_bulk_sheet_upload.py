"""Bulk company-info sheet ingest — Excel/CSV → versioned IKT facts."""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("IKT_STORE_ROOT", "/tmp/ikt_bulk_sheet_test_store")

import pandas as pd

from institutional_knowledge_tables.bulk_sheet import ingest_company_sheet
from institutional_knowledge_tables.store import delete_company, get_field_history, get_table


def _xlsx_bytes(df: "pd.DataFrame") -> bytes:
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


def setup_function():
    for t in ("HDFCBANK", "IDBI", "RELIANCE"):
        delete_company(t)


def test_ingest_by_exact_ticker():
    df = pd.DataFrame(
        [
            {"Ticker": "HDFCBANK", "Sector": "Banking", "CEO": "Sashidhar Jagdishan", "PE": 18.4},
            {"Ticker": "IDBI", "Sector": "Banking", "CEO": "Rakesh Sharma", "PE": 12.1},
        ]
    )
    out = ingest_company_sheet(_xlsx_bytes(df), "companies.xlsx")
    assert out["ok"] is True
    assert out["resolved_count"] == 2
    assert out["unresolved_count"] == 0
    assert "company_master.sector" in out["mapped_columns"].values()
    assert "management.ceo" in out["mapped_columns"].values()
    assert "valuation.pe" in out["mapped_columns"].values()

    sector_hist = get_field_history("HDFCBANK", "company_master", "sector")
    assert sector_hist[-1]["value"] == "Banking"
    assert sector_hist[-1]["source"].startswith("bulk_upload:companies.xlsx")

    ceo = get_table("IDBI", "management")
    assert ceo["row"]["ceo"]["value"] == "Rakesh Sharma"


def test_ingest_by_company_name_when_no_ticker():
    df = pd.DataFrame([{"Company Name": "IDBI Bank Limited", "Industry": "Bank"}])
    out = ingest_company_sheet(_xlsx_bytes(df), "names_only.xlsx")
    assert out["ok"] is True
    assert out["resolved_count"] == 1
    assert out["resolved_sample"][0]["ticker"] == "IDBI"
    assert out["resolved_sample"][0]["method"] == "exact_name_match"


def test_unresolved_rows_are_reported_not_guessed():
    df = pd.DataFrame(
        [
            {"Ticker": "HDFCBANK", "Sector": "Banking"},
            {"Ticker": "TOTALLYFAKEXYZ", "Sector": "Nowhere"},
        ]
    )
    out = ingest_company_sheet(_xlsx_bytes(df), "mixed.xlsx")
    assert out["resolved_count"] == 1
    assert out["unresolved_count"] == 1
    assert out["unresolved_rows"][0]["ticker_raw"] == "TOTALLYFAKEXYZ"
    assert out["unresolved_rows"][0]["reason"] == "unresolved"
    # never fabricated a table row for the unresolved ticker
    from institutional_knowledge_tables.store import get_table as _gt

    fake = _gt("TOTALLYFAKEXYZ", "company_master")
    assert fake["missing_fields"] == list(fake["row"].keys())


def test_dry_run_does_not_write():
    df = pd.DataFrame([{"Ticker": "RELIANCE", "Sector": "Energy"}])
    out = ingest_company_sheet(_xlsx_bytes(df), "dry.xlsx", dry_run=True)
    assert out["ok"] is True
    assert out["resolved_count"] == 1
    table = get_table("RELIANCE", "company_master")
    assert table["row"]["sector"] is None  # nothing actually written


def test_unmapped_columns_reported():
    df = pd.DataFrame([{"Ticker": "RELIANCE", "Some Random Column": "xyz"}])
    out = ingest_company_sheet(_xlsx_bytes(df), "extra.xlsx")
    assert "Some Random Column" in out["unmapped_columns"]


def test_missing_ticker_and_name_column_rejected():
    df = pd.DataFrame([{"Sector": "Energy"}])
    out = ingest_company_sheet(_xlsx_bytes(df), "no_id.xlsx")
    assert out["ok"] is False
    assert out["error"] == "no_ticker_or_company_name_column"


def test_csv_input_also_supported():
    csv_bytes = b"Ticker,Sector\nHDFCBANK,Banking\n"
    out = ingest_company_sheet(csv_bytes, "companies.csv")
    assert out["ok"] is True
    assert out["resolved_count"] == 1


def test_exchange_prefixed_ticker_resolves_and_writes_canonical_value():
    """A raw sheet code like 'BSE:500180' must resolve via company name and
    the written company_master.ticker fact must be the canonical ticker,
    never the raw exchange-prefixed source code."""
    df = pd.DataFrame(
        [{"Ticker": "BSE:500180", "Company Name": "HDFC Bank Limited", "Primary Sector": "Financials"}]
    )
    out = ingest_company_sheet(_xlsx_bytes(df), "capiq_style.xlsx")
    assert out["ok"] is True
    assert out["resolved_count"] == 1
    assert out["resolved_sample"][0]["ticker"] == "HDFCBANK"

    table = get_table("HDFCBANK", "company_master")
    assert table["row"]["ticker"]["value"] == "HDFCBANK"
    assert table["row"]["sector"]["value"] == "Financials"


def test_ltm_and_latest_period_labels_inferred_from_header():
    df = pd.DataFrame(
        [
            {
                "Ticker": "RELIANCE",
                "EBITDA [LTM] ($USDmm, Historical rate)": 12000,
                "Market Capitalization [My Setting] [Latest] ($USDmm, Historical rate)": 250000,
            }
        ]
    )
    out = ingest_company_sheet(_xlsx_bytes(df), "capiq2.xlsx")
    assert out["ok"] is True
    fin = get_table("RELIANCE", "financial_statements", period="LTM")
    assert fin["found"] is True
    assert fin["row"]["ebitda"]["value"] == 12000
    market = get_table("RELIANCE", "market_data", period="latest")
    assert market["found"] is True
    assert market["row"]["market_cap"]["value"] == 250000
