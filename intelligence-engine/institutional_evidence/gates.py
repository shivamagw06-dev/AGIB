"""Soft gates for Research Writer, Decision Engine, and Publishing."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .flags import iep_flags
from .schema import ALLOWED_WHEN_BLOCKED, BLOCKED_RECOMMENDATIONS


def ensure_research_pack(ticker: str, pack: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if isinstance(pack, dict) and pack.get("schema") == "InstitutionalResearchPack.v1":
        return pack
    from .research_pack.builder import build_institutional_research_pack

    return build_institutional_research_pack(str(ticker or "").upper())


def gate_research_writer(
    ticker: str,
    *,
    pack: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Research Writer cannot execute unless ResearchPack.claim_safe == true."""
    flags = iep_flags()
    p = ensure_research_pack(ticker, pack)
    if not flags.get("block_research_without_evidence"):
        return {"allowed": True, "soft_bypass": True, "pack": p}
    if p.get("claim_safe"):
        return {"allowed": True, "pack": p}
    return {
        "allowed": False,
        "blocked": True,
        "reason": "ResearchPack.claim_safe != true",
        "message": "Evidence unavailable.",
        "failures": (p.get("validation") or {}).get("failures") or p.get("missing_components"),
        "forbidden_invented_fields": p.get("forbidden_invented_fields"),
        "rule": "Never invent revenue/EPS/EBITDA/debt/margins/ARPU/GRM/capex/valuation",
        "pack_summary": {
            "ticker": p.get("ticker"),
            "research_ready": p.get("research_ready"),
            "claim_safe": p.get("claim_safe"),
        },
    }


def gate_decision_recommendation(
    ticker: str,
    recommendation: str,
    *,
    pack: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Cannot issue BUY/SELL/OW/UW unless evidence complete + statements + readiness."""
    flags = iep_flags()
    p = ensure_research_pack(ticker, pack)
    rec = str(recommendation or "").upper().strip()
    if not flags.get("block_recommendation_without_statements"):
        return {"allowed": True, "recommendation": rec, "soft_bypass": True}

    ready = bool(p.get("claim_safe") and p.get("research_ready"))
    if rec in BLOCKED_RECOMMENDATIONS and not ready:
        return {
            "allowed": False,
            "recommendation": "NO RECOMMENDATION",
            "alternate": list(ALLOWED_WHEN_BLOCKED),
            "original_recommendation": rec,
            "reason": "Evidence incomplete — financial statements not published or readiness below threshold",
            "pack_summary": {
                "claim_safe": p.get("claim_safe"),
                "research_ready": p.get("research_ready"),
                "score": (p.get("research_readiness") or {}).get("score"),
            },
        }
    if rec in ALLOWED_WHEN_BLOCKED or ready:
        return {"allowed": True, "recommendation": rec or "MONITOR", "pack": p}
    return {"allowed": True, "recommendation": rec, "pack": p}


def gate_publishing(
    ticker: str,
    *,
    pack: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Reject publication if claim_safe == false or Research Ready == false."""
    flags = iep_flags()
    p = ensure_research_pack(ticker, pack)
    if not flags.get("block_publish_unless_ready"):
        return {"allowed": True, "soft_bypass": True}
    if p.get("claim_safe") and p.get("research_ready"):
        return {"allowed": True, "pack": p}
    reasons = []
    if not p.get("claim_safe"):
        reasons.append("claim_safe == false")
    if not p.get("research_ready"):
        reasons.append("Research Ready == false")
    return {
        "allowed": False,
        "rejected": True,
        "failure_reasons": reasons,
        "failures": (p.get("validation") or {}).get("failures") or [],
        "message": "Publication rejected — institutional evidence incomplete",
    }
