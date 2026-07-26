"""YFP Financial Intelligence Enrichment — canonical history only (no Yahoo-native leaks)."""

from __future__ import annotations

from yfp.enrich import merge_financial_intelligence, merge_yahoo_into_dossier
from yfp.history import financial_coverage, kpi_trends, valuation_coverage
from yfp.leo_evidence import evidence_from_financial_intelligence
from yfp.production import is_cid_enrichment_enabled, quality_gates
from app.market_data.providers.yahoo_mapper import (
    map_financial_history_from_quote_summary,
    map_valuation_snapshot_from_quote_summary,
)


def _fixture():
    return {
        "quoteSummary": {
            "result": [
                {
                    "price": {"currency": "INR", "symbol": "INFY.NS"},
                    "summaryDetail": {
                        "trailingPE": {"raw": 24.0},
                        "forwardPE": {"raw": 22.0},
                        "marketCap": {"raw": 6e12},
                        "priceToSalesTrailing12Months": {"raw": 4.5},
                        "dividendYield": {"raw": 0.025},
                        "dividendRate": {"raw": 40.0},
                    },
                    "defaultKeyStatistics": {
                        "enterpriseValue": {"raw": 5.8e12},
                        "enterpriseToEbitda": {"raw": 16.0},
                        "pegRatio": {"raw": 2.1},
                        "priceToBook": {"raw": 7.0},
                        "beta": {"raw": 0.8},
                        "sharesOutstanding": {"raw": 4e9},
                        "floatShares": {"raw": 3.5e9},
                        "bookValue": {"raw": 200.0},
                    },
                    "incomeStatementHistory": {
                        "incomeStatementHistory": [
                            {
                                "endDate": {"fmt": "2023-12-31"},
                                "totalRevenue": {"raw": 1.8e12},
                                "ebitda": {"raw": 4.5e11},
                                "ebit": {"raw": 4e11},
                                "operatingIncome": {"raw": 4e11},
                                "grossProfit": {"raw": 6e11},
                                "netIncome": {"raw": 3e11},
                                "dilutedEPS": {"raw": 70.0},
                                "basicEPS": {"raw": 70.5},
                                "incomeTaxExpense": {"raw": 8e10},
                                "interestExpense": {"raw": 5e9},
                                "costOfRevenue": {"raw": 1.2e12},
                                "totalOperatingExpenses": {"raw": 2e11},
                            },
                            {
                                "endDate": {"fmt": "2022-12-31"},
                                "totalRevenue": {"raw": 1.6e12},
                                "ebitda": {"raw": 4e11},
                                "netIncome": {"raw": 2.7e11},
                                "dilutedEPS": {"raw": 63.0},
                            },
                        ]
                    },
                    "incomeStatementHistoryQuarterly": {
                        "incomeStatementHistory": [
                            {
                                "endDate": {"fmt": "2023-09-30"},
                                "totalRevenue": {"raw": 4.5e11},
                                "netIncome": {"raw": 7.5e10},
                                "dilutedEPS": {"raw": 18.0},
                            }
                        ]
                    },
                    "balanceSheetHistory": {
                        "balanceSheetStatements": [
                            {
                                "endDate": {"fmt": "2023-12-31"},
                                "totalAssets": {"raw": 1e12},
                                "totalCurrentAssets": {"raw": 6e11},
                                "cash": {"raw": 1e11},
                                "cashAndCashEquivalents": {"raw": 1.2e11},
                                "shortTermInvestments": {"raw": 5e10},
                                "longTermDebt": {"raw": 4e10},
                                "shortLongTermDebt": {"raw": 1e10},
                                "totalLiab": {"raw": 3e11},
                                "totalCurrentLiabilities": {"raw": 2e11},
                                "totalStockholderEquity": {"raw": 7e11},
                            }
                        ]
                    },
                    "cashflowStatementHistory": {
                        "cashflowStatements": [
                            {
                                "endDate": {"fmt": "2023-12-31"},
                                "totalCashFromOperatingActivities": {"raw": 3.5e11},
                                "totalCashflowsFromInvestingActivities": {"raw": -8e10},
                                "totalCashFromFinancingActivities": {"raw": -1e11},
                                "capitalExpenditures": {"raw": -4e10},
                                "depreciation": {"raw": 5e10},
                                "dividendsPaid": {"raw": -9e10},
                                "repurchaseOfStock": {"raw": -2e10},
                                "freeCashFlow": {"raw": 3.1e11},
                            }
                        ]
                    },
                }
            ]
        }
    }


def test_map_financial_history_canonical_keys():
    hist = map_financial_history_from_quote_summary(_fixture(), symbol="INFY.NS")
    income = hist["income_statement"]["annual"]
    assert income[0]["line_items"]["revenue"] == 1.8e12
    assert income[0]["line_items"]["ebitda"] == 4.5e11
    assert income[0]["line_items"]["ebit"] == 4e11
    assert income[0]["line_items"]["net_income"] == 3e11
    assert income[0]["line_items"]["diluted_eps"] == 70.0
    bal = hist["balance_sheet"]["annual"][0]
    assert bal["line_items"]["total_assets"] == 1e12
    assert bal["line_items"]["total_liabilities"] == 3e11
    assert bal["line_items"]["shareholders_equity"] == 7e11
    assert bal["line_items"]["cash"] == 1e11
    assert bal["line_items"]["total_debt"] == 5e10  # 40+10
    assert bal["validation"]["accounting_equation_ok"] is True
    cash = hist["cash_flow"]["annual"][0]
    assert cash["line_items"]["operating_cash_flow"] == 3.5e11
    assert cash["line_items"]["free_cash_flow"] == 3.1e11
    assert cash["line_items"]["capital_expenditure"] == -4e10
    # No Yahoo-native keys in line_items
    for row in income + hist["balance_sheet"]["annual"] + hist["cash_flow"]["annual"]:
        for k in row["line_items"]:
            assert "totalRevenue" not in k
            assert k == k.lower()


def test_valuation_snapshot_and_coverage():
    val = map_valuation_snapshot_from_quote_summary(_fixture(), symbol="INFY.NS")
    m = val["metrics"]
    assert m["trailing_pe"] == 24.0
    assert m["forward_pe"] == 22.0
    assert m["enterprise_value"] == 5.8e12
    assert m["ev_ebitda"] == 16.0
    assert m["price_to_book"] == 7.0
    assert m["price_to_sales"] == 4.5
    assert m["peg"] == 2.1
    assert m["dividend_yield"] == 0.025
    cov = valuation_coverage(val)
    assert cov["coverage"] >= 0.7


def test_merge_into_cid_fill_empties():
    hist = map_financial_history_from_quote_summary(_fixture(), symbol="INFY.NS")
    val = map_valuation_snapshot_from_quote_summary(_fixture(), symbol="INFY.NS")
    dossier = {
        "ticker": "INFY",
        "market_data": {},
        "valuation": {"current": {"trailing_pe": 99.0}, "historical": []},  # higher-trust PE present
        "financial_statements": {
            "income_statement": {"annual": [], "quarterly": []},
            "balance_sheet": {"annual": [], "quarterly": []},
            "cash_flow": {"annual": [], "quarterly": []},
            "versions": [],
        },
    }
    enrich = {
        "enabled": True,
        "financial_history": hist,
        "valuation_snapshot": val,
        "fundamentals": {"metrics": {}},
        "quote": {},
    }
    merged = merge_yahoo_into_dossier(dossier, enrich)
    # Does not overwrite existing PE
    assert merged["valuation"]["current"]["trailing_pe"] == 99.0
    # Fills other valuation gaps
    assert merged["valuation"]["current"].get("ev_ebitda") == 16.0
    assert merged["financial_statements"]["income_statement"]["annual"]
    assert merged["historical_kpi_trends"]["revenue"]
    assert financial_coverage(hist)["coverage"] > 0.5
    assert kpi_trends(hist)["net_income"]


def test_leo_evidence_package():
    hist = map_financial_history_from_quote_summary(_fixture(), symbol="INFY.NS")
    val = map_valuation_snapshot_from_quote_summary(_fixture(), symbol="INFY.NS")
    objs = evidence_from_financial_intelligence("INFY", financial_history=hist, valuation_snapshot=val)
    types = {o["evidence_type"] for o in objs}
    assert "financial_statements" in types
    assert "valuation_metrics" in types
    assert all(o.get("source_id") == "yahoo" for o in objs)


def test_quality_gates_offline():
    assert is_cid_enrichment_enabled() is True
    gates = quality_gates()
    assert gates["passed"] is True
    assert gates["checks"]["revenue_history_mapped"] is True
    assert gates["checks"]["accounting_equation_ok"] is True
    assert gates["checks"]["no_yahoo_native_leaks"] is True


def test_merge_financial_intelligence_idempotent_fill():
    hist = map_financial_history_from_quote_summary(_fixture(), symbol="INFY.NS")
    d = {
        "ticker": "INFY",
        "financial_statements": {
            "income_statement": {
                "annual": [{"at": "x", "source": "official", "period_rows": [{"period_end": "2023-12-31"}]}],
                "quarterly": [],
            },
            "balance_sheet": {"annual": [], "quarterly": []},
            "cash_flow": {"annual": [], "quarterly": []},
            "versions": [],
        },
    }
    out = merge_financial_intelligence(d, {"financial_history": hist, "valuation_snapshot": {}})
    # Official annual income not overwritten
    assert out["financial_statements"]["income_statement"]["annual"][0]["source"] == "official"
    # Empty balance filled
    assert out["financial_statements"]["balance_sheet"]["annual"]
