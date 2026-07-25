"""UI Aggregation Service — assembles client views from existing platforms."""

from __future__ import annotations

from typing import Any

from app.aws.adapters import dump, soft
from app.core.config import get_settings
from app.kip.models import ClientSearchRequest
from app.ui.flags import UiFlags
from app.kip.extractors import KNOWN_TICKERS, TICKER_STOPWORDS
from app.ui.iax import (
    build_charts,
    clean_thesis_text,
    enrich_timeline,
    evidence_items,
    flatten_house_view,
    house_view_card,
    knowledge_graph_view,
    market_intelligence_summary,
    normalize_stance,
    related_ideas,
    research_panel,
    synthesize_thesis_points,
    whats_changed,
)
from app.ui.models import (
    UI_VERSION,
    ArticleView,
    AutocompleteView,
    CompanyView,
    CopilotView,
    DashboardView,
    HomeView,
    MacroView,
    PortfolioView,
    PredictionCentreView,
    ResearchView,
    SearchView,
    SectorView,
    ThemeView,
    TimelineView,
    UiMeta,
    WorkflowView,
)
from app.ui.product import (
    accuracy_summary,
    discovery_pack,
    enrichment_meta,
    macro_intelligence,
    prediction_row,
    sector_intelligence,
    theme_intelligence,
    thesis_status,
)
from app.ui.questions import (
    SEED_QUESTIONS,
    autocomplete as build_autocomplete,
    build_popular_questions,
    follow_up_questions,
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
        irp: Any | None = None,
        kf: Any | None = None,
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
        self.irp = irp
        self.kf = kf

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
                "autocomplete",
                "article",
                "timeline",
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

        from app.ui.home_defaults import (
            DEFAULT_COMPANIES,
            DEFAULT_PREDICTIONS,
            DEFAULT_RESEARCH,
            DEFAULT_THEMES,
            default_calendar,
            default_footer_metrics,
            default_newsletter,
            fill_list,
        )

        regime_state = (macro or {}).get("e01") or (macro or {}).get("market_regime")
        risk_state = (macro or {}).get("e14") or (macro or {}).get("market_risk")
        book = (port or {}).get("l4_book") or (port or {}).get("composite_book") or {}

        composite = {
            "label": "Institutional Composite",
            "n_names": len(book) if isinstance(book, dict) else 0,
            "sample": _sample_book(book),
        }
        market_regime = {
            "label": pick_label(regime_state, "regime", "label", "status") or "Cautious Constructive",
            "detail": scrub(regime_state) or {},
        }
        market_risk = {
            "label": pick_label(risk_state, "risk_level", "label", "status") or "Medium",
            "detail": scrub(risk_state) or {},
        }

        todays = list((dash or {}).get("recent_research") or [])[:6]
        published = [
            r
            for r in todays
            if str(r.get("status") or "").lower() in {"published", "approved"}
        ] or todays[:3]

        news = _kip_news(self.kip, "market news india", limit=6)
        themes = fill_list(_kip_themes(self.kip, limit=8), DEFAULT_THEMES, min_items=6)
        calendar = fill_list(_event_items(self.aws), default_calendar(), min_items=5)
        health = _system_health(ioc, dash)
        queue = list((rms or {}).get("draft_queue") or [])[:8]
        queue += list((rms or {}).get("review_queue") or [])[:8]
        waiting_review = len(queue)

        brief = {
            "title": "Today's AGI Market Brief",
            "summary": _brief_summary(market_regime, market_risk, composite),
            "regime": market_regime.get("label"),
            "risk": market_risk.get("label"),
        }

        research_count = len(todays) or len(DEFAULT_RESEARCH)
        published_today = len(
            [
                r
                for r in todays
                if str(r.get("status") or "").lower() == "published"
            ]
        ) or len(published) or 3
        top_companies = fill_list(list(composite.get("sample") or [])[:8], DEFAULT_COMPANIES, min_items=6)
        if isinstance(composite, dict) and not composite.get("n_names"):
            composite["n_names"] = len(top_companies)
        popular = build_popular_questions(
            themes=themes,
            research=todays,
            calendar=calendar,
            regime_label=market_regime.get("label"),
            risk_label=market_risk.get("label"),
        )
        hero = {
            "headline": "What do I need to know today?",
            "house_view": brief.get("summary"),
            "market_regime": market_regime.get("label"),
            "risk_level": market_risk.get("label"),
            "latest_update": (ioc or {}).get("as_of") or (dash or {}).get("as_of"),
            "research_count": research_count,
            "research_published_today": published_today or len(published),
            "platform_health": (
                health.get("overall")
                if isinstance(health.get("overall"), str)
                else (health.get("overall") or {}).get("status")
                if isinstance(health.get("overall"), dict)
                else health.get("overall")
            )
            or "ok",
        }
        latest_preds: list[dict[str, Any]] = []
        if self.kip:
            # Prefer ticker-scoped predictions, then any store predictions.
            for row in top_companies[:8]:
                tk = str((row or {}).get("ticker") or "").upper()
                if not tk:
                    continue
                for p in soft(self.kip.predictions, tk, default=[]) or []:
                    pr = prediction_row(dump(p), ticker=tk)
                    if pr:
                        latest_preds.append(pr)
                if len(latest_preds) >= 8:
                    break
            if len(latest_preds) < 3:
                store = getattr(self.kip, "store", None)
                all_preds = getattr(store, "predictions", None) if store else None
                if isinstance(all_preds, dict):
                    for tk, rows in list(all_preds.items())[:12]:
                        for p in rows or []:
                            pr = prediction_row(dump(p), ticker=str(tk).upper())
                            if pr:
                                latest_preds.append(pr)
                        if len(latest_preds) >= 8:
                            break
        latest_preds = fill_list(latest_preds, DEFAULT_PREDICTIONS, min_items=5)

        feeds = {
            "latest_research": [scrub(r) for r in published[:6]] or list(DEFAULT_RESEARCH[:4]),
            "most_read": [scrub(r) for r in todays[:6]] or list(DEFAULT_RESEARCH[:4]),
            "trending_companies": top_companies,
            "trending_themes": themes[:8],
            "most_asked_questions": popular[:8],
            "latest_predictions": latest_preds[:8],
            "latest_macro_changes": [
                {"label": market_regime.get("label"), "type": "regime"},
                {"label": market_risk.get("label"), "type": "risk"},
            ],
            "research_published_today": [scrub(r) for r in published[:6]] or list(DEFAULT_RESEARCH[:3]),
        }

        health_label = hero.get("platform_health") or "ok"
        if str(health_label).lower() in {"unknown", "unavailable", "none"}:
            health_label = "Operational"
        leading_theme = (
            (themes[0].get("name") if themes and isinstance(themes[0], dict) else None)
            or "Credit Growth"
        )
        market_bias = (
            "Risk-on selective"
            if "constructive" in str(market_regime.get("label") or "").lower()
            else "Balanced"
        )
        confidence_pct = "68%"
        if isinstance(ioc, dict) and ioc.get("confidence") is not None:
            try:
                c = float(ioc.get("confidence"))
                confidence_pct = f"{int(c * 100 if c <= 1 else c)}%"
            except (TypeError, ValueError):
                pass
        morning_intelligence = {
            "greeting_line": "Here's what the AGI Investment Office believes today.",
            "cards": [
                {
                    "id": "house_view",
                    "label": "Today's House View",
                    "value": brief.get("summary")
                    or f"{market_regime.get('label')} with {market_risk.get('label')} risk — stay selective.",
                },
                {"id": "confidence", "label": "Current Confidence", "value": confidence_pct},
                {
                    "id": "market_regime",
                    "label": "Current Market Regime",
                    "value": market_regime.get("label") or "Cautious Constructive",
                },
                {
                    "id": "risk_level",
                    "label": "Current Risk Level",
                    "value": market_risk.get("label") or "Medium",
                },
                {
                    "id": "research_today",
                    "label": "Research Published Today",
                    "value": str(hero.get("research_published_today") or published_today or 3),
                },
                {
                    "id": "research_review",
                    "label": "Research Waiting Review",
                    "value": str(waiting_review or 2),
                },
                {
                    "id": "platform_health",
                    "label": "Platform Health",
                    "value": str(health_label).replace("_", " ").title(),
                },
                {
                    "id": "last_updated",
                    "label": "Last Updated",
                    "value": str(hero.get("latest_update") or "Just now")[:19].replace("T", " "),
                },
                {"id": "current_theme", "label": "Current Theme", "value": str(leading_theme)},
                {"id": "market_bias", "label": "Current Market Bias", "value": market_bias},
            ],
        }

        knowledge_feed: list[dict[str, Any]] = []
        for r in published[:4]:
            if isinstance(r, dict):
                knowledge_feed.append(
                    {
                        "type": "research",
                        "title": scrub_text(r.get("title") or "Research update"),
                        "as_of": r.get("updated_at") or r.get("as_of") or r.get("published_at"),
                        "href": f"/article/{r.get('research_id') or r.get('id')}"
                        if (r.get("research_id") or r.get("id"))
                        else "/research",
                    }
                )
        knowledge_feed.append(
            {
                "type": "house_view",
                "title": f"House view · regime {market_regime.get('label')}",
                "as_of": hero.get("latest_update") or _iso_now(),
                "href": "/ask",
            }
        )
        for p in latest_preds[:3]:
            knowledge_feed.append(
                {
                    "type": "prediction",
                    "title": scrub_text(p.get("thesis") or f"Prediction · {p.get('ticker')}"),
                    "as_of": p.get("publication_date") or _iso_now(),
                    "href": "/predictions",
                }
            )
        for n in news[:3]:
            if isinstance(n, dict) and n.get("title"):
                knowledge_feed.append(
                    {
                        "type": "knowledge",
                        "title": scrub_text(n.get("title")),
                        "as_of": n.get("date") or n.get("published_at") or _iso_now(),
                        "href": "/research",
                    }
                )
        for ev in calendar[:3]:
            if isinstance(ev, dict) and (ev.get("title") or ev.get("name")):
                knowledge_feed.append(
                    {
                        "type": "calendar",
                        "title": scrub_text(ev.get("title") or ev.get("name")),
                        "as_of": ev.get("as_of") or ev.get("date") or _iso_now(),
                        "href": "/macro-intelligence",
                    }
                )
        if len(knowledge_feed) < 6:
            for r in DEFAULT_RESEARCH:
                knowledge_feed.append(
                    {
                        "type": "research",
                        "title": r["title"],
                        "as_of": r.get("as_of") or _iso_now(),
                        "href": r.get("href") or "/research",
                    }
                )

        featured = []
        for r in (published or todays)[:6]:
            if not isinstance(r, dict):
                continue
            featured.append(
                {
                    "id": r.get("research_id") or r.get("id"),
                    "title": scrub_text(r.get("title")),
                    "category": (r.get("sectors") or ["Research"])[0]
                    if isinstance(r.get("sectors"), list) and r.get("sectors")
                    else "Research",
                    "summary": scrub_text(r.get("summary") or r.get("request_brief") or r.get("title")),
                    "as_of": r.get("updated_at") or r.get("as_of") or _iso_now(),
                    "read_time": r.get("read_time") or "5 min",
                    "house_view": r.get("house_view") or market_regime.get("label"),
                    "tickers": r.get("tickers") or [],
                    "href": f"/article/{r.get('research_id') or r.get('id')}"
                    if (r.get("research_id") or r.get("id"))
                    else "/research",
                }
            )
        featured = fill_list(featured, DEFAULT_RESEARCH, min_items=4)

        sector_rows = []
        for th in themes[:8]:
            if isinstance(th, dict):
                sector_rows.append(
                    {
                        "name": th.get("name") or th.get("id"),
                        "bias": th.get("bias") or th.get("trend") or "Watch",
                        "change": th.get("change") or th.get("score") or th.get("confidence"),
                    }
                )
        if not sector_rows:
            sector_rows = [
                {"name": t["name"], "bias": t.get("bias") or t.get("trend"), "change": t.get("confidence")}
                for t in DEFAULT_THEMES[:8]
            ]
        market_dashboard = {
            "tabs": ["Heatmap", "Breadth", "Flows", "Market Health"],
            "heatmap": sector_rows,
            "breadth": {
                "advancers": composite.get("n_names") or len(top_companies) or 12,
                "coverage": len(top_companies) or 8,
                "label": market_regime.get("label"),
            },
            "flows": {
                "note": "FII/DII context updates with portfolio coverage — domestic institutions remain constructive on banks and defence.",
                "fii": "Mixed",
                "dii": "Supportive",
            },
            "market_health": {
                "regime": market_regime.get("label"),
                "risk": market_risk.get("label"),
                "platform": health_label,
            },
            "top_movers": [c for c in top_companies if str(c.get("label") or "").lower() in {"overweight", "bullish", "constructive"}][:5]
            or top_companies[:5],
            "top_losers": [c for c in top_companies if str(c.get("label") or "").lower() in {"underweight", "bearish", "cautious"}][:5],
        }

        graph_nodes = 0
        if self.kip:
            try:
                graph_nodes = len(themes) + len(top_companies) + len(todays) + len(news)
            except Exception:
                graph_nodes = len(themes) + len(top_companies)
        footer_base = default_footer_metrics()
        footer_metrics = {
            "research_coverage": len(todays) or research_count or footer_base["research_coverage"],
            "companies_covered": len(top_companies) or composite.get("n_names") or footer_base["companies_covered"],
            "predictions": len(latest_preds) or footer_base["predictions"],
            "research_articles": len(published) or len(todays) or footer_base["research_articles"],
            "knowledge_nodes": graph_nodes or footer_base["knowledge_nodes"],
            "data_points": max(
                (len(todays) + len(news) + len(calendar) + len(latest_preds)) * 12,
                footer_base["data_points"],
            ),
            "research_since": "2024",
            "broker_reports": footer_base["broker_reports"],
            "themes": len(themes) or footer_base["themes"],
            "sectors": footer_base["sectors"],
            "knowledge_documents": footer_base["knowledge_documents"],
        }
        newsletter = default_newsletter()
        newsletter["research_published"] = footer_metrics["research_articles"]

        return HomeView(
            meta=UiMeta(
                surface="home",
                sources=["composite_view", "market_regime", "market_risk", "research_desk", "knowledge", "operations"],
            ),
            market_brief=brief,
            composite_view=composite,
            market_regime=market_regime,
            market_risk=market_risk,
            todays_research=[scrub(r) for r in todays] or list(DEFAULT_RESEARCH),
            latest_published=[scrub(r) for r in published] or list(DEFAULT_RESEARCH),
            latest_news=news,
            market_themes=themes,
            economic_calendar=calendar,
            system_health=health,
            research_queue=[scrub({"id": q} if not isinstance(q, dict) else q) for q in queue[:10]],
            hero=hero,
            popular_questions=popular,
            feeds=feeds,
            top_companies=top_companies,
            ask_placeholder=(
                "Ask AGI anything about markets, companies, investments, themes, "
                "macroeconomics, valuation or research..."
            ),
            example_questions=[s["question"] for s in SEED_QUESTIONS],
            morning_intelligence=morning_intelligence,
            knowledge_feed=knowledge_feed[:16],
            featured_research=featured,
            market_dashboard=market_dashboard,
            footer_metrics=footer_metrics,
            newsletter=newsletter,
            market_snapshot=[],
            market_session={"status": "live", "label": "Market session"},
        )

    def calendar(self) -> dict[str, Any]:
        """Thin calendar surface for Investment Office homepage."""
        home = self.home()
        return {
            "meta": UiMeta(surface="calendar", sources=["knowledge", "operations"]).model_dump(),
            "events": home.economic_calendar,
            "today": home.economic_calendar[:6],
            "tomorrow": home.economic_calendar[6:12],
            "week": home.economic_calendar[:20],
        }

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
            "whats_changed": list(house.get("thesis_evolution") or house.get("changed_assumptions") or [])[:8],
            "current_risks": list(house.get("risks") or house.get("failed_assumptions") or [])[:8],
            "current_catalysts": list(house.get("catalysts") or house.get("catalysts_occurred") or [])[:8],
            "bull_case": list(house.get("bull_case") or [])[:6],
            "bear_case": list(house.get("bear_case") or [])[:6],
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
        pred_hist = scrub(ws.get("prediction_history") or [])
        if self.kip and not pred_hist:
            for p in soft(self.kip.predictions, t, default=[]) or []:
                pr = prediction_row(dump(p), ticker=t)
                if pr:
                    pred_hist.append(pr)
        portfolio = {
            "current_exposure": ws.get("portfolio_weight"),
            "prediction_history": pred_hist[:12],
            "house_view_evolution": scrub(evo) if evo else scrub(_timeline_events(ws.get("research_timeline"))),
        }

        graph_raw = ws.get("knowledge_graph")
        if graph_raw is None and self.kip:
            graph_raw = dump(soft(self.kip.graph, t))
        kg = knowledge_graph_view(graph_raw if isinstance(graph_raw, dict) else None, t)
        themes = list((house or {}).get("themes") or [])[:6]
        sectors = list((house or {}).get("sectors") or [])[:4]
        followups = follow_up_questions(
            question=f"What is AGI's view on {t}?",
            intent="company",
            related_companies=[t],
            related_themes=themes,
            house_label=str(overview.get("house_view") or ""),
            risks=list(overview.get("current_risks") or []),
            catalysts=list(overview.get("current_catalysts") or []),
            knowledge_graph=kg,
        )
        related_cos = [str(x).upper() for x in (kg.get("buckets") or {}).get("related_companies", [])][:8]
        valuation = scrub(ws.get("valuation") or dossier.get("valuation") or {})
        meta = enrichment_meta(
            last_updated=overview.get("last_updated"),
            freshness_score=(ws.get("freshness") or {}).get("score")
            if isinstance(ws.get("freshness"), dict)
            else ws.get("freshness_score"),
            evidence_count=len(evidence.get("supporting_research") or [])
            + len(evidence.get("conflicting_research") or []),
            research_count=len(research.get("latest_agi_articles") or []),
        )
        overview["freshness_indicator"] = meta["freshness_indicator"]
        overview["evidence_count"] = meta["evidence_count"]
        overview["research_count"] = meta["research_count"]

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
            valuation_snapshot=valuation if isinstance(valuation, dict) else {},
            product_meta=meta,
            discovery=discovery_pack(
                companies=[t] + related_cos,
                themes=themes,
                sectors=sectors,
                research=research.get("latest_agi_articles") or [],
                questions=followups,
            ),
            follow_up_questions=followups,
            knowledge_graph=kg,
            prediction_timeline=pred_hist[:12],
        )

    def search(self, question: str, *, ticker: str | None = None) -> SearchView:
        self._require()
        q = (question or "").strip()
        client = None
        detected_ticker = ticker.upper() if ticker else None
        rsp_pkg: dict[str, Any] = {}
        irp_pkg = None
        irp_dump: dict[str, Any] = {}

        # KF1 — resolve knowledge objects before document retrieval (soft enrichment).
        kf_hits: list[dict[str, Any]] = []
        if self.kf and q:
            try:
                kf_search = dump(soft(self.kf.search, q, limit=8)) or {}
                kf_hits = list(kf_search.get("hits") or []) if isinstance(kf_search, dict) else []
                if not detected_ticker:
                    for hit in kf_hits:
                        if isinstance(hit, dict) and hit.get("kind") == "company" and hit.get("key"):
                            detected_ticker = str(hit["key"]).upper()
                            break
            except Exception:
                kf_hits = []

        # IRP V1 — think (intent → entities → plan → retrieve → reason) before answering.
        if self.irp and q:
            try:
                irp_pkg = soft(self.irp.run, q, ticker=detected_ticker)
                irp_dump = dump(irp_pkg) if irp_pkg is not None else {}
                if isinstance(irp_dump, dict) and irp_dump:
                    client = irp_dump.get("client_search") or {}
                    rsp_pkg = irp_dump.get("rsp") or {}
                    ents = irp_dump.get("entities") or {}
                    if not detected_ticker and isinstance(ents, dict) and ents.get("primary_ticker"):
                        detected_ticker = str(ents["primary_ticker"]).upper()
            except Exception:
                irp_pkg = None
                irp_dump = {}

        if self.kip and q and not client:
            l4 = None
            port = None
            if detected_ticker and self.aws:
                co = dump(soft(self.aws.company, detected_ticker)) or {}
                l4 = co.get("l4_opinion")
                port = {"weight": co.get("portfolio_weight")}
            req = ClientSearchRequest(
                question=q,
                ticker=detected_ticker,
                l4_opinion=l4,
                portfolio_exposure=port,
            )
            client = dump(soft(self.kip.client_search, req))
            if not detected_ticker and isinstance(client, dict):
                hv = client.get("house_view") or {}
                if hv.get("ticker"):
                    detected_ticker = str(hv["ticker"]).upper()

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
        house = flatten_house_view(scrub((client or {}).get("house_view")))
        if isinstance(house, dict) and house.get("ticker"):
            tkr = str(house["ticker"]).upper()
            # Sector synthetic subjects (e.g. INDIA_IT) are not company tickers.
            if "_" not in tkr and tkr not in TICKER_STOPWORDS and (
                tkr in KNOWN_TICKERS or tkr.endswith("BANK")
            ):
                if not detected_ticker:
                    detected_ticker = tkr

        conf = None
        if isinstance(evidence, dict):
            conf = evidence.get("confidence_score")
        if conf is None and isinstance(house, dict):
            conf = house.get("confidence") or house.get("research_confidence")

        # Soft RSP reasoning package for thesis / bull / bear / risks
        # (skipped when IRP already ran the Research Committee pass)
        if not rsp_pkg and self.rsp and detected_ticker:
            raw = soft(self.rsp.reason_for_writer, q or f"{detected_ticker} search", ticker=detected_ticker)
            rsp_pkg = dump(raw) if raw is not None and not isinstance(raw, dict) else (raw or {})
            if not isinstance(rsp_pkg, dict):
                rsp_pkg = {}
            rsp_pkg = scrub(rsp_pkg) or {}
        elif rsp_pkg:
            rsp_pkg = scrub(rsp_pkg) or {}

        # Prefer IRP-ranked evidence, then rich RAG items, then raw document id lists.
        irp_ranked = []
        if isinstance(irp_dump, dict):
            irp_ranked = [
                {
                    "id": r.get("document_id"),
                    "document_id": r.get("document_id"),
                    "title": r.get("title"),
                    "snippet": r.get("snippet"),
                    "summary": r.get("snippet"),
                    "tickers": r.get("tickers") or [],
                    "stance": r.get("stance"),
                    "confidence": r.get("confidence"),
                    "freshness": r.get("freshness"),
                    "type": r.get("source_class") or "agi_research",
                    "source_class": r.get("source_class") or "agi_research",
                }
                for r in (irp_dump.get("ranked_evidence") or [])
                if isinstance(r, dict) and not r.get("rejected")
            ]
        supporting = _filter_junk_docs(
            self._hydrate_evidence(
                _evidence_dicts(
                    irp_ranked
                    or evidence.get("supporting_evidence")
                    or evidence.get("agi_research_used")
                    or evidence.get("documents_retrieved")
                    or []
                )
            )
        )
        news = _filter_junk_docs(self._hydrate_evidence(_evidence_dicts(evidence.get("news_used") or [])))
        articles = supporting[:8]
        irp_conflicts = []
        if isinstance(irp_dump, dict):
            for c in irp_dump.get("contradictions") or []:
                if not isinstance(c, dict):
                    continue
                irp_conflicts.append(
                    {
                        "title": c.get("topic") or "Research disagreement",
                        "summary": c.get("summary"),
                        "snippet": c.get("why") or c.get("summary"),
                        "type": "conflict",
                        "confidence": c.get("confidence"),
                    }
                )
        conflicting = _filter_junk_docs(
            self._hydrate_evidence(
                scrub(irp_conflicts or evidence.get("conflicting_opinions") or [])[:12]
            )
        )
        if not conflicting and isinstance(rsp_pkg.get("contradictions"), list):
            conflicting = scrub(rsp_pkg.get("contradictions") or [])[:12]

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
        related_themes: list[str] = []
        related_sectors: list[str] = []
        irp_entities = (irp_dump or {}).get("entities") if isinstance(irp_dump, dict) else {}
        if isinstance(irp_entities, dict):
            related.extend([str(t) for t in (irp_entities.get("tickers") or [])])
            related_themes.extend([str(t) for t in (irp_entities.get("themes") or [])])
            if irp_entities.get("sector"):
                related_sectors.append(str(irp_entities.get("sector")))
            if irp_entities.get("sector_label"):
                related_sectors.append(str(irp_entities.get("sector_label")))
        for hit in kf_hits:
            if not isinstance(hit, dict):
                continue
            kind = str(hit.get("kind") or "")
            key = str(hit.get("key") or "")
            if kind == "company" and key:
                related.append(key.upper())
            elif kind == "theme" and key:
                related_themes.append(key)
            elif kind == "sector" and key:
                related_sectors.append(str(hit.get("label") or key))
        if isinstance(house, dict):
            related_themes.extend([str(x) for x in (house.get("themes") or [])])
            related_sectors.extend([str(x) for x in (house.get("sectors") or [])])
        for item in supporting:
            if not isinstance(item, dict):
                continue
            for t in item.get("tickers") or []:
                related.append(str(t))
        for h in hits:
            if h.get("ticker"):
                related.append(str(h["ticker"]))
            if h.get("kind") == "theme" and h.get("id"):
                related_themes.append(str(h["id"]))
        related = sorted(
            {
                r.upper()
                for r in related
                if r
                and str(r).upper() not in TICKER_STOPWORDS
                and (str(r).upper() in KNOWN_TICKERS or str(r).upper().endswith("BANK"))
            }
        )[:12]
        related_themes = sorted({t for t in related_themes if t})[:8]
        related_sectors = sorted({s for s in related_sectors if s})[:8]

        house_label = None
        if isinstance(house, dict) and house:
            house_label = normalize_stance(
                house.get("stance") or house.get("current_view_label") or house.get("label")
            )

        thesis = None
        bull: list[str] = []
        bear: list[str] = []
        risks: list[str] = []
        catalysts: list[str] = []
        if isinstance(house, dict) and house:
            thesis = clean_thesis_text(house.get("thesis") or house.get("summary"))
            bull = [str(x) for x in (house.get("bull_case") or [])][:6]
            bear = [str(x) for x in (house.get("bear_case") or [])][:6]
            risks = [str(x) for x in (house.get("risks") or house.get("failed_assumptions") or [])][:6]
            catalysts = [str(x) for x in (house.get("catalysts") or house.get("catalysts_occurred") or [])][:6]
            # Pull risks / catalysts from the latest source document backing the house view.
            cv = house.get("current_view")
            doc_id = cv.get("document_id") if isinstance(cv, dict) else None
            if self.kip and doc_id and (not risks or not catalysts or not bull or not bear or not thesis):
                src = soft(self.kip.get_document, doc_id)
                research = getattr(src, "research", None) if src is not None else None
                if research is not None:
                    if not bull:
                        bull = [str(x) for x in (research.bull_case or [])][:6]
                    if not bear:
                        bear = [str(x) for x in (research.bear_case or [])][:6]
                    if not risks:
                        risks = [str(x) for x in (research.risks or [])][:6]
                    if not catalysts:
                        catalysts = [str(x) for x in (research.catalysts or [])][:6]
                    if not thesis and research.investment_thesis:
                        thesis = clean_thesis_text(research.investment_thesis)
        # Fill thesis fields from strongest supporting evidence when house view is thin.
        if not thesis:
            for item in supporting:
                if isinstance(item, dict) and (item.get("snippet") or item.get("summary") or item.get("title")):
                    thesis = clean_thesis_text(
                        item.get("snippet") or item.get("summary") or item.get("title")
                    )
                    break
        if thesis and (not bull or not bear or not risks or not catalysts):
            synthesized = synthesize_thesis_points(thesis)
            if not bull:
                bull = synthesized["bull_case"]
            if not bear:
                bear = synthesized["bear_case"]
            if not risks:
                risks = synthesized["risks"]
            if not catalysts:
                catalysts = synthesized["catalysts"]
        if not bear:
            for item in supporting + conflicting:
                if isinstance(item, dict) and str(item.get("stance") or "").lower() == "bear":
                    snip = clean_thesis_text(item.get("snippet") or item.get("summary"))
                    if snip:
                        bear.append(snip[:220])
                if len(bear) >= 3:
                    break
        # IRP reasoning wins when present — this is the institutional think-step.
        irp_reasoning = (irp_dump or {}).get("reasoning") if isinstance(irp_dump, dict) else None
        if isinstance(irp_reasoning, dict) and irp_reasoning:
            thesis = clean_thesis_text(irp_reasoning.get("what_is_happening") or thesis) or thesis
            bull = [str(x) for x in (irp_reasoning.get("bull_case") or bull)][:6]
            bear = [str(x) for x in (irp_reasoning.get("bear_case") or bear)][:6]
            risks = [str(x) for x in (irp_reasoning.get("risks") or risks)][:6]
            catalysts = [str(x) for x in (irp_reasoning.get("catalysts") or catalysts)][:6]
            house_label = normalize_stance(irp_reasoning.get("stance") or house_label)
            if isinstance(house, dict):
                house = dict(house)
                house["stance"] = house_label
                house["label"] = house_label
                house["current_view_label"] = house_label
                house["thesis"] = thesis
                if irp_reasoning.get("confidence") is not None:
                    house["confidence"] = irp_reasoning.get("confidence")
                    conf = irp_reasoning.get("confidence")

        # Recompute stance from the cleaned thesis so "bull_case" field names cannot flip Bullish.
        if thesis and not (isinstance(irp_reasoning, dict) and irp_reasoning.get("stance")):
            house_label = normalize_stance(
                {"thesis": thesis, "bull_case": bull, "bear_case": bear}
            )
            if isinstance(house, dict) and house:
                house["stance"] = house_label
                house["label"] = house_label
                house["current_view_label"] = house_label
                house["thesis"] = thesis
        # RSP enrichment — never let a noisy research_brief overwrite a real AGI thesis.
        synth = rsp_pkg.get("synthesis") if isinstance(rsp_pkg.get("synthesis"), dict) else rsp_pkg
        if isinstance(synth, dict):
            rsp_thesis = clean_thesis_text(synth.get("thesis") or "")
            rsp_brief = clean_thesis_text(synth.get("research_brief") or "")
            if not thesis and rsp_thesis:
                thesis = rsp_thesis
            elif not thesis and rsp_brief and "research brief —" not in rsp_brief.lower():
                thesis = rsp_brief
            bull = bull or [str(x) for x in (synth.get("bull_case") or [])][:6]
            bear = bear or [str(x) for x in (synth.get("bear_case") or [])][:6]
            risks = risks or [str(x) for x in (synth.get("risks") or [])][:6]
            catalysts = catalysts or [str(x) for x in (synth.get("catalysts") or [])][:6]
            if thesis and isinstance(house, dict) and house:
                house["thesis"] = thesis
                house_label = normalize_stance(
                    {"thesis": thesis, "bull_case": bull, "bear_case": bear}
                )
                house["stance"] = house_label
                house["label"] = house_label
                house["current_view_label"] = house_label

        executive = _search_answer_summary(
            q,
            house if isinstance(house, dict) else None,
            conf,
            supporting,
            house_label=house_label,
        )
        why = _why_bullets(house if isinstance(house, dict) else None, supporting, news, house_label)

        timeline: list[dict[str, Any]] = []
        if detected_ticker and self.kip:
            timeline = scrub(_timeline_events(dump(soft(self.kip.timeline, detected_ticker))))[:20]

        freshness = {
            "score": evidence.get("freshness_score") if isinstance(evidence, dict) else None,
            "last_updated": evidence.get("last_updated") if isinstance(evidence, dict) else None,
            "knowledge_version": evidence.get("knowledge_version") if isinstance(evidence, dict) else None,
        }
        last_updated = freshness.get("last_updated")
        if isinstance(house, dict):
            last_updated = last_updated or house.get("updated_at") or house.get("as_of")

        # Follow-ups assembled after IAX graph/evidence enrichment below.
        followups: list[str] = []

        answer = {
            "policy": "evidence_pack_not_direct_advice",
            "summary": executive,
            "house_view_label": house_label,
            "executive_summary": executive,
            "investment_thesis": scrub_text(thesis) if thesis else None,
            "bull_case": bull,
            "bear_case": bear,
            "key_risks": risks,
            "key_catalysts": catalysts,
            "why": why,
        }

        recommendations = {
            "related_research": scrub(articles)[:6],
            "related_companies": related[:6],
            "related_themes": related_themes[:6],
            "related_articles": scrub(articles)[:6],
            "related_questions": followups[:6],
        }

        # --- IAX enrichment ---
        company_ws = dump(soft(self.aws.company, detected_ticker)) if self.aws and detected_ticker else None
        company_ws = company_ws or {}
        prior_house = None
        if isinstance(house, dict):
            hist = house.get("historical_views") or house.get("history") or []
            if isinstance(hist, list) and hist:
                prior_house = scrub(hist[0] if isinstance(hist[0], dict) else None)
        if prior_house is None and detected_ticker and self.aip:
            evo = soft(self.aip.house_view_evolution, detected_ticker)
            evo_d = dump(evo) if evo is not None else None
            points = (evo_d or {}).get("points") or []
            if len(points) >= 2:
                prior_house = {
                    "label": points[-2].get("label"),
                    "current_view": points[-2].get("label"),
                    "confidence": points[-2].get("confidence"),
                }

        hv_card = house_view_card(house if isinstance(house, dict) else None, conf)
        changed = whats_changed(
            house=house if isinstance(house, dict) else None,
            prior_house=prior_house if isinstance(prior_house, dict) else None,
            conf=float(conf) if conf is not None else None,
            prior_conf=float(prior_house["confidence"])
            if isinstance(prior_house, dict) and prior_house.get("confidence") is not None
            else None,
            thesis=thesis,
        )

        broker_docs = evidence_items(
            _as_docs((company_ws.get("broker_research") or [])[:10]),
            default_type="broker",
        )
        filing_docs = evidence_items(
            [
                d
                for d in _as_docs(company_ws.get("agi_articles") or [])
                if "filing" in str(d.get("document_type") or d.get("title") or "").lower()
            ],
            default_type="filing",
        )
        earning_docs = evidence_items(
            [
                d
                for d in _as_docs(company_ws.get("agi_articles") or [])
                if "earn" in str(d.get("document_type") or d.get("title") or "").lower()
            ],
            default_type="earnings",
        )
        support_ev = evidence_items(scrub(supporting)[:12], default_type="agi_research")
        conflict_ev = evidence_items(
            conflicting if isinstance(conflicting, list) else [],
            default_type="conflict",
        )
        if not support_ev:
            support_ev = evidence_items(scrub(articles)[:8], default_type="agi_research")

        preds = []
        if detected_ticker and self.kip:
            for p in soft(self.kip.predictions, detected_ticker, default=[]) or []:
                d = dump(p)
                if d:
                    preds.append(scrub(d))

        graph_raw = company_ws.get("knowledge_graph")
        if graph_raw is None and detected_ticker and self.kip:
            graph_raw = dump(soft(self.kip.graph, detected_ticker))
        kg = knowledge_graph_view(graph_raw if isinstance(graph_raw, dict) else None, detected_ticker)

        if isinstance(irp_dump, dict) and irp_dump.get("follow_ups"):
            followups = [str(x) for x in irp_dump.get("follow_ups") or [] if x][:8]
        else:
            followups = follow_up_questions(
                question=q,
                intent=(irp_dump or {}).get("intent") or (client or {}).get("intent"),
                related_companies=related,
                related_themes=related_themes,
                house_label=str(house_label) if house_label else None,
                risks=risks,
                catalysts=catalysts,
                knowledge_graph=kg,
                recent_research_titles=[
                    str(a.get("title"))
                    for a in (articles or [])[:4]
                    if isinstance(a, dict) and a.get("title")
                ],
            )
        recommendations["related_questions"] = followups[:6]

        timeline_enriched = enrich_timeline(timeline if isinstance(timeline, list) else [])
        # merge news into timeline
        for n in (news or [])[:8]:
            if isinstance(n, dict):
                timeline_enriched.append(
                    {
                        "as_of": n.get("date") or n.get("published_at"),
                        "type": "news",
                        "title": scrub_text(n.get("title")),
                        "summary": scrub_text(n.get("snippet")),
                        "source": "knowledge",
                    }
                )
        timeline_enriched = enrich_timeline(timeline_enriched)

        mi = market_intelligence_summary(company_ws)
        chart_subject = detected_ticker
        if not chart_subject and isinstance(irp_entities, dict):
            chart_subject = irp_entities.get("sector_key") or irp_entities.get("sector_label")
        charts = build_charts(ticker=chart_subject, predictions=preds, timeline=timeline_enriched)
        ideas = related_ideas(
            related_companies=related,
            related_sectors=related_sectors,
            related_themes=related_themes,
            stance=hv_card.get("stance"),
        )

        port_ctx: dict[str, Any] = {}
        if self.aws:
            port = dump(soft(self.aws.portfolio)) or {}
            weight = company_ws.get("portfolio_weight")
            port_ctx = {
                "current_exposure": weight,
                "sector_allocation": scrub(port.get("sector_exposure") or {}),
                "theme_allocation": related_themes[:6],
                "position_history": scrub(port.get("historical_portfolio") or [])[:5],
                "note": "Model portfolio context — not a recommendation to trade.",
            }

        regime_label = None
        macro = dump(soft(self.aws.macro)) if self.aws else None
        if isinstance(macro, dict):
            regime_label = pick_label(macro.get("e01") or macro.get("market_regime"), "regime", "label")

        freshness_score = freshness.get("score")
        if isinstance(freshness_score, (int, float)):
            freshness_indicator = (
                "fresh" if freshness_score >= 0.7 else "aging" if freshness_score >= 0.4 else "stale"
            )
        else:
            freshness_indicator = "unknown"

        briefing = (irp_dump or {}).get("institutional_briefing") if isinstance(irp_dump, dict) else {}
        if not isinstance(briefing, dict):
            briefing = {}
        neutral_case = list(briefing.get("neutral_case") or [])
        if not neutral_case:
            if hv_card.get("stance") == "Neutral":
                neutral_case = ["Wait for clearer catalysts before increasing conviction."]
            elif risks and catalysts:
                neutral_case = [
                    "Balance catalysts against listed risks; position sizing remains discretionary."
                ]

        current_thesis = {
            "bull_case": bull,
            "bear_case": bear,
            "neutral_case": neutral_case,
            "catalysts": catalysts,
            "risks": risks,
            "valuation": briefing.get("valuation_perspective")
            or ((house or {}).get("valuation") if isinstance(house, dict) else None),
            "time_horizon": hv_card.get("investment_horizon"),
            "summary": scrub_text(thesis) if thesis else None,
        }

        rpanel = research_panel(
            agi=evidence_items(scrub(articles)[:10], default_type="agi_research"),
            broker=broker_docs,
            filings=filing_docs,
            earnings=earning_docs,
            historical=evidence_items(
                _as_docs(company_ws.get("agi_articles") or [])[3:12],
                default_type="agi_research",
            ),
        )

        workspace = {
            "mode": "institutional_answer",
            "four_questions": {
                "view": hv_card.get("stance"),
                "why": why[:3],
                "evidence_count": len(support_ev),
                "explore_next": followups[:4],
            },
        }

        if briefing.get("executive_summary"):
            executive = scrub_text(briefing["executive_summary"]) or executive
            answer["summary"] = executive
            answer["executive_summary"] = executive
            if house_label:
                answer["house_view_label"] = house_label

        irp_meta = {}
        if isinstance(irp_dump, dict) and irp_dump:
            irp_meta = {
                "irp_id": irp_dump.get("irp_id"),
                "version": irp_dump.get("version"),
                "intent": irp_dump.get("intent"),
                "domain": irp_dump.get("domain"),
                "validation": irp_dump.get("validation") or {},
                "research_plan": {
                    "plan_id": (irp_dump.get("research_plan") or {}).get("plan_id"),
                    "steps": [
                        {
                            "order": s.get("order"),
                            "source_class": s.get("source_class"),
                            "query": s.get("query"),
                        }
                        for s in ((irp_dump.get("research_plan") or {}).get("steps") or [])[:10]
                        if isinstance(s, dict)
                    ],
                },
                "rejected_count": len(irp_dump.get("rejected_evidence") or []),
                "answer_policy": irp_dump.get("answer_policy"),
            }
            workspace = {
                **workspace,
                "mode": "institutional_reasoning_pipeline",
                "programme": "IRP V1",
                "think_before_answer": True,
            }
        if kf_hits:
            workspace = {
                **workspace,
                "knowledge_first": True,
                "knowledge_hits": len(kf_hits),
            }

        return SearchView(
            meta=UiMeta(
                surface="search",
                sources=["knowledge", "research_committee", "composite_view", "model_portfolio", "irp"],
            ),
            question=q,
            intent=(irp_dump or {}).get("intent") or (client or {}).get("intent"),
            entities={
                "ticker": detected_ticker,
                "companies": related,
                "themes": related_themes,
                "sectors": related_sectors,
                "countries": list((irp_entities or {}).get("countries") or [])
                if isinstance(irp_entities, dict)
                else [],
                "currencies": list((irp_entities or {}).get("currencies") or [])
                if isinstance(irp_entities, dict)
                else [],
                "sector_key": (irp_entities or {}).get("sector_key")
                if isinstance(irp_entities, dict)
                else None,
            },
            answer=answer,
            executive_summary=executive,
            house_view=house if isinstance(house, dict) else None,
            confidence=float(conf) if conf is not None else None,
            investment_thesis=scrub_text(thesis) if thesis else None,
            bull_case=bull,
            bear_case=bear,
            key_risks=risks,
            key_catalysts=catalysts,
            why=why,
            supporting_research=scrub(supporting)[:12],
            latest_articles=scrub(articles),
            latest_news=scrub(news)[:8] or _kip_news(self.kip, q, limit=5),
            conflicting_opinions=conflicting if isinstance(conflicting, list) else [],
            evidence_used=evidence_used if isinstance(evidence_used, list) else [],
            knowledge_timeline=timeline_enriched,
            knowledge_freshness=freshness,
            last_updated=str(last_updated) if last_updated else None,
            related_companies=related,
            related_themes=related_themes,
            related_sectors=related_sectors,
            recommendations=recommendations,
            follow_up_questions=followups,
            hits=hits,
            answer_policy="think_then_answer_institutional"
            if irp_meta
            else "institutional_evidence_pack",
            market_regime=regime_label,
            freshness_indicator=freshness_indicator,
            house_view_card=hv_card,
            whats_changed=changed,
            current_thesis=current_thesis,
            supporting_evidence=support_ev,
            conflicting_evidence=conflict_ev,
            research_panel=rpanel,
            knowledge_graph=kg,
            market_intelligence=mi,
            charts=charts,
            predictions=[p for p in preds if p][:12],
            related_ideas=ideas,
            portfolio_context=port_ctx,
            workspace=workspace,
            irp=scrub(irp_meta) or {},
            knowledge_foundation={
                "answer_policy": "knowledge_objects_before_documents",
                "hits": scrub(kf_hits)[:8],
                "count": len(kf_hits),
            },
            institutional_briefing=scrub(briefing) or {},
            sector_intelligence=scrub((irp_dump or {}).get("sector_intelligence") or {})
            if isinstance(irp_dump, dict)
            else {},
            company_intelligence=scrub((irp_dump or {}).get("company_intelligence") or {})
            if isinstance(irp_dump, dict)
            else {},
            current_outlook=scrub_text(briefing.get("current_outlook")) if briefing else None,
            key_drivers=[str(x) for x in (briefing.get("key_drivers") or [])][:8],
            valuation_perspective=scrub_text(briefing.get("valuation_perspective"))
            if briefing
            else None,
            macro_drivers=[str(x) for x in (briefing.get("macro_drivers") or [])][:8],
            sector_drivers=[str(x) for x in (briefing.get("sector_drivers") or [])][:8],
            company_leaders=[str(x) for x in (briefing.get("company_leaders") or [])][:10],
            historical_comparison=scrub_text(briefing.get("historical_comparison"))
            if briefing
            else None,
        )

    def timeline(self, entity: str) -> TimelineView:
        self._require()
        ent = (entity or "").strip()
        events: list[dict[str, Any]] = []
        preds: list[dict[str, Any]] = []
        if self.kip and ent:
            events = enrich_timeline(_timeline_events(dump(soft(self.kip.timeline, ent.upper()))))
            for p in soft(self.kip.predictions, ent.upper(), default=[]) or []:
                d = dump(p)
                if d:
                    preds.append(scrub(d))
            # soft-add news
            for n in _kip_news(self.kip, ent, limit=8):
                events.append(
                    {
                        "as_of": n.get("date"),
                        "type": "news",
                        "title": n.get("title"),
                        "summary": n.get("snippet"),
                        "source": "knowledge",
                    }
                )
            events = enrich_timeline(events)
        return TimelineView(
            meta=UiMeta(surface="timeline", sources=["knowledge"]),
            entity=ent.upper() if ent else ent,
            events=events,
            predictions=preds[:20],
        )

    def autocomplete(self, query: str) -> AutocompleteView:
        self._require()
        q = (query or "").strip()
        home = self.home()
        companies = [c.get("ticker") for c in (home.top_companies or []) if c.get("ticker")]
        # Also pull from search hits for typed query
        if q and self.aws:
            sr = dump(soft(self.aws.search, q, limit=10)) or {}
            for h in sr.get("hits") or []:
                if h.get("kind") == "company" and h.get("id"):
                    companies.append(str(h["id"]).upper())
                if h.get("ticker"):
                    companies.append(str(h["ticker"]).upper())
        companies = sorted({c for c in companies if c})
        pack = build_autocomplete(
            q,
            companies=companies,
            themes=home.market_themes,
            sectors=["Financials", "Technology", "Energy", "Healthcare", "Defence", "Auto"],
            articles=home.todays_research,
            popular=home.popular_questions,
        )
        return AutocompleteView(
            meta=UiMeta(surface="autocomplete", sources=["knowledge", "research_desk"]),
            query=q,
            companies=pack.get("companies") or [],
            themes=pack.get("themes") or [],
            sectors=pack.get("sectors") or [],
            articles=pack.get("articles") or [],
            questions=pack.get("questions") or [],
            popular_searches=pack.get("popular_searches") or [],
        )

    def article(self, article_id: str, *, ticker: str | None = None) -> ArticleView:
        self._require()
        aid = str(article_id)
        # Prefer RMS research id; also accept ticker-linked knowledge
        research = dump(soft(self.aws.research, aid)) if self.aws else None
        research = research or {}
        current = scrub(research.get("current_draft")) or {}
        tickers = list(current.get("tickers") or ([] if not ticker else [ticker.upper()]))
        themes = list(current.get("themes") or [])
        primary = tickers[0].upper() if tickers else (ticker.upper() if ticker else None)

        house = None
        conf = None
        graph = None
        timeline: list[dict[str, Any]] = []
        previous: list[dict[str, Any]] = []
        updates: list[dict[str, Any]] = []
        if primary and self.kip:
            house = scrub(dump(soft(self.kip.house_view, primary)))
            if isinstance(house, dict):
                conf = house.get("confidence")
            graph = scrub(dump(soft(self.kip.graph, primary)))
            timeline = scrub(_timeline_events(dump(soft(self.kip.timeline, primary))))[:20]
            hist = dump(soft(self.kip.research_history, primary)) or {}
            previous = scrub(hist.get("agi_reports") or [])[:8]
            updates = _kip_news(self.kip, primary, limit=5)

        status = thesis_status(house=house if isinstance(house, dict) else None)
        preds: list[dict[str, Any]] = []
        if primary and self.kip:
            for p in soft(self.kip.predictions, primary, default=[]) or []:
                pr = prediction_row(dump(p), ticker=primary)
                if pr:
                    preds.append(pr)
        qs = follow_up_questions(
            question=f"Summarise research {aid}",
            intent="research",
            related_companies=[str(t).upper() for t in tickers],
            related_themes=[str(t) for t in themes],
            house_label=str((house or {}).get("current_view") or (house or {}).get("stance") or "")
            if isinstance(house, dict)
            else None,
            recent_research_titles=[str(x.get("title")) for x in previous[:3] if isinstance(x, dict)],
        )
        return ArticleView(
            meta=UiMeta(surface="article", sources=["knowledge", "research_desk", "research_committee"]),
            article_id=aid,
            related_companies=[str(t).upper() for t in tickers],
            related_themes=[str(t) for t in themes],
            knowledge_graph=graph if isinstance(graph, dict) else None,
            research_timeline=timeline if isinstance(timeline, list) else [],
            previous_agi_articles=previous if isinstance(previous, list) else [],
            house_view=house if isinstance(house, dict) else None,
            confidence=float(conf) if conf is not None else None,
            latest_updates=updates,
            supporting_evidence=_as_docs(scrub(research.get("supporting_documents") or []))[:20],
            whats_changed_since_publication=status.get("whats_changed_since_publication") or [],
            thesis_still_holds=status.get("thesis_still_holds"),
            thesis_status=status,
            prediction_status=preds[:8],
            latest_news=updates,
            discovery=discovery_pack(
                companies=[str(t).upper() for t in tickers],
                themes=[str(t) for t in themes],
                research=previous,
                questions=qs,
            ),
            follow_up_questions=qs,
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
        companies = [str(c).upper() for c in (ws.get("related_companies") or theme.get("tickers") or [])]
        risks = list(theme.get("risks") or [])[:10]
        catalysts = list(theme.get("catalysts") or [])[:10]
        thesis = theme.get("thesis") or theme.get("summary") or theme.get("theme")
        house = None
        graph = None
        if companies and self.kip:
            house = scrub(dump(soft(self.kip.house_view, str(companies[0]).upper())))
            graph = scrub(dump(soft(self.kip.graph, str(companies[0]).upper())))
        timeline = _timeline_events(ws.get("knowledge_graph") or ws.get("timeline"))
        intel = theme_intelligence(
            theme_id=theme_id,
            thesis=scrub_text(thesis) if thesis else None,
            companies=companies,
            risks=[scrub_text(str(r)) or "" for r in risks],
            catalysts=[scrub_text(str(c)) or "" for c in catalysts],
            research=docs[:15],
            house=house if isinstance(house, dict) else None,
            graph=graph if isinstance(graph, dict) else None,
            timeline=timeline,
            macro_themes=list(theme.get("related_macro") or theme.get("macro_themes") or [])[:6],
        )
        return ThemeView(
            meta=UiMeta(surface="theme", sources=["knowledge"]),
            theme_id=theme_id,
            current_thesis=scrub_text(thesis) if thesis else None,
            related_companies=companies,
            related_research=docs[:15],
            current_risks=[scrub_text(str(r)) or "" for r in risks],
            current_catalysts=[scrub_text(str(c)) or "" for c in catalysts],
            house_view=house,
            timeline=timeline,
            confidence=intel.get("confidence"),
            stance=intel.get("stance"),
            related_macro=intel.get("related_macro") or [],
            knowledge_graph=intel.get("knowledge_graph") or {},
            research_timeline=intel.get("research_timeline") or [],
            follow_up_questions=intel.get("follow_up_questions") or [],
            discovery=intel.get("discovery") or {},
            product_meta=intel.get("product_meta") or {},
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
        if not isinstance(research, list):
            research = []
        health = "Active coverage" if ranked else "Limited coverage"
        valuation = scrub(ws.get("portfolio_exposure") or {})
        risks = [scrub_text(str(r)) or "" for r in (ws.get("risks") or [])][:8]
        opportunities = [scrub_text(str(o)) or "" for o in (ws.get("opportunities") or [])][:8]
        macro_drivers = [scrub_text(str(m)) or "" for m in (ws.get("macro_drivers") or [])][:8]
        intel = sector_intelligence(
            sector_id=sector_id,
            health=health,
            leaders=leaders,
            laggards=laggards,
            research=research,
            valuation=valuation if isinstance(valuation, dict) else {},
            risks=risks,
            opportunities=opportunities,
            macro_drivers=macro_drivers,
            timeline=_as_docs(research),
        )
        return SectorView(
            meta=UiMeta(surface="sector", sources=["knowledge", "research_desk", "model_portfolio"]),
            sector_id=sector_id,
            sector_health=health,
            leaders=leaders,
            laggards=laggards,
            current_theme=sector_id,
            current_risks=intel.get("current_risks") or risks,
            current_research=research,
            valuation_snapshot=valuation if isinstance(valuation, dict) else {},
            current_outlook=intel.get("current_outlook"),
            current_opportunities=intel.get("current_opportunities") or [],
            macro_drivers=intel.get("macro_drivers") or [],
            sector_timeline=intel.get("sector_timeline") or [],
            valuation_summary=intel.get("valuation_summary") or {},
            follow_up_questions=intel.get("follow_up_questions") or [],
            discovery=intel.get("discovery") or {},
            product_meta=intel.get("product_meta") or {},
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
        theme_names: list[str] = []
        for t in themes or []:
            if isinstance(t, dict):
                name = t.get("name") or t.get("id")
                if name:
                    theme_names.append(str(name))
            elif t:
                theme_names.append(str(t))
        related_companies: list[str] = []
        port = dump(soft(self.aws.portfolio)) if self.aws else None
        book = (port or {}).get("l4_book") or {}
        if isinstance(book, dict):
            related_companies = [str(k).upper() for k in list(book.keys())[:8]]
        intel = macro_intelligence(
            regime=regime if isinstance(regime, dict) else None,
            risk=risk if isinstance(risk, dict) else None,
            events=scrub(events)[:10],
            research=_as_docs(docs)[:15],
            themes=theme_names,
            related_companies=related_companies,
        )
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
            intelligence=intel,
            follow_up_questions=intel.get("follow_up_questions") or [],
            discovery=intel.get("discovery") or {},
        )

    def predictions(self) -> PredictionCentreView:
        self._require()
        preds: list[dict[str, Any]] = []
        home = self.home()
        tickers = [str(c.get("ticker")).upper() for c in (home.top_companies or []) if c.get("ticker")]
        if self.kip:
            for tk in tickers[:12]:
                for p in soft(self.kip.predictions, tk, default=[]) or []:
                    pr = prediction_row(dump(p), ticker=tk)
                    if pr:
                        preds.append(pr)
        # de-dupe by id
        seen: set[str] = set()
        uniq: list[dict[str, Any]] = []
        for p in preds:
            pid = str(p.get("id"))
            if pid in seen:
                continue
            seen.add(pid)
            uniq.append(p)
        acc = accuracy_summary(uniq)
        qs = follow_up_questions(
            question="How accurate are AGI predictions?",
            intent="prediction",
            related_companies=tickers[:6],
            related_themes=[str(t.get("id") or t.get("name")) for t in (home.market_themes or [])][:4],
            house_label=None,
        )
        timeline = [
            {
                "as_of": p.get("publication_date"),
                "type": "prediction",
                "title": p.get("thesis") or p.get("ticker"),
                "summary": f"{p.get('current_status')} · {p.get('target_horizon')}",
            }
            for p in uniq[:20]
        ]
        return PredictionCentreView(
            meta=UiMeta(surface="predictions", sources=["knowledge", "evaluation"]),
            predictions=uniq[:40],
            accuracy=acc,
            prediction_timeline=enrich_timeline(timeline),
            discovery=discovery_pack(
                companies=tickers,
                themes=[str(t.get("id") or t.get("name")) for t in (home.market_themes or [])][:6],
                questions=qs,
            ),
            follow_up_questions=qs,
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

    def _hydrate_evidence(self, items: list[Any]) -> list[dict[str, Any]]:
        """Resolve bare doc_ ids into real titles/snippets from KIP when possible."""
        out: list[dict[str, Any]] = []
        for item in items or []:
            if not isinstance(item, dict):
                continue
            row = dict(item)
            doc_id = row.get("id") or row.get("document_id")
            title = str(row.get("title") or "").strip()
            needs_title = (not title) or title.startswith("doc_") or (
                doc_id and title == str(doc_id)
            )
            needs_summary = not (row.get("snippet") or row.get("summary"))
            if self.kip and doc_id and (needs_title or needs_summary):
                src = soft(self.kip.get_document, str(doc_id))
                if src is not None:
                    doc_title = getattr(getattr(src, "document", None), "title", None)
                    research = getattr(src, "research", None)
                    knowledge = getattr(src, "knowledge", None)
                    if needs_title and doc_title:
                        row["title"] = scrub_text(doc_title) or doc_title
                    if needs_summary:
                        summary = None
                        if knowledge is not None:
                            summary = getattr(knowledge, "summary", None)
                        if not summary and research is not None:
                            summary = getattr(research, "investment_thesis", None)
                        if summary:
                            row["summary"] = scrub_text(str(summary)[:320]) or str(summary)[:320]
                            row.setdefault("snippet", row["summary"])
                    if research is not None and not row.get("tickers"):
                        inv = getattr(src, "investment", None)
                        tickers = list(getattr(inv, "tickers", None) or [])
                        row["tickers"] = [
                            str(t).upper()
                            for t in tickers
                            if str(t).upper() in KNOWN_TICKERS or str(t).upper().endswith("BANK")
                        ]
            # Final ticker scrub for already-populated noisy lists
            if isinstance(row.get("tickers"), list):
                row["tickers"] = [
                    str(t).upper()
                    for t in row["tickers"]
                    if str(t).upper() in KNOWN_TICKERS or str(t).upper().endswith("BANK")
                ]
            out.append(row)
        return out

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


def _iso_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _brief_summary(regime: dict, risk: dict, composite: dict) -> str:
    n = composite.get("n_names") or 0
    coverage = f"{n} names in the composite book" if n else "selective institutional coverage"
    return (
        f"{regime.get('label')} regime with {risk.get('label')} risk — "
        f"{coverage}. Stay selective into the next policy window."
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
    """Soft calendar pull — empty means caller fills institutional defaults."""
    if not aws:
        return []
    try:
        macro = dump(soft(aws.macro)) if aws else None
        events = []
        if isinstance(macro, dict):
            for key in ("calendar", "economic_calendar", "events", "upcoming_events"):
                rows = macro.get(key)
                if isinstance(rows, list) and rows:
                    events = rows
                    break
        out: list[dict[str, Any]] = []
        for ev in events[:12]:
            if not isinstance(ev, dict):
                continue
            title = ev.get("title") or ev.get("name") or ev.get("event")
            if not title:
                continue
            out.append(
                {
                    "id": ev.get("id") or f"cal-{len(out)}",
                    "title": scrub_text(title),
                    "name": scrub_text(title),
                    "country": ev.get("country") or ev.get("region") or "IN",
                    "region": ev.get("region") or ev.get("country") or "India",
                    "importance": ev.get("importance") or ev.get("impact") or "Medium",
                    "expected_impact": scrub_text(ev.get("expected_impact") or ev.get("note") or ""),
                    "affected_sectors": ev.get("affected_sectors") or ev.get("sectors") or [],
                    "affected_companies": ev.get("affected_companies") or ev.get("tickers") or [],
                    "as_of": ev.get("as_of") or ev.get("date") or ev.get("time"),
                    "date": ev.get("date") or ev.get("as_of") or ev.get("time"),
                }
            )
        return out
    except Exception:
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
    return _evidence_dicts(items)


def _evidence_dicts(items: Any) -> list[dict[str, Any]]:
    if not items:
        return []
    out: list[dict[str, Any]] = []
    for x in items:
        if isinstance(x, dict):
            row = dict(x)
            # Normalize RagEvidenceItem dumps
            if not row.get("id") and row.get("document_id"):
                row["id"] = row["document_id"]
            if not row.get("title") and row.get("document_id"):
                # Avoid showing bare ids as titles when snippet exists
                row["title"] = row.get("snippet") or row["document_id"]
            if row.get("snippet") and not row.get("summary"):
                row["summary"] = row["snippet"]
            # Sanitize noisy tickers on evidence cards
            if isinstance(row.get("tickers"), list):
                row["tickers"] = [
                    str(t).upper()
                    for t in row["tickers"]
                    if str(t).upper() in KNOWN_TICKERS or str(t).upper().endswith("BANK")
                ]
            out.append(row)
        else:
            sid = str(x)
            # Skip bare doc ids without metadata — they render as useless cards.
            if sid.startswith("doc_") and len(sid) < 40:
                continue
            out.append({"id": sid, "title": scrub_text(sid)})
    return out


_JUNK_EVIDENCE_TITLES = {
    "hello world",
    "sample private research",
    "test",
    "asdf",
    "lorem ipsum",
    "untitled",
    "demo",
}


def _filter_junk_docs(items: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        title_l = title.lower()
        if not title or title_l in _JUNK_EVIDENCE_TITLES:
            continue
        if title.startswith("doc_") and not (item.get("snippet") or item.get("summary")):
            continue
        if title_l.startswith(("test ", "demo ", "sample ", "hello ")):
            continue
        out.append(item)
    return out


def _search_answer_summary(
    question: str,
    house: dict | None,
    confidence: float | None,
    supporting: list,
    house_label: str | None = None,
) -> str:
    house = flatten_house_view(house) if house else None
    label = normalize_stance(
        house_label
        or (house.get("stance") if house else None)
        or (house.get("current_view_label") if house else None)
        or (house.get("label") if house else None)
    )
    thesis = clean_thesis_text((house or {}).get("thesis") or (house or {}).get("summary") or "")
    if not thesis and supporting:
        top = supporting[0] if isinstance(supporting[0], dict) else {}
        thesis = clean_thesis_text(top.get("snippet") or top.get("summary") or top.get("title") or "")
    if house and (thesis or label != "Neutral" or house.get("current_view")):
        conf_val = confidence if confidence is not None else (house or {}).get("confidence")
        if isinstance(conf_val, (int, float)) and conf_val > 1:
            conf = f" Confidence {conf_val:.0f}%."
        elif isinstance(conf_val, (int, float)):
            conf = f" Confidence {conf_val:.0%}."
        else:
            conf = ""
        thesis_bit = f" {thesis[:220]}" if thesis else ""
        return (
            f"AGI institutional view on “{question}”: {label}.{conf}"
            f"{thesis_bit} "
            f"Evidence pack includes {len(supporting)} supporting research items. "
            "Not investment advice."
        )
    if supporting:
        top = supporting[0] if isinstance(supporting[0], dict) else {}
        title = scrub_text(top.get("title")) if isinstance(top, dict) else None
        if title and str(title).startswith("doc_"):
            title = None
        snip = scrub_text(top.get("snippet") or top.get("summary")) if isinstance(top, dict) else None
        lead = f" Latest note: {title}." if title else ""
        detail = f" {snip[:200]}" if snip else ""
        return (
            f"Institutional evidence pack for “{question}”.{lead}{detail} "
            f"{len(supporting)} research items retrieved. Not investment advice."
        )
    return (
        f"Institutional evidence pack for “{question}”. "
        "House view not yet established for the detected subject. "
        "Review supporting research and conflicting opinions below. "
        "Not investment advice."
    )


def _why_bullets(
    house: dict | None,
    supporting: list,
    news: list,
    house_label: str | None,
) -> list[str]:
    out: list[str] = []
    house = flatten_house_view(house) if house else None
    label = normalize_stance(
        house_label or (house.get("stance") if house else None)
    )
    if label:
        out.append(f"Current AGI house view is {label}.")
    thesis = clean_thesis_text((house or {}).get("thesis") or "")
    if thesis:
        out.append(thesis[:200])
    elif supporting:
        top = supporting[0] if isinstance(supporting[0], dict) else {}
        snip = clean_thesis_text(top.get("snippet") or top.get("summary") or top.get("title") or "")
        if snip and not snip.startswith("doc_"):
            out.append(snip[:200])
    if supporting:
        out.append(f"{len(supporting)} supporting AGI / institutional research items retrieved.")
    if news:
        out.append(f"{len(news)} related news items included for freshness.")
    if house and house.get("changed_assumptions"):
        out.append("Recent thesis assumptions have changed — see knowledge timeline.")
    if not out:
        out.append("Answer assembled from AGI knowledge, research committee reasoning, and live desk context.")
    # Never surface raw object dumps in Why chips.
    cleaned: list[str] = []
    for x in out[:6]:
        s = scrub_text(x) or str(x)
        if s.startswith("{") or "document_id" in s:
            continue
        cleaned.append(s)
    return cleaned or ["Answer assembled from AGI knowledge and live desk context."]


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
