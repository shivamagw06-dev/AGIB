"""Optional public search API connector (Tavily / SerpAPI / Exa / Bing).

Enabled only when corresponding API keys exist and FAA_SEARCH_API is on.
Never used as the sole answer path — discovery only.
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote_plus

from app.faa.connectors.base import AcquisitionConnector
from app.faa.models import CandidateDocument, DiscoveryTask


def available_search_providers() -> list[str]:
    out = []
    if (os.environ.get("TAVILY_API_KEY") or "").strip():
        out.append("tavily")
    if (os.environ.get("SERPAPI_API_KEY") or os.environ.get("SERPAPI_KEY") or "").strip():
        out.append("serpapi")
    if (os.environ.get("EXA_API_KEY") or "").strip():
        out.append("exa")
    if (os.environ.get("BING_SEARCH_API_KEY") or "").strip():
        out.append("bing")
    if (os.environ.get("GOOGLE_CSE_ID") or "").strip() and (os.environ.get("GOOGLE_CSE_API_KEY") or "").strip():
        out.append("google_cse")
    return out


class SearchApiConnector(AcquisitionConnector):
    connector_id = "search_api"
    name = "Public Search APIs"
    tier = 6

    def discover(self, task: DiscoveryTask) -> list[CandidateDocument]:
        providers = available_search_providers()
        q = task.query or task.description
        if not providers:
            # No key configured — emit a deferred candidate marker (not fetched).
            return [
                CandidateDocument(
                    title=f"Search deferred (no API key): {q}",
                    url=f"search://unconfigured?q={quote_plus(q)}",
                    connector_id=self.connector_id,
                    document_type=task.document_type or "general_web",
                    company=task.company,
                    symbol=task.symbol,
                    organisation="search_api",
                    discovery_task_id=task.task_id,
                    metadata={"providers_available": [], "deferred": True},
                )
            ]

        # Live provider calls happen in FetchService for these candidates.
        return [
            CandidateDocument(
                title=f"Search: {q}",
                url=f"search://{providers[0]}?q={quote_plus(q)}",
                connector_id=self.connector_id,
                document_type=task.document_type or "general_web",
                company=task.company,
                symbol=task.symbol,
                organisation=providers[0],
                discovery_task_id=task.task_id,
                metadata={"providers_available": providers, "query": q},
            )
        ]

    def health(self) -> dict[str, Any]:
        base = super().health()
        base["providers_available"] = available_search_providers()
        return base
