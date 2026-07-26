"""Public search API connectors — Tavily / SerpAPI / Exa / Bing / Google CSE.

Discovery-only adapters. Actual provider calls run in FetchService when live.
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
    max_per_minute = 20
    document_types = ["general_web", "news", "industry_report", "research_publication"]

    def search(self, task: DiscoveryTask) -> list[CandidateDocument]:
        providers = available_search_providers()
        q = task.query or task.description
        if not providers:
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
                    metadata={"providers_available": [], "deferred": True, "authority": 2},
                )
            ]
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
                metadata={"providers_available": providers, "query": q, "authority": 4},
            )
        ]

    def health(self) -> dict[str, Any]:
        base = super().health()
        base["providers_available"] = available_search_providers()
        return base


class TavilyConnector(SearchApiConnector):
    connector_id = "tavily"
    name = "Tavily Search"

    def search(self, task: DiscoveryTask) -> list[CandidateDocument]:
        if "tavily" not in available_search_providers():
            return []
        q = task.query or task.description
        return [
            CandidateDocument(
                title=f"Tavily: {q}",
                url=f"search://tavily?q={quote_plus(q)}",
                connector_id=self.connector_id,
                document_type=task.document_type or "general_web",
                company=task.company,
                symbol=task.symbol,
                organisation="tavily",
                discovery_task_id=task.task_id,
                metadata={"providers_available": ["tavily"], "query": q, "authority": 4},
            )
        ]


class ExaConnector(SearchApiConnector):
    connector_id = "exa"
    name = "Exa Search"

    def search(self, task: DiscoveryTask) -> list[CandidateDocument]:
        if "exa" not in available_search_providers():
            return []
        q = task.query or task.description
        return [
            CandidateDocument(
                title=f"Exa: {q}",
                url=f"search://exa?q={quote_plus(q)}",
                connector_id=self.connector_id,
                document_type=task.document_type or "general_web",
                company=task.company,
                symbol=task.symbol,
                organisation="exa",
                discovery_task_id=task.task_id,
                metadata={"providers_available": ["exa"], "query": q, "authority": 4},
            )
        ]


class SerpApiConnector(SearchApiConnector):
    connector_id = "serpapi"
    name = "SerpAPI"

    def search(self, task: DiscoveryTask) -> list[CandidateDocument]:
        if "serpapi" not in available_search_providers():
            return []
        q = task.query or task.description
        return [
            CandidateDocument(
                title=f"SerpAPI: {q}",
                url=f"search://serpapi?q={quote_plus(q)}",
                connector_id=self.connector_id,
                document_type=task.document_type or "general_web",
                company=task.company,
                symbol=task.symbol,
                organisation="serpapi",
                discovery_task_id=task.task_id,
                metadata={"providers_available": ["serpapi"], "query": q, "authority": 4},
            )
        ]


class GoogleCseConnector(SearchApiConnector):
    connector_id = "google_cse"
    name = "Google Custom Search"

    def search(self, task: DiscoveryTask) -> list[CandidateDocument]:
        if "google_cse" not in available_search_providers():
            return []
        q = task.query or task.description
        return [
            CandidateDocument(
                title=f"Google CSE: {q}",
                url=f"search://google_cse?q={quote_plus(q)}",
                connector_id=self.connector_id,
                document_type=task.document_type or "general_web",
                company=task.company,
                symbol=task.symbol,
                organisation="google_cse",
                discovery_task_id=task.task_id,
                metadata={"providers_available": ["google_cse"], "query": q, "authority": 4},
            )
        ]


class BingConnector(SearchApiConnector):
    connector_id = "bing"
    name = "Bing Search API"

    def search(self, task: DiscoveryTask) -> list[CandidateDocument]:
        if "bing" not in available_search_providers():
            return []
        q = task.query or task.description
        return [
            CandidateDocument(
                title=f"Bing: {q}",
                url=f"search://bing?q={quote_plus(q)}",
                connector_id=self.connector_id,
                document_type=task.document_type or "general_web",
                company=task.company,
                symbol=task.symbol,
                organisation="bing",
                discovery_task_id=task.task_id,
                metadata={"providers_available": ["bing"], "query": q, "authority": 4},
            )
        ]
