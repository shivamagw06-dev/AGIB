"""Soft bridge from KRIG → HIP Timeline Intelligence (Sprint 8.2).

Ask / IE never call Yahoo/NSE/BSE. When HIP is configured, KRIG composes
historical timelines and compare bundles from the Historical Knowledge Store.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger("kaip.krig.historical")


class HistoricalKnowledgeBridge:
    def __init__(self, base_url: str | None, *, timeout_seconds: float = 3.0) -> None:
        self.base_url = (base_url or "").rstrip("/") or None
        self.timeout_seconds = timeout_seconds

    @property
    def enabled(self) -> bool:
        return bool(self.base_url)

    def fetch_timeline(self, symbol: str) -> list[dict[str, Any]]:
        body = self._get(f"/v1/history/timeline/{symbol.upper()}")
        if not body:
            return []
        return list(body.get("timeline") or body.get("narrative") or [])

    def fetch_compare(self, symbol: str, *, as_of_period: str = "FY2018") -> dict[str, Any] | None:
        return self._post(
            "/v1/history/compare",
            {"symbol": symbol.upper(), "as_of_period": as_of_period},
        )

    def _get(self, path: str) -> dict[str, Any] | None:
        if not self.base_url:
            return None
        url = f"{self.base_url}{path}"
        try:
            req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            logger.info("HIP timeline bridge miss path=%s err=%s", path, exc)
            return None

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        if not self.base_url:
            return None
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        try:
            req = urllib.request.Request(
                url,
                data=data,
                method="POST",
                headers={"Accept": "application/json", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            logger.info("HIP compare bridge miss path=%s err=%s", path, exc)
            return None
