"""KOC-01 production façades."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from knowledge_operations.flags import is_koc_enabled
from knowledge_operations.schema import (
    DOCUMENT_UPLOAD_TYPES,
    KOC_PRODUCT,
    KOC_SPEC,
    KOC_VERSION,
    KOC_WORKSTREAM_ID,
    MISSION,
)


def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "enabled": is_koc_enabled(),
        "workstream_id": KOC_WORKSTREAM_ID,
        "product": KOC_PRODUCT,
        "version": KOC_VERSION,
        "spec": KOC_SPEC,
        "admin_only": True,
    }


def get_status() -> Dict[str, Any]:
    return {
        **health(),
        "mission": MISSION,
        "upload_types": list(DOCUMENT_UPLOAD_TYPES),
        "role": "Institutional Knowledge Operations Center — not a developer dashboard",
    }


def get_desk(*, scope: str = "TOP20") -> Dict[str, Any]:
    from knowledge_operations.desk import build_desk

    return build_desk(scope=scope)


def get_missing_inbox(*, scope: str = "TOP20", limit: int = 50) -> Dict[str, Any]:
    from knowledge_operations.missing_inbox import build_missing_inbox

    return build_missing_inbox(scope=scope, limit=limit)


def get_company(ticker: str) -> Dict[str, Any]:
    from knowledge_operations.desk import company_detail

    return company_detail(ticker)


def upload_knowledge(**kwargs: Any) -> Dict[str, Any]:
    from knowledge_operations.upload import upload_knowledge as _up

    return _up(**kwargs)


def get_queue(*, limit: int = 100) -> Dict[str, Any]:
    from knowledge_operations.upload import list_queue

    return list_queue(limit=limit)


def get_audit(*, limit: int = 100, ticker: Optional[str] = None) -> Dict[str, Any]:
    from knowledge_operations.audit import list_audit

    return list_audit(limit=limit, ticker=ticker)


def run_action(action: str, **kwargs: Any) -> Dict[str, Any]:
    from knowledge_operations.actions import run_action as _run

    return _run(action, **kwargs)


def soft_slice_mission_control() -> Dict[str, Any]:
    try:
        inbox = get_missing_inbox(scope="TOP20", limit=5)
        return {
            "status": "ok",
            "board": "Knowledge Operations",
            "workstream_id": KOC_WORKSTREAM_ID,
            "version": KOC_VERSION,
            "mission": MISSION,
            "missing_inbox_count": inbox.get("count"),
            "critical_gaps": (inbox.get("by_priority") or {}).get("Critical"),
            "note": "Open /admin/knowledge-operations — admin only",
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)[:240]}
