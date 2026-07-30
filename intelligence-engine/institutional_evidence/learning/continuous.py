"""Continuous Learning — evidence learning, not model training.

New filing / transcript / guidance / corp action / rating change →
Acquire → Normalize → Update Memory → Recompute KG → Refresh FI →
Refresh Watchlists → Invalidate stale research → Notify analysts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


def learning_pipeline() -> List[str]:
    return [
        "Acquire",
        "Normalize",
        "Update Company Memory",
        "Recompute Knowledge Graph",
        "Refresh Financial Intelligence",
        "Refresh Watchlists",
        "Invalidate stale research",
        "Notify analysts",
    ]


def on_evidence_event(
    ticker: str,
    *,
    event_type: str = "new_filing",
    force_ingest: bool = False,
) -> Dict[str, Any]:
    from ..orchestrator.workflow import orchestrate_company_research
    from ..lifecycle.research_object import mark_stale_for_ticker
    from ..entity.resolve import resolve_entity

    t = str(ticker or "").upper().strip()
    resolved = resolve_entity(t)
    steps: List[Dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    steps.append({"step": "event_received", "event_type": event_type, "at": now})

    # Acquire → Normalize → Memory → FI via orchestrator
    orch = orchestrate_company_research(t, generate_research=False, force_ingest=force_ingest)
    steps.append({"step": "acquire_normalize_memory_fi", "ok": orch.get("ok")})

    # Soft KG recompute
    try:
        from institutional_knowledge_graph.production import refresh_company  # type: ignore

        refresh_company(t)
        steps.append({"step": "recompute_knowledge_graph", "ok": True})
    except Exception as exc:
        steps.append({"step": "recompute_knowledge_graph", "ok": False, "error": str(exc)[:160]})

    # Soft watchlist refresh
    try:
        from company_monitor.production import refresh_watchlist  # type: ignore

        refresh_watchlist(t)
        steps.append({"step": "refresh_watchlists", "ok": True})
    except Exception as exc:
        steps.append({"step": "refresh_watchlists", "ok": False, "soft": True, "error": str(exc)[:120]})

    stale = mark_stale_for_ticker(t, reason=f"evidence_event:{event_type}")
    steps.append({"step": "invalidate_stale_research", "result": stale})

    notify = {
        "channel": "analyst_notifications",
        "message": f"{t}: new {event_type} — company memory/research may need refresh",
        "entity_id": resolved.get("entity_id"),
        "delivered": False,
        "queued": True,
    }
    steps.append({"step": "notify_analysts", "notification": notify})

    return {
        "ok": True,
        "ticker": t,
        "entity_id": resolved.get("entity_id"),
        "event_type": event_type,
        "pipeline": learning_pipeline(),
        "steps": steps,
        "research_pack_claim_safe": (orch.get("research_pack") or {}).get("claim_safe"),
        "rule": "Evidence learning — not model training",
    }
