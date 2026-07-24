from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


class AgibClient:
    """Read-only client for AGIB Node cached endpoints. Never call third-party APIs here."""

    def __init__(self, base_url: str | None = None, timeout: float = 30.0):
    settings = get_settings()
        base = (base_url or settings.agib_api_base_url).rstrip("/")
        if base and not base.startswith(("http://", "https://")):
            base = f"https://{base}"
        self.base_url = base
        self.timeout = timeout
        self.token = settings.agib_service_token

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def get_json(self, path: str) -> dict[str, Any] | None:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._headers())
                if response.status_code >= 400:
                    log.warning("agib_fetch_failed", extra={"url": url, "status": response.status_code})
                    return None
                return response.json()
        except Exception as exc:
            log.warning("agib_fetch_error", extra={"url": url, "error": str(exc)})
            return None

    async def macro_briefing(self) -> dict[str, Any] | None:
        return await self.get_json("/api/market/macro-briefing")

    async def market_briefing(self) -> dict[str, Any] | None:
        return await self.get_json("/api/market/briefing")

    async def pre_market_briefing(self) -> dict[str, Any] | None:
        return await self.get_json("/api/market/pre-market-briefing")

    async def market_context(self) -> dict[str, Any] | None:
        return await self.get_json("/api/market-context")
