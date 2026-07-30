"""KIL — Knowledge Integration Layer (AGI v1.1.2).

Bridge: Continuous Gather → Learn → Canonical Evidence → IEP.
There must never be two knowledge systems.
"""

from .layer import integrate_cgl_run, integrate_company, kil_status

__all__ = ["integrate_cgl_run", "integrate_company", "kil_status"]
