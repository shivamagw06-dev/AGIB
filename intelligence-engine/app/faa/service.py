"""FAA service facade — acquire public docs and notify FRE."""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.faa.cache import DocumentCache
from app.faa.connectors import build_connectors
from app.faa.connectors.search_api import available_search_providers
from app.faa.flags import FaaFlags
from app.faa.models import FaaMetrics
from app.faa.pipeline import FaaPipeline
from app.faa.scheduler import FaaScheduler


class FaaService:
    """Finance Acquisition Agent — gather/update public data only."""

    def __init__(
        self,
        *,
        flags: FaaFlags | None = None,
        fre: Any | None = None,
        aoi: Any | None = None,
        cache: DocumentCache | None = None,
    ) -> None:
        self.flags = flags or FaaFlags.from_settings(get_settings())
        self.fre = fre
        self.aoi = aoi
        self.cache = cache or DocumentCache()
        self.metrics = FaaMetrics()
        self.scheduler = FaaScheduler()
        self.pipeline = FaaPipeline(
            cache=self.cache,
            fre=fre,
            aoi=aoi,
            live_fetch=self.flags.faa_live_fetch,
            pdf_enabled=self.flags.faa_pdf,
            metrics=self.metrics,
        )
        self.connectors = build_connectors(live_fetch=self.flags.faa_live_fetch)

    def bind(self, **engines: Any) -> None:
        if "fre" in engines:
            self.fre = engines["fre"]
            self.pipeline.bind_fre(self.fre)
        if "aoi" in engines:
            self.aoi = engines["aoi"]
            self.pipeline.aoi = self.aoi

    def _require(self) -> None:
        if not self.flags.faa:
            raise RuntimeError("FAA disabled")

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok" if self.flags.faa else "disabled",
            "layer": "Finance Acquisition Agent",
            "programme": "FAA",
            "version": "faa-v1.0.0",
            "architecture_status": "v1.0.1 LOCKED",
            "position": "upstream_of_fre",
            "does_not_answer": True,
            "never_reasons": True,
            "feeds": ["fre"],
            "no_redesign": ["fre", "aoi", "eve", "cae", "ask_agi"],
            "services": ["discovery", "fetch", "processing", "index"],
            "invariants": [
                "never_answer_user",
                "never_reason",
                "dedupe_by_url_checksum",
                "version_on_change",
                "prefer_authoritative_connectors",
            ],
            "flags": self.flags.as_dict(),
            "live_fetch_enabled": self.flags.faa_live_fetch,
            "search_providers_configured": available_search_providers(),
            "connectors": [c.health() for c in self.connectors.values()],
            "cache": self.cache.snapshot(),
            "metrics": self.metrics.model_dump(),
            "scheduler": self.scheduler.status() if self.flags.faa_scheduler else {},
            "fre_bound": self.fre is not None,
        }

    def dashboard(self) -> dict[str, Any]:
        self._require()
        return {
            "programme": "FAA",
            "architecture_status": "v1.0.1 LOCKED",
            "does_not_answer": True,
            "live_fetch_enabled": self.flags.faa_live_fetch,
            "search_providers_configured": available_search_providers(),
            "metrics": self.metrics.model_dump(),
            "cache": self.cache.snapshot(),
            "scheduler": self.scheduler.status(),
            "connectors": [c.health() for c in self.connectors.values()],
            "recent_urls": list(self.cache.by_url.values())[-30:],
        }

    def acquire(self, q: str, *, limit: int = 24) -> dict[str, Any]:
        """Run full acquisition cycle for a question and index into FRE."""
        self._require()
        result = self.pipeline.acquire_for_query(q, limit=limit)
        self.scheduler.mark_run(
            "query_acquire",
            query=q,
            discovered=result.discovered,
            fetched=result.fetched,
            indexed=result.indexed_to_fre,
            live_fetch=result.live_fetch,
        )
        return {
            "programme": "FAA",
            "architecture_status": "v1.0.1 LOCKED",
            "does_not_answer": True,
            "never_reasons": True,
            **result.to_dict(),
        }

    def discover(self, q: str, *, limit: int = 40) -> dict[str, Any]:
        self._require()
        tasks, candidates = self.pipeline.discovery.discover(q, aoi=self.aoi, limit=limit)
        return {
            "programme": "FAA",
            "query": q,
            "tasks": [t.to_dict() for t in tasks],
            "candidates": [c.to_dict() for c in candidates],
        }

    def connectors_health(self) -> dict[str, Any]:
        return {
            "programme": "FAA",
            "live_fetch_enabled": self.flags.faa_live_fetch,
            "search_providers_configured": available_search_providers(),
            "connectors": [c.health() for c in self.connectors.values()],
        }

    def run_jobs(self) -> dict[str, Any]:
        self._require()
        # Scheduled soft cycles for key universes
        queries = [
            "Reliance Industries filings and annual report",
            "Infosys quarterly results and guidance",
            "RBI monetary policy latest",
        ]
        runs = []
        for q in queries:
            runs.append(self.acquire(q, limit=12))
        self.scheduler.mark_run("scheduled_batch", queries=len(queries))
        return {
            "programme": "FAA",
            "runs": runs,
            "scheduler": self.scheduler.status(),
            "metrics": self.metrics.model_dump(),
        }

    def consult(self, query: str, *, limit: int = 8) -> dict[str, Any]:
        """Soft path for Ask AGI observability — acquisition summary only, never an answer."""
        self._require()
        result = self.acquire(query, limit=max(limit, 12))
        return {
            "programme": "FAA",
            "architecture_status": "v1.0.1 LOCKED",
            "does_not_answer": True,
            "never_reasons": True,
            "query": query,
            "live_fetch": result.get("live_fetch"),
            "discovered": result.get("discovered"),
            "fetched": result.get("fetched"),
            "skipped_cached": result.get("skipped_cached"),
            "indexed_to_fre": result.get("indexed_to_fre"),
            "documents": (result.get("documents") or [])[:limit],
            "errors": result.get("errors") or [],
            "guidance": {
                "enable_live_fetch": "Set FAA_LIVE_FETCH=true on intelligence-engine",
                "optional_search_keys": [
                    "TAVILY_API_KEY",
                    "SERPAPI_API_KEY",
                    "EXA_API_KEY",
                    "BING_SEARCH_API_KEY",
                    "GOOGLE_CSE_API_KEY+GOOGLE_CSE_ID",
                ],
            },
        }
