"""Freshness Engine — every section reports freshness vs institutional SLAs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.contracts.models import KnowledgeObjectType
from app.krig.policies import BundleSection


@dataclass(frozen=True)
class FreshnessSla:
    label: str
    max_age_seconds: int


# Institutional defaults (Sprint 6.4)
SLA_BY_SECTION: dict[BundleSection, FreshnessSla] = {
    BundleSection.COMPANY: FreshnessSla("7 days", 7 * 86400),
    BundleSection.FINANCIALS: FreshnessSla("Quarterly", 7 * 86400),
    BundleSection.VALUATION: FreshnessSla("30 seconds", 30),
    BundleSection.CORPORATE_EVENTS: FreshnessSla("1 day", 86400),
    BundleSection.SECTOR: FreshnessSla("1 day", 86400),
    BundleSection.MARKET: FreshnessSla("30 seconds", 30),
    BundleSection.MACRO: FreshnessSla("1 hour", 3600),
    BundleSection.LEARNING: FreshnessSla("1 day", 86400),
    BundleSection.MEMORY: FreshnessSla("1 day", 86400),
    BundleSection.TIMELINE: FreshnessSla("1 day", 86400),
    BundleSection.RELATIONSHIPS: FreshnessSla("1 day", 86400),
    BundleSection.MONITORING: FreshnessSla("1 day", 86400),
    BundleSection.EVIDENCE: FreshnessSla("1 day", 86400),
    BundleSection.CONFLICTS: FreshnessSla("1 day", 86400),
}

OBJECT_TYPE_SLA: dict[KnowledgeObjectType, FreshnessSla] = {
    KnowledgeObjectType.MARKET_SNAPSHOT: FreshnessSla("30 seconds", 30),
    KnowledgeObjectType.COMPANY_PROFILE: FreshnessSla("7 days", 7 * 86400),
    KnowledgeObjectType.FINANCIAL_STATEMENT: FreshnessSla("Quarterly", 7 * 86400),
    KnowledgeObjectType.CORPORATE_EVENT: FreshnessSla("1 day", 86400),
    KnowledgeObjectType.SECTOR_KNOWLEDGE: FreshnessSla("1 day", 86400),
    KnowledgeObjectType.MARKET_KNOWLEDGE: FreshnessSla("1 hour", 3600),
}


def _parse_ts(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value:
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def evaluate_freshness(
    section: BundleSection,
    *,
    updated_at: Any = None,
    present: bool = True,
    now: datetime | None = None,
) -> dict[str, Any]:
    sla = SLA_BY_SECTION[section]
    now = now or datetime.now(timezone.utc)
    if not present:
        return {
            "status": "Missing",
            "sla": sla.label,
            "updated": None,
            "age_seconds": None,
            "needs_refresh": True,
        }
    ts = _parse_ts(updated_at)
    if ts is None:
        return {
            "status": "Unknown",
            "sla": sla.label,
            "updated": None,
            "age_seconds": None,
            "needs_refresh": True,
        }
    age = max(0.0, (now - ts).total_seconds())
    fresh = age <= sla.max_age_seconds
    return {
        "status": "Fresh" if fresh else "Stale",
        "sla": sla.label,
        "updated": ts.isoformat(),
        "age_seconds": int(age),
        "needs_refresh": not fresh,
    }


class FreshnessEngine:
    def register(self, store, *, object_type: str, subject_key: str, updated_at: str) -> None:
        store.upsert_freshness(object_type=object_type, subject_key=subject_key, updated_at=updated_at)

    def section_report(self, section: BundleSection, *, updated_at: Any, present: bool) -> dict[str, Any]:
        return evaluate_freshness(section, updated_at=updated_at, present=present)
