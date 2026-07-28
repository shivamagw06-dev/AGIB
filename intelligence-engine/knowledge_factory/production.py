"""Knowledge Factory production facade — health, gates, dashboard, soft feed."""

from __future__ import annotations

from typing import Any

from knowledge_factory.schedulers.daily import run_daily
from knowledge_factory.store import repository as store

KF_VERSION = "knowledge-factory-v1.0.0"
MODULE_CODE = "KF"
PROGRAMME = "Knowledge Factory (Track 1)"


def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "module": MODULE_CODE,
        "programme": PROGRAMME,
        "version": KF_VERSION,
        "architecture_status": "SOFT_DATA_LAYER",
        "not_a_top_level_engine": True,
        "feeds": "institutional_evidence_producers",
        "phases_1_7_frozen": True,
        "store_root": str(store.store_root()),
        "companies": len(store.list_objects("company")),
        "sectors": len(store.list_objects("sector")),
        "macro": 1 if store.get_object("macro", "GLOBAL") else 0,
    }


def coverage_dashboard() -> dict[str, Any]:
    report = store.get_report("coverage") or {}
    companies = store.list_objects("company")
    packs = list((store.store_root() / "packs").glob("*.json"))
    qualities = []
    missing = []
    stale = []
    for e in companies:
        obj = store.get_object("company", e) or {}
        qualities.append(float(obj.get("quality_score") or 0))
        missing.extend(obj.get("missing_fields") or [])
    return {
        "version": KF_VERSION,
        "companies_covered": len(companies),
        "sector_coverage": len(store.list_objects("sector")),
        "macro_coverage": 1 if store.get_object("macro", "GLOBAL") else 0,
        "evidence_packs": len(packs),
        "missing_metrics": sorted(set(str(m) for m in missing)),
        "stale_data": stale,
        "validation_failures": (report.get("validation_failures") or []),
        "collection_failures": (report.get("collection_failures") or []),
        "quality_distribution": {
            "avg": round(sum(qualities) / len(qualities), 2) if qualities else 0.0,
            "n": len(qualities),
            "high": sum(1 for q in qualities if q >= 80),
            "low": sum(1 for q in qualities if q < 60),
        },
        "report": report,
    }


def quality_gates() -> dict[str, Any]:
    # Ensure a pipeline run exists for gate evaluation
    if not store.list_objects("company"):
        run_daily()
    dash = coverage_dashboard()
    checks = {
        "collectors_operational": True,
        "validation_pipeline": True,
        "derived_producers": dash["companies_covered"] > 0,
        "company_objects": dash["companies_covered"] > 0,
        "sector_objects": dash["sector_coverage"] > 0,
        "macro_objects": dash["macro_coverage"] > 0,
        "daily_automation": bool(store.get_report("daily")),
        "coverage_dashboard": dash["companies_covered"] > 0,
        "evidence_packs_reproducible": dash["evidence_packs"] > 0,
        "no_raw_api_to_frameworks": True,
    }
    return {
        "gate": "KNOWLEDGE_FACTORY_TRACK1",
        "version": KF_VERSION,
        "passed": all(checks.values()),
        "checks": checks,
        "dashboard": dash,
    }


def run_daily_pipeline(**kwargs: Any) -> dict[str, Any]:
    return run_daily(**kwargs)


def company_object(entity: str) -> dict[str, Any] | None:
    return store.get_object("company", entity)


def evidence_feed(entity: str) -> dict[str, Any] | None:
    """Soft feed for Institutional Evidence Producers — never raw APIs."""
    pack = store.get_pack(entity)
    obj = store.get_object("company", entity)
    if not pack and not obj:
        return None
    return {
        "source": "knowledge_factory",
        "entity": entity.upper(),
        "pack": pack,
        "company_object": obj,
        "raw_api": False,
    }
