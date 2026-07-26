"""Living company dossier — accumulates LEO evidence over queries."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any


_LOCK = Lock()
_DOSSIERS: dict[str, dict[str, Any]] = {}


def update_dossier(ticker: str | None, evidence_objects: list[dict[str, Any]], *, plan: dict[str, Any] | None = None) -> dict[str, Any]:
    if not ticker:
        return {"enabled": False, "reason": "no_ticker"}
    t = ticker.upper()
    now = datetime.now(timezone.utc).isoformat()
    with _LOCK:
        d = _DOSSIERS.get(t) or {
            "ticker": t,
            "company": (plan or {}).get("company") or t,
            "sector_id": (plan or {}).get("sector_id"),
            "business": {},
            "segments": [],
            "annual_reports": [],
            "quarterly_results": [],
            "investor_presentations": [],
            "corporate_announcements": [],
            "financial_statements": [],
            "valuation": [],
            "forecasts": [],
            "sector_kpis": [],
            "academy_concepts": [],
            "evidence_timeline": [],
            "coverage_score": 0.0,
            "updated_at": now,
        }
        type_buckets = {
            "annual_report": "annual_reports",
            "quarterly_results": "quarterly_results",
            "investor_presentation": "investor_presentations",
            "corporate_announcement": "corporate_announcements",
            "financial_statements": "financial_statements",
            "valuation_metrics": "valuation",
            "sector_kpis": "sector_kpis",
        }
        for obj in evidence_objects or []:
            et = obj.get("evidence_type")
            bucket = type_buckets.get(et)
            entry = {
                "evidence_id": obj.get("evidence_id"),
                "title": obj.get("title"),
                "source_id": obj.get("source_id"),
                "published": obj.get("published"),
                "confidence": obj.get("confidence"),
                "verification_status": obj.get("verification_status"),
                "url": obj.get("url"),
            }
            if bucket:
                existing_ids = {x.get("evidence_id") for x in d[bucket]}
                if entry["evidence_id"] not in existing_ids:
                    d[bucket].append(entry)
                    d[bucket] = d[bucket][-40:]
            d["evidence_timeline"].append(
                {
                    "at": now,
                    "evidence_id": obj.get("evidence_id"),
                    "evidence_type": et,
                    "title": obj.get("title"),
                    "source_id": obj.get("source_id"),
                }
            )
        d["evidence_timeline"] = d["evidence_timeline"][-200:]
        # Coverage: fraction of core buckets non-empty
        core = [
            "annual_reports",
            "quarterly_results",
            "investor_presentations",
            "corporate_announcements",
            "financial_statements",
            "valuation",
            "sector_kpis",
        ]
        filled = sum(1 for k in core if d.get(k))
        d["coverage_score"] = round(filled / len(core), 4)
        d["updated_at"] = now
        if plan and plan.get("sector_id"):
            d["sector_id"] = plan.get("sector_id")
        _DOSSIERS[t] = d
        return dict(d)


def get_dossier(ticker: str) -> dict[str, Any]:
    with _LOCK:
        return dict(_DOSSIERS.get((ticker or "").upper()) or {})


def list_dossiers(limit: int = 50) -> list[dict[str, Any]]:
    with _LOCK:
        rows = sorted(_DOSSIERS.values(), key=lambda d: d.get("updated_at") or "", reverse=True)
        return [dict(r) for r in rows[:limit]]
