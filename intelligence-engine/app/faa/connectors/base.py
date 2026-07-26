"""Base connector contract for FAA discovery/fetch."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.faa.models import CandidateDocument, DiscoveryTask


class AcquisitionConnector(ABC):
    connector_id: str = "base"
    name: str = "Base"
    tier: int = 6

    def __init__(self, *, live_fetch: bool = False, config: dict[str, Any] | None = None) -> None:
        self.live_fetch = live_fetch
        self.config = config or {}

    @abstractmethod
    def discover(self, task: DiscoveryTask) -> list[CandidateDocument]:
        """Return candidate public documents for a discovery task."""

    def health(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "name": self.name,
            "tier": self.tier,
            "live_fetch": self.live_fetch,
            "status": "ok",
        }
