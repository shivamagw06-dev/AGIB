"""UI Aggregation Service — assembles client views from existing platforms."""

from __future__ import annotations

from typing import Any

from app.aws.adapters import dump, soft
from app.core.config import get_settings
from app.kip.models import ClientSearchRequest
from app.ui.flags import UiFlags
from app.ui.models import (
    UI_VERSION,
    CompanyView,
    CopilotView,
    DashboardView,
    HomeView,
    MacroView,
    PortfolioView,
    ResearchView,
    SearchView,
    SectorView,
    ThemeView,
    UiMeta,
    WorkflowView,
)
from app.ui.sanitize import (
    pick_label,
    pick_number,
    public_source,
    scrub,
    scrub_text,
)


class UiService:
    """Client facade. Soft-consumes platforms; never calls engines as a product API."""

    def __init__(
        self,
        flags: UiFlags | None = None,
        *,
        aws: Any | None = None,
        ioc: Any | None = None,
        kip: Any | None = None,
        rsp: Any | None = None,
        rms: Any | None = None,
        cre: Any | None = None,
        validation: Any | None = None,
        aip: Any | None = None,
    ) -> None:
        self.flags = flags or UiFlags.from_settings(get_settings())
        self.aws = aws
        self.ioc = ioc
        self.kip = kip
        self.rsp = rsp
        self.rms = rms
        self.cre = cre
        self.validation = validation
        self.aip = aip

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok" if self.flags.ui else "disabled",
            "layer": "UI Aggregation",
            "ui_version": UI_VERSION,
            "architecture_status": "v1.0.1 LOCKED",
            "exposes_engine_names": False,
            "flags": self.flags.as_dict(),
            "surfaces": [
                "home",
                "company",
                "search",
                "research",
                "theme",
                "sector",
                "dashboard",
                "macro",
                "portfolio",
                "copilot",
                "workflow",
            ],
        }

    def home(self) -> HomeView:
        self._require()
        dash = dump(soft(self.aws.dashboard)) if self.aws else None
        macro = dump(soft(self.aws.macro)) if self.aws else None
        port = dump(soft(self.aws.portfolio)) if self.aws else None
        ioc = dump(soft(self.ioc.dashboard)) if self.ioc else None
        rms = dump(soft(self.rms.dashboard)) if self.rms else None

        regime_state = (macro or {}).get("e01") or (macro or {}).get("market_regime")
        risk_state = (macro or {}).get("e14") or (macro or {}).get("market_risk")
        book = (port or {}).get("l4_book") or (port or {}).get("composite_book") or {}

        composite = {
            "label": "Institutional Composite",
            "n_names": len(book) if isinstance(book, dict) else 0,
            "sample": _sample_book(book),
        }
        market_regime = {
            "label": pick_label(regime_state, "regime", "label", "status") or "Unavailable",
            "detail": scrub(regime_state) or {},
        }
        market_risk = {
            "label": pick_label(risk_state, "risk_level", "label", "status") or "Unavailable",
            "detail": scrub(risk_state) or {},
        }

        todays = list((dash or {}).get("recent_research") or [])[:6]
        published = [
            r
            for r in todays
            if str(r.get("status") or "").lower() in {"published", "approved"}
        ] or todays[:3]

        news = _kip_news(self.kip, "market news india", limit=6)
        themes = _kip_themes(self.kip, limit=8)
        calendar = _event_items(self.aws)
        health = _system_health(ioc, dash)
        queue = list((rms or {}).get("draft_queue") or [])[:8]
        queue += list((rms or {}).get("review_queue") or [])[:8]

        brief = {
            "title": "Today's AGI Market Brief",
            "summary": _brief_summary(market_regime, market_risk, composite),
            "regime": market_regime.get("label"),
            "risk": market_risk.get("label"),
        }

        return HomeView(
            meta=UiMeta(
                surface="home",
                sources=["composite_view", "market_regime", "market_risk", "research_desk", "knowledge", "operations"],
            ),
            market_brief=brief,
            composite_view=composite,
            market_regime=market_regime,
            market_risk=market_risk,
            todays_research=[scrub(r) for r in todays],
            latest_published=[scrub(r) for r in published],
            latest_news=news,
            market_themes=themes,
            economic_calendar=calendar,
            system_health=health,
            research_queue=[scrub({"id": q} if not isinstance(q, dict) else q) for q in queue[:10]],
        )

    def company(self, ticker: str) -> CompanyView:
        self._require()
        t = ticker.upper()
        ws = dump(soft(self.aws.company, t)) if self.aws else None
        ws = ws or {}
        house = scrub(ws.get("house_view")) or {}
        dossier = scrub(ws.get("dossier")) or {}

        overview = {
            "ticker": t,
            "house_view": house.get("current_view") or house.get("stance") or house.get("label"),
            "confidence": house.get("confidence") or pick_number(ws.get("l4_opinion"), "confidence"),
            "investment_thesis": house.get("thesis")
            or dossier.get("latest_thesis")
            or house.get("summary"),
            "last_updated": house.get("updated_at") or house.get("as_of") or dossier.get("updated_at"),
            "composite_label": pick_label(ws.get("l4_opinion"), "label", "side"),
            "composite_score": pick_number(ws.get("l4_opinion"), "composite_score", "score"),
        }

        market_intelligence = {
            "technical_summary": scrub(ws.get("technical")),
            "fundamental_summary": scrub(ws.get("fundamental")),
            "macro_context": scrub(ws.get("macro")),
            "risk_summary": scrub(ws.get("risk")),
            "volatility_summary": scrub(ws.get("volatility")),
            "trend_summary": scrub(ws.get("trend")),
            "event_summary": scrub(ws.get("events")),
            "sentiment_summary": scrub(ws.get("sentiment")),
        }

        research = {
            "latest_agi_articles": scrub(ws.get("agi_articles") or []),
            "broker_research": scrub(ws.get("broker_research") or []),
            "earnings": _filter_docs(ws.get("agi_articles") or [], "earning"),
            "filings": _filter_docs(ws.get("broker_research") or ws.get("agi_articles") or [], "filing"),
            "knowledge_timeline": scrub(_timeline_events(ws.get("research_timeline"))),
        }

        # Evidence via RSP soft reason when available
        evidence = {"supporting_research": [], "conflicting_research": [], "evidence_confidence": None}
        if self.rsp:
            pkg = soft(self.rsp.reason_for_writer, f"{t} institutional view", ticker=t)
            if isinstance(pkg, dict):
                evidence["supporting_research"] = scrub(
                    pkg.get("supporting_documents")
                    or (pkg.get("validation") or {}).get("supporting_documents")
                    or []
                )[:20]
                evidence["conflicting_research"] = scrub(pkg.get("contradictions") or [])[:20]
                evidence["evidence_confidence"] = (pkg.get("validation") or {}).get("confidence")
            else:
                d = dump(pkg) or {}
                evidence["supporting_research"] = scrub(
                    d.get("supporting_documents")
                    or (d.get("validation") or {}).get("supporting_documents")
                    or []
                )[:20]
                evidence["conflicting_research"] = scrub(d.get("contradictions") or [])[:20]
                evidence["evidence_confidence"] = (d.get("validation") or {}).get("confidence")

        if not evidence["supporting_research"]:
            evidence["supporting_research"] = scrub(ws.get("agi_articles") or [])[:10]

        evo = None
        if self.aip:
            evo = soft(self.aip.house_view_evolution, t)
        portfolio = {
            "current_exposure": ws.get("portfolio_weight"),
            "prediction_history": scrub(ws.get("prediction_history") or []),
            "house_view_evolution": scrub(evo) if evo else scrub(_timeline_events(ws.get("research_timeline"))),
        }

        return CompanyView(
            meta=UiMeta(
                surface="company",
                sources=["knowledge", "composite_view", "research_committee", "model_portfolio"],
            ),
            ticker=t,
            overview=overview,
            market_intelligence=market_intelligence,
            research=research,
            evidence=evidence,
            portfolio=portfolio,
        )

    def search(self, question: str, *, ticker: str | None = None) -> SearchView:
        self._require()
        q = (question or "").strip()
        client = None
        if self.kip and q:
            # Attach soft composite / portfolio context without exposing codes
            l4 = None
            port = None
            if ticker and self.aws:
                co = dump(soft(self.aws.company, ticker.upper())) or {}
                l4 = co.get("l4_opinion")
                port = {"weight": co.get("portfolio_weight")}
            req = ClientSearchRequest(
                question=q,
                ticker=ticker.upper() if ticker else None,
                l4_opinion=l4,
                portfolio_exposure=port,
            )
            client = dump(soft(self.kip.client_search, req))

        aws_hits = dump(soft(self.aws.search, q, limit=12)) if self.aws and q else None
        hits = []
        for h in (aws_hits or {}).get("hits") or []:
            hits.append(
                {
                    "kind": h.get("kind"),
                    "id": h.get("id"),
                    "title": scrub_text(h.get("title")),
                    "score": h.get("score"),
                    "ticker": h.get("ticker"),
                    "snippet": scrub_text(h.get("snippet")),
                    "source": public_source(h.get("source")),
                }
            )

        evidence = (client or {}).get("evidence") or {}
        house = scrub((client or {}).get("house_view"))
        conf = None
        if isinstance(evidence, dict):
            conf = evidence.get("confidence_score")
        if conf is None and isinstance(house, dict):
            conf = house.get("confidence")

        supporting = _as_docs(
            evidence.get("agi_research_used")
            or evidence.get("documents_retrieved")
            or []
        )
        news = _as_docs(evidence.get("news_used") or [])
        articles = supporting[:8]
        conflicting = scrub(evidence.get("conflicting_opinions") or [])[:12]
        evidence_used = scrub(
            [
                {"type": "agi_research", "items": evidence.get("agi_research_used") or []},
                {"type": "broker", "items": evidence.get("broker_reports_used") or []},
                {"type": "news", "items": evidence.get("news_used") or []},
                {"type": "filings", "items": evidence.get("filings_used") or []},
                {"type": "model_evidence", "items": evidence.get("engine_evidence") or []},
            ]
        )

        related = []
        if isinstance(house, dict) and house.get("ticker"):
            related.append(str(house["ticker"]))
        for h in hits:
            if h.get("ticker"):
                related.append(str(h["ticker"]))
        related = sorted({r.upper() for r in related})[:12]

        answer = {
            "policy": "evidence_pack_not_direct_advice",
            "summary": _search_answer_summary(q, house, conf, supporting),
            "house_view_label": (house or {}).get("current_view")
            or (house or {}).get("stance")
            or (house or {}).get("label"),
        }

        followups = [
            f"What is the current house view on {related[0]}?" if related else "What is AGI's house view?",
            "What evidence supports this view?",
            "What are the key risks and catalysts?",
            "Show related research and latest news",
        ]

        # Soft RSP enrichment for institutional framing
        if self.rsp and (ticker or related):
            t = (ticker or related[0]).upper()
            soft(self.rsp.reason_for_writer, q or f"{t} search", ticker=t)

        return SearchView(
            meta=UiMeta(
                surface="search",
                sources=["knowledge", "research_committee", "composite_view", "model_portfolio"],
            ),
            question=q,
            intent=(client or {}).get("intent"),
            answer=answer,
            house_view=house,
            confidence=float(conf) if conf is not None else None,
            supporting_research=scrub(supporting)[:12],
            latest_articles=scrub(articles),
            latest_news=scrub(news)[:8] or _kip_news(self.kip, q, limit=5),
            conflicting_opinions=conflicting if isinstance(conflicting, list) else [],
            evidence_used=evidence_used if isinstance(evidence_used, list) else [],
            related_companies=related,
            follow_up_questions=followups,
            hits=hits,
            answer_policy="institutional_evidence_pack",
        )

    def research(self, research_id: str) -> ResearchView:
        self._require()
        ws = dump(soft(self.aws.research, research_id)) if self.aws else None
        ws = ws or {}
        current = scrub(ws.get("current_draft")) or {}
        tickers = list(current.get("tickers") or [])
        themes = list(current.get("themes") or [])
        sectors = list(current.get("sectors") or [])

        related = []
        if self.aws:
            for t in tickers[:3]:
                hits = dump(soft(self.aws.search, t, limit=5)) or {}
                for h in hits.get("hits") or []:
                    if h.get("kind") in {"research", "report"} and h.get("id") != research_id:
                        related.append(
                            {
                                "id": h.get("id"),
                                "title": scrub_text(h.get("title")),
                                "ticker": h.get("ticker"),
                            }
                        )

        news = _kip_news(self.kip, " ".join(tickers) or research_id, limit=5)
        timeline = scrub(_timeline_events(ws.get("research_timeline")))
        preds = []
        if self.kip and tickers:
            for t in tickers[:2]:
                for p in soft(self.kip.predictions, t, default=[]) or []:
                    d = dump(p)
                    if d:
                        preds.append(scrub(d))

        workflow = {
            "status": current.get("status"),
            "review_status": ws.get("review_status"),
            "approval_status": ws.get("approval_status"),
            "publishing_status": ws.get("publishing_status"),
            "stages": _workflow_stages(current.get("status")),
        }

        return ResearchView(
            meta=UiMeta(surface="research", sources=["research_desk", "knowledge", "research_committee"]),
            research_id=research_id,
            article=current,
            related_research=related[:10],
            related_companies=[str(x).upper() for x in tickers],
            related_themes=[str(x) for x in themes],
            related_sectors=[str(x) for x in sectors],
            latest_news=news,
            knowledge_timeline=timeline,
            research_timeline=timeline,
            supporting_evidence=_as_docs(scrub(ws.get("supporting_documents") or []))[:20],
            prediction_tracker=preds[:20],
            workflow=workflow,
        )

    def theme(self, theme_id: str) -> ThemeView:
        self._require()
        ws = dump(soft(self.aws.theme, theme_id)) if self.aws else None
        ws = ws or {}
        theme = scrub(ws.get("theme")) or {}
        docs = _as_docs(scrub(ws.get("documents") or ws.get("search_hits") or []))
        companies = list(ws.get("related_companies") or theme.get("tickers") or [])
        risks = list(theme.get("risks") or [])[:10]
        catalysts = list(theme.get("catalysts") or [])[:10]
        thesis = theme.get("thesis") or theme.get("summary") or theme.get("theme")
        house = None
        if companies and self.kip:
            house = scrub(dump(soft(self.kip.house_view, str(companies[0]).upper())))
        return ThemeView(
            meta=UiMeta(surface="theme", sources=["knowledge"]),
            theme_id=theme_id,
            current_thesis=scrub_text(thesis) if thesis else None,
            related_companies=[str(c).upper() for c in companies],
            related_research=docs[:15],
            current_risks=[scrub_text(str(r)) or "" for r in risks],
            current_catalysts=[scrub_text(str(c)) or "" for c in catalysts],
            house_view=house,
            timeline=_timeline_events(ws.get("knowledge_graph")),
        )

    def sector(self, sector_id: str) -> SectorView:
        self._require()
        ws = dump(soft(self.aws.sector, sector_id)) if self.aws else None
        ws = ws or {}
        coverage = ws.get("company_coverage") or {}
        ranked = sorted(
            ((str(k).upper(), int(v)) for k, v in coverage.items()),
            key=lambda kv: kv[1],
            reverse=True,
        )
        leaders = [k for k, _ in ranked[:5]]
        laggards = [k for k, _ in ranked[-3:]] if len(ranked) > 3 else []
        research = scrub(ws.get("rms_research") or ws.get("documents") or [])[:12]
        health = "Active coverage" if ranked else "Limited coverage"
        return SectorView(
            meta=UiMeta(surface="sector", sources=["knowledge", "research_desk", "model_portfolio"]),
            sector_id=sector_id,
            sector_health=health,
            leaders=leaders,
            laggards=laggards,
            current_theme=sector_id,
            current_risks=[],
            current_research=research if isinstance(research, list) else [],
            valuation_snapshot=scrub(ws.get("portfolio_exposure") or {}),
        )

    def dashboard(self) -> DashboardView:
        self._require()
        home = self.home()
        return DashboardView(
            meta=UiMeta(surface="dashboard", sources=home.meta.sources),
            market_brief=home.market_brief,
            market_regime=home.market_regime,
            market_risk=home.market_risk,
            todays_events=home.economic_calendar,
            research_queue=home.research_queue,
            latest_reports=home.latest_published or home.todays_research,
            system_health=home.system_health,
            sentiment={"themes": home.market_themes[:6]},
        )

    def macro(self) -> MacroView:
        self._require()
        ws = dump(soft(self.aws.macro)) if self.aws else None
        ws = ws or {}
        regime = scrub(ws.get("e01") or ws.get("market_regime") or {})
        risk = scrub(ws.get("e14") or ws.get("market_risk") or {})
        docs = scrub(ws.get("macro_documents") or [])
        themes = list(ws.get("themes") or [])
        events = [
            {"title": t, "category": "theme"}
            for t in themes[:8]
        ]
        events += [
            d
            for d in docs
            if isinstance(d, dict)
            and any(x in str(d.get("title") or "").lower() for x in ("rbi", "fed", "ecb", "central"))
        ][:8]
        return MacroView(
            meta=UiMeta(surface="macro", sources=["market_regime", "market_risk", "knowledge"]),
            current_regime={
                "label": pick_label(regime if isinstance(regime, dict) else None, "regime", "label")
                or "Unavailable",
                "detail": regime if isinstance(regime, dict) else {},
            },
            macro_dashboard={
                "regime": regime,
                "risk": risk,
                "themes": themes,
            },
            regime_history=[],
            macro_timeline=_as_docs(docs)[:15],
            macro_research=_as_docs(docs)[:15],
            central_bank_events=scrub(events)[:10],
            market_risk=risk if isinstance(risk, dict) else {},
        )

    def portfolio(self) -> PortfolioView:
        self._require()
        ws = dump(soft(self.aws.portfolio)) if self.aws else None
        ws = ws or {}
        current = scrub(ws.get("current_portfolio"))
        conf = None
        if isinstance(current, dict):
            conf = pick_number(current, "confidence", "average_confidence")
        book = scrub(ws.get("l4_book") or {})
        return PortfolioView(
            meta=UiMeta(
                surface="portfolio",
                sources=["model_portfolio", "market_risk", "composite_view", "evaluation"],
            ),
            current_portfolio=current,
            historical_portfolio=scrub(ws.get("historical_portfolio") or []),
            sector_allocation=scrub(ws.get("sector_exposure") or {}),
            risk=scrub(ws.get("risk")),
            performance=scrub(ws.get("performance")),
            attribution=scrub(ws.get("attribution")),
            confidence=conf,
            composite_book=book if isinstance(book, dict) else {},
        )

    def copilot(
        self,
        *,
        page: str = "home",
        question: str = "",
        ticker: str | None = None,
        theme_id: str | None = None,
        sector_id: str | None = None,
        research_id: str | None = None,
    ) -> CopilotView:
        self._require()
        raw = (
            dump(
                soft(
                    self.aws.copilot,
                    workspace=_page_to_workspace(page),
                    question=question,
                    ticker=ticker,
                    theme_id=theme_id,
                    sector_id=sector_id,
                    research_id=research_id,
                )
            )
            if self.aws
            else None
        )
        raw = raw or {}
        ctx = {
            "page": page,
            "house_view": scrub(raw.get("house_view")),
            "knowledge": scrub(raw.get("kip")),
            "research_committee": scrub(raw.get("rsp")),
            "composite_view": scrub(raw.get("l4")),
            "portfolio": scrub(raw.get("portfolio")),
            "research": scrub(raw.get("research")),
            "model_evidence": scrub(raw.get("engines") or raw.get("model_evidence") or {}),
            "latest_news": _kip_news(self.kip, question or ticker or page, limit=4),
        }
        return CopilotView(
            meta=UiMeta(surface="copilot", sources=["knowledge", "research_committee", "composite_view"]),
            page=page,
            question=question or f"Assist with {page}",
            context=ctx,
            answer_policy="context_aware_never_empty",
        )

    def workflow(self) -> WorkflowView:
        self._require()
        dash = dump(soft(self.rms.dashboard)) if self.rms else None
        dash = dash or {}
        stages = [
            {"id": "idea", "label": "Idea"},
            {"id": "draft", "label": "Draft"},
            {"id": "review", "label": "Review"},
            {"id": "compliance", "label": "Compliance"},
            {"id": "approval", "label": "Approval"},
            {"id": "published", "label": "Published"},
            {"id": "knowledge_ingested", "label": "Knowledge Ingested"},
            {"id": "prediction_tracking", "label": "Prediction Tracking"},
        ]
        pipeline = []
        for r in soft(self.rms.store.list_all, default=[]) or []:
            pipeline.append(
                {
                    "research_id": r.research_id,
                    "title": scrub_text(r.title),
                    "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                    "tickers": r.tickers,
                    "stages": _workflow_stages(
                        r.status.value if hasattr(r.status, "value") else str(r.status)
                    ),
                }
            )
        return WorkflowView(
            meta=UiMeta(surface="workflow", sources=["research_desk", "knowledge"]),
            stages=stages,
            pipeline=scrub(pipeline)[:40],
            draft_queue=scrub(dash.get("draft_queue") or []),
            review_queue=scrub(dash.get("review_queue") or []),
            published=[
                p for p in pipeline if str(p.get("status")).lower() == "published"
            ][:20],
        )

    def _require(self) -> None:
        if not self.flags.ui:
            raise RuntimeError("UI aggregation disabled (UI=false)")


def _sample_book(book: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    if not isinstance(book, dict):
        return out
    for sym, opinion in list(book.items())[:8]:
        if not isinstance(opinion, dict):
            continue
        out.append(
            {
                "ticker": str(sym).upper(),
                "label": pick_label(opinion, "label", "side") or "Neutral",
                "score": pick_number(opinion, "composite_score", "score"),
                "confidence": pick_number(opinion, "confidence"),
            }
        )
    return out


def _brief_summary(regime: dict, risk: dict, composite: dict) -> str:
    return (
        f"Market regime: {regime.get('label')}. "
        f"Risk level: {risk.get('label')}. "
        f"Composite coverage: {composite.get('n_names', 0)} names."
    )


def _system_health(ioc: dict | None, dash: dict | None) -> dict[str, Any]:
    if ioc:
        return {
            "overall": ioc.get("overall") or ioc.get("status") or "unknown",
            "readiness": ioc.get("readiness") or ioc.get("morning_readiness"),
            "alerts": len(ioc.get("alerts") or []),
            "detail": scrub(
                {
                    k: v
                    for k, v in ioc.items()
                    if k in {"overall", "status", "platforms", "engines", "queues"}
                }
            ),
        }
    if dash:
        return {"overall": "degraded" if not dash.get("platform_health") else "ok", "detail": scrub(dash.get("platform_health"))}
    return {"overall": "unknown"}


def _kip_news(kip: Any, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
    if not kip:
        return []
    sr = soft(kip.search, query or "markets", mode="hybrid", limit=limit)
    if not sr:
        return []
    out = []
    for h in getattr(sr, "hits", []) or []:
        d = dump(h) or {}
        out.append(
            {
                "id": d.get("document_id"),
                "title": scrub_text(d.get("title")),
                "snippet": scrub_text(d.get("snippet")),
                "tickers": d.get("tickers") or [],
                "type": d.get("document_type"),
            }
        )
    return out


def _kip_themes(kip: Any, *, limit: int = 8) -> list[dict[str, Any]]:
    if not kip:
        return []
    # Derive from recent search / store themes if available
    out: list[dict[str, Any]] = []
    store = getattr(kip, "store", None)
    theme_map = getattr(store, "themes", None) if store else None
    if isinstance(theme_map, dict):
        for theme_id in list(theme_map.keys())[:limit]:
            out.append(
                {
                    "id": str(theme_id),
                    "name": scrub_text(str(theme_id).replace("_", " ").title()),
                    "tickers": [],
                }
            )
    if out:
        return out
    # Fallback: scan search hits for theme tags
    sr = soft(kip.search, "theme investment", mode="hybrid", limit=limit)
    for h in getattr(sr, "hits", []) or []:
        d = dump(h) or {}
        for t in d.get("themes") or []:
            out.append({"id": str(t), "name": scrub_text(str(t)), "tickers": d.get("tickers") or []})
        if len(out) >= limit:
            break
    # de-dupe
    seen = set()
    uniq = []
    for row in out:
        key = row.get("id") or row.get("name")
        if key in seen:
            continue
        seen.add(key)
        uniq.append(row)
    return uniq[:limit]


def _event_items(aws: Any) -> list[dict[str, Any]]:
    if not aws:
        return []
    # Soft pull a few symbols' event summaries is too heavy; use macro docs / empty
    return []


def _timeline_events(timeline: Any) -> list[dict[str, Any]]:
    if timeline is None:
        return []
    if isinstance(timeline, list):
        return timeline[:30]
    if isinstance(timeline, dict):
        for key in ("events", "points", "items", "nodes", "entries"):
            if isinstance(timeline.get(key), list):
                return timeline[key][:30]
        return [timeline]
    return []


def _filter_docs(docs: list, needle: str) -> list[dict[str, Any]]:
    out = []
    for d in docs:
        if not isinstance(d, dict):
            continue
        blob = f"{d.get('title')} {d.get('document_type')}".lower()
        if needle in blob:
            out.append(d)
    return out[:10]


def _as_docs(items: Any) -> list[dict[str, Any]]:
    if not items:
        return []
    out = []
    for x in items:
        if isinstance(x, dict):
            out.append(x)
        else:
            out.append({"id": str(x), "title": scrub_text(str(x))})
    return out


def _search_answer_summary(
    question: str,
    house: dict | None,
    confidence: float | None,
    supporting: list,
) -> str:
    if house:
        label = house.get("current_view") or house.get("stance") or house.get("label") or "Under review"
        conf = f" Confidence {confidence:.0%}." if isinstance(confidence, (int, float)) else ""
        return (
            f"Institutional evidence pack for “{question}”. "
            f"Current house view: {label}.{conf} "
            f"{len(supporting)} supporting research items retrieved. "
            "This is not a buy/sell instruction."
        )
    return (
        f"Institutional evidence pack for “{question}”. "
        "House view not yet established for the detected subject. "
        "Review supporting research and conflicting opinions below."
    )


def _workflow_stages(status: str | None) -> list[dict[str, Any]]:
    order = [
        "idea",
        "requested",
        "draft",
        "internal_review",
        "compliance_review",
        "approved",
        "published",
        "ingested",
        "prediction_tracking",
    ]
    aliases = {
        "request": "requested",
        "review": "internal_review",
        "compliance": "compliance_review",
        "approval": "approved",
        "knowledge_ingested": "ingested",
    }
    cur = aliases.get(str(status or "").lower(), str(status or "").lower())
    reached = True
    out = []
    # Map coarse status into pipeline
    status_rank = {
        "idea": 0,
        "requested": 1,
        "draft": 2,
        "internal_review": 3,
        "compliance_review": 4,
        "approved": 5,
        "published": 6,
        "ingested": 7,
        "prediction_tracking": 8,
    }
    rank = status_rank.get(cur, 0)
    labels = {
        "idea": "Idea",
        "requested": "Request",
        "draft": "Draft",
        "internal_review": "Review",
        "compliance_review": "Compliance",
        "approved": "Approval",
        "published": "Published",
        "ingested": "Knowledge Ingested",
        "prediction_tracking": "Prediction Tracking",
    }
    for i, sid in enumerate(order):
        out.append(
            {
                "id": sid,
                "label": labels[sid],
                "state": "done" if i <= rank else "pending",
                "current": i == rank,
            }
        )
    return out


def _page_to_workspace(page: str) -> str:
    p = (page or "home").lower()
    if p in {"company", "sector", "theme", "macro", "portfolio", "research", "replay", "cre"}:
        return p
    if p in {"home", "dashboard", "market"}:
        return "company"
    return "company"
