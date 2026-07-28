"""Read Knowledge Objects from KAIP internal APIs.

The Intelligence Engine must never call Yahoo/NSE/BSE directly for knowledge supply.
Sprint 6.1: retrieval client only — no reasoning, no write-back.
"""

from __future__ import annotations

import os
from typing import Any

import httpx


class KaipClientError(RuntimeError):
    pass


class KaipClient:
    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout_seconds: float = 5.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("KAIP_BASE_URL") or "http://127.0.0.1:8091").rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._client = client

    def _get(self, path: str) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            if self._client is not None:
                resp = self._client.get(url, timeout=self.timeout_seconds)
            else:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    resp = client.get(url)
        except httpx.HTTPError as exc:
            raise KaipClientError(f"kaip_unreachable:{exc}") from exc
        if resp.status_code == 404:
            raise KaipClientError("kaip_not_found")
        if resp.status_code >= 400:
            raise KaipClientError(f"kaip_http_{resp.status_code}")
        data = resp.json()
        if not isinstance(data, dict):
            raise KaipClientError("kaip_invalid_payload")
        return data

    def get_company_profile(self, symbol: str) -> dict[str, Any]:
        return self._get(f"/v1/knowledge/company/{symbol.upper()}")

    def get_market_snapshot(self, symbol: str) -> dict[str, Any]:
        return self._get(f"/v1/knowledge/market/{symbol.upper()}")

    def get_events(self, symbol: str) -> dict[str, Any]:
        return self._get(f"/v1/knowledge/events/{symbol.upper()}")

    def get_financials(self, symbol: str) -> dict[str, Any]:
        return self._get(f"/v1/knowledge/financials/{symbol.upper()}")

    def get_learning(self, symbol: str) -> dict[str, Any]:
        return self._get(f"/v1/knowledge/learning/{symbol.upper()}")

    def health(self) -> dict[str, Any]:
        return self._get("/healthz")
