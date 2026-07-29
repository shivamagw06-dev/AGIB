"""AGIB Phase 2 — Institutional Investment Intelligence Programme registry."""

from phase2_investment_intelligence.production import health, programme
from phase2_investment_intelligence.schema import PROGRAMME, PROGRAMME_VERSION

__all__ = ["PROGRAMME", "PROGRAMME_VERSION", "health", "programme"]
