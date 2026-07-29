"""Persistent historical backfill backlog queue — survives restarts."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from knowledge_factory.historical_depth import store as hd_store
from knowledge_factory.historical_depth.completion import history_years
from knowledge_factory.historical_depth.universe_priority import (
    prioritised_universe,
    priority_tier,
    supported_universe,
    tier_label,
)

QUEUE_REPORT = "historical_backfill_queue"
ENGINE_STATE = "historical_backfill_engine_state"
QUEUE_VERSION = "hd-queue-v1.0.0"

STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_COMPLETE = "complete"
STATUS_FAILED = "failed"
STATUS_COOLDOWN = "cooldown"
STATUS_MAINTENANCE = "maintenance"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def load_queue() -> dict[str, Any]:
    raw = hd_store.get_report(QUEUE_REPORT) or {}
    companies = list(raw.get("companies") or [])
    return {
        "queue_version": QUEUE_VERSION,
        "companies": companies,
        "updated_at": raw.get("updated_at"),
    }


def save_queue(payload: dict[str, Any]) -> dict[str, Any]:
    body = {
        **payload,
        "queue_version": QUEUE_VERSION,
        "updated_at": _now_iso(),
        "queue_length": len([c for c in (payload.get("companies") or []) if c.get("status") != STATUS_COMPLETE]),
        "completed_count": len([c for c in (payload.get("companies") or []) if c.get("status") in {STATUS_COMPLETE, STATUS_MAINTENANCE}]),
    }
    hd_store.put_report(QUEUE_REPORT, body)
    return body


def load_engine_state() -> dict[str, Any]:
    return hd_store.get_report(ENGINE_STATE) or {
        "mode": "deep_backfill",
        "deep_backfill_enabled": True,
        "maintenance_only": False,
        "completed_at": None,
        "companies_processed_today": 0,
        "day_key": None,
    }


def save_engine_state(state: dict[str, Any]) -> dict[str, Any]:
    body = {**state, "updated_at": _now_iso()}
    hd_store.put_report(ENGINE_STATE, body)
    return body


def ensure_queue(*, force_refresh: bool = False) -> dict[str, Any]:
    """Ensure every supported listed company is on the queue."""
    q = load_queue()
    existing = {str(c.get("company") or "").upper(): c for c in (q.get("companies") or [])}
    years_map = {s: history_years(s) for s in supported_universe()}
    ordered = prioritised_universe(coverage_years=years_map)
    changed = False
    for s in ordered:
        if s in existing and not force_refresh:
            # Refresh coverage/years/priority fields
            row = existing[s]
            row["years"] = years_map.get(s, 0.0)
            row["priority"] = priority_tier(s)
            row["tier"] = tier_label(priority_tier(s))
            continue
        if s in existing:
            continue
        existing[s] = {
            "company": s,
            "priority": priority_tier(s),
            "tier": tier_label(priority_tier(s)),
            "status": STATUS_PENDING,
            "attempts": 0,
            "last_run": None,
            "coverage": 0.0,
            "years": years_map.get(s, 0.0),
            "errors": [],
            "mode": "backfill",
        }
        changed = True
    companies = list(existing.values())
    # Re-sort
    companies.sort(key=lambda c: (int(c.get("priority") or 99), float(c.get("years") or 0.0), str(c.get("company"))))
    q["companies"] = companies
    if changed or force_refresh or not q.get("updated_at"):
        return save_queue(q)
    return save_queue(q)


def _backoff_seconds(attempts: int) -> float:
    # Exponential: 2^min(attempts,8) minutes, capped ~4h
    mins = min(240.0, float(2 ** min(max(1, attempts), 8)))
    return mins * 60.0


def next_batch(*, batch_size: int = 12, maintenance: bool = False) -> list[dict[str, Any]]:
    """Select next companies respecting cooldown and priority."""
    q = ensure_queue()
    now = _now()
    selected: list[dict[str, Any]] = []
    companies = list(q.get("companies") or [])
    # Sort: priority, then lowest years, then oldest last_run
    companies.sort(
        key=lambda c: (
            int(c.get("priority") or 99),
            float(c.get("years") or 0.0),
            str(c.get("last_run") or ""),
            str(c.get("company") or ""),
        )
    )
    for row in companies:
        if len(selected) >= batch_size:
            break
        status = str(row.get("status") or STATUS_PENDING)
        if maintenance:
            if status not in {STATUS_COMPLETE, STATUS_MAINTENANCE}:
                continue
        else:
            if status in {STATUS_COMPLETE, STATUS_MAINTENANCE}:
                continue
            if status == STATUS_COOLDOWN:
                ready = _parse_iso(row.get("cooldown_until"))
                if ready and ready > now:
                    continue
        selected.append(row)
    return selected


def mark_running(company: str) -> None:
    _update_row(company, status=STATUS_RUNNING, last_run=_now_iso())


def mark_result(company: str, evaluation: dict[str, Any], *, error: str | None = None) -> dict[str, Any]:
    e = company.upper()
    q = load_queue()
    rows = list(q.get("companies") or [])
    out_row = None
    for row in rows:
        if str(row.get("company") or "").upper() != e:
            continue
        row["attempts"] = int(row.get("attempts") or 0) + 1
        row["last_run"] = _now_iso()
        row["years"] = evaluation.get("history_years") or row.get("years") or 0.0
        row["coverage"] = evaluation.get("coverage_pct") or 0.0
        if error:
            errs = list(row.get("errors") or [])
            errs.insert(0, {"at": _now_iso(), "error": error[:200]})
            row["errors"] = errs[:10]
            delay = _backoff_seconds(int(row["attempts"]))
            row["status"] = STATUS_COOLDOWN
            row["cooldown_until"] = (_now() + timedelta(seconds=delay)).isoformat()
            row["mode"] = "backfill"
        elif evaluation.get("complete"):
            row["status"] = STATUS_MAINTENANCE
            row["mode"] = "maintenance"
            row["completed_at"] = row.get("completed_at") or _now_iso()
            row["errors"] = []
            row.pop("cooldown_until", None)
        else:
            row["status"] = STATUS_PENDING
            row["mode"] = "backfill"
            # Light backoff even on partial progress to rotate fairly
            if int(row["attempts"]) > 3 and float(row.get("coverage") or 0) < 50:
                delay = _backoff_seconds(int(row["attempts"]) // 2)
                row["status"] = STATUS_COOLDOWN
                row["cooldown_until"] = (_now() + timedelta(seconds=delay)).isoformat()
        out_row = row
        break
    q["companies"] = rows
    save_queue(q)
    return out_row or {}


def _update_row(company: str, **fields: Any) -> None:
    e = company.upper()
    q = load_queue()
    for row in q.get("companies") or []:
        if str(row.get("company") or "").upper() == e:
            row.update(fields)
            break
    save_queue(q)


def backlog_stats() -> dict[str, Any]:
    q = ensure_queue()
    companies = list(q.get("companies") or [])
    remaining = [
        c
        for c in companies
        if str(c.get("status")) not in {STATUS_COMPLETE, STATUS_MAINTENANCE}
    ]
    done = [c for c in companies if str(c.get("status")) in {STATUS_COMPLETE, STATUS_MAINTENANCE}]
    years = [float(c.get("years") or 0.0) for c in companies] or [0.0]
    state = load_engine_state()
    return {
        "total_companies": len(companies),
        "fully_backfilled": len(done),
        "remaining": len(remaining),
        "queue_length": len(remaining),
        "average_years": round(sum(years) / max(1, len(years)), 2),
        "coverage_pct": round(100.0 * len(done) / max(1, len(companies)), 2),
        "mode": state.get("mode") or "deep_backfill",
        "maintenance_only": bool(state.get("maintenance_only")),
        "completed_at": state.get("completed_at"),
        "companies_processed_today": int(state.get("companies_processed_today") or 0),
    }


def maybe_transition_to_maintenance() -> dict[str, Any]:
    """When remaining=0, disable deep backfill and enable maintenance-only forever."""
    stats = backlog_stats()
    state = load_engine_state()
    if int(stats.get("remaining") or 0) == 0 and int(stats.get("total_companies") or 0) > 0:
        if not state.get("maintenance_only"):
            state = save_engine_state(
                {
                    **state,
                    "mode": "maintenance",
                    "deep_backfill_enabled": False,
                    "maintenance_only": True,
                    "completed_at": state.get("completed_at") or _now_iso(),
                    "note": "Coverage target reached — incremental maintenance only",
                }
            )
        return {**stats, "transitioned": True, "engine": state}
    # Still in deep mode
    if state.get("maintenance_only") and int(stats.get("remaining") or 0) > 0:
        # New companies added — reopen deep backfill
        state = save_engine_state(
            {
                **state,
                "mode": "deep_backfill",
                "deep_backfill_enabled": True,
                "maintenance_only": False,
                "reopened_at": _now_iso(),
            }
        )
    else:
        state = save_engine_state(
            {
                **state,
                "mode": "deep_backfill" if not state.get("maintenance_only") else "maintenance",
                "deep_backfill_enabled": not bool(state.get("maintenance_only")),
            }
        )
    return {**stats, "transitioned": False, "engine": state}


def bump_processed_today(n: int = 1) -> None:
    state = load_engine_state()
    day = _now().date().isoformat()
    if state.get("day_key") != day:
        state["day_key"] = day
        state["companies_processed_today"] = 0
    state["companies_processed_today"] = int(state.get("companies_processed_today") or 0) + n
    save_engine_state(state)


def eta_days(*, processed_today: int | None = None, remaining: int | None = None) -> float | None:
    stats = backlog_stats()
    rem = remaining if remaining is not None else int(stats.get("remaining") or 0)
    today = processed_today if processed_today is not None else int(stats.get("companies_processed_today") or 0)
    # Prefer last-batch rate from report
    last = hd_store.get_report("historical_backfill_last") or {}
    processed = int(last.get("processed") or 0)
    runtime = float(last.get("runtime_seconds") or 0) or 0.0
    if processed > 0 and runtime > 0:
        per_day = (processed / runtime) * 86400.0
        if per_day > 0:
            return round(rem / per_day, 1)
    if today > 0:
        return round(rem / max(today, 1), 1)
    return None
