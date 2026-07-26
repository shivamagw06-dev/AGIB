"""Discovery Service — intelligent task generation + connector routing."""

from __future__ import annotations

from typing import Any

from app.faa.connectors import build_connectors
from app.faa.connectors.base import AcquisitionConnector
from app.faa.models import CandidateDocument, DiscoveryTask
from app.fre.planner import plan_retrieval
from app.fre.understanding import understand_query

# Map FRE planner document types → FAA connectors
_TYPE_TO_CONNECTORS: dict[str, list[str]] = {
    "annual_report": ["company_ir"],
    "quarterly_report": ["company_ir"],
    "investor_presentation": ["company_ir"],
    "transcript": ["company_ir"],
    "conference_call": ["company_ir"],
    "exchange_filing": ["nse", "bse"],
    "nse_bse_filing": ["nse", "bse"],
    "news": ["news", "search_api"],
    "government": ["rbi", "sebi", "government"],
    "rbi": ["rbi"],
    "sebi": ["sebi"],
    "industry_report": ["search_api"],
    "research_publication": ["search_api"],
    "fred": ["search_api"],
    "imf": ["search_api"],
    "world_bank": ["search_api"],
}


class DiscoveryService:
    def __init__(self, *, live_fetch: bool = False, connectors: dict[str, AcquisitionConnector] | None = None) -> None:
        self.connectors = connectors or build_connectors(live_fetch=live_fetch)

    def build_tasks(self, query: str, *, aoi: Any | None = None) -> list[DiscoveryTask]:
        ud = understand_query(query, aoi=aoi)
        plan = plan_retrieval(query, aoi=aoi, understanding=ud)
        tasks: list[DiscoveryTask] = []
        for t in plan.tasks:
            connectors: list[str] = []
            for dt in t.document_types:
                for cid in _TYPE_TO_CONNECTORS.get(dt, ["search_api"]):
                    if cid not in connectors:
                        connectors.append(cid)
            if not connectors:
                connectors = ["search_api"]
            for cid in connectors:
                tasks.append(
                    DiscoveryTask(
                        description=t.description,
                        connector_id=cid,
                        query=f"{ud.primary_entity or ''} {t.description}".strip(),
                        company=t.company or (ud.companies[0] if ud.companies else None),
                        symbol=t.symbol or (ud.symbols[0] if ud.symbols else ud.primary_entity),
                        document_type=(t.document_types[0] if t.document_types else "unknown"),
                        priority=t.priority,
                    )
                )
        # Always include IR + filings + news for investment analysis
        if ud.intent == "investment_analysis" and ud.primary_entity:
            for cid, desc, dtype, pri in [
                ("company_ir", "Latest annual report", "annual_report", 1),
                ("company_ir", "Latest quarterly results", "quarterly_report", 1),
                ("nse", "Exchange filings", "exchange_filing", 2),
                ("news", "Latest news", "news", 3),
            ]:
                tasks.append(
                    DiscoveryTask(
                        description=desc,
                        connector_id=cid,
                        query=f"{ud.primary_entity} {desc}",
                        company=ud.companies[0] if ud.companies else None,
                        symbol=ud.primary_entity,
                        document_type=dtype,
                        priority=pri,
                    )
                )
        # de-dupe by connector+description+symbol
        seen = set()
        unique: list[DiscoveryTask] = []
        for task in sorted(tasks, key=lambda x: x.priority):
            key = (task.connector_id, task.description, task.symbol, task.document_type)
            if key in seen:
                continue
            seen.add(key)
            unique.append(task)
        return unique

    def discover(self, query: str, *, aoi: Any | None = None, limit: int = 40) -> tuple[list[DiscoveryTask], list[CandidateDocument]]:
        tasks = self.build_tasks(query, aoi=aoi)
        candidates: list[CandidateDocument] = []
        for task in tasks:
            conn = self.connectors.get(task.connector_id)
            if not conn:
                continue
            try:
                found = conn.discover(task)
            except Exception:
                found = []
            for c in found:
                candidates.append(c)
            if len(candidates) >= limit:
                break
        # de-dupe by URL
        by_url: dict[str, CandidateDocument] = {}
        for c in candidates:
            if c.url and c.url not in by_url:
                by_url[c.url] = c
        return tasks, list(by_url.values())[:limit]
