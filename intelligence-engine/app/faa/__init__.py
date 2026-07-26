"""AGI Finance Acquisition Agent (FAA) v1.0.

Upstream live-evidence acquisition layer for FRE.

FAA discovers, downloads, parses and stores public financial documents.
It never reasons and never answers users. It only feeds FRE.

Position (additive soft-wire):
  FAA (Acquire) → FRE (Retrieve & Rank) → CAE → Ask AGI

Architecture: v1.0.1 LOCKED.
"""

from app.faa.flags import FaaFlags
from app.faa.service import FaaService

__all__ = ["FaaFlags", "FaaService"]
