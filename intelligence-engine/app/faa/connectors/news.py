"""Trusted financial news discovery connector."""

from __future__ import annotations

from urllib.parse import quote_plus

from app.faa.connectors.base import AcquisitionConnector
from app.faa.connectors.catalog import resolve_symbol
from app.faa.models import CandidateDocument, DiscoveryTask

_NEWS_HOMES = [
    ("business_standard", "https://www.business-standard.com/search?q={q}", "Business Standard"),
    ("moneycontrol", "https://www.moneycontrol.com/news/tags/{q}.html", "Moneycontrol"),
    ("economic_times", "https://economictimes.indiatimes.com/topic/{q}", "Economic Times"),
]


class NewsConnector(AcquisitionConnector):
    connector_id = "news"
    name = "Trusted Financial News"
    tier = 4

    def discover(self, task: DiscoveryTask) -> list[CandidateDocument]:
        sym = resolve_symbol(task.company, task.symbol)
        q = quote_plus(sym or task.company or task.query or "markets")
        out: list[CandidateDocument] = []
        for source, template, org in _NEWS_HOMES:
            out.append(
                CandidateDocument(
                    title=f"{org} — {task.description}",
                    url=template.format(q=q),
                    connector_id=self.connector_id,
                    document_type="news",
                    company=task.company,
                    symbol=sym,
                    organisation=org,
                    discovery_task_id=task.task_id,
                    metadata={"news_source": source},
                )
            )
        return out[:2]
