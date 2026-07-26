from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi import Body

from app.agents.registry import list_agents
from app.core.config import Settings, get_settings
from app.engines.e01.consumer import register_e01_with_orch_l2
from app.engines.e01.service import E01Service
from app.engines.e02.consumer import register_e02_with_orch
from app.engines.e02.service import E02Service
from app.engines.e03.consumer import register_e03_with_orch
from app.engines.e03.service import E03Service
from app.engines.e04.consumer import register_e04_with_orch
from app.engines.e04.service import E04Service
from app.engines.e05.consumer import register_e05_with_orch
from app.engines.e05.service import E05Service
from app.engines.e11.consumer import register_e11_with_orch
from app.engines.e11.service import E11Service
from app.engines.e14.consumer import register_e14_with_orch
from app.engines.e14.service import E14Service
from app.engines.e10.consumer import register_e10_with_orch
from app.engines.e10.service import E10Service
from app.engines.e08.consumer import register_e08_with_orch
from app.engines.e08.service import E08Service
from app.engines.e09.consumer import register_e09_with_orch
from app.engines.e09.service import E09Service
from app.engines.e13.consumer import register_e13_with_orch
from app.engines.e13.service import E13Service
from app.engines.l4.consumer import register_l4_with_orch
from app.engines.l4.service import L4Service
from app.eval.evaluation_agent import EvaluationAgent
from app.cre.service import CREService
from app.kip.models import (
    BulkIngestRequest,
    ChannelIngestRequest,
    ClientSearchRequest,
    IngestRequest,
    PredictionEvalRequest,
)
from app.kip.service import KipService
from app.rsp.models import CommitteeRequest, ReasonRequest, SynthesizeRequest
from app.rsp.service import RspService
from app.rms.models import (
    ApproveRequest,
    DraftRequest,
    PublishRequest,
    ResearchRequestCreate,
    ReviewRequest,
)
from app.rms.service import RmsService
from app.rms.workflow import WorkflowError
from app.aws.service import AwsService
from app.ioc.service import IocService
from app.aip.models import ExperimentHypothesis, ExperimentRequest
from app.aip.service import AipService
from app.irp.service import IrpService
from app.kf.service import KfService
from app.kc.service import KcService
from app.aoi.service import AoiService
from app.eve.service import EveService
from app.iie.service import IieService
from app.fle.service import FleService
from app.mee.service import MeeService
from app.cae.service import CaeService
from app.ib.service import IbService
from app.ve.service import VeService
from app.fiml.service import FimlService
from app.academy.service import AcademyService
from app.ui.service import UiService
from app.validation.service import ValidationService
from app.features.models import FeatureMetadata
from app.features.service import FeatureRegistryService
from app.market_data.client import MarketDataClient
from app.memory.store import ResearchStore
from app.orch.l2.executor import L2FeatureBuildService
from app.orch.l2.models import BuildBatchRequest, MarketDataUpdateEvent
from app.orch.ledger import OrchLedger
from app.orchestration.director import ResearchDirector
from app.schemas.models import PredictionRecord, ResearchRun, ResearchRunCreate

router = APIRouter(prefix="/v1")
_store = ResearchStore()
_director = ResearchDirector(store=_store)
_eval = EvaluationAgent()
_market_data = MarketDataClient.from_settings(get_settings())
_features = FeatureRegistryService()
_orch_ledger = OrchLedger()
_l2 = L2FeatureBuildService(_features, orch_ledger=_orch_ledger)
_e01 = E01Service(_features, orch_ledger=_orch_ledger)
_e14 = E14Service(_features, e01=_e01, orch_ledger=_orch_ledger)
_e02 = E02Service(_features, e01=_e01, e14=_e14, orch_ledger=_orch_ledger)
_e13 = E13Service(_features, e01=_e01, e14=_e14, orch_ledger=_orch_ledger)
_e08 = E08Service(_features, e01=_e01, e14=_e14, orch_ledger=_orch_ledger)
_e09 = E09Service(_features, e01=_e01, e14=_e14, orch_ledger=_orch_ledger)
_e03 = E03Service(_features, e01=_e01, e14=_e14, e02=_e02, orch_ledger=_orch_ledger)
_e04 = E04Service(
    _features, e01=_e01, e14=_e14, e02=_e02, e03=_e03, orch_ledger=_orch_ledger
)
_e05 = E05Service(_features, e01=_e01, e14=_e14, orch_ledger=_orch_ledger)
_e11 = E11Service(_features, e01=_e01, e14=_e14, orch_ledger=_orch_ledger)
_l4 = L4Service(
    e01=_e01, e14=_e14, e02=_e02, e03=_e03, e11=_e11, orch_ledger=_orch_ledger
)
_e10 = E10Service(l4=_l4, e14=_e14, e02=_e02, orch_ledger=_orch_ledger)
_validation = ValidationService()
_cre = CREService()
_kip = KipService()
_rsp = RspService(kip=_kip)
_rms = RmsService(kip=_kip, rsp=_rsp)
_aws = AwsService(
    kip=_kip,
    rsp=_rsp,
    rms=_rms,
    cre=_cre,
    validation=_validation,
    e01=_e01,
    e02=_e02,
    e03=_e03,
    e04=_e04,
    e05=_e05,
    e08=_e08,
    e09=_e09,
    e10=_e10,
    e11=_e11,
    e13=_e13,
    e14=_e14,
    l4=_l4,
)
_ioc = IocService(
    market_data=_market_data,
    features=_features,
    orch_l2=_l2,
    orch_ledger=_orch_ledger,
    e01=_e01,
    e02=_e02,
    e03=_e03,
    e04=_e04,
    e05=_e05,
    e08=_e08,
    e09=_e09,
    e10=_e10,
    e11=_e11,
    e13=_e13,
    e14=_e14,
    l4=_l4,
    validation=_validation,
    cre=_cre,
    kip=_kip,
    rsp=_rsp,
    rms=_rms,
    aws=_aws,
)
_aip = AipService()
_irp = IrpService(kip=_kip, rsp=_rsp)
_kf = KfService(kip=_kip)
_kc = KcService(kf=_kf, kip=_kip)
_aoi = AoiService(kip=_kip, kc=_kc, kf=_kf)
_eve = EveService(aoi=_aoi, kc=_kc, kf=_kf)
_aoi.bind_eve(_eve)
_iie = IieService(eve=_eve, kc=_kc, kf=_kf, aoi=_aoi)
_fle = FleService(iie=_iie, eve=_eve, kc=_kc, kf=_kf, aoi=_aoi)
_mee = MeeService(eve=_eve, iie=_iie, fle=_fle, aoi=_aoi, kf=_kf, kc=_kc)
_cae = CaeService(kf=_kf, kc=_kc, aoi=_aoi, eve=_eve, iie=_iie, fle=_fle, mee=_mee)
_ib = IbService(aoi=_aoi, eve=_eve, iie=_iie, fle=_fle, mee=_mee, cae=_cae)
_ve = VeService(eve=_eve, iie=_iie, fle=_fle, mee=_mee, aoi=_aoi, ib=_ib)
# Soft IB subscriber for valuation recalculation (additive; engines unchanged).
try:
    _ib.subscribe(
        {
            "subscriber": "ve",
            "event_types": [
                "EvidenceVerified",
                "ForecastUpdated",
                "ForecastResolved",
                "InvestmentThesisUpdated",
                "CorporateEventDetected",
                "CompanyUpdated",
            ],
            "priority": "normal",
            "retry_max": 2,
        }
    )
    _ib.delivery.register_handler("ve", _ve.on_bus_event)
except Exception:
    pass
# FIML — shared domain model library (not an engine; engines consume via models.consumers).
_fiml = FimlService()
# Finance Academy — curriculum knowledge library (not an engine; soft consumers only).
_academy = AcademyService()
_ui = UiService(
    aws=_aws,
    ioc=_ioc,
    kip=_kip,
    rsp=_rsp,
    rms=_rms,
    cre=_cre,
    validation=_validation,
    aip=_aip,
    irp=_irp,
    kf=_kf,
    kc=_kc,
    aoi=_aoi,
    eve=_eve,
    iie=_iie,
    fle=_fle,
    mee=_mee,
    cae=_cae,
    ib=_ib,
    ve=_ve,
)
# Soft-wire KIP retrieve → RSP reason into Research Director (no engine redesign).
_director.kip = _kip
_director.rsp = _rsp


def _wire_market_data_to_l2() -> None:
    """MarketData publishes updates; ORCH L2 marks dirty + schedules builds."""

    def _on_update(event: MarketDataUpdateEvent) -> None:
        _l2.on_market_data_update(event, drain=False)

    _market_data.on_update(_on_update)


def _wire_e01_passive_consumer() -> None:
    """E01 registers as passive FeatureSnapshot consumer on ORCH L2 ready events."""
    register_e01_with_orch_l2(_l2, _e01)


def _wire_e14_passive_consumer() -> None:
    """E14 registers as passive consumer of FeatureSnapshot + E01State."""
    register_e14_with_orch(_l2, _e14, _e01)


def _wire_e02_passive_consumer() -> None:
    """E02 registers as passive consumer of FeatureSnapshot + E01State + E14State."""
    register_e02_with_orch(_l2, _e02, _e01, _e14)


def _wire_e13_passive_consumer() -> None:
    """E13 registers as passive consumer of FeatureSnapshot + E01State + E14State."""
    register_e13_with_orch(_l2, _e13, _e01, _e14)


def _wire_e08_passive_consumer() -> None:
    """E08 registers as passive consumer of FeatureSnapshot + E01State + E14State."""
    register_e08_with_orch(_l2, _e08, _e01, _e14)


def _wire_e09_passive_consumer() -> None:
    """E09 registers as passive consumer of FeatureSnapshot + E01State + E14State."""
    register_e09_with_orch(_l2, _e09, _e01, _e14)


def _wire_e05_passive_consumer() -> None:
    """E05 registers as passive consumer of FeatureSnapshot + E01State + E14State."""
    register_e05_with_orch(_l2, _e05, _e01, _e14)


def _wire_e11_passive_consumer() -> None:
    """E11 registers as passive soft voter after Feature Ready + E01 + E14 Ready."""
    register_e11_with_orch(_l2, _e11, _e01, _e14)


def _wire_e03_passive_consumer() -> None:
    """E03 registers as passive consumer of FeatureSnapshot + E01/E14/E02 Ready."""
    register_e03_with_orch(_l2, _e03, _e01, _e14, _e02)


def _wire_e04_passive_consumer() -> None:
    """E04 registers as passive consumer of Feature/E01/E14/E02/E03 Ready."""
    register_e04_with_orch(_l2, _e04, _e01, _e14, _e02, _e03)


def _wire_l4_passive_consumer() -> None:
    """L4 shadow registers as passive consumer of E01/E14/E02/E03 Ready only."""
    register_l4_with_orch(_l4, _e01, _e14, _e02, _e03)


def _wire_e10_passive_consumer() -> None:
    """E10 registers as passive model-portfolio builder after L4 Ready."""
    register_e10_with_orch(_e10, _l4)


_wire_market_data_to_l2()
_wire_e01_passive_consumer()
_wire_e14_passive_consumer()
_wire_e02_passive_consumer()
_wire_e13_passive_consumer()
_wire_e08_passive_consumer()
_wire_e09_passive_consumer()
_wire_e05_passive_consumer()
_wire_e11_passive_consumer()
_wire_e03_passive_consumer()
_wire_e04_passive_consumer()
_wire_l4_passive_consumer()
_wire_e10_passive_consumer()


def require_token(
    authorization: str | None = Header(default=None),
    x_agi_token: str | None = Header(default=None, alias="X-AGI-Intelligence-Token"),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = settings.intelligence_engine_token
    provided = None
    if authorization and authorization.lower().startswith("bearer "):
        provided = authorization.split(" ", 1)[1].strip()
    elif x_agi_token:
        provided = x_agi_token.strip()
    if not provided or provided != expected:
        raise HTTPException(status_code=401, detail="Invalid intelligence engine token")


@router.get("/health")
async def health():
    return {
        "ok": True,
        "service": "agi-intelligence-engine",
        "agents": list_agents(),
    }


@router.get("/orch/status")
async def orch_status():
    """ORCH control-plane status (Document ID ORCH; not E00 Layer 5 / E10)."""
    summary = _orch_ledger.status_summary()
    summary["l2"] = _l2.health()
    return summary


@router.get("/orch/l2/health")
async def orch_l2_health():
    """ORCH Layer 2 Feature Build health (ORCH-003–005)."""
    return _l2.health()


@router.get("/e01/health")
async def e01_health():
    """E01 Macro & Regime Engine health (E01-001–005 P0)."""
    return _e01.health()


@router.get("/e01/state")
async def e01_state(as_of: str | None = None):
    """Frontend-ready E01 EngineState (warm cache)."""
    state = _e01.get_state(as_of=as_of)
    if state is None:
        raise HTTPException(status_code=404, detail="E01 state not available")
    return state.model_dump(mode="json")


@router.get("/e01/history")
async def e01_history(limit: int = 50):
    """E01 regime history (newest first)."""
    return [s.model_dump(mode="json") for s in _e01.history(limit=min(limit, 200))]


@router.get("/e14/health")
async def e14_health():
    """E14 Risk & Crowding Overlay health (E14-001–005 P0)."""
    return _e14.health()


@router.get("/e14/state")
async def e14_state(as_of: str | None = None):
    """Frontend-ready E14 EngineState (warm cache)."""
    state = _e14.get_state(as_of=as_of)
    if state is None:
        raise HTTPException(status_code=404, detail="E14 state not available")
    return state.model_dump(mode="json")


@router.get("/e14/history")
async def e14_history(limit: int = 50):
    """E14 firm risk history (newest first)."""
    return [s.model_dump(mode="json") for s in _e14.history(limit=min(limit, 200))]


@router.get("/e02/health")
async def e02_health():
    """E02 Factor & Style Engine health (E02-001–005 P0)."""
    return _e02.health()


@router.get("/e02/exposure/{symbol}")
async def e02_exposure(symbol: str, as_of: str | None = None):
    """Frontend-ready E02Exposure (warm cache)."""
    exp = _e02.get_exposure(symbol, as_of=as_of)
    if exp is None:
        raise HTTPException(status_code=404, detail="E02 exposure not available")
    return exp.model_dump(mode="json")


@router.get("/e02/history/{symbol}")
async def e02_history(symbol: str, limit: int = 50):
    """E02 EngineState history for a symbol (newest first)."""
    return [s.model_dump(mode="json") for s in _e02.history(symbol, limit=min(limit, 200))]


@router.get("/e13/health")
async def e13_health():
    """E13 Equity Fundamental L/S Engine health (E13-001–005 P0)."""
    return _e13.health()


@router.get("/e13/fundamental/{symbol}")
async def e13_fundamental(symbol: str, as_of: str | None = None):
    """Frontend-ready E13Fundamental (warm cache)."""
    fund = _e13.get_fundamental(symbol, as_of=as_of)
    if fund is None:
        raise HTTPException(status_code=404, detail="E13 fundamental not available")
    return fund.model_dump(mode="json")


@router.get("/e13/history/{symbol}")
async def e13_history(symbol: str, limit: int = 50):
    """E13 EngineState history for a symbol (newest first)."""
    return [s.model_dump(mode="json") for s in _e13.history(symbol, limit=min(limit, 200))]


@router.get("/e08/health")
async def e08_health():
    """E08 Volatility & Options Intelligence health (E08-001–005 P0)."""
    return _e08.health()


@router.get("/e08/state/{symbol}")
async def e08_state(symbol: str, as_of: str | None = None):
    """Frontend-ready E08State (warm cache)."""
    vol = _e08.get_vol_state(symbol, as_of=as_of)
    if vol is None:
        raise HTTPException(status_code=404, detail="E08 state not available")
    return vol.model_dump(mode="json")


@router.get("/e08/history/{symbol}")
async def e08_history(symbol: str, limit: int = 50):
    """E08 EngineState history for a symbol (newest first)."""
    return [s.model_dump(mode="json") for s in _e08.history(symbol, limit=min(limit, 200))]


@router.get("/e09/health")
async def e09_health():
    """E09 CTA Trend Engine health (E09-001–005 P0)."""
    return _e09.health()


@router.get("/e09/state/{symbol}")
async def e09_state(symbol: str, as_of: str | None = None):
    """Frontend-ready E09State (warm cache)."""
    trend = _e09.get_trend_state(symbol, as_of=as_of)
    if trend is None:
        raise HTTPException(status_code=404, detail="E09 state not available")
    return trend.model_dump(mode="json")


@router.get("/e09/history/{symbol}")
async def e09_history(symbol: str, limit: int = 50):
    """E09 EngineState history for a symbol (newest first)."""
    return [s.model_dump(mode="json") for s in _e09.history(symbol, limit=min(limit, 200))]


@router.get("/e04/health")
async def e04_health():
    """E04 Statistical Arbitrage & Relative Value health (E04-001–005 P0)."""
    return _e04.health()


@router.get("/e04/state/{pair}")
async def e04_state(pair: str, as_of: str | None = None):
    """Frontend-ready E04State for a pair id (warm cache)."""
    rv = _e04.get_rv_state(pair, as_of=as_of)
    if rv is None:
        raise HTTPException(status_code=404, detail="E04 state not available")
    return rv.model_dump(mode="json")


@router.get("/e04/history/{pair}")
async def e04_history(pair: str, limit: int = 50):
    """E04 EngineState history for a pair (newest first)."""
    return [s.model_dump(mode="json") for s in _e04.history(pair, limit=min(limit, 200))]


@router.get("/e05/health")
async def e05_health():
    """E05 Event-Driven & Special Situations health (E05-001–005 P0)."""
    return _e05.health()


@router.get("/e05/events/{symbol}")
async def e05_events(symbol: str, as_of: str | None = None):
    """Frontend-ready E05EventState (warm cache)."""
    evt = _e05.get_event_state(symbol, as_of=as_of)
    if evt is None:
        raise HTTPException(status_code=404, detail="E05 event state not available")
    return evt.model_dump(mode="json")


@router.get("/e05/history/{symbol}")
async def e05_history(symbol: str, limit: int = 50):
    """E05 EngineState history for a symbol (newest first)."""
    return [s.model_dump(mode="json") for s in _e05.history(symbol, limit=min(limit, 200))]


@router.get("/e11/health")
async def e11_health():
    """E11 Sentiment & Alternative Data health (E11-001–005 P0)."""
    return _e11.health()


@router.get("/e11/sentiment/{symbol}")
async def e11_sentiment(symbol: str, as_of: str | None = None):
    """Frontend-ready E11State soft sentiment (warm cache)."""
    sent = _e11.get_sentiment_state(symbol, as_of=as_of)
    if sent is None:
        raise HTTPException(status_code=404, detail="E11 sentiment not available")
    return sent.model_dump(mode="json")


@router.get("/e11/state/{symbol}")
async def e11_state(symbol: str, as_of: str | None = None):
    """Alias of /e11/sentiment/{symbol} for EngineState-style clients."""
    sent = _e11.get_sentiment_state(symbol, as_of=as_of)
    if sent is None:
        raise HTTPException(status_code=404, detail="E11 state not available")
    return sent.model_dump(mode="json")


@router.get("/e11/history/{symbol}")
async def e11_history(symbol: str, limit: int = 50):
    """E11 EngineState history for a symbol (newest first)."""
    return [s.model_dump(mode="json") for s in _e11.history(symbol, limit=min(limit, 200))]


@router.get("/e03/health")
async def e03_health():
    """E03 Cross-Sectional Quant Engine health (E03-001–005 P0/M0)."""
    return _e03.health()


@router.get("/e03/alpha/{symbol}")
async def e03_alpha(symbol: str, as_of: str | None = None):
    """Frontend-ready E03Alpha (warm cache)."""
    alpha = _e03.get_alpha(symbol, as_of=as_of)
    if alpha is None:
        raise HTTPException(status_code=404, detail="E03 alpha not available")
    return alpha.model_dump(mode="json")


@router.get("/e03/history/{symbol}")
async def e03_history(symbol: str, limit: int = 50):
    """E03 EngineState history for a symbol (newest first)."""
    return [s.model_dump(mode="json") for s in _e03.history(symbol, limit=min(limit, 200))]


@router.get("/e03/parity")
async def e03_parity():
    """Latest SM_AGI_TECH vs legacy score_research parity report."""
    report = _e03.get_parity()
    if report is None:
        raise HTTPException(status_code=404, detail="E03 parity report not available")
    return report.model_dump(mode="json")


@router.get("/l4/health")
async def l4_health():
    """L4 Composite Intelligence health (L4-001–005 P0 Shadow)."""
    return _l4.health()


@router.get("/l4/opinion/{symbol}")
async def l4_opinion(symbol: str, as_of: str | None = None):
    """Shadow L4Opinion (warm cache). Never replaces E03 production."""
    opinion = _l4.get_opinion(symbol, as_of=as_of)
    if opinion is None:
        raise HTTPException(status_code=404, detail="L4 opinion not available")
    return opinion.model_dump(mode="json")


@router.get("/l4/history/{symbol}")
async def l4_history(symbol: str, limit: int = 50):
    """L4 EngineState history for a symbol (newest first)."""
    return [s.model_dump(mode="json") for s in _l4.history(symbol, limit=min(limit, 200))]


@router.get("/e10/health")
async def e10_health():
    """E10 Portfolio Construction health (E10-001–005 P0)."""
    return _e10.health()


@router.get("/e10/portfolio")
async def e10_portfolio(as_of: str | None = None):
    """Current model E10Portfolio (warm cache). Research only — not executable."""
    port = _e10.get_portfolio(as_of=as_of)
    if port is None:
        raise HTTPException(status_code=404, detail="E10 portfolio not available")
    return port.model_dump(mode="json")


@router.get("/e10/history")
async def e10_history(limit: int = 50):
    """E10 PortfolioState history (newest first)."""
    return [s.model_dump(mode="json") for s in _e10.history(limit=min(limit, 200))]


@router.get("/validation/health")
async def validation_health():
    """Validation & Backtesting platform health (BT-001–005 P0)."""
    return _validation.health()


@router.get("/validation/datasets")
async def validation_datasets():
    """List frozen golden datasets available for replay."""
    return _validation.list_datasets()


@router.post("/validation/replay")
async def validation_replay(dataset_id: str = Query(default="golden_p0_v1")):
    """Run institutional historical replay (isolated engines; no production influence)."""
    try:
        result = _validation.run_replay(dataset_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@router.get("/validation/runs")
async def validation_runs(limit: int = 50):
    """List recent ReplayRun records."""
    return [r.model_dump(mode="json") for r in _validation.list_runs(limit=min(limit, 200))]


@router.get("/validation/runs/{run_id}")
async def validation_run(run_id: str):
    """Full ReplayResult for a run."""
    result = _validation.get_result(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Replay run not found")
    return result.model_dump(mode="json")


@router.get("/validation/dashboard/{run_id}")
async def validation_dashboard(run_id: str):
    """Validation dashboard payload (timeline, portfolio, L4 vs E03, distributions)."""
    dash = _validation.get_dashboard(run_id)
    if dash is None:
        raise HTTPException(status_code=404, detail="Replay dashboard not found")
    return dash


@router.get("/cre/health")
async def cre_health():
    """Continuous Research Evaluation platform health (CRE-001–005 P0)."""
    return _cre.health()


@router.post("/cre/evaluate")
async def cre_evaluate(dataset_id: str = Query(default="golden_p0_v1")):
    """Run nightly/on-demand CRE evaluation over Historical Replay (no production influence)."""
    try:
        result = _cre.evaluate(dataset_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@router.get("/cre/scorecards")
async def cre_scorecards():
    """Latest EngineScorecards + CompositeScorecard."""
    composite = _cre.get_composite()
    return {
        "engines": [s.model_dump(mode="json") for s in _cre.list_scorecards()],
        "composite": composite.model_dump(mode="json") if composite else None,
    }


@router.get("/cre/scorecards/{engine}")
async def cre_scorecard(engine: str):
    """Latest EngineScorecard for one engine."""
    card = _cre.get_scorecard(engine)
    if card is None:
        raise HTTPException(status_code=404, detail="Engine scorecard not found")
    return card.model_dump(mode="json")


@router.get("/cre/alerts")
async def cre_alerts():
    """Latest DriftAlert + RegressionAlert sets."""
    return _cre.get_alerts()


@router.get("/cre/promotion")
async def cre_promotion():
    """Promotion evidence report (PROMOTION=false ⇒ never ready)."""
    report = _cre.get_promotion()
    if report is None:
        raise HTTPException(status_code=404, detail="Promotion report not found")
    return report.model_dump(mode="json")


@router.get("/cre/dashboard")
async def cre_dashboard():
    """CRE dashboard: trends, rankings, confidence/performance, promotion readiness."""
    dash = _cre.get_dashboard()
    if dash is None:
        raise HTTPException(status_code=404, detail="CRE dashboard not found")
    return dash


@router.get("/kip/health")
async def kip_health():
    """Knowledge Intelligence Platform health (institutional memory layer)."""
    return _kip.health()


@router.post("/kip/ingest")
async def kip_ingest(body: IngestRequest):
    """Ingest a document into AGI institutional knowledge."""
    try:
        doc = _kip.ingest(body)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _kf_soft_learn(doc)
    return doc.model_dump(mode="json")


def _kf_soft_learn(doc) -> None:
    """Soft KF + Knowledge Corpus learning hook — never fails the KIP ingest path."""
    try:
        _kf.on_document(doc)
    except Exception:
        pass
    try:
        _kc.on_document(doc)
    except Exception:
        return


def _channel_ingest(body: ChannelIngestRequest, channel: str):
    try:
        if body.items or body.zip_base64:
            bulk = BulkIngestRequest(
                items=body.items,
                zip_base64=body.zip_base64,
                default_broker=body.default_broker or body.broker,
                source_channel=channel,  # type: ignore[arg-type]
            )
            if channel == "broker":
                result = _kip.ingest_broker(bulk)
            elif channel == "newsletter":
                result = _kip.ingest_newsletter(bulk)
            else:
                result = _kip.ingest_bulk(bulk.model_copy(update={"source_channel": channel}))
            # Soft-learn each ingested document into Knowledge Foundation.
            for item in getattr(result, "ingested", None) or []:
                _kf_soft_learn(item)
            return result.model_dump(mode="json")
        single = IngestRequest(**body.model_dump(exclude={"items", "zip_base64", "default_broker"}))
        if channel == "agi":
            doc = _kip.ingest_agi(single)
        elif channel == "broker":
            doc = _kip.ingest_broker(single)
        elif channel == "newsletter":
            doc = _kip.ingest_newsletter(single)
        else:
            doc = _kip.ingest_internal(single)
        _kf_soft_learn(doc)
        return doc.model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/kip/ingest/agi")
async def kip_ingest_agi(body: ChannelIngestRequest):
    """Auto-ingest published AGI research into institutional memory."""
    return _channel_ingest(body, "agi")


@router.post("/kip/ingest/broker")
async def kip_ingest_broker(body: ChannelIngestRequest):
    """Ingest broker research (single or bulk PDF/DOCX/MD/Email/ZIP)."""
    return _channel_ingest(body, "broker")


@router.post("/kip/ingest/newsletter")
async def kip_ingest_newsletter(body: ChannelIngestRequest):
    """Ingest newsletter content (single or bulk)."""
    return _channel_ingest(body, "newsletter")


@router.post("/kip/ingest/internal")
async def kip_ingest_internal(body: ChannelIngestRequest):
    """Ingest internal AGI research notes."""
    return _channel_ingest(body, "internal")


@router.get("/kip/document/{document_id}")
async def kip_document(document_id: str):
    doc = _kip.get_document(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc.model_dump(mode="json")


@router.get("/kip/company/{ticker}")
async def kip_company(ticker: str):
    try:
        return _kip.get_company(ticker).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kip/theme/{theme_id}")
async def kip_theme(theme_id: str):
    try:
        return _kip.get_theme(theme_id).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kip/house-view/{ticker}")
async def kip_house_view(ticker: str):
    """Current AGI House View + thesis evolution for a company."""
    try:
        return _kip.house_view(ticker).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kip/research-history/{ticker}")
async def kip_research_history(ticker: str):
    try:
        return _kip.research_history(ticker).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kip/predictions/{ticker}")
async def kip_predictions(ticker: str):
    try:
        preds = _kip.predictions(ticker)
        stats = _kip.prediction_stats(ticker)
        return {
            "ticker": ticker.upper(),
            "predictions": [p.model_dump(mode="json") for p in preds],
            "stats": stats.model_dump(mode="json"),
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/kip/predictions/evaluate")
async def kip_predictions_evaluate(body: PredictionEvalRequest):
    try:
        return _kip.evaluate_prediction(body).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kip/company-dossier/{ticker}")
async def kip_company_dossier(ticker: str):
    """Full institutional dossier: house view, history, predictions, timeline, graph."""
    try:
        return _kip.company_dossier(ticker).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kip/search")
async def kip_search(
    q: str = Query(..., description="Search query"),
    mode: str = Query(default="hybrid"),
    limit: int = Query(default=10, ge=1, le=50),
    ticker: str | None = None,
    sector: str | None = None,
    theme: str | None = None,
    broker: str | None = None,
):
    try:
        return _kip.search(
            q, mode=mode, limit=limit, ticker=ticker, sector=sector, theme=theme, broker=broker
        ).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/kip/client-search")
async def kip_client_search(body: ClientSearchRequest):
    """Homepage search — NEVER answers directly; returns evidence for LLM synthesis."""
    try:
        return _kip.client_search(body).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kip/timeline/{ticker}")
async def kip_timeline(ticker: str):
    try:
        return _kip.timeline(ticker).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kip/similar/{document_id}")
async def kip_similar(document_id: str, limit: int = Query(default=10, ge=1, le=50)):
    try:
        return _kip.similar(document_id, limit=limit).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kip/graph/{entity}")
async def kip_graph(entity: str):
    try:
        return _kip.graph(entity).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kip/rag")
async def kip_rag(
    q: str = Query(..., description="RAG query"),
    ticker: str | None = None,
    limit: int = Query(default=8, ge=1, le=30),
):
    """Priority RAG evidence pack (AGI house view first; never model memory alone)."""
    try:
        return _kip.rag(q, ticker=ticker, limit=limit).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kip/research-context")
async def kip_research_context(q: str = Query(...), ticker: str | None = None):
    """Research continuity context for AGI Research Writer (validation fields included)."""
    try:
        return _kip.research_context(q, ticker=ticker)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/rsp/health")
async def rsp_health():
    """Reasoning & Research Synthesis Platform health."""
    return _rsp.health()


@router.post("/rsp/reason")
async def rsp_reason(body: ReasonRequest):
    """Run institutional reasoning pipeline → ReasoningPackage (no raw docs to LLM)."""
    try:
        return _rsp.reason(body).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/rsp/synthesize")
async def rsp_synthesize(body: SynthesizeRequest):
    """Generate / refresh research synthesis from reasoning inputs."""
    try:
        return _rsp.synthesize(body).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/rsp/committee")
async def rsp_committee(body: CommitteeRequest):
    """Full Research Committee pass (reason + synthesize)."""
    try:
        return _rsp.committee(body).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/rsp/reasoning/{reasoning_id}")
async def rsp_get_reasoning(reasoning_id: str):
    pkg = _rsp.get_reasoning(reasoning_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="Reasoning package not found")
    return pkg.model_dump(mode="json")


@router.get("/rsp/evidence/{evidence_id}")
async def rsp_get_evidence(evidence_id: str):
    ev = _rsp.get_evidence(evidence_id)
    if ev is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return ev.model_dump(mode="json")


@router.get("/rms/health")
async def rms_health():
    """Research Management System health."""
    return _rms.health()


@router.post("/rms/request")
async def rms_request(body: ResearchRequestCreate):
    """Create research idea/request and optionally collect KIP + run RSP."""
    try:
        return _rms.create_request(body).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/rms/draft")
async def rms_draft(body: DraftRequest):
    """Create or update a research draft."""
    try:
        return _rms.create_or_update_draft(body).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/rms/review")
async def rms_review(body: ReviewRequest):
    """Add review comment / internal or compliance decision."""
    try:
        return _rms.review(body).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/rms/approve")
async def rms_approve(body: ApproveRequest):
    """Compliance / final approval gate."""
    try:
        return _rms.approve(body).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/rms/publish")
async def rms_publish(body: PublishRequest):
    """Publish approved research → website/newsletter/LinkedIn/archive + KIP + predictions."""
    try:
        return _rms.publish(body).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/rms/dashboard")
async def rms_dashboard():
    """Research pipeline, queues, calendar, coverage, prediction tracker."""
    try:
        return _rms.dashboard().model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/rms/research/{research_id}")
async def rms_research(research_id: str):
    obj = _rms.get_research(research_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Research not found")
    return obj.model_dump(mode="json")


@router.get("/aws/health")
async def aws_health():
    """AGI Analyst Workspace health (internal terminal — no public website)."""
    return _aws.health()


@router.get("/aws/company/{ticker}")
async def aws_company(ticker: str, as_of: str | None = None):
    """Company workspace — house view, engines, L4, portfolio, KIP, timeline, graph."""
    try:
        return _aws.company(ticker, as_of=as_of).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aws/theme/{theme_id}")
async def aws_theme(theme_id: str):
    try:
        return _aws.theme(theme_id).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aws/sector/{sector_id}")
async def aws_sector(sector_id: str):
    try:
        return _aws.sector(sector_id).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aws/replay/{as_of}")
async def aws_replay(as_of: str):
    """Replay explorer for a historical date."""
    try:
        return _aws.replay(as_of).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aws/dashboard")
async def aws_dashboard():
    try:
        return _aws.dashboard().model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aws/search")
async def aws_search(q: str = Query(...), limit: int = Query(default=20, ge=1, le=100)):
    """Global search across companies, themes, reports, research, predictions, people."""
    try:
        return _aws.search(q, limit=limit).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aws/copilot")
async def aws_copilot(
    workspace: str = Query(default="company"),
    q: str = Query(default=""),
    ticker: str | None = None,
    theme_id: str | None = None,
    sector_id: str | None = None,
    research_id: str | None = None,
    as_of: str | None = None,
):
    """Context-aware AI copilot pack — never starts from an empty prompt."""
    try:
        return _aws.copilot(
            workspace=workspace,
            question=q,
            ticker=ticker,
            theme_id=theme_id,
            sector_id=sector_id,
            research_id=research_id,
            as_of=as_of,
        ).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aws/macro")
async def aws_macro(as_of: str | None = None):
    try:
        return _aws.macro(as_of=as_of).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aws/portfolio")
async def aws_portfolio(as_of: str | None = None):
    try:
        return _aws.portfolio(as_of=as_of).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aws/research")
async def aws_research(research_id: str | None = None):
    try:
        return _aws.research(research_id).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aws/cre")
async def aws_cre():
    try:
        return _aws.cre_workspace().model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aws/knowledge/{entity}")
async def aws_knowledge(entity: str):
    """Knowledge explorer — graph, themes, industries, research relationships."""
    try:
        return _aws.knowledge_explorer(entity).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ioc/health")
async def ioc_health():
    """Investment Operations Centre health (monitor-only mission control)."""
    return _ioc.health()


@router.get("/ioc/dashboard")
async def ioc_dashboard():
    """Ops dashboard: overall/engine/platform health, queues, failures, alerts."""
    try:
        return _ioc.dashboard().model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ioc/alerts")
async def ioc_alerts():
    try:
        rows = _ioc.alerts()
        return {
            "alerts": [a.model_dump(mode="json") for a in rows],
            "count": len(rows),
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ioc/providers")
async def ioc_providers():
    try:
        return _ioc.providers()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ioc/readiness")
async def ioc_readiness():
    """Morning / market-open readiness checklist."""
    try:
        return _ioc.readiness().model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ioc/report")
async def ioc_report(
    type: str = Query(
        default="daily_operations",
        description="daily_operations|morning_readiness|market_open|end_of_day|weekly_operations",
    ),
):
    try:
        return _ioc.report(type).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aip/health")
async def aip_health():
    """Alpha Improvement Programme health (research programme, not a platform)."""
    return _aip.health()


@router.get("/aip/roadmap")
async def aip_roadmap():
    """Long-term AIP research roadmap (AIP-01 … AIP-10)."""
    return _aip.roadmap()


@router.get("/aip/weights")
async def aip_weights():
    """Dynamic Weight Registry — shadow weight sets only."""
    try:
        rows = _aip.list_weights()
        return {
            "weight_sets": [w.model_dump(mode="json") for w in rows],
            "count": len(rows),
            "production_influence": False,
            "l4_remains_shadow": True,
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/aip/weights")
async def aip_register_weight(
    weight_set_id: str = Query(...),
    name: str = Query(...),
    e03: float = Query(default=0.7),
    e01: float = Query(default=0.2),
    e14: float = Query(default=0.1),
    e11: float = Query(default=0.05),
    e02: float = Query(default=0.0),
    regime: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    description: str = Query(default=""),
):
    """Register a shadow candidate weight set (never applied to production L4)."""
    try:
        ws = _aip.register_weight(
            weight_set_id=weight_set_id,
            name=name,
            weights={"E03": e03, "E01": e01, "E14": e14, "E11": e11, "E02": e02},
            description=description,
            regime=regime,
            sector=sector,
        )
        return ws.model_dump(mode="json")
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/aip/experiment")
async def aip_experiment(
    candidate_weight_set_id: str | None = Query(default="aip_e03_heavier_v1"),
    dataset_id: str = Query(default="golden_p0_v1"),
    workstream: str = Query(default="AIP-02"),
    hypothesis: str | None = Query(default=None),
    regime: str | None = Query(default=None),
    sector: str | None = Query(default=None),
):
    """Run an AIP shadow experiment vs L4 / E03 / replay / golden / paper portfolio."""
    try:
        req = ExperimentRequest(
            hypothesis=ExperimentHypothesis(
                statement=hypothesis
                or (
                    "Candidate L4 shadow weights improve measurable alpha metrics "
                    "versus current L4 without worsening risk or calibration."
                ),
                workstream=workstream,
                expected_effect="Positive research / portfolio deltas with evidence",
            ),
            candidate_weight_set_id=candidate_weight_set_id,
            dataset_id=dataset_id,
            regime=regime,
            sector=sector,
            name=f"{workstream}:{candidate_weight_set_id}",
        )
        result = _aip.run_experiment(req)
        return result.model_dump(mode="json")
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aip/experiments")
async def aip_experiments(limit: int = Query(default=50, ge=1, le=200)):
    try:
        rows = _aip.list_experiments(limit=limit)
        return {
            "experiments": [r.model_dump(mode="json") for r in rows],
            "count": len(rows),
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aip/experiments/{experiment_id}")
async def aip_experiment_get(experiment_id: str):
    try:
        row = _aip.get_experiment(experiment_id)
        if row is None:
            raise HTTPException(status_code=404, detail="experiment not found")
        return row.model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aip/contribution")
async def aip_contribution(
    dataset_id: str = Query(default="golden_p0_v1"),
    weight_set_id: str | None = Query(default=None),
):
    """Engine contribution + marginal information gain (AIP-03)."""
    try:
        return _aip.contribution(dataset_id, weight_set_id=weight_set_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aip/calibration")
async def aip_calibration():
    """Latest confidence calibration plan (suggestion only)."""
    try:
        plan = _aip.calibration()
        if plan is None:
            return {"plan": None, "note": "Run an experiment first"}
        return plan
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aip/attribution")
async def aip_attribution():
    try:
        report = _aip.attribution()
        if report is None:
            return {"report": None, "note": "Run an experiment first"}
        return report
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aip/house-view-evolution/{ticker}")
async def aip_house_view_evolution(
    ticker: str,
    dataset_id: str = Query(default="golden_p0_v1"),
):
    try:
        return _aip.house_view_evolution(ticker, dataset_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/aip/quality")
async def aip_quality(
    domain: str = Query(default="research"),
    evidence_count: int = Query(default=0),
    has_reasoning_package: bool = Query(default=False),
    has_house_view: bool = Query(default=False),
    contradiction_resolved: bool = Query(default=False),
    grounded: bool = Query(default=False),
    cites_evidence: bool = Query(default=False),
    confidence_stated: bool = Query(default=False),
    unknowns_stated: bool = Query(default=False),
    answer_chars: int = Query(default=0),
):
    """Research / client answer quality scoring (AIP-09 / AIP-10)."""
    try:
        score = _aip.score_quality(
            {
                "domain": domain,
                "evidence_count": evidence_count,
                "has_reasoning_package": has_reasoning_package,
                "has_house_view": has_house_view,
                "contradiction_resolved": contradiction_resolved,
                "grounded": grounded,
                "cites_evidence": cites_evidence,
                "confidence_stated": confidence_stated,
                "unknowns_stated": unknowns_stated,
                "answer_chars": answer_chars,
            }
        )
        return score.model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aip/promotion")
async def aip_promotion():
    """Promotion evidence checklist — never ready when AIP_PROMOTION=false."""
    try:
        return _aip.promotion()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aip/dashboard")
async def aip_dashboard():
    try:
        return _aip.dashboard()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- KF1 Knowledge Foundation (structured knowledge over KIP; no redesign) ---


@router.get("/kf/health")
async def kf_health():
    return _kf.health()


@router.get("/kf/coverage")
async def kf_coverage():
    try:
        return _kf.coverage()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/kf/seed")
async def kf_seed():
    try:
        return _kf.seed()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/kf/rebuild")
async def kf_rebuild():
    try:
        return _kf.rebuild()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kf/search")
async def kf_search(q: str = Query(...), limit: int = Query(default=12, ge=1, le=50)):
    try:
        return _kf.search(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kf/companies")
async def kf_companies():
    try:
        return {"companies": _kf.list_companies()}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kf/company/{ticker}")
async def kf_company(ticker: str):
    try:
        return _kf.get_company(ticker)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kf/sectors")
async def kf_sectors():
    try:
        return {"sectors": _kf.list_sectors()}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kf/sector/{sector_id}")
async def kf_sector(sector_id: str):
    try:
        return _kf.get_sector(sector_id)
    except (RuntimeError, KeyError) as exc:
        raise HTTPException(status_code=404 if isinstance(exc, KeyError) else 400, detail=str(exc)) from exc


@router.get("/kf/themes")
async def kf_themes():
    try:
        return {"themes": _kf.list_themes()}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kf/theme/{theme_id}")
async def kf_theme(theme_id: str):
    try:
        return _kf.get_theme(theme_id)
    except (RuntimeError, KeyError) as exc:
        raise HTTPException(status_code=404 if isinstance(exc, KeyError) else 400, detail=str(exc)) from exc


@router.get("/kf/macros")
async def kf_macros():
    try:
        return {"macros": _kf.list_macros()}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kf/macro/{macro_id}")
async def kf_macro(macro_id: str):
    try:
        return _kf.get_macro(macro_id)
    except (RuntimeError, KeyError) as exc:
        raise HTTPException(status_code=404 if isinstance(exc, KeyError) else 400, detail=str(exc)) from exc


@router.get("/kf/predictions")
async def kf_predictions():
    try:
        return {"predictions": _kf.list_predictions()}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kf/extracts")
async def kf_extracts():
    try:
        return {"extracts": _kf.list_extracts()}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- KCV1 Knowledge Corpus (populate/improve KF; no KF/KIP/IRP/RSP redesign) ---


@router.get("/kc/health")
async def kc_health():
    return _kc.health()


@router.get("/kc/metrics")
async def kc_metrics():
    try:
        return _kc.metrics()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kc/dashboard")
async def kc_dashboard():
    try:
        return _kc.dashboard()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/kc/populate")
async def kc_populate(rebuild_kip: bool = Query(default=True)):
    try:
        return _kc.populate(rebuild_kip=rebuild_kip)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/kc/universe")
async def kc_universe():
    try:
        return _kc.ensure_universe()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kc/gaps")
async def kc_gaps():
    try:
        return _kc.gaps()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kc/learning")
async def kc_learning():
    try:
        return _kc.learning()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kc/quality")
async def kc_quality(kind: str | None = Query(default=None), key: str | None = Query(default=None)):
    try:
        return _kc.quality(kind=kind, key=key)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/kc/consult")
async def kc_consult(q: str = Query(...), limit: int = Query(default=8, ge=1, le=40)):
    try:
        return _kc.consult(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- AOI v1 Open Intelligence (public acquisition → KC/KF; no core redesign) ---


@router.get("/aoi/health")
async def aoi_health():
    return _aoi.health()


@router.get("/aoi/dashboard")
async def aoi_dashboard():
    try:
        return _aoi.dashboard()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/aoi/registry/seed")
async def aoi_registry_seed():
    try:
        return _aoi.seed_registry()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/aoi/run")
async def aoi_run(
    connector_id: str | None = Query(default=None),
    limit_per_connector: int | None = Query(default=30, ge=1, le=500),
    publish: bool = Query(default=True),
):
    try:
        ids = [connector_id] if connector_id else None
        return _aoi.run_cycle(connector_ids=ids, limit_per_connector=limit_per_connector, publish=publish)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aoi/companies")
async def aoi_companies(universe: str | None = Query(default="nifty_50")):
    try:
        return _aoi.list_companies(universe=universe)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aoi/company/{key}")
async def aoi_company(key: str):
    try:
        return _aoi.get_company(key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aoi/search")
async def aoi_search(q: str = Query(...), limit: int = Query(default=20, ge=1, le=100)):
    try:
        return _aoi.search(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aoi/consult")
async def aoi_consult(q: str = Query(...), limit: int = Query(default=8, ge=1, le=40)):
    try:
        return _aoi.consult(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aoi/connectors")
async def aoi_connectors():
    try:
        return _aoi.connector_health()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aoi/scheduler")
async def aoi_scheduler():
    try:
        return _aoi.pipeline.scheduler.status()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aoi/gaps")
async def aoi_gaps():
    try:
        dash = _aoi.dashboard()
        return {"count": len(dash.get("gaps") or []), "tasks": dash.get("gaps") or []}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/aoi/learning")
async def aoi_learning():
    try:
        dash = _aoi.dashboard()
        return dash.get("learning") or {}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- EVE v1 Evidence & Verification (between AOI and KCV/KF; no core redesign) ---


@router.get("/eve/health")
async def eve_health():
    return _eve.health()


@router.get("/eve/dashboard")
async def eve_dashboard():
    try:
        return _eve.dashboard()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/eve/evidence")
async def eve_evidence(
    company_id: str | None = Query(default=None),
    fact_key: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    try:
        return _eve.list_evidence(company_id=company_id, fact_key=fact_key, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/eve/evidence/{evidence_id}")
async def eve_evidence_one(evidence_id: str):
    try:
        return _eve.get_evidence(evidence_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/eve/company/{key}")
async def eve_company(key: str):
    try:
        return _eve.company_pack(key)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/eve/conflicts")
async def eve_conflicts(status: str = Query(default="open")):
    try:
        return _eve.conflicts(status=status)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/eve/timeline")
async def eve_timeline(
    company_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return _eve.timeline(company_id=company_id, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/eve/trust")
async def eve_trust():
    try:
        return _eve.trust()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/eve/source")
async def eve_source():
    try:
        return _eve.list_sources()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/eve/verification")
async def eve_verification():
    try:
        return _eve.verification_queue()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/eve/verification/run")
async def eve_verification_run():
    try:
        return _eve.run_verification_jobs()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/eve/search")
async def eve_search(q: str = Query(...), limit: int = Query(default=20, ge=1, le=100)):
    try:
        return _eve.search(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/eve/consult")
async def eve_consult(q: str = Query(...), limit: int = Query(default=8, ge=1, le=40)):
    try:
        return _eve.consult(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/eve/audit")
async def eve_audit(limit: int = Query(default=50, ge=1, le=200)):
    try:
        return _eve.audit_logs(limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- IIE v1 Investment Intelligence (after EVE/KCV/KF, before reasoning; no core redesign) ---


@router.get("/iie/health")
async def iie_health():
    return _iie.health()


@router.get("/iie/dashboard")
async def iie_dashboard():
    try:
        return _iie.dashboard()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/iie/analyse")
async def iie_analyse(key: str = Query(...)):
    try:
        return _iie.analyse(key)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/iie/batch")
async def iie_batch(limit: int = Query(default=20, ge=1, le=100)):
    try:
        return _iie.run_batch(limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/iie/company/{key}")
async def iie_company(key: str):
    try:
        return _iie.company(key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/iie/sector")
async def iie_sectors():
    try:
        return _iie.list_sectors()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/iie/sector/{sector_id}")
async def iie_sector(sector_id: str):
    try:
        return _iie.sector(sector_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/iie/theme")
async def iie_themes():
    try:
        return _iie.list_themes()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/iie/theme/{theme_id}")
async def iie_theme(theme_id: str):
    try:
        return _iie.theme(theme_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/iie/thesis/{key}")
async def iie_thesis(key: str):
    try:
        return _iie.thesis(key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/iie/scenario/{key}")
async def iie_scenario(key: str):
    try:
        return _iie.scenario(key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/iie/catalysts")
async def iie_catalysts(
    company_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return _iie.catalysts(company_id=company_id, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/iie/risks")
async def iie_risks(
    company_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return _iie.risks(company_id=company_id, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/iie/opportunities")
async def iie_opportunities(
    company_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return _iie.opportunities(company_id=company_id, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/iie/compare")
async def iie_compare(
    companies: str = Query(..., description="Comma-separated company ids/symbols"),
    dimensions: str | None = Query(default=None),
):
    try:
        ids = [c.strip() for c in companies.split(",") if c.strip()]
        dims = [d.strip() for d in dimensions.split(",") if d.strip()] if dimensions else None
        return _iie.compare(ids, dimensions=dims)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/iie/monitor/{key}")
async def iie_monitor(key: str):
    try:
        return _iie.monitor(key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/iie/dna/{key}")
async def iie_dna(key: str):
    try:
        return _iie.dna(key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/iie/macro")
async def iie_macro(event: str = Query(...)):
    try:
        return _iie.macro(event)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/iie/evolution")
async def iie_evolution(
    entity_id: str | None = Query(default=None),
    object_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return _iie.evolution(entity_id=entity_id, object_type=object_type, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/iie/search")
async def iie_search(q: str = Query(...), limit: int = Query(default=20, ge=1, le=100)):
    try:
        return _iie.search(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/iie/consult")
async def iie_consult(q: str = Query(...), limit: int = Query(default=8, ge=1, le=40)):
    try:
        return _iie.consult(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- FLE v1 Forecasting & Learning (after IIE, before reasoning; no core redesign) ---


@router.get("/fle/health")
async def fle_health():
    return _fle.health()


@router.get("/fle/dashboard")
async def fle_dashboard():
    try:
        return _fle.dashboard()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fle/forecast")
async def fle_list_forecasts(
    company_id: str | None = Query(default=None),
    sector_id: str | None = Query(default=None),
    metric: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return _fle.list_forecasts(
            company_id=company_id, sector_id=sector_id, metric=metric, status=status, limit=limit
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fle/forecast")
async def fle_create_forecast(payload: dict[str, Any] = Body(default_factory=dict)):
    try:
        return _fle.create_forecast(payload or {})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fle/forecast/{forecast_id}")
async def fle_get_forecast(forecast_id: str):
    try:
        return _fle.get_forecast(forecast_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fle/forecast/{forecast_id}/resolve")
async def fle_resolve_forecast(forecast_id: str, payload: dict[str, Any] = Body(default_factory=dict)):
    try:
        return _fle.resolve(forecast_id, payload or {})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fle/forecast/{forecast_id}/version")
async def fle_version_forecast(forecast_id: str, payload: dict[str, Any] = Body(default_factory=dict)):
    try:
        return _fle.version(forecast_id, payload or {})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fle/compare/{forecast_id}")
async def fle_compare(forecast_id: str):
    try:
        return _fle.compare(forecast_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fle/company/{key}")
async def fle_company(key: str):
    try:
        return _fle.company(key)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fle/outcomes")
async def fle_outcomes(
    company_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return _fle.outcomes(company_id=company_id, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fle/learning")
async def fle_learning(
    q: str | None = Query(default=None),
    company_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return _fle.learning(q=q, company_id=company_id, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fle/calibration")
async def fle_calibration():
    try:
        return _fle.calibration()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fle/scenarios/{forecast_id}")
async def fle_scenarios(forecast_id: str):
    try:
        return _fle.scenarios(forecast_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fle/accuracy")
async def fle_accuracy(
    scope: str | None = Query(default=None),
    scope_id: str | None = Query(default=None),
):
    try:
        return _fle.accuracy(scope=scope, scope_id=scope_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fle/history")
async def fle_history(
    company_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return _fle.history(company_id=company_id, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fle/generate")
async def fle_generate(key: str = Query(...)):
    try:
        return _fle.generate(key)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fle/batch")
async def fle_batch(limit: int = Query(default=20, ge=1, le=100)):
    try:
        return _fle.batch(limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fle/jobs")
async def fle_jobs():
    try:
        return _fle.run_jobs()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fle/search")
async def fle_search(q: str = Query(...), limit: int = Query(default=20, ge=1, le=100)):
    try:
        return _fle.search(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fle/consult")
async def fle_consult(q: str = Query(...), limit: int = Query(default=8, ge=1, le=40)):
    try:
        return _fle.consult(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- MEE v1 Market Event Engine (after FLE; event backbone; no core redesign) ---


@router.get("/mee/health")
async def mee_health():
    return _mee.health()


@router.get("/mee/dashboard")
async def mee_dashboard():
    try:
        return _mee.dashboard()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mee/events")
async def mee_list_events(
    company_id: str | None = Query(default=None),
    sector_id: str | None = Query(default=None),
    theme_id: str | None = Query(default=None),
    category: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return _mee.list_events(
            company_id=company_id,
            sector_id=sector_id,
            theme_id=theme_id,
            category=category,
            event_type=event_type,
            status=status,
            severity=severity,
            limit=limit,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/mee/events")
async def mee_create_event(payload: dict[str, Any] = Body(default_factory=dict)):
    try:
        return _mee.create_event(payload or {})
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mee/events/{event_id}")
async def mee_get_event(event_id: str):
    try:
        return _mee.get_event(event_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/mee/events/{event_id}/verify")
async def mee_verify_event(event_id: str):
    try:
        return _mee.verify(event_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/mee/events/{event_id}/version")
async def mee_version_event(event_id: str, payload: dict[str, Any] = Body(default_factory=dict)):
    try:
        return _mee.version(event_id, payload or {})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mee/company/{key}")
async def mee_company(key: str):
    try:
        return _mee.company(key)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mee/sector/{sector_id}")
async def mee_sector(sector_id: str):
    try:
        return _mee.sector(sector_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mee/theme/{theme_id}")
async def mee_theme(theme_id: str):
    try:
        return _mee.theme(theme_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mee/timeline")
async def mee_timeline(
    scope: str = Query(default="company"),
    scope_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return _mee.timeline(scope=scope, scope_id=scope_id, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mee/impact/{event_id}")
async def mee_impact(event_id: str):
    try:
        return _mee.impact(event_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mee/relationships")
async def mee_relationships(
    event_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    try:
        return _mee.relationships(event_id=event_id, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mee/history")
async def mee_history(
    company_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return _mee.history(company_id=company_id, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mee/similar/{event_id}")
async def mee_similar(event_id: str, limit: int = Query(default=8, ge=1, le=40)):
    try:
        return _mee.similar(event_id, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/mee/cycle")
async def mee_cycle(limit: int = Query(default=40, ge=1, le=200)):
    try:
        return _mee.run_cycle(limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mee/search")
async def mee_search(q: str = Query(...), limit: int = Query(default=20, ge=1, le=100)):
    try:
        return _mee.search(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mee/consult")
async def mee_consult(q: str = Query(...), limit: int = Query(default=8, ge=1, le=40)):
    try:
        return _mee.consult(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- CAE v1 Context Assembly (Ask AGI orchestration gateway; no core redesign) ---


@router.get("/cae/health")
async def cae_health():
    return _cae.health()


@router.get("/cae/dashboard")
async def cae_dashboard():
    try:
        return _cae.dashboard()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/cae/context")
async def cae_context(
    q: str = Query(...),
    ticker: str | None = Query(default=None),
    use_cache: bool | None = Query(default=None),
):
    try:
        return _cae.context(q, ticker=ticker, use_cache=use_cache)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/cae/query-plan")
async def cae_query_plan(q: str = Query(...), ticker: str | None = Query(default=None)):
    try:
        return _cae.query_plan(q, ticker=ticker)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/cae/retrieval")
async def cae_retrieval(q: str = Query(...), ticker: str | None = Query(default=None)):
    try:
        return _cae.retrieve(q, ticker=ticker)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/cae/cache")
async def cae_cache_stats():
    try:
        return _cae.cache(action="stats")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/cae/cache/clear")
async def cae_cache_clear():
    try:
        return _cae.cache(action="clear")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/cae/metrics")
async def cae_metrics():
    try:
        return _cae.metrics()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/cae/explain/{package_id}")
async def cae_explain(package_id: str):
    try:
        return _cae.explain(package_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/cae/package/{package_id}")
async def cae_package(package_id: str):
    try:
        return _cae.get_package(package_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/cae/search")
async def cae_search(q: str = Query(...), limit: int = Query(default=20, ge=1, le=100)):
    try:
        return _cae.search(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- IB v1 Intelligence Bus (event-driven backbone; no platform redesign) ---


@router.get("/ib/health")
async def ib_health():
    return _ib.health()


@router.get("/ib/dashboard")
async def ib_dashboard():
    try:
        return _ib.dashboard()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ib/events")
async def ib_events(
    event_type: str | None = Query(default=None),
    producer: str | None = Query(default=None),
    aggregate_id: str | None = Query(default=None),
    correlation_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
):
    try:
        return _ib.list_events(
            event_type=event_type,
            producer=producer,
            aggregate_id=aggregate_id,
            correlation_id=correlation_id,
            limit=limit,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ib/publish")
async def ib_publish(payload: dict[str, Any] = Body(default={})):
    try:
        return _ib.publish(payload or {})
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ib/subscriptions")
async def ib_subscriptions_list():
    try:
        return _ib.list_subscriptions()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ib/subscriptions")
async def ib_subscriptions_create(payload: dict[str, Any] = Body(default={})):
    try:
        return _ib.subscribe(payload or {})
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ib/replay")
async def ib_replay(payload: dict[str, Any] = Body(default={})):
    try:
        return _ib.replay(payload or {})
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ib/history")
async def ib_history(
    aggregate_id: str | None = Query(default=None),
    correlation_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
):
    try:
        return _ib.history(aggregate_id=aggregate_id, correlation_id=correlation_id, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ib/metrics")
async def ib_metrics():
    try:
        return _ib.metrics()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ib/traces")
async def ib_traces(
    correlation_id: str | None = Query(default=None),
    event_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return _ib.traces(correlation_id=correlation_id, event_id=event_id, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ib/dead-letter")
async def ib_dead_letter(limit: int = Query(default=50, ge=1, le=200)):
    try:
        return _ib.dead_letter(limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ib/dead-letter/{dlq_id}/resolve")
async def ib_dead_letter_resolve(dlq_id: str):
    try:
        return _ib.dead_letter(resolve_id=dlq_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ib/schema")
async def ib_schema(event_type: str | None = Query(default=None)):
    try:
        return _ib.schemas(event_type=event_type)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ib/demo-chain")
async def ib_demo_chain(company_symbol: str = Query(default="INFY")):
    try:
        return _ib.publish_chain_demo(company_symbol=company_symbol)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- VE v1 Valuation Engine (after FLE/MEE; no platform redesign) ---


@router.get("/ve/health")
async def ve_health():
    return _ve.health()


@router.get("/ve/dashboard")
async def ve_dashboard():
    try:
        return _ve.dashboard()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ve/company/{key}")
async def ve_company(key: str, value_if_empty: bool = Query(default=True)):
    try:
        return _ve.company(key, value_if_empty=value_if_empty)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ve/model")
async def ve_model(
    model: str = Query(...),
    key: str = Query(...),
    market_price: float | None = Query(default=None),
):
    try:
        return _ve.model(model, key, market_price=market_price)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ve/history")
async def ve_history(key: str = Query(...), limit: int = Query(default=50, ge=1, le=200)):
    try:
        return _ve.history(key, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ve/scenarios")
async def ve_scenarios(key: str = Query(...)):
    try:
        return _ve.scenarios(key)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ve/compare")
async def ve_compare(key: str = Query(...), peers: str | None = Query(default=None)):
    try:
        peer_list = [p.strip() for p in (peers or "").split(",") if p.strip()] or None
        return _ve.compare(key, peers=peer_list)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ve/sensitivity")
async def ve_sensitivity(key: str = Query(...)):
    try:
        return _ve.sensitivity(key)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ve/search")
async def ve_search(q: str = Query(...), limit: int = Query(default=20, ge=1, le=100)):
    try:
        return _ve.search(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ve/consult")
async def ve_consult(q: str = Query(...), limit: int = Query(default=8, ge=1, le=40)):
    try:
        return _ve.consult(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ve/value")
async def ve_value(payload: dict[str, Any] = Body(default={})):
    try:
        key = str((payload or {}).get("key") or (payload or {}).get("symbol") or "").strip()
        if not key:
            raise RuntimeError("key is required")
        models = (payload or {}).get("models")
        market_price = (payload or {}).get("market_price")
        fiscal_year = (payload or {}).get("fiscal_year")
        return _ve.value(
            key,
            models=models,
            market_price=float(market_price) if market_price is not None else None,
            trigger=str((payload or {}).get("trigger") or "api"),
            fiscal_year=fiscal_year,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ve/valuation/{valuation_id}")
async def ve_valuation(valuation_id: str):
    try:
        return _ve.get_valuation(valuation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- FIML v1 Financial Intelligence Model Library (not an engine; no platform redesign) ---


@router.get("/fiml/health")
async def fiml_health():
    return _fiml.health()


@router.get("/fiml/dashboard")
async def fiml_dashboard():
    try:
        return _fiml.dashboard()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fiml/models")
async def fiml_models():
    try:
        return _fiml.list_models()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fiml/industries")
async def fiml_industries():
    try:
        return _fiml.industries()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fiml/analyse/{domain}")
async def fiml_analyse(domain: str, payload: dict[str, Any] = Body(default={})):
    try:
        return _fiml.analyse(domain, payload or {})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fiml/score/{domain}")
async def fiml_score(domain: str, payload: dict[str, Any] = Body(default={})):
    try:
        return _fiml.score(domain, payload or {})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fiml/explain/{domain}")
async def fiml_explain(domain: str, payload: dict[str, Any] = Body(default={})):
    try:
        return _fiml.explain(domain, payload or {})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fiml/compare/{domain}")
async def fiml_compare(domain: str, payload: dict[str, Any] = Body(default={})):
    try:
        return _fiml.compare(domain, payload or {})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fiml/monitor/{domain}")
async def fiml_monitor(domain: str, payload: dict[str, Any] = Body(default={})):
    try:
        return _fiml.monitor(domain, payload or {})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fiml/relationships/{domain}")
async def fiml_relationships(domain: str, payload: dict[str, Any] = Body(default={})):
    try:
        return _fiml.relationships(domain, payload or {})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fiml/bundle")
async def fiml_bundle(payload: dict[str, Any] = Body(default={})):
    try:
        return _fiml.bundle(payload or {})
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fiml/consumer/{engine}")
async def fiml_consumer(engine: str, payload: dict[str, Any] = Body(default={})):
    try:
        return _fiml.consumer(engine, payload or {})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fiml/search")
async def fiml_search(
    q: str = Query(...),
    domain: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    try:
        return _fiml.search(q, domain=domain, limit=limit)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fiml/metrics")
async def fiml_metrics():
    try:
        return _fiml.metrics()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fiml/graph")
async def fiml_graph():
    try:
        return _fiml.graph()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- AGI Finance Academy v1 (curriculum library; not an engine; no locked-engine redesign) ---


@router.get("/academy/health")
async def academy_health():
    return _academy.health()


@router.get("/academy/dashboard")
async def academy_dashboard():
    try:
        return _academy.dashboard()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/academy/course")
async def academy_course():
    try:
        return _academy.course()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/academy/concepts")
async def academy_concepts(tag: str | None = Query(default=None)):
    try:
        return _academy.list_concepts(tag=tag)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/academy/concepts/{concept_id}")
async def academy_concept(concept_id: str):
    try:
        return _academy.get_concept(concept_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/academy/teach/{concept_id}")
async def academy_teach(concept_id: str):
    try:
        return _academy.teach(concept_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/academy/graph")
async def academy_graph():
    try:
        return _academy.graph()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/academy/neighborhood/{concept_id}")
async def academy_neighborhood(concept_id: str):
    try:
        return _academy.neighborhood(concept_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/academy/causal-models")
async def academy_causal_models():
    try:
        return _academy.causal_models()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/academy/mental-models")
async def academy_mental_models():
    try:
        return _academy.mental_models()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/academy/quality")
async def academy_quality():
    try:
        return _academy.quality()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/academy/provenance")
async def academy_provenance():
    try:
        return _academy.provenance()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/academy/enrich/{concept_id}")
async def academy_enrich(concept_id: str):
    try:
        return _academy.enrich(concept_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/academy/exams")
async def academy_exams():
    try:
        return _academy.exams()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/academy/exams/{question_id}")
async def academy_exam_answer(question_id: str):
    try:
        return _academy.answer(question_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/academy/consumer/{engine}")
async def academy_consumer(engine: str, payload: dict[str, Any] = Body(default={})):
    try:
        return _academy.consumer(engine, payload or {})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/academy/search")
async def academy_search(q: str = Query(...), limit: int = Query(default=20, ge=1, le=100)):
    try:
        return _academy.search(q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/academy/completion")
async def academy_completion():
    try:
        return _academy.completion()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/academy/metrics")
async def academy_metrics():
    try:
        return _academy.metrics()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- IRP V1 (above KIP/RSP, below Ask AGI; no platform redesign) ---


@router.get("/irp/health")
async def irp_health():
    return _irp.health()


@router.post("/irp/run")
async def irp_run(
    question: str = Query(...),
    ticker: str | None = Query(default=None),
):
    try:
        return _irp.run(question, ticker=ticker).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/irp/learning")
async def irp_learning(limit: int = Query(default=20, ge=1, le=100)):
    try:
        return {"records": _irp.recent_learning(limit=limit)}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- UI Aggregation Layer (client facade; no engine name exposure) ---


@router.get("/ui/health")
async def ui_health():
    return _ui.health()


@router.get("/ui/home")
async def ui_home():
    try:
        return _ui.home().model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ui/calendar")
async def ui_calendar():
    try:
        return _ui.calendar()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ui/company/{ticker}")
async def ui_company(ticker: str):
    try:
        return _ui.company(ticker).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ui/search")
async def ui_search(
    question: str = Query(...),
    ticker: str | None = Query(default=None),
):
    try:
        return _ui.search(question, ticker=ticker).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ui/autocomplete")
async def ui_autocomplete(q: str = Query(default="")):
    try:
        return _ui.autocomplete(q).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ui/article/{article_id}")
async def ui_article(
    article_id: str,
    ticker: str | None = Query(default=None),
):
    try:
        return _ui.article(article_id, ticker=ticker).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ui/timeline/{entity}")
async def ui_timeline(entity: str):
    try:
        return _ui.timeline(entity).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ui/research/{research_id}")
async def ui_research(research_id: str):
    try:
        return _ui.research(research_id).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ui/theme/{theme_id}")
async def ui_theme(theme_id: str):
    try:
        return _ui.theme(theme_id).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ui/sector/{sector_id}")
async def ui_sector(sector_id: str):
    try:
        return _ui.sector(sector_id).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ui/dashboard")
async def ui_dashboard():
    try:
        return _ui.dashboard().model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ui/macro")
async def ui_macro():
    try:
        return _ui.macro().model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ui/predictions")
async def ui_predictions():
    try:
        return _ui.predictions().model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ui/portfolio")
async def ui_portfolio():
    try:
        return _ui.portfolio().model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ui/copilot")
async def ui_copilot(
    page: str = Query(default="home"),
    question: str = Query(default=""),
    ticker: str | None = Query(default=None),
    theme_id: str | None = Query(default=None),
    sector_id: str | None = Query(default=None),
    research_id: str | None = Query(default=None),
):
    try:
        return _ui.copilot(
            page=page,
            question=question,
            ticker=ticker,
            theme_id=theme_id,
            sector_id=sector_id,
            research_id=research_id,
        ).model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ui/workflow")
async def ui_workflow():
    try:
        return _ui.workflow().model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/orch/l2/trigger", dependencies=[Depends(require_token)])
async def orch_l2_trigger(body: BuildBatchRequest):
    """Enqueue + drain an L2 feature build. Engines must not call this for research."""
    if body.feature_ids:
        _l2.enqueue_manual(
            as_of=body.as_of,
            symbol=body.symbol,
            feature_ids=body.feature_ids,
            ctx=body.ctx,
        )
    else:
        event = MarketDataUpdateEvent(
            update_type=body.update_type,
            symbol=body.symbol,
            as_of=body.as_of,
            input_keys=body.input_keys,
        )
        _l2.dirty.mark(event)
        _l2.queue.enqueue(
            as_of=body.as_of,
            symbol=body.symbol,
            feature_ids=_l2.dirty.snapshot(symbol=body.symbol, as_of=body.as_of),
            ctx=body.ctx,
            update_type=body.update_type,
        )
    result = _l2.drain(parallel=body.parallel, max_workers=body.max_workers)
    if result is None:
        return {"ok": True, "status": "empty", "impacted": []}
    return {
        "ok": True,
        "status": result.status,
        "batch_id": result.batch_id,
        "orch_run_id": result.orch_run_id,
        "impacted": result.impacted,
        "snapshot_id": result.snapshot.snapshot_id if result.snapshot else None,
        "ready": result.ready.model_dump(mode="json") if result.ready else None,
        "builds": [b.model_dump(mode="json") for b in result.builds],
    }


@router.get("/orch/l2/builds", dependencies=[Depends(require_token)])
async def orch_l2_builds(limit: int = 50):
    return [b.model_dump(mode="json") for b in _l2.build_ledger.recent(limit=min(limit, 200))]


@router.get("/orch/l2/builds/{build_id}", dependencies=[Depends(require_token)])
async def orch_l2_build(build_id: str):
    row = _l2.build_ledger.get(build_id)
    if row is None:
        raise HTTPException(status_code=404, detail="build not found")
    return row.model_dump(mode="json")


@router.post("/orch/l2/drain", dependencies=[Depends(require_token)])
async def orch_l2_drain(parallel: bool = True, max_workers: int = 4):
    result = _l2.drain(parallel=parallel, max_workers=max_workers)
    if result is None:
        return {"ok": True, "status": "empty"}
    return {
        "ok": True,
        "status": result.status,
        "batch_id": result.batch_id,
        "impacted": result.impacted,
        "ready": result.ready.model_dump(mode="json") if result.ready else None,
    }


@router.get("/market-data/health")
async def market_data_health():
    """WS02 provider health + cache/latency metrics (no provider-native payloads)."""
    return _market_data.health.snapshot()


@router.get("/features/health")
async def features_health():
    """WS03 Feature Registry health + cache/metrics."""
    return _features.health()


@router.get("/features", dependencies=[Depends(require_token)])
async def list_features():
    return [m.model_dump(mode="json") for m in _features.list_features()]


@router.get("/features/dependency-order", dependencies=[Depends(require_token)])
async def feature_dependency_order(feature_id: str | None = None):
    ids = [feature_id] if feature_id else None
    return {"order": _features.dependency_order(ids)}


@router.post("/features/register", dependencies=[Depends(require_token)])
async def register_feature(body: FeatureMetadata):
    _features.register_metadata(body)
    return {"ok": True, "feature_id": body.feature_id}


@router.get("/features/schedule/frequencies", dependencies=[Depends(require_token)])
async def feature_schedule_frequencies():
    """Calculation Scheduler frequency map (topo-ordered calculator IDs)."""
    return {"frequencies": _features.scheduler.frequencies()}


@router.get("/features/schedule/plan", dependencies=[Depends(require_token)])
async def feature_schedule_plan(
    as_of: str = Query(...),
    refresh_frequency: str | None = None,
    feature_id: list[str] | None = Query(default=None),
):
    plan = _features.scheduler.plan(
        as_of=as_of,
        refresh_frequency=refresh_frequency,
        feature_ids=feature_id,
    )
    return {
        "as_of": plan.as_of,
        "refresh_frequency": plan.refresh_frequency,
        "feature_ids": plan.feature_ids,
        "symbols": plan.symbols,
    }


@router.get("/features/{feature_id}", dependencies=[Depends(require_token)])
async def get_feature_metadata(feature_id: str):
    meta = _features.get_metadata(feature_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="feature not found")
    return meta.model_dump(mode="json")


@router.get("/features/{feature_id}/value", dependencies=[Depends(require_token)])
async def get_feature_value(
    feature_id: str,
    as_of: str = Query(...),
    symbol: str | None = None,
    pit_mode: bool = True,
):
    value = _features.get(feature_id, symbol=symbol, as_of=as_of, pit_mode=pit_mode)
    if value is None:
        raise HTTPException(status_code=404, detail="feature value not found")
    return value.model_dump(mode="json")


@router.post("/research/runs", response_model=ResearchRun, dependencies=[Depends(require_token)])
async def create_run(body: ResearchRunCreate):
    return await _director.execute(body)


@router.get("/research/runs/{run_id}", response_model=ResearchRun, dependencies=[Depends(require_token)])
async def get_run(run_id: str):
    run = await _store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/research/runs", response_model=list[ResearchRun], dependencies=[Depends(require_token)])
async def list_runs(desk: str | None = None, limit: int = 10):
    return await _store.latest_runs(desk=desk, limit=min(limit, 50))


@router.post("/eval/predictions", response_model=PredictionRecord, dependencies=[Depends(require_token)])
async def record_prediction(body: PredictionRecord):
    return _eval.record(body)


@router.get("/eval/predictions/pending", response_model=list[PredictionRecord], dependencies=[Depends(require_token)])
async def pending_predictions(limit: int = 50):
    return _eval.list_pending(limit=limit)
