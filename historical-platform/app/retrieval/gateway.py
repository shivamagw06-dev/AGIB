"""Historical Retrieval API helpers — store only, never call external providers."""

from __future__ import annotations

from typing import Any

from app.config.settings import Settings
from app.coverage.policy import policy_snapshot
from app.storage.db import HipStore


class HistoricalRetrievalGateway:
    def __init__(self, store: HipStore, settings: Settings) -> None:
        self.store = store
        self.settings = settings

    def company_history(self, symbol: str) -> dict[str, Any]:
        symbol = symbol.upper()
        entity = self.store.get_entity(symbol)
        return {
            "company_symbol": symbol,
            "entity": entity,
            "providers_queried": [],  # hard guarantee
            "profiles": self.store.list_profiles(symbol),
            "prices_daily": self.store.list_prices(symbol, period_kind="daily", limit=5000),
            "financials": self.store.list_financials(symbol, limit=500),
            "dividends": self.store.list_dividends(symbol),
            "actions": self.store.list_actions(symbol),
            "events": self.store.list_events(symbol),
            "reports": self.store.list_reports(symbol),
            "news": self.store.list_news(symbol),
            "coverage": self.store.coverage_report(symbol, self.settings),
        }

    def revenue_growth(
        self,
        symbol: str,
        *,
        from_period: str = "FY2015",
        to_period: str = "FY2025",
    ) -> dict[str, Any]:
        """Success-path retrieval: Infosys revenue FY2015–FY2025 + valuation per cycle."""
        series = self.store.revenue_series(symbol, from_period=from_period, to_period=to_period)
        growth = []
        prev = None
        for row in series:
            rev = row.get("revenue")
            yoY = None
            if prev and prev.get("revenue") and rev:
                yoY = round((float(rev) - float(prev["revenue"])) / float(prev["revenue"]) * 100, 2)
            growth.append({**row, "revenue_growth_pct": yoY})
            prev = row
        return {
            "company_symbol": symbol.upper(),
            "from_period": from_period,
            "to_period": to_period,
            "providers_queried": [],
            "series": growth,
            "entity": self.store.get_entity(symbol),
            "note": "Retrieved exclusively from Historical Knowledge Store.",
        }

    def coverage(self, symbol: str) -> dict[str, Any]:
        return self.store.coverage_report(symbol, self.settings)

    def policy(self) -> dict[str, Any]:
        return policy_snapshot(self.settings)
