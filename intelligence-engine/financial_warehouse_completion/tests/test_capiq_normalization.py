from __future__ import annotations

from financial_warehouse_completion.capiq_normalization import audit_and_prepare, resolve_identity


def _masters():
    return {
        "TCS": {
            "company_id": "1", "symbol": "TCS", "isin": "INE467B01029",
            "company_name": "Tata Consultancy Services Limited", "sector": "Information Technology",
        },
        "ICICIBANK": {
            "company_id": "2", "symbol": "ICICIBANK", "isin": "INE090A01021",
            "company_name": "ICICI Bank Limited", "sector": "Financials",
        },
    }


def test_exact_symbol_identity_is_verified_and_classified():
    result = resolve_identity({"symbol": "ICICIBANK"}, _masters())
    assert result["identity_status"] == "VERIFIED"
    assert result["identity_map"]["match_method"] == "SYMBOL_EXACT"
    assert result["identity_map"]["company_type"] == "BANK"


def test_unmatched_company_is_held_not_written():
    prepared = audit_and_prepare(
        [{"symbol": "UNKNOWN", "fiscal_year": "FY2025", "pat": 10, "assets": 20, "equity": 5}],
        field_map={"PAT": "pat", "Total Assets": "assets", "Total Equity": "equity"},
        source_file="2016-2026.xlsx", masters=_masters(),
    )
    assert prepared["accepted"] == []
    assert prepared["audits"][0]["overall_status"] == "REVIEW_REQUIRED"
    assert prepared["audits"][0]["write_status"] == "HELD"


def test_verified_company_period_has_all_required_fields_before_release():
    prepared = audit_and_prepare(
        [{"symbol": "TCS", "fiscal_year": "FY2025", "pat": 100, "assets": 500, "equity": 300, "revenue": 1000}],
        field_map={"PAT": "pat", "Total Assets": "assets", "Total Equity": "equity", "Revenue": "revenue"},
        source_file="2016-2026.xlsx", masters=_masters(),
    )
    assert len(prepared["accepted"]) == 1
    assert prepared["audits"][0]["overall_status"] == "VERIFIED"
    assert prepared["audits"][0]["required_fields_found"] == 3
