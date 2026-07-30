"""UAG-01 production façades — ask / stream / query / Orchestration Center."""

from __future__ import annotations

import hashlib
import time
from dataclasses import replace
from typing import Any, Iterator, Optional

from institutional_orchestrator.diagnostics import build_diagnostics
from institutional_orchestrator.flags import flags_dict, is_enabled
from institutional_orchestrator import history as query_history
from institutional_orchestrator.intent_classifier import classify_intent, extract_entities
from institutional_orchestrator.object_registry import catalog, reset_registry_for_tests
from institutional_orchestrator.planner import plan_query
from institutional_orchestrator.response_builder import build_response
from institutional_orchestrator.retrieval import execute_plan
from institutional_orchestrator.router import route_plan
from institutional_orchestrator.schema import (
    ORCHESTRATOR_VERSION,
    UAG_PRODUCT,
    UAG_ROLE,
    UAG_SPEC,
    UAG_VERSION,
    UAG_WORKSTREAM_ID,
    VALIDATOR_VERSION,
)
from institutional_orchestrator.validator import validate_response

try:
    from financial_statements_engine.util import now_iso
except Exception:  # noqa: BLE001
    from datetime import datetime, timezone

    def now_iso() -> str:  # type: ignore[misc]
        return datetime.now(timezone.utc).isoformat()


def reset_for_tests() -> None:
    query_history.reset_for_tests()
    reset_registry_for_tests()


def health() -> dict[str, Any]:
    return {
        "status": "ok" if is_enabled() else "disabled",
        "workstream_id": UAG_WORKSTREAM_ID,
        "product": UAG_PRODUCT,
        "version": UAG_VERSION,
        "role": UAG_ROLE,
        "llm": False,
        "generates_recommendations": False,
        "owns_business_state": False,
        "stateless": True,
        "orchestration_only": True,
        "orchestrator_version": ORCHESTRATOR_VERSION,
        "validator_version": VALIDATOR_VERSION,
        "registered_objects": catalog(),
        "flags": flags_dict(),
        "enabled": is_enabled(),
        "spec": UAG_SPEC,
        "brand": "AGI",
        "phase": 5,
        "history": query_history.metrics(),
        "as_of": now_iso(),
    }


def soft_slice_mission_control() -> dict[str, Any]:
    h = health()
    m = query_history.metrics()
    recent = query_history.recent(8)
    regs = catalog()
    return {
        "status": h.get("status"),
        "workstream_id": UAG_WORKSTREAM_ID,
        "product": UAG_PRODUCT,
        "version": UAG_VERSION,
        "llm": False,
        "orchestration_center": True,
        "active_queries": m.get("active_cached") or 0,
        "planner_performance": {
            "query_count": m.get("query_count") or 0,
            "average_latency_ms": m.get("average_latency_ms") or 0,
        },
        "routing_accuracy": None,  # filled after labeled evals; soft null
        "object_coverage": len([r for r in regs if r.get("has_provider")]),
        "registered_object_count": len(regs),
        "average_latency": m.get("average_latency_ms") or 0,
        "failed_plans": m.get("failed_plans") or 0,
        "missing_registrations": [r["object_type"] for r in regs if not r.get("has_provider")],
        "recent_queries": recent,
    }


def _query_id(question: str) -> str:
    raw = f"{question}|{now_iso()}|{ORCHESTRATOR_VERSION}"
    return f"uag-{hashlib.sha256(raw.encode()).hexdigest()[:14]}"


def ask(payload: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    if not is_enabled():
        return {
            "ok": False,
            "enabled": False,
            "workstream_id": UAG_WORKSTREAM_ID,
            "rejected": True,
            "validation_errors": ["UAG-01 disabled"],
        }

    t0 = time.perf_counter()
    body = dict(payload or {})
    question = str(body.get("question") or body.get("query") or body.get("q") or "").strip()
    if not question:
        return {
            "ok": False,
            "rejected": True,
            "workstream_id": UAG_WORKSTREAM_ID,
            "validation_errors": ["question required"],
        }

    portfolio_id = str(body.get("portfolio_id") or body.get("portfolio") or "agi-core-equity")
    policy = str(body.get("policy") or "family_office")
    entities_override = body.get("entities")

    intent_info = classify_intent(question)
    intent = str(intent_info.get("intent") or "Search")
    entities = (
        tuple(str(e).upper() for e in entities_override)
        if entities_override
        else extract_entities(question)
    )

    qid = _query_id(question)
    generated_at = now_iso()
    query = plan_query(
        query_id=qid,
        question=question,
        intent=intent,
        entities=entities,
        generated_at=generated_at,
    )
    routed = route_plan(query)
    steps, payloads = execute_plan(query, portfolio_id=portfolio_id, policy=policy)
    query = replace(query, execution_plan=steps)

    response = build_response(
        query,
        steps=steps,
        payloads=payloads,
        generated_at=generated_at,
    )
    latency = (time.perf_counter() - t0) * 1000.0
    prelim = build_diagnostics(query, response, latency_ms=latency, routed=routed)
    response = replace(response, diagnostics=prelim)

    validation = validate_response(query, response)
    diag = build_diagnostics(
        query,
        response,
        validation=validation.to_dict(),
        latency_ms=(time.perf_counter() - t0) * 1000.0,
        routed=routed,
    )
    response = replace(response, diagnostics=diag)
    query = replace(query, diagnostics={"intent": intent_info, **(query.diagnostics or {})})

    ok = validation.ok
    query_history.record(query, response, ok=ok, latency_ms=diag["latency_ms"])

    # Soft deep-link into RW-01 Research Workspace (Ask answers where; workspace shows everything).
    workspace_link: dict[str, Any] = {}
    try:
        from institutional_workspace.navigation import (
            workspace_deep_link,
            workspace_focus_for_intent,
        )

        focus = workspace_focus_for_intent(intent)
        ticker = entities[0] if entities else ""
        workspace_link = {
            "focus": focus,
            "href": workspace_deep_link(
                ticker=ticker,
                portfolio_id=portfolio_id if not ticker else "",
                focus=focus,
                context="portfolio" if not ticker else "company",
            ),
            "lineage_hint": [
                "Decision",
                "Timeline",
                "Observation",
                "Evidence",
            ],
            "engine": "RW-01",
        }
    except Exception:
        workspace_link = {}

    if not ok:
        return {
            "ok": False,
            "rejected": True,
            "workstream_id": UAG_WORKSTREAM_ID,
            "validation_errors": list(validation.errors),
            "gates": validation.gates,
            "query": query.to_dict(),
            "response": response.to_dict(),
            "workspace": workspace_link,
            "diagnostics": diag,
            "llm": False,
            "generates_recommendations": False,
            "owns_business_state": False,
        }

    return {
        "ok": True,
        "rejected": False,
        "workstream_id": UAG_WORKSTREAM_ID,
        "product": UAG_PRODUCT,
        "version": UAG_VERSION,
        "query": query.to_dict(),
        "response": response.to_dict(),
        "workspace": workspace_link,
        "diagnostics": diag,
        "llm": False,
        "generates_recommendations": False,
        "owns_business_state": False,
        "stateless": True,
    }


def ask_stream(payload: Optional[dict[str, Any]] = None) -> Iterator[dict[str, Any]]:
    """
    Streaming façade — yields plan, then steps, then final response.

    Not token-LLM streaming; structured orchestration events.
    """
    body = dict(payload or {})
    question = str(body.get("question") or body.get("query") or "").strip()
    yield {"event": "start", "question": question, "workstream_id": UAG_WORKSTREAM_ID}

    # Build plan first for progressive disclosure
    intent_info = classify_intent(question)
    entities = extract_entities(question)
    qid = _query_id(question or "empty")
    query = plan_query(
        query_id=qid,
        question=question,
        intent=str(intent_info.get("intent") or "Search"),
        entities=entities,
        generated_at=now_iso(),
    )
    yield {"event": "plan", "query": query.to_dict()}

    result = ask(payload)
    yield {"event": "step", "execution_plan": (result.get("response") or {}).get("execution_plan")}
    yield {"event": "final", "result": result}


def get_query(query_id: str) -> dict[str, Any]:
    row = query_history.get_query(query_id)
    if row is None:
        return {
            "ok": False,
            "workstream_id": UAG_WORKSTREAM_ID,
            "error": "query_not_found",
            "query_id": query_id,
        }
    return {
        "ok": True,
        "workstream_id": UAG_WORKSTREAM_ID,
        "query_id": query_id,
        **row,
        "owns_business_state": False,
        "llm": False,
    }
