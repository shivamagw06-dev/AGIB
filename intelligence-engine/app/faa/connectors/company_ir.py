"""Company Investor Relations discovery connector."""

from __future__ import annotations

from app.faa.connectors.base import AcquisitionConnector
from app.faa.connectors.catalog import COMPANY_IR, resolve_symbol
from app.faa.models import CandidateDocument, DiscoveryTask

_DOC_KEY = {
    "annual_report": "annual",
    "quarterly_report": "quarterly",
    "quarterly_result": "quarterly",
    "investor_presentation": "presentation",
    "transcript": "transcript",
    "conference_call": "transcript",
    "news": "news",
}


class CompanyIrConnector(AcquisitionConnector):
    connector_id = "company_ir"
    name = "Company Investor Relations"
    tier = 1

    def discover(self, task: DiscoveryTask) -> list[CandidateDocument]:
        sym = resolve_symbol(task.company, task.symbol)
        if not sym or sym not in COMPANY_IR:
            # Generic IR search candidate via search_api handoff metadata
            if task.preferred_url:
                return [
                    CandidateDocument(
                        title=task.description,
                        url=task.preferred_url,
                        connector_id=self.connector_id,
                        document_type=task.document_type,
                        company=task.company,
                        symbol=task.symbol,
                        organisation=task.company or "",
                        discovery_task_id=task.task_id,
                        metadata={"generic": True},
                    )
                ]
            return []

        profile = COMPANY_IR[sym]
        key = _DOC_KEY.get(task.document_type, "ir_home")
        url = profile.get(key) or profile.get("ir_home")
        if not url:
            return []
        return [
            CandidateDocument(
                title=f"{profile['company']} — {task.description}",
                url=url,
                connector_id=self.connector_id,
                document_type=task.document_type or "investor_relations",
                company=profile["company"],
                symbol=sym,
                organisation=profile["company"],
                discovery_task_id=task.task_id,
                metadata={"ir_home": profile.get("ir_home"), "doc_key": key},
            )
        ]
