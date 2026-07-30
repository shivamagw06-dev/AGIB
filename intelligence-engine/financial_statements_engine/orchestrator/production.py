"""FSE-00 Mission Control façades for the Pipeline Orchestrator."""

from __future__ import annotations

from typing import Any

from financial_statements_engine.collection.event_bus import get_bus
from financial_statements_engine.orchestrator.engine import (
    cancel_workflow,
    create_workflow,
    replay_workflow,
    retry_workflow,
    run_workflow,
)
from financial_statements_engine.orchestrator.schema import (
    ISSUES_RECOMMENDATIONS,
    ORCH_VERSION,
    ORCHESTRATOR_EVENTS,
    PROGRAMME,
    RECOMMENDATION_POLICY,
    STAGES,
    SUBSYSTEM,
    VERSION,
    WORKFLOW_STATES,
    WORKSTREAM_ID,
)
from financial_statements_engine.orchestrator.store import count_by_state, history_tail, list_workflows, load_workflow
from financial_statements_engine.util import now_iso


def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "programme": PROGRAMME,
        "workstream_id": WORKSTREAM_ID,
        "subsystem": SUBSYSTEM,
        "version": VERSION,
        "orch_version": ORCH_VERSION,
        "stages": list(STAGES),
        "workflow_states": list(WORKFLOW_STATES),
        "orchestrator_events": list(ORCHESTRATOR_EVENTS),
        "foundation": "fse_event_bus_plus_disk_workflow_store",
        "never_parses": True,
        "never_validates_accounting": True,
        "never_calculates_metrics": True,
        "never_publishes_facts_itself": True,
        "coordinates_only": True,
        "issues_recommendations": ISSUES_RECOMMENDATIONS,
        "recommendation_policy": RECOMMENDATION_POLICY,
        "spec": "docs/FSE_00_PIPELINE_ORCHESTRATOR.md",
        "as_of": now_iso(),
    }


def dashboard() -> dict[str, Any]:
    counts = count_by_state()
    rows = list_workflows(limit=500)
    durations = []
    failures = []
    longest = None
    longest_ms = -1
    for wf in rows:
        st = wf.get("stages") or {}
        total = 0
        for meta in st.values():
            if isinstance(meta, dict) and meta.get("duration_ms") is not None:
                total += int(meta["duration_ms"])
        if total:
            durations.append(total)
            if total > longest_ms:
                longest_ms = total
                longest = {
                    "workflow_id": wf.get("workflow_id"),
                    "ticker": wf.get("ticker"),
                    "duration_ms": total,
                    "state": wf.get("state"),
                }
        if wf.get("state") == "FAILED":
            failures.append(
                {
                    "workflow_id": wf.get("workflow_id"),
                    "ticker": wf.get("ticker"),
                    "reason": wf.get("failure_reason"),
                    "stage": wf.get("current_stage"),
                }
            )
    events = [e for e in get_bus().tail(300) if str(e.get("event_type", "")).startswith("workflow.") or str(e.get("event_type", "")).startswith("stage.")]
    return {
        "status": "ok",
        "workstream_id": WORKSTREAM_ID,
        "queued": counts.get("QUEUED", 0),
        "running": counts.get("RUNNING", 0),
        "completed": counts.get("COMPLETED", 0),
        "failed": counts.get("FAILED", 0),
        "retrying": counts.get("RETRYING", 0),
        "cancelled": counts.get("CANCELLED", 0),
        "received": counts.get("RECEIVED", 0),
        "counts_by_state": counts,
        "average_duration_ms": round(sum(durations) / len(durations), 2) if durations else 0.0,
        "longest_running": longest,
        "recent_failures": failures[:20],
        "recent_orch_events": events[-30:],
        "issues_recommendations": False,
        "as_of": now_iso(),
    }


def queue(limit: int = 100) -> dict[str, Any]:
    rows = [w for w in list_workflows(limit=1000) if w.get("state") in ("QUEUED", "RUNNING", "RETRYING", "RECEIVED")]
    return {"ok": True, "n": len(rows[:limit]), "workflows": rows[:limit]}


def workflows(state: str | None = None, limit: int = 100) -> dict[str, Any]:
    rows = list_workflows(state=state, limit=limit)
    return {"ok": True, "n": len(rows), "workflows": rows}


def workflow_detail(workflow_id: str) -> dict[str, Any]:
    wf = load_workflow(workflow_id)
    if not wf:
        return {"ok": False, "error": "workflow_not_found", "workflow_id": workflow_id}
    return {"ok": True, "workflow": wf}


def history(limit: int = 100) -> dict[str, Any]:
    return {"ok": True, "n": min(limit, 1000), "history": history_tail(limit)}


def start(payload: dict[str, Any], *, run: bool = True) -> dict[str, Any]:
    created = create_workflow(payload, auto_queue=True)
    wf = created["workflow"]
    if run and not created.get("duplicate"):
        wf = run_workflow(str(wf["workflow_id"]))
    elif run and created.get("duplicate") and wf.get("state") not in ("COMPLETED", "RUNNING"):
        wf = run_workflow(str(wf["workflow_id"]))
    return {"ok": True, "created": created.get("created"), "duplicate": created.get("duplicate"), "workflow": wf}


def retry(workflow_id: str) -> dict[str, Any]:
    return {"ok": True, "workflow": retry_workflow(workflow_id)}


def replay(workflow_id: str, *, from_stage: str | None = None) -> dict[str, Any]:
    return {"ok": True, "workflow": replay_workflow(workflow_id, from_stage=from_stage)}


def cancel(workflow_id: str) -> dict[str, Any]:
    return {"ok": True, "workflow": cancel_workflow(workflow_id)}
