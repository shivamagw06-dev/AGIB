"""FAA continuous acquisition schedule."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


SCHEDULE = [
    {"stream": "exchange_filings", "cadence": "immediate", "connectors": ["nse", "bse"]},
    {"stream": "news", "cadence": "every_5_15_minutes", "connectors": ["news", "search_api"]},
    {"stream": "government", "cadence": "hourly", "connectors": ["rbi", "sebi", "government"]},
    {"stream": "company_ir", "cadence": "detect_automatically", "connectors": ["company_ir"]},
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
            "last_run_at": self.last_run_at,
            "recent_runs": self.runs[-20:],
        }

    def mark_run(self, stream: str, **kwargs: Any) -> dict[str, Any]:
        row = {
            "stream": stream,
            "at": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        }
        self.last_run_at = row["at"]
        self.runs.append(row)
        self.runs = self.runs[-100:]
        return row
