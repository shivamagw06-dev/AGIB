"""Canonical financial metric registry — single naming authority for FSE-01.

Principle 4: every financial concept exists once.
Consumers and extractors must resolve names through this registry.
"""

from __future__ import annotations

from typing import Iterable

# Canonical income statement metrics
INCOME_CANONICAL = (
    "revenue",
    "other_income",
    "total_income",
    "expenses",
    "employee_benefit_expense",
    "finance_costs",
    "depreciation",
    "ebitda",
    "ebit",
    "pbt",
    "tax_expense",
    "pat",
    "pat_owners",
    "eps_basic",
    "eps_diluted",
)

# Canonical balance sheet metrics
BALANCE_CANONICAL = (
    "total_assets",
    "current_assets",
    "non_current_assets",
    "cash",
    "total_equity",
    "equity_share_capital",
    "equity_owners",
    "reserves",
    "face_value",
    "shares_outstanding",
    "deposits",
    "total_liabilities",
    "current_liabilities",
    "non_current_liabilities",
    "total_debt",
    "working_capital",
)

# Canonical cash-flow metrics
CASHFLOW_CANONICAL = (
    "operating_cash_flow",
    "investing_cash_flow",
    "financing_cash_flow",
    "free_cash_flow",
    "capex",
    "net_change_in_cash",
)

# Synonyms / legacy pack keys → canonical
# Includes P2.1 earnings_intelligence keys and common XBRL local names.
SYNONYMS: dict[str, str] = {
    # Income
    "revenue_from_operations": "revenue",
    "RevenueFromOperations": "revenue",
    "revenue_from_operations_total": "revenue",
    "total_revenue": "revenue",
    "net_sales": "revenue",
    "OtherIncome": "other_income",
    "TotalIncome": "total_income",
    "EmployeeBenefitExpense": "employee_benefit_expense",
    "FinanceCosts": "finance_costs",
    "DepreciationAndAmortisation": "depreciation",
    "depreciation_and_amortisation": "depreciation",
    "ProfitBeforeTax": "pbt",
    "TaxExpense": "tax_expense",
    "ProfitAfterTax": "pat",
    "ProfitForThePeriod": "pat",
    "ProfitAttributableToOwners": "pat_owners",
    "BasicEPS": "eps_basic",
    "DilutedEPS": "eps_diluted",
    # Balance
    "TotalAssets": "total_assets",
    "CurrentAssets": "current_assets",
    "NonCurrentAssets": "non_current_assets",
    "CashAndCashEquivalents": "cash",
    "TotalEquity": "total_equity",
    "EquityShareCapital": "equity_share_capital",
    "EquityAttributableToOwners": "equity_owners",
    "OtherEquity": "reserves",
    "FaceValue": "face_value",
    "NumberOfShares": "shares_outstanding",
    "TotalLiabilities": "total_liabilities",
    "CurrentLiabilities": "current_liabilities",
    "NonCurrentLiabilities": "non_current_liabilities",
    "Borrowings": "total_debt",
    "total_borrowings": "total_debt",
    # Cash flow
    "CashFlowsFromUsedInOperatingActivities": "operating_cash_flow",
    "CashFlowsFromUsedInInvestingActivities": "investing_cash_flow",
    "CashFlowsFromUsedInFinancingActivities": "financing_cash_flow",
    "NetCashFlowsFromUsedInOperatingActivities": "operating_cash_flow",
    "PurchaseOfPropertyPlantAndEquipment": "capex",
    "IncreaseDecreaseInCashAndCashEquivalents": "net_change_in_cash",
}

UNIT_SCALES = ("ones", "thousands", "lakhs", "crores", "millions", "billions")

UNIT_SCALE_TO_ONES: dict[str, float] = {
    "ones": 1.0,
    "thousands": 1_000.0,
    "lakhs": 100_000.0,
    "crores": 10_000_000.0,
    "millions": 1_000_000.0,
    "billions": 1_000_000_000.0,
}


def all_canonical() -> tuple[str, ...]:
    return INCOME_CANONICAL + BALANCE_CANONICAL + CASHFLOW_CANONICAL


def canonical_set() -> set[str]:
    return set(all_canonical())


def assert_unique_canonical(names: Iterable[str] | None = None) -> None:
    seq = list(names if names is not None else all_canonical())
    if len(seq) != len(set(seq)):
        seen: set[str] = set()
        dupes: list[str] = []
        for n in seq:
            if n in seen:
                dupes.append(n)
            seen.add(n)
        raise ValueError(f"duplicate canonical metrics: {dupes}")


def resolve(name: str | None) -> str | None:
    """Resolve extractor/legacy name to canonical metric, or None if unknown."""
    if not name:
        return None
    key = str(name).strip()
    if not key:
        return None
    if key in canonical_set():
        return key
    return SYNONYMS.get(key) or SYNONYMS.get(key.lower())


def to_value_inr(reported_value: float | int | None, unit_scale: str | None) -> float | None:
    if reported_value is None:
        return None
    scale = (unit_scale or "ones").lower()
    mult = UNIT_SCALE_TO_ONES.get(scale)
    if mult is None:
        return None
    return float(reported_value) * mult


def registry_manifest() -> dict:
    assert_unique_canonical()
    return {
        "income": list(INCOME_CANONICAL),
        "balance_sheet": list(BALANCE_CANONICAL),
        "cash_flow": list(CASHFLOW_CANONICAL),
        "synonym_count": len(SYNONYMS),
        "canonical_count": len(all_canonical()),
        "unit_scales": list(UNIT_SCALES),
    }
