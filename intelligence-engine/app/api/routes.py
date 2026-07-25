from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query

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
_l4 = L4Service(e01=_e01, e14=_e14, e02=_e02, e03=_e03, orch_ledger=_orch_ledger)
_e10 = E10Service(l4=_l4, e14=_e14, e02=_e02, orch_ledger=_orch_ledger)
_validation = ValidationService()
_cre = CREService()


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
