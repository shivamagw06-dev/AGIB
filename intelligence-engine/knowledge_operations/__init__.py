"""KOC-01 — Institutional Knowledge Operations Center."""

from __future__ import annotations

from knowledge_operations.production import (
    get_desk,
    get_missing_inbox,
    get_status,
    health,
    soft_slice_mission_control,
)
from knowledge_operations.schema import KOC_VERSION, KOC_WORKSTREAM_ID

__all__ = [
    "KOC_VERSION",
    "KOC_WORKSTREAM_ID",
    "health",
    "get_status",
    "get_desk",
    "get_missing_inbox",
    "soft_slice_mission_control",
]
