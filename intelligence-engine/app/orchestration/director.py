from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.agents.cio_synthesizer import ChiefInvestmentOfficer
from app.agents.registry import get_agent
from app.core.logging import get_logger
from app.engines.citation import CitationEngine
from app.engines.confidence import ConfidenceEngine
from app.engines.debate import DebateEngine
from app.engines.evidence import EvidenceEngine
from app.memory.store import ResearchStore
from app.schemas.models import (
    DeskType,
    DirectorPlan,
    ResearchRun,
    ResearchRunCreate,
    RunStatus,
)

log = get_logger(__name__)

DESK_PLANS: dict[DeskType, list[str]] = {
    DeskType.SMOKE: ["smoke_analyst"],
    DeskType.CIO_MORNING: [
        "macro_economist",
        "news_analyst",
        "market_analyst",
        "risk_manager",
    ],
    DeskType.EQUITY: ["smoke_analyst"],  # Phase 3 expands
    DeskType.CUSTOM: ["smoke_analyst"],
}


class ResearchDirector:
    """Orchestrates agents only. Does not write the investment thesis."""

    def __init__(self, store: ResearchStore | None = None):
        self.store = store or ResearchStore()
        self.evidence_engine = EvidenceEngine()
        self.confidence_engine = ConfidenceEngine()
        self.citation_engine = CitationEngine()
        self.debate_engine = DebateEngine()
        self.cio = ChiefInvestmentOfficer()

    def plan(self, desk: DeskType, query: str | None = None) -> DirectorPlan:
        agent_ids = DESK_PLANS.get(desk, DESK_PLANS[DeskType.SMOKE])
        return DirectorPlan(
            desk=desk,
            agent_ids=agent_ids,
            rationale=f"Desk {desk.value} requires {', '.join(agent_ids)}",
            require_all=False,
        )

    async def execute(self, request: ResearchRunCreate) -> ResearchRun:
        run = ResearchRun(
            desk=request.desk,
            status=RunStatus.RUNNING,
            query=request.query,
            symbols=request.symbols,
            metadata=request.metadata,
        )
        run.director_plan = self.plan(request.desk, request.query)
        await self.store.save_run(run)
        log.info("director_start", extra={"run_id": run.run_id, "desk": run.desk.value})

        context: dict[str, Any] = {
            "run_id": run.run_id,
            "desk": run.desk,
            "query": run.query,
            "symbols": run.symbols,
            "metadata": run.metadata,
        }

        # Memory retrieval (similar past runs) — soft fail
        try:
            similar = await self.store.similar_runs(run.desk.value, limit=3)
            context["similar_runs"] = similar
        except Exception as exc:
            run.errors.append(f"memory_retrieve: {exc}")

        outputs = []
        for agent_id in run.director_plan.agent_ids:
            try:
                agent = get_agent(agent_id)
                output = await agent.run(context)
                outputs.append(output)
            except Exception as exc:
                run.errors.append(f"{agent_id}: {exc}")
                log.exception("director_agent_error", extra={"run_id": run.run_id, "agent_id": agent_id})

        run.agent_outputs = outputs
        validation_errors = self.evidence_engine.validate_outputs(outputs)
        run.errors.extend(validation_errors)

        evidence = self.evidence_engine.collect(outputs)
        confidence = self.confidence_engine.combine(outputs, evidence)
        debate = self.debate_engine.debate(outputs, evidence)
        run.debate = debate

        try:
            report = await self.cio.synthesize(
                {
                    "desk": run.desk,
                    "agent_outputs": outputs,
                    "debate": debate,
                    "confidence": confidence,
                    "evidence": evidence,
                    "query": run.query,
                }
            )
            citations = self.citation_engine.build_citation_map(outputs, evidence)
            report = self.citation_engine.attach(report, citations)
            run.report = report
            run.cio_thesis = report.executive_summary
            run.status = RunStatus.COMPLETED if not run.errors else RunStatus.PARTIAL
        except Exception as exc:
            run.errors.append(f"cio_synthesize: {exc}")
            run.status = RunStatus.FAILED if not outputs else RunStatus.PARTIAL
            log.exception("cio_failed", extra={"run_id": run.run_id})

        run.updated_at = datetime.now(timezone.utc)
        run.completed_at = run.updated_at
        await self.store.save_run(run)
        if run.report:
            await self.store.save_report_embedding(run)
        log.info("director_complete", extra={"run_id": run.run_id, "status": run.status.value})
        return run
