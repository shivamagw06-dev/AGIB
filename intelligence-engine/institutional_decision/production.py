"""IDS-01 production façades — health / decide / history."""

from __future__ import annotations

from typing import Any, Optional

from institutional_decision.decision_engine import generate_decision
from institutional_decision.decision_validator import validate_decision
from institutional_decision.diagnostics import build_diagnostics
from institutional_decision.flags import flags_dict, is_enabled
from institutional_decision import history as decision_history
from institutional_decision.schema import (
    DECISION_ENGINE_VERSION,
    DECISION_VALIDATOR_VERSION,
    IDS_PRODUCT,
    IDS_ROLE,
    IDS_SPEC,
    IDS_VERSION,
    IDS_WORKSTREAM_ID,
)

try:
    from financial_statements_engine.util import now_iso
except Exception:  # noqa: BLE001
    from datetime import datetime, timezone

    def now_iso() -> str:  # type: ignore[misc]
        return datetime.now(timezone.utc).isoformat()


def health() -> dict[str, Any]:
    return {
        "status": "ok" if is_enabled() else "disabled",
        "workstream_id": IDS_WORKSTREAM_ID,
        "product": IDS_PRODUCT,
        "version": IDS_VERSION,
        "role": IDS_ROLE,
        "owns_recommendation": True,
        "llm": False,
        "external_writer": False,
        "decision_engine_version": DECISION_ENGINE_VERSION,
        "validator_version": DECISION_VALIDATOR_VERSION,
        "flags": flags_dict(),
        "enabled": is_enabled(),
        "spec": IDS_SPEC,
        "brand": "AGI",
        "history": decision_history.metrics(),
        "as_of": now_iso(),
    }


def _decide_from_report_input(inp: Any, *, reason_graph: Any = None) -> dict[str, Any]:
    from institutional_reporting.schema import IRE_VERSION, REASON_COMPOSER_VERSION

    prev = decision_history.latest(inp.ticker)
    previous_version = prev.decision_version if prev else 0
    reasons = None
    if reason_graph is not None and hasattr(reason_graph, "reasons"):
        reasons = reason_graph.reasons
    evidence_ids = [e.evidence_id for e in (inp.evidence or ()) if getattr(e, "evidence_id", None)]
    decision = generate_decision(
        reasons=reasons,
        valuation=inp.valuation,
        risks=list(inp.risks or ()),
        confidence=inp.confidence,
        business_quality=inp.business_quality,
        financial_quality=inp.financial_quality,
        overall_risk=inp.overall_risk,
        ticker=inp.ticker,
        company_name=inp.company_name,
        sector=inp.sector,
        unknowns=list(inp.unknowns or ()),
        evidence_ids=evidence_ids,
        reason_version=REASON_COMPOSER_VERSION,
        report_version=IRE_VERSION,
        previous_version=previous_version,
        investment_horizon=str(inp.horizon or ""),
    )
    validation = validate_decision(
        decision,
        business_quality=inp.business_quality,
        valuation=str(inp.valuation or ""),
        overall_risk=str(inp.overall_risk or ""),
    )
    diagnostics = build_diagnostics(decision, validation)
    if not validation.ok:
        return {
            "ok": False,
            "rejected": True,
            "workstream_id": IDS_WORKSTREAM_ID,
            "validation_errors": validation.errors,
            "decision": decision.to_dict(),
            "diagnostics": diagnostics,
        }
    decision_history.record(decision)
    return {
        "ok": True,
        "rejected": False,
        "workstream_id": IDS_WORKSTREAM_ID,
        "decision": decision.to_dict(),
        "diagnostics": diagnostics,
        "institutional_decision": decision,  # object for in-process consumers
    }


def decide_company(payload: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """POST /v1/decision/company"""
    if not is_enabled():
        return {
            "ok": False,
            "enabled": False,
            "workstream_id": IDS_WORKSTREAM_ID,
            "rejected": True,
            "validation_errors": ["IDS-01 disabled"],
        }
    body = dict(payload or {})
    include_history = body.pop("include_history", False)
    if isinstance(include_history, str):
        include_history = include_history.strip().lower() in {"1", "true", "yes", "on"}

    # Prefer full InstitutionalReportInput-shaped payload; ticker-only uses IRE fixtures.
    from institutional_reporting.fixtures import get_fixture
    from institutional_reporting.models import InstitutionalReportInput
    from institutional_reporting.reason_composer import compose_reasons

    ticker = str(body.get("ticker") or "").strip()
    occupied = {k for k, v in body.items() if v not in (None, "", [], {})}
    ticker_only = occupied <= {"ticker", "as_of", "include_history"} and bool(ticker)

    if ticker_only and get_fixture(ticker):
        inp = get_fixture(ticker)
    else:
        inp = InstitutionalReportInput.from_dict(body)

    graph = compose_reasons(inp)
    result = _decide_from_report_input(inp, reason_graph=graph)
    # Strip in-process object from API payload
    decision_obj = result.pop("institutional_decision", None)
    if include_history and inp.ticker:
        result["history"] = decision_history.history_for(inp.ticker)
    if decision_obj is not None:
        result["_decision_obj"] = decision_obj  # optional internal; remove for JSON
    # Ensure JSON-safe
    result.pop("_decision_obj", None)
    return result


def get_company_decision(ticker: str, *, include_history: bool = False) -> dict[str, Any]:
    """GET /v1/decision/company/{ticker} — latest or freshly generated from fixture."""
    if not is_enabled():
        return {"ok": False, "enabled": False, "workstream_id": IDS_WORKSTREAM_ID}
    latest = decision_history.latest(ticker)
    if latest is None:
        # Generate from fixture if available
        generated = decide_company({"ticker": ticker})
        if include_history:
            generated["history"] = decision_history.history_for(ticker)
        return generated
    validation = validate_decision(latest)
    out = {
        "ok": validation.ok,
        "rejected": not validation.ok,
        "workstream_id": IDS_WORKSTREAM_ID,
        "decision": latest.to_dict(),
        "diagnostics": build_diagnostics(latest, validation),
        "validation_errors": validation.errors,
    }
    if include_history:
        out["history"] = decision_history.history_for(ticker)
    return out


def soft_slice_mission_control() -> dict[str, Any]:
    h = health()
    return {
        "status": h.get("status"),
        "workstream_id": IDS_WORKSTREAM_ID,
        "product": IDS_PRODUCT,
        "version": IDS_VERSION,
        "owns_recommendation": True,
        "llm": False,
        "history": h.get("history"),
    }
