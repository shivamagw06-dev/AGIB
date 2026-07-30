"""Continuous acquisition scheduler — institutional cadences."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


SCHEDULE = [
    {"stream": "exchange_filings", "cadence": "every_5_minutes", "connectors": ["nse", "bse"]},
    {"stream": "news", "cadence": "every_5_minutes", "connectors": ["news", "rss", "search_api"]},
    {"stream": "rss", "cadence": "every_10_minutes", "connectors": ["rss"]},
    {"stream": "government", "cadence": "hourly", "connectors": ["rbi", "sebi", "government", "pib", "mca"]},
    {"stream": "annual_reports", "cadence": "daily", "connectors": ["company_ir", "pdf_url"]},
    {"stream": "investor_presentations", "cadence": "daily", "connectors": ["company_ir"]},
    {
        "stream": "quarterly_reports",
        "cadence": "every_hour_during_earnings_season",
        "connectors": ["company_ir", "nse", "bse"],
    },
]

WATCHLIST_QUERIES = [
    "Reliance Industries annual report filings news",
    "Infosys quarterly results guidance transcript",
    "TCS investor presentation and filings",
    "HDFC Bank exchange filings and news",
    "RBI monetary policy press release",
    "SEBI notifications latest",
]


class FaaScheduler:
    def __init__(self) -> None:
        self.enabled = True
        self.last_run_at: str | None = None
        self.runs: list[dict[str, Any]] = []

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "schedule": SCHEDULE,
            "watchlist_queries": WATCHLIST_QUERIES,
            "last_run_at": self.last_run_at,
            "recent_runs": self.runs[-30:],
        }

    def mark_run(self, stream: str, **kwargs: Any) -> dict[str, Any]:
        row = {
            "stream": stream,
            "at": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        }
        self.last_run_at = row["at"]
        self.runs.append(row)
        self.runs = self.runs[-120:]
        return row
