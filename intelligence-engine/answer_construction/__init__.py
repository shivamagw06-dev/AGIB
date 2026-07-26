"""Ask AGI Institutional Answer Construction V3 — soft-wire orchestration."""

from answer_construction.production import health, package_for_ask_agi, quality_gates
from answer_construction.schema import AC_VERSION, PROGRAMME

__all__ = ["PROGRAMME", "AC_VERSION", "health", "package_for_ask_agi", "quality_gates"]
