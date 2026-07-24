from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.agents.registry import list_agents
from app.core.config import Settings, get_settings
from app.eval.evaluation_agent import EvaluationAgent
from app.memory.store import ResearchStore
from app.orchestration.director import ResearchDirector
from app.portfolio.normalize import MODEL_PORTFOLIOS
from app.portfolio.pack import build_portfolio_package, evaluate_scenario
from app.schemas.models import (
    DeskType,
    PortfolioIngestRequest,
    PortfolioPackage,
    PredictionRecord,
    ResearchRun,
    ResearchRunCreate,
)

router = APIRouter(prefix="/v1")
_store = ResearchStore()
_director = ResearchDirector(store=_store)
_eval = EvaluationAgent()


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


@router.get("/portfolio/models", dependencies=[Depends(require_token)])
async def list_model_portfolios():
    return {
        "models": {
            mid: [
                {"symbol": h["symbol"], "weight": h["weight"], "sector": h.get("sector")}
                for h in rows
            ]
            for mid, rows in MODEL_PORTFOLIOS.items()
        },
        "note": "Identity weight templates only — not performance claims.",
    }


@router.post("/portfolio/normalize", response_model=PortfolioPackage, dependencies=[Depends(require_token)])
async def normalize_portfolio(body: PortfolioIngestRequest):
    """Normalize manual/CSV/model holdings into PortfolioPackage (no CIO run)."""
    try:
        return build_portfolio_package(req=body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/portfolio/ingest", response_model=PortfolioPackage, dependencies=[Depends(require_token)])
async def ingest_portfolio(body: PortfolioIngestRequest):
    """Alias of normalize — common Portfolio schema ingestion."""
    return await normalize_portfolio(body)


class ScenarioRequest(BaseModel):
    question: str
    portfolio: PortfolioIngestRequest | None = None


@router.post("/portfolio/scenario", dependencies=[Depends(require_token)])
async def portfolio_scenario(body: ScenarioRequest):
    package = None
    if body.portfolio is not None:
        package = build_portfolio_package(req=body.portfolio)
    return evaluate_scenario(body.question, package)


@router.post("/portfolio/office", response_model=ResearchRun, dependencies=[Depends(require_token)])
async def run_portfolio_office(body: PortfolioIngestRequest):
    """Full Portfolio Office desk run via Research Director + CIO."""
    create = ResearchRunCreate(
        desk=DeskType.PORTFOLIO,
        query=f"Portfolio Office: {body.name}",
        symbols=[str(h.get("symbol") or "") for h in (body.holdings or []) if h.get("symbol")],
        metadata={"portfolio": body.model_dump()},
    )
    return await _director.execute(create)
