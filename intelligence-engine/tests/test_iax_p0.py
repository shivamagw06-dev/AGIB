"""IAX P0 — Institutional Answer Experience workspace fields."""

from __future__ import annotations

from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

from app.aws.service import AwsService
from app.cre.service import CREService
from app.ioc.service import IocService
from app.kip.models import DocumentType, IngestRequest
from app.kip.service import KipService
from app.main import app
from app.rms.models import ResearchRequestCreate
from app.rms.service import RmsService
from app.rsp.service import RspService
from app.ui.iax import (
    evidence_items,
    house_view_card,
    market_intelligence_summary,
    normalize_stance,
    whats_changed,
)
from app.ui.service import UiService
from app.validation.service import ValidationService


def _ui() -> UiService:
    kip = KipService()
    kip.ingest_agi(
        IngestRequest(
            title="AGI ICICI IAX Brief",
            content=(
                "ICICIBANK Investment Thesis preferred private bank.\n"
                "Bull Case\n- Franchise growth\nBear Case\n- Credit costs\n"
                "Risks\n- NIMs compression\nCatalysts\n- Loan growth rebound\n"
                "Theme: credit_growth\nSector: Financials\n"
            ),
            tickers=["ICICIBANK"],
            themes=["credit_growth"],
            sectors=["Financials"],
            date=date(2026, 1, 15),
            article_id="iax_agi_1",
            document_type=DocumentType.AGI_RESEARCH,
        )
    )
    rsp = RspService(kip=kip)
    rms = RmsService(kip=kip, rsp=rsp)
    rms.create_request(
        ResearchRequestCreate(
            title="IAX ICICI note",
            owner="analyst",
            tickers=["ICICIBANK"],
            sectors=["Financials"],
            themes=["credit_growth"],
            request_brief="Update house view",
        )
    )
    aws = AwsService(kip=kip, rsp=rsp, rms=rms, cre=CREService(), validation=ValidationService())
    ioc = IocService(kip=kip, rsp=rsp, rms=rms, aws=aws, cre=CREService(), validation=ValidationService())
    return UiService(aws=aws, ioc=ioc, kip=kip, rsp=rsp, rms=rms, cre=CREService(), validation=ValidationService())


def test_normalize_stance_and_house_card():
    assert normalize_stance("Strongly Bullish") == "Bullish"
    assert normalize_stance("bear case") == "Bearish"
    card = house_view_card({"current_view": "Bullish", "horizon": "12m", "conviction": "high"}, 0.72)
    assert card["stance"] == "Bullish"
    assert card["bullish"] is True
    assert card["confidence"] == 0.72


def test_whats_changed_highlights_deltas():
    changed = whats_changed(
        house={
            "current_view": "Bullish",
            "thesis_evolution": ["Loan growth improving"],
            "failed_assumptions": ["NIM pressure rising"],
            "catalysts_occurred": ["Deposit franchise held"],
        },
        prior_house={"current_view": "Neutral", "confidence": 0.4, "thesis": "Old thesis"},
        conf=0.7,
        prior_conf=0.4,
        thesis="New franchise thesis",
    )
    kinds = {i["kind"] for i in changed["items"]}
    assert "stance" in kinds
    assert "confidence" in kinds
    assert changed["buckets"]["new_risks"]
    assert changed["buckets"]["new_catalysts"]


def test_evidence_and_market_intelligence_scrub_engines():
    items = evidence_items(
        [{"title": "Broker note E03 overlay", "source": "broker_desk", "document_type": "broker", "snippet": "Supportive"}],
        default_type="broker",
    )
    blob = str(items)
    assert "E03" not in blob
    mi = market_intelligence_summary({"macro": {"regime": "RiskOn", "confidence": 0.8}})
    dims = {row["dimension"] for row in mi}
    assert {"Market", "Business", "Risk", "Momentum", "Events", "Sentiment", "Volatility"} <= dims
    assert "E01" not in str(mi)


def test_search_returns_iax_workspace_fields():
    pack = _ui().search("Should I buy ICICIBANK?")
    assert pack.executive_summary
    assert pack.house_view_card.get("stance")
    assert pack.whats_changed.get("items")
    assert pack.current_thesis
    assert isinstance(pack.supporting_evidence, list)
    assert isinstance(pack.conflicting_evidence, list)
    assert pack.research_panel
    assert pack.knowledge_graph.get("buckets") is not None
    assert pack.market_intelligence
    assert isinstance(pack.charts, list)
    assert pack.related_ideas
    assert pack.workspace.get("mode") == "institutional_answer"
    assert 4 <= len(pack.follow_up_questions) <= 8
    dumped = str(pack.model_dump())
    assert "E01" not in dumped
    assert "E03" not in dumped
    assert "EngineState" not in dumped


def test_timeline_surface():
    view = _ui().timeline("ICICIBANK")
    assert view.meta.surface == "timeline"
    assert view.entity == "ICICIBANK"
    assert isinstance(view.events, list)


@pytest.mark.asyncio
async def test_iax_api_routes():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        search = await client.post("/v1/ui/search", params={"question": "Should I buy ICICIBANK?"})
        assert search.status_code == 200
        body = search.json()
        assert body["house_view_card"]
        assert body["whats_changed"]
        assert body["supporting_evidence"] is not None
        assert body["market_intelligence"]
        assert "E14" not in str(body)

        tl = await client.get("/v1/ui/timeline/ICICIBANK")
        assert tl.status_code == 200
        assert tl.json()["entity"] == "ICICIBANK"
