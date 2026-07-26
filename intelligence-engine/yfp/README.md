# YFP — Yahoo Finance Institutional Provider

**Architecture status:** v1.0.1 LOCKED  
**Role:** Secondary MarketData provider (priority 40) — enrichment only

## Financial Intelligence Enrichment

Canonical financial statement + valuation history via MarketDataClient only.

| Flag | Purpose |
|------|---------|
| `YAHOO_FINANCIAL_HISTORY` | Income / balance / cash-flow annual+quarterly history |
| `YAHOO_VALUATION_HISTORY` | PE, EV, EV/EBITDA, PB, PS, PEG, yields, shares |
| `YAHOO_CID_ENRICHMENT` | Soft-merge into CID (fill empties only) |
| `YAHOO_YFINANCE_FALLBACK` | Soft path via `yfinance.Ticker.get_income_stmt` / balance / cashflow when quoteSummary crumb fails |

Fetch order for financial intelligence: quoteSummary modules → (if empty/auth fail) yfinance fundamentals-timeseries (`freq=yearly|quarterly`). Mapped to canonical keys only.

Soft side-effects (no redesign): CID financial timeline, KF company financial_history, LEO evidence packages, DVC validated_fields (secondary).

Ask AGI benefits via enriched CID — never mention Yahoo in answers.
