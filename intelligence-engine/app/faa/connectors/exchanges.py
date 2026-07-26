"""NSE / BSE / SEBI / RBI / government discovery connectors."""

from __future__ import annotations

from app.faa.connectors.base import AcquisitionConnector
from app.faa.connectors.catalog import EXCHANGE_URLS, resolve_symbol
from app.faa.models import CandidateDocument, DiscoveryTask


class NseConnector(AcquisitionConnector):
    connector_id = "nse"
    name = "NSE Corporate Filings"
    tier = 2

    def discover(self, task: DiscoveryTask) -> list[CandidateDocument]:
        sym = resolve_symbol(task.company, task.symbol)
        url = EXCHANGE_URLS["nse_filings"]
        title = f"NSE filings — {sym or task.company or 'market'}"
        return [
            CandidateDocument(
                title=title,
                url=url,
                connector_id=self.connector_id,
                document_type="exchange_filing",
                company=task.company,
                symbol=sym,
                organisation="NSE",
                discovery_task_id=task.task_id,
                metadata={"symbol": sym},
            )
        ]


class BseConnector(AcquisitionConnector):
    connector_id = "bse"
    name = "BSE Announcements"
    tier = 2

    def discover(self, task: DiscoveryTask) -> list[CandidateDocument]:
        sym = resolve_symbol(task.company, task.symbol)
        return [
            CandidateDocument(
                title=f"BSE announcements — {sym or task.company or 'market'}",
                url=EXCHANGE_URLS["bse_announcements"],
                connector_id=self.connector_id,
                document_type="exchange_filing",
                company=task.company,
                symbol=sym,
                organisation="BSE",
                discovery_task_id=task.task_id,
            )
        ]


class SebiConnector(AcquisitionConnector):
    connector_id = "sebi"
    name = "SEBI"
    tier = 2

    def discover(self, task: DiscoveryTask) -> list[CandidateDocument]:
        return [
            CandidateDocument(
                title="SEBI circulars / listings",
                url=EXCHANGE_URLS["sebi"],
                connector_id=self.connector_id,
                document_type="government",
                company=task.company,
                symbol=resolve_symbol(task.company, task.symbol),
                organisation="SEBI",
                discovery_task_id=task.task_id,
            )
        ]


class RbiConnector(AcquisitionConnector):
    connector_id = "rbi"
    name = "RBI Press / Policy"
    tier = 2

    def discover(self, task: DiscoveryTask) -> list[CandidateDocument]:
        return [
            CandidateDocument(
                title="RBI press releases",
                url=EXCHANGE_URLS["rbi_press"],
                connector_id=self.connector_id,
                document_type="government",
                organisation="RBI",
                discovery_task_id=task.task_id,
            ),
            CandidateDocument(
                title="RBI bulletins / policy materials",
                url=EXCHANGE_URLS["rbi_mp"],
                connector_id=self.connector_id,
                document_type="government",
                organisation="RBI",
                discovery_task_id=task.task_id,
            ),
        ]


class GovernmentConnector(AcquisitionConnector):
    connector_id = "government"
    name = "Government / PIB"
    tier = 2

    def discover(self, task: DiscoveryTask) -> list[CandidateDocument]:
        return [
            CandidateDocument(
                title="PIB press releases",
                url="https://pib.gov.in/AllRel.aspx",
                connector_id=self.connector_id,
                document_type="government",
                organisation="PIB",
                discovery_task_id=task.task_id,
            )
        ]
