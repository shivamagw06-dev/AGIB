"""Knowledge Versioning — every CGL cycle creates an immutable Knowledge Snapshot."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_SNAPSHOTS: List[Dict[str, Any]] = []


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _version_label(slot: str, when: Optional[datetime] = None) -> str:
    dt = when or _now()
    return f"{dt.strftime('%Y.%m.%d')}.{slot or 'cycle'}"


def create_knowledge_snapshot(
    *,
    run_id: str,
    slot: str = "cycle",
    companies_updated: Optional[List[str]] = None,
    evidence_added: int = 0,
    financial_statements_updated: int = 0,
    knowledge_graph_changes: int = 0,
    research_invalidated: Optional[List[str]] = None,
) -> Dict[str, Any]:
    when = _now()
    version = _version_label(slot, when)
    snap = {
        "snapshot_id": f"ks_{uuid.uuid4().hex[:14]}",
        "run_id": run_id,
        "timestamp": when.isoformat().replace("+00:00", "Z"),
        "companies_updated": [str(t).upper() for t in (companies_updated or [])],
        "evidence_added": int(evidence_added),
        "financial_statements_updated": int(financial_statements_updated),
        "knowledge_graph_changes": int(knowledge_graph_changes),
        "research_invalidated": list(research_invalidated or []),
        "version_number": len(_SNAPSHOTS) + 1,
        "knowledge_version": version,
        "immutable": True,
        "schema": "KnowledgeSnapshot.v1",
    }
    _SNAPSHOTS.append(snap)
    return dict(snap)


def get_latest_snapshot() -> Optional[Dict[str, Any]]:
    return dict(_SNAPSHOTS[-1]) if _SNAPSHOTS else None


def list_snapshots(*, limit: int = 50) -> Dict[str, Any]:
    rows = _SNAPSHOTS[-max(1, min(limit, 200)) :]
    return {"ok": True, "count": len(rows), "snapshots": list(rows)}
