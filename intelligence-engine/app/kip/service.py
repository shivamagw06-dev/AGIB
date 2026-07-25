"""KIP service facade — institutional knowledge APIs."""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.kip.flags import KipFlags
from app.kip.graph import view_for_entity
from app.kip.models import (
    CompanyKnowledge,
    IngestRequest,
    KipDocument,
    RagEvidencePack,
    ResearchTimeline,
    SearchResponse,
    ThemeKnowledge,
)
from app.kip.pipeline import KipPipeline
from app.kip.rag import build_evidence_pack, research_writer_context
from app.kip.search import search, similar_documents
from app.kip.store import KipStore


class KipService:
    """Knowledge Intelligence Platform — permanent institutional memory of AGI."""

    def __init__(
        self,
        store: KipStore | None = None,
        flags: KipFlags | None = None,
        *,
        embedding_dim: int | None = None,
    ) -> None:
        settings = get_settings()
        self.flags = flags or KipFlags.from_settings(settings)
        self.store = store or KipStore()
        # Prefer compact hashing dim for in-process hybrid search; settings dim reserved for pgvector.
        self.embedding_dim = embedding_dim if embedding_dim is not None else 256
        self.pipeline = KipPipeline(self.store, self.flags, embedding_dim=self.embedding_dim)

    def ingest(self, request: IngestRequest) -> KipDocument:
        self._require_enabled()
        return self.pipeline.ingest(request)

    def get_document(self, document_id: str) -> KipDocument | None:
        self._require_enabled()
        return self.store.get_document(document_id)

    def get_company(self, ticker: str) -> CompanyKnowledge:
        self._require_enabled()
        t = ticker.upper()
        doc_ids = self.store.company_document_ids(t)
        docs = [self.store.get_document(i) for i in doc_ids]
        docs = [d for d in docs if d is not None]
        themes: list[str] = []
        sectors: list[str] = []
        related: list[str] = []
        bull: list[str] = []
        bear: list[str] = []
        risks: list[str] = []
        catalysts: list[str] = []
        latest_thesis = ""
        latest_date = None
        for d in docs:
            for x in d.investment.themes:
                if x not in themes:
                    themes.append(x)
            for x in d.investment.sectors:
                if x not in sectors:
                    sectors.append(x)
            for x in d.investment.tickers:
                if x.upper() != t and x not in related:
                    related.append(x)
            bull.extend(d.research.bull_case)
            bear.extend(d.research.bear_case)
            risks.extend(d.research.risks)
            catalysts.extend(d.research.catalysts)
            if d.research.investment_thesis and (
                latest_date is None or (d.document.date and d.document.date >= latest_date)
            ):
                latest_thesis = d.research.investment_thesis
                latest_date = d.document.date
        timeline = ResearchTimeline(ticker=t, events=self.store.get_timeline(t))
        graph = None
        if self.flags.kip_graph:
            graph = view_for_entity(t, nodes=self.store.nodes, edges=self.store.edges)
        return CompanyKnowledge(
            ticker=t,
            documents=doc_ids,
            themes=themes,
            sectors=sectors,
            related_companies=related,
            latest_thesis=latest_thesis,
            bull_case=_uniq(bull)[:20],
            bear_case=_uniq(bear)[:20],
            risks=_uniq(risks)[:20],
            catalysts=_uniq(catalysts)[:20],
            timeline=timeline,
            graph=graph,
        )

    def get_theme(self, theme_id: str) -> ThemeKnowledge:
        self._require_enabled()
        key = theme_id.lower()
        doc_ids = self.store.theme_document_ids(key)
        tickers: list[str] = []
        related_themes: list[str] = []
        for i in doc_ids:
            d = self.store.get_document(i)
            if d is None:
                continue
            for t in d.investment.tickers:
                if t not in tickers:
                    tickers.append(t)
            for th in d.investment.themes:
                if th.lower() != key and th not in related_themes:
                    related_themes.append(th)
        return ThemeKnowledge(
            theme_id=key,
            theme=theme_id,
            documents=doc_ids,
            tickers=tickers,
            related_themes=related_themes,
        )

    def search(
        self,
        query: str,
        *,
        mode: str = "hybrid",
        limit: int = 10,
        ticker: str | None = None,
        sector: str | None = None,
        theme: str | None = None,
        broker: str | None = None,
    ) -> SearchResponse:
        self._require_enabled()
        return search(
            query,
            documents=self.store.documents,
            chunks=self.store.chunks,
            mode=mode,
            limit=limit,
            ticker=ticker,
            sector=sector,
            theme=theme,
            broker=broker,
            dim=self.embedding_dim,
        )

    def timeline(self, ticker: str) -> ResearchTimeline:
        self._require_enabled()
        return ResearchTimeline(ticker=ticker.upper(), events=self.store.get_timeline(ticker))

    def similar(self, document_id: str, *, limit: int = 10) -> SearchResponse:
        self._require_enabled()
        return similar_documents(
            document_id,
            documents=self.store.documents,
            chunks=self.store.chunks,
            limit=limit,
        )

    def graph(self, entity: str):
        self._require_enabled()
        if not self.flags.kip_graph:
            raise RuntimeError("KIP_GRAPH is disabled")
        return view_for_entity(entity, nodes=self.store.nodes, edges=self.store.edges)

    def rag(
        self,
        query: str,
        *,
        ticker: str | None = None,
        limit: int = 8,
    ) -> RagEvidencePack:
        self._require_enabled()
        if not self.flags.kip_rag:
            raise RuntimeError("KIP_RAG is disabled")
        return build_evidence_pack(
            query,
            documents=self.store.documents,
            chunks=self.store.chunks,
            ticker=ticker,
            limit=limit,
            dim=self.embedding_dim,
        )

    def research_context(self, query: str, *, ticker: str | None = None) -> dict[str, Any]:
        self._require_enabled()
        if not self.flags.kip_rag:
            raise RuntimeError("KIP_RAG is disabled")
        return research_writer_context(
            ticker=ticker,
            query=query,
            documents=self.store.documents,
            chunks=self.store.chunks,
            dim=self.embedding_dim,
        )

    def ingest_research_run(self, run: Any) -> KipDocument | None:
        """Self-learning hook: index completed AGI research into institutional memory."""
        if not self.flags.kip:
            return None
        report = getattr(run, "report", None)
        if report is None:
            return None
        title = getattr(report, "title", None) or f"AGI Research {getattr(run, 'run_id', '')}"
        body_parts = [
            "Investment Thesis",
            getattr(report, "executive_summary", "") or "",
            getattr(run, "cio_thesis", "") or "",
        ]
        for attr, header in (
            ("macro_view", "Macro"),
            ("market_view", "Market"),
            ("sector_view", "Sector"),
            ("company_view", "Company"),
            ("valuation_view", "Valuation"),
        ):
            val = getattr(report, attr, None)
            if val:
                body_parts.append(f"{header}\n{val}")
        findings = getattr(report, "key_findings", None) or []
        if findings:
            body_parts.append("Key Findings\n" + "\n".join(f"- {x}" for x in findings))
        risks = getattr(report, "risks", None) or []
        if risks:
            body_parts.append("Risks\n" + "\n".join(f"- {x}" for x in risks))
        catalysts = getattr(report, "catalysts", None) or []
        if catalysts:
            body_parts.append("Catalysts\n" + "\n".join(f"- {x}" for x in catalysts))
        for case_name in ("bull_case", "bear_case", "base_case"):
            case = getattr(report, case_name, None)
            if case is not None:
                detail = getattr(case, "detail", "") or ""
                label = getattr(case, "label", case_name)
                body_parts.append(f"{case_name.replace('_', ' ').title()}\n- {label}: {detail}")
        content = "\n\n".join(p for p in body_parts if p)
        symbols = list(getattr(run, "symbols", None) or [])
        desk = getattr(getattr(run, "desk", None), "value", None) or str(getattr(run, "desk", "agi"))
        from app.kip.models import DocumentType

        dtype = DocumentType.AGI_RESEARCH
        if "cio" in str(desk).lower():
            dtype = DocumentType.AGI_CIO_REPORT
        elif "brief" in str(desk).lower() or "morning" in str(desk).lower():
            dtype = DocumentType.AGI_DAILY_BRIEF
        req = IngestRequest(
            title=str(title)[:300],
            content=content or str(title),
            author="AGI",
            source="agi",
            document_type=dtype,
            tickers=[str(s).upper() for s in symbols],
            metadata={"run_id": getattr(run, "run_id", None), "desk": desk},
        )
        return self.ingest(req)

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok" if self.flags.kip else "disabled",
            "platform": "KIP",
            "knowledge_version": "kip-v1.0.1",
            "flags": self.flags.as_dict(),
            "stats": self.store.stats(),
            "out_of_scope": [
                "model_fine_tuning",
                "broker_execution",
                "portfolio_management",
                "research_engine_redesign",
            ],
        }

    def _require_enabled(self) -> None:
        if not self.flags.kip:
            raise RuntimeError("KIP is disabled")


def _uniq(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for i in items:
        key = i.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(i.strip())
    return out
