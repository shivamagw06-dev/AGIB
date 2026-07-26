"""FAA acquisition connectors."""

from __future__ import annotations

from typing import Any

from app.faa.connectors.base import AcquisitionConnector
from app.faa.connectors.company_ir import CompanyIrConnector
from app.faa.connectors.exchanges import (
    BseConnector,
    GovernmentConnector,
    NseConnector,
    RbiConnector,
    SebiConnector,
)
from app.faa.connectors.news import NewsConnector
from app.faa.connectors.search_api import SearchApiConnector


def build_connectors(*, live_fetch: bool = False) -> dict[str, AcquisitionConnector]:
    args: dict[str, Any] = {"live_fetch": live_fetch}
    connectors: list[AcquisitionConnector] = [
        CompanyIrConnector(**args),
        NseConnector(**args),
        BseConnector(**args),
        SebiConnector(**args),
        RbiConnector(**args),
        GovernmentConnector(**args),
        NewsConnector(**args),
        SearchApiConnector(**args),
    ]
    return {c.connector_id: c for c in connectors}
