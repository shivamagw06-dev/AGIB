from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from app.agents.registry import list_agents
from app.core.config import Settings, get_settings
from app.eval.evaluation_agent import EvaluationAgent
from app.features.models import FeatureMetadata
from app.features.service import FeatureRegistryService
from app.market_data.client import MarketDataClient
from app.memory.store import ResearchStore
from app.orch.ledger import OrchLedger
from app.orchestration.director import ResearchDirector
from app.schemas.models import PredictionRecord, ResearchRun, ResearchRunCreate

router = APIRouter(prefix="/v1")
_store = ResearchStore()
_director = ResearchDirector(store=_store)
_eval = EvaluationAgent()
<<<<<<< HEAD
_market_data = MarketDataClient.from_settings(get_settings())
_features = FeatureRegistryService()
=======
_orch_ledger = OrchLedger()
>>>>>>> 89c8748f (Implement WBS S01 EngineState SSOT and ORCH run ledger.)


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


<<<<<<< HEAD
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
=======
@router.get("/orch/status")
async def orch_status():
    """ORCH control-plane status (Document ID ORCH; not E00 Layer 5 / E10)."""
    return _orch_ledger.status_summary()
>>>>>>> 89c8748f (Implement WBS S01 EngineState SSOT and ORCH run ledger.)


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
