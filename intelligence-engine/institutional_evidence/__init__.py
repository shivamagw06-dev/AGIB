"""IEP-01 — Institutional Evidence Platform (AGI v1.1 foundation)."""

from .schema import (
    IEP_WORKSTREAM_ID,
    IEP_VERSION,
    PHASE1_TOP20,
    RESEARCH_READY_THRESHOLD,
    FORBIDDEN_INVENTED_FIELDS,
)
from .flags import is_iep_enabled, iep_flags
from .production import (
    get_iep_status,
    get_research_pack,
    get_research_readiness,
    validate_research_pack,
    orchestrate_research,
    get_evidence_registry,
    get_canonical_statements,
    get_company_memory_bridge,
    get_phase1_coverage,
    get_success_metrics,
    get_evidence_center_board,
    soft_slice_mission_control,
    health,
)

__all__ = [
    "IEP_WORKSTREAM_ID",
    "IEP_VERSION",
    "PHASE1_TOP20",
    "RESEARCH_READY_THRESHOLD",
    "FORBIDDEN_INVENTED_FIELDS",
    "is_iep_enabled",
    "iep_flags",
    "get_iep_status",
    "get_research_pack",
    "get_research_readiness",
    "validate_research_pack",
    "orchestrate_research",
    "get_evidence_registry",
    "get_canonical_statements",
    "get_company_memory_bridge",
    "get_phase1_coverage",
    "get_success_metrics",
    "get_evidence_center_board",
    "soft_slice_mission_control",
    "health",
]
