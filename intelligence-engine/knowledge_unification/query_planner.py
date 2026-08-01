"""Module 2 — Query Planner (deterministic question typing)."""

from __future__ import annotations

import re
from typing import Optional

from knowledge_unification.schema import QueryPlan

_CONCEPT_RE = re.compile(
    r"\b(explain|what is|what are|define|definition of|meaning of)\b",
    re.I,
)
_ACCOUNTING_RE = re.compile(
    r"\b(journal|debit|credit|balance sheet|income statement|retained earnings|"
    r"double entry|trial balance|ledger|accrual|depreciation|amortisation|amortization)\b",
    re.I,
)
_FSA_RE = re.compile(
    r"\b(financial statement|read the (p&l|pnl|balance sheet)|cash flow statement|"
    r"working capital|days sales|inventory days|dupont|"
    r"earnings quality|receivables|inventory doubles|ocf|operating cash|"
    r"reconstruct the cash flow|interpret\.?$)\b",
    re.I,
)
_FSA_SHAPE_RE = re.compile(
    r"(%|％).{0,40}(%|％)|"
    r"\b(revenue|pat|ebitda|fcf|ocf|capex|receivables|inventory)\b.{0,30}"
    r"(\+|−|-|up|down|flat|doubled|grew|falling)",
    re.I,
)
_VALUATION_RE = re.compile(
    r"\b(valuation|enterprise value|equity value|dcf|ev/ebitda|p/e|pe ratio|wacc|terminal value)\b",
    re.I,
)
_BUSINESS_RE = re.compile(
    r"\b(business model|how does .+ make money|products?|competitors?|moat|segments?)\b",
    re.I,
)
_INDUSTRY_RE = re.compile(r"\b(industry|sector|peers?|competitive landscape)\b", re.I)
_MACRO_RE = re.compile(r"\b(macro|gdp|inflation|interest rate|rbi|fed|risk premium|country premium)\b", re.I)
_MARKET_RE = re.compile(r"\b(price|return|returns|market cap|volume|earnings date|ytd)\b", re.I)
_PORTFOLIO_RE = re.compile(r"\b(portfolio|position sizing|allocation|watchlist)\b", re.I)
_NEWS_RE = re.compile(r"\b(news|latest|recent|announced|filing|transcript)\b", re.I)

_FINANCE_TERMS = re.compile(
    r"\b(ebitda|ebit|roic|roe|roa|fcf|free cash flow|enterprise value|wacc|capex|"
    r"working capital|gross margin|operating margin|nim|npa|casa|book value)\b",
    re.I,
)


def _detect_company_hint(question: str) -> tuple[Optional[str], Optional[str]]:
    """Return (company_hint, ticker_hint) using CapIQ router + light heuristics."""
    ticker = None
    company = None
    try:
        from app.ui.company_router import detect_ikt_company

        ticker = detect_ikt_company(question)
    except Exception:
        ticker = None
    if ticker:
        try:
            from institutional_knowledge_tables.store import get_table

            row = (get_table(ticker, "company_master").get("row") or {}).get("company_name") or {}
            company = row.get("value") if isinstance(row, dict) else None
        except Exception:
            company = None
        return company, ticker

    # Alias seed / common names
    aliases = {
        "reliance": "RELIANCE",
        "hdfc bank": "HDFCBANK",
        "infosys": "INFY",
        "tcs": "TCS",
        "wipro": "WIPRO",
        "icici bank": "ICICIBANK",
        "sbi": "SBIN",
        "state bank of india": "SBIN",
    }
    low = question.lower()
    for name, tk in aliases.items():
        if name in low:
            return name.title(), tk
    return None, None


_EXPLICIT_COMPANY_ALIASES = (
    "reliance", "hdfc bank", "infosys", "tcs", "wipro", "icici bank", "sbi",
    "state bank of india", "axis bank", "kotak", "tata steel", "tata motors",
    "tata power", "adani", "hmt limited", "goodricke", "utique", "aakaar",
    "spright agro", "titan company",
)


_CORPORATE_FORM_RE = re.compile(
    r"\b(limited|ltd\.?|pvt\.?|private limited|corporation|corp\.?|inc\.?|plc)\b",
    re.I,
)
# Tokens too generic to prove a CapIQ name was intentional in a pedagogy Q.
_GENERIC_NAME_TOKENS = frozenset(
    {
        "capital", "finance", "financial", "india", "indian", "limited", "group",
        "industries", "enterprise", "enterprises", "company", "global", "national",
        "international", "investment", "investments", "services", "power", "energy",
        "steel", "motors", "bank", "banking", "tech", "technology", "technologies",
        "holdings", "corporation", "private", "public", "agro", "labs", "lab",
        "allocation", "value", "equity", "growth", "income", "credit", "money",
        "market", "markets", "securities", "asset", "assets", "fund", "funds",
    }
)


def _has_explicit_company_signal(question: str, *, company_hint: Optional[str] = None, ticker_hint: Optional[str] = None) -> bool:
    """True only when the question clearly names a firm — not a fuzzy CapIQ hit.

    Pedagogy questions like "Customer pays ₹20 lakh in advance" must NOT keep
    a CapIQ bind to "Advance Agrolife Limited" just because one token overlaps.
    """
    low = (question or "").lower()
    if any(a in low for a in _EXPLICIT_COMPANY_ALIASES):
        return True
    # Corporate-form questions ("Explain Margo Finance Limited").
    if _CORPORATE_FORM_RE.search(low):
        return True
    # Only treat ticker_hint as explicit when it appears as a ticker token
    # (not as an English word — ADVANCE must not bind on "in advance").
    if ticker_hint:
        tk = str(ticker_hint).strip()
        if re.search(rf"(?<![a-z0-9]){re.escape(tk)}(?![a-z0-9])", question or "", re.I):
            # Reject pure common-English tickers unless corporate form present.
            if tk.lower() not in _GENERIC_NAME_TOKENS or _CORPORATE_FORM_RE.search(low):
                if tk.isupper() or _CORPORATE_FORM_RE.search(low) or any(
                    a in low for a in _EXPLICIT_COMPANY_ALIASES
                ):
                    # Bare uppercase ticker in the original question.
                    if re.search(rf"\b{re.escape(tk)}\b", question or ""):
                        return True
    if company_hint:
        name_low = str(company_hint).lower().strip()
        # Full/near-full company name present (strong signal).
        if len(name_low) >= 8 and name_low in low:
            return True
        # Or ≥2 distinctive name tokens (avoids "advance" → Advance Agrolife).
        tokens = [t for t in re.split(r"[^a-z0-9]+", name_low) if len(t) >= 4]
        distinctive = [t for t in tokens if t not in _GENERIC_NAME_TOKENS]
        matches = [t for t in distinctive if t in low]
        if len(matches) >= 2:
            return True
    finance_acronyms = {
        "EBITDA", "EBIT", "ROIC", "ROE", "ROA", "FCF", "WACC", "CAPEX", "EV",
        "GDP", "NPA", "NIM", "CASA", "PE", "EPS", "CAGR", "LTM", "YOY",
    }
    for tok in re.findall(r"\b([A-Z]{2,12}\d{0,4})\b", question or ""):
        if tok not in finance_acronyms:
            return True
    return False


def plan_query(question: str) -> QueryPlan:
    q = (question or "").strip()
    types: list[str] = []

    if _ACCOUNTING_RE.search(q):
        types.append("accounting")
    if _FSA_RE.search(q) or _FSA_SHAPE_RE.search(q):
        types.append("financial_statement")
    if _VALUATION_RE.search(q) or _FINANCE_TERMS.search(q):
        types.append("valuation" if _VALUATION_RE.search(q) else "concept")
    if _BUSINESS_RE.search(q):
        types.append("business_model")
    if _INDUSTRY_RE.search(q):
        types.append("industry")
    if _MACRO_RE.search(q):
        types.append("macro")
    if _MARKET_RE.search(q):
        types.append("market")
    if _PORTFOLIO_RE.search(q):
        types.append("portfolio")
    if _NEWS_RE.search(q):
        types.append("news")
    if _CONCEPT_RE.search(q) or _FINANCE_TERMS.search(q):
        if "concept" not in types:
            types.append("concept")

    company, ticker = _detect_company_hint(q)
    # CapIQ name matching is aggressive ("advance" → Advance Agrolife).
    # Keep a bind only when the question explicitly names a firm/ticker, or
    # is clearly company-shaped (business model / industry / market / news).
    explicit = _has_explicit_company_signal(q, company_hint=company, ticker_hint=ticker)
    company_shaped = bool(
        _BUSINESS_RE.search(q) or _INDUSTRY_RE.search(q) or _MARKET_RE.search(q) or _NEWS_RE.search(q)
    )
    if (company or ticker) and not explicit and not company_shaped:
        company, ticker = None, None
    if company or ticker:
        types.insert(0, "company")

    # Dedup preserving order
    seen = set()
    ordered = []
    for t in types:
        if t not in seen:
            seen.add(t)
            ordered.append(t)
    if not ordered:
        ordered = ["unknown"]

    requires_company = bool(ticker or company) or (
        "company" in ordered and "concept" not in ordered and "accounting" not in ordered
    )
    requires_det = bool(
        set(ordered).intersection({"concept", "accounting", "financial_statement", "valuation"})
        and not ticker
    )

    concept_hint = None
    if "concept" in ordered or "valuation" in ordered:
        concept_hint = q

    return QueryPlan(
        question=q,
        question_types=ordered,
        company_hint=company,
        ticker_hint=ticker,
        concept_hint=concept_hint,
        requires_company=requires_company,
        requires_deterministic_finance=requires_det,
    )
