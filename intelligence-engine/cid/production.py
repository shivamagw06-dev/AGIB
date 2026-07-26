"""CID production bridge — soft adapters for locked engines (no redesign)."""

from __future__ import annotations

from typing import Any

from cid.coverage import compute_coverage
from cid.ingest import ensure_dossier, ingest_leo_evidence
from cid.schema import CID_VERSION
from cid.store import get_cid_store


TRACKED_TICKERS = (
    "HDFCBANK",
    "INFY",
    "RELIANCE",
    "ULTRACEMCO",
    "ASIANPAINT",
    "TATASTEEL",
    "SUNPHARMA",
    "POWERGRID",
)


def is_cid_enabled() -> bool:
    try:
        from app.core.config import get_settings

        return bool(getattr(get_settings(), "cid", True))
    except Exception:
        return True


def get_dossier(ticker: str) -> dict[str, Any]:
    if not is_cid_enabled():
        return {"enabled": False, "cid_version": CID_VERSION, "bypassed": True}
    t = (ticker or "").upper()
    d = get_cid_store().get(t)
    if not d:
        d = ensure_dossier(t)
    return {**d, "enabled": True}


def get_or_build(
    ticker: str | None,
    *,
    query: str | None = None,
    leo_pkg: dict[str, Any] | None = None,
    finance_academy: dict[str, Any] | None = None,
    sif_pkg: dict[str, Any] | None = None,
    valuation_pack: dict[str, Any] | None = None,
    forecast_pack: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Primary Ask AGI / CAE entry — always prefer living dossier over raw APIs."""
    if not is_cid_enabled():
        return {"enabled": False, "cid_version": CID_VERSION, "bypassed": True, "answer_policy": "cid_disabled"}

    t = (ticker or (leo_pkg or {}).get("ticker") or "").upper() or None
    if not t:
        return {
            "enabled": True,
            "cid_version": CID_VERSION,
            "ticker": None,
            "reason": "no_ticker",
            "answer_policy": "dossier_before_raw_apis",
        }

    # Prefer LEO-driven ingest when fresh evidence is present
    if isinstance(leo_pkg, dict) and leo_pkg.get("evidence_objects"):
        dossier = ingest_leo_evidence(
            t,
            leo_pkg.get("evidence_objects") or [],
            plan=leo_pkg.get("evidence_plan") or {"ticker": t, "query": query, "company": (leo_pkg.get("entity") or {}).get("company")},
            finance_academy=finance_academy
            if isinstance(finance_academy, dict)
            else (leo_pkg.get("finance_academy") if isinstance(leo_pkg.get("finance_academy"), dict) else None),
            sif_pkg=sif_pkg
            if isinstance(sif_pkg, dict)
            else (
                leo_pkg.get("sector_intelligence")
                if isinstance(leo_pkg.get("sector_intelligence"), dict)
                else None
            ),
            valuation_pack=valuation_pack,
            forecast_pack=forecast_pack,
        )
    else:
        dossier = ensure_dossier(t, query=query)
        if finance_academy or sif_pkg:
            dossier = ingest_leo_evidence(
                t,
                [],
                plan={"ticker": t, "query": query},
                finance_academy=finance_academy,
                sif_pkg=sif_pkg,
                valuation_pack=valuation_pack,
                forecast_pack=forecast_pack,
            )

    return {
        **dossier,
        "enabled": True,
        "cid_version": CID_VERSION,
        "answer_policy": "dossier_before_raw_apis",
        "reasoning_hint": _reasoning_hint(dossier),
    }


def attach_for_engine(engine: str, ticker: str | None, **kwargs: Any) -> dict[str, Any]:
    pkg = get_or_build(ticker, **kwargs)
    return {
        "company_dossier": pkg,
        "attached": bool(pkg.get("enabled")) and bool(pkg.get("ticker")),
        "engine": engine,
    }


def package_for_ask_agi(
    query: str,
    *,
    ticker: str | None = None,
    leo_pkg: dict[str, Any] | None = None,
    finance_academy: dict[str, Any] | None = None,
    sif_pkg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return get_or_build(
        ticker,
        query=query,
        leo_pkg=leo_pkg,
        finance_academy=finance_academy,
        sif_pkg=sif_pkg,
    )


def timeline(ticker: str, *, limit: int = 100) -> dict[str, Any]:
    d = get_dossier(ticker)
    events = list(d.get("evidence_timeline") or [])[-limit:]
    events = list(reversed(events))
    return {
        "ticker": (ticker or "").upper(),
        "count": len(events),
        "events": events,
        "cid_version": CID_VERSION,
    }


def coverage(ticker: str) -> dict[str, Any]:
    d = get_dossier(ticker)
    cov = compute_coverage(d)
    return {
        "ticker": (ticker or "").upper(),
        "coverage_score": cov["coverage_score"],
        "coverage_grade": cov["coverage_grade"],
        "institutional_ready": cov["institutional_ready"],
        "categories": cov["coverage"],
        "missing_evidence": cov["missing_evidence"],
        "cid_version": CID_VERSION,
    }


def valuation_view(ticker: str) -> dict[str, Any]:
    d = get_dossier(ticker)
    return {
        "ticker": (ticker or "").upper(),
        "valuation": d.get("valuation") or {},
        "market_data": d.get("market_data") or {},
        "sector_framework": d.get("sector_framework") or {},
        "cid_version": CID_VERSION,
    }


def risk_view(ticker: str) -> dict[str, Any]:
    d = get_dossier(ticker)
    return {
        "ticker": (ticker or "").upper(),
        "risks": d.get("risks") or {},
        "catalysts": d.get("catalysts") or {},
        "cid_version": CID_VERSION,
    }


def forecast_view(ticker: str) -> dict[str, Any]:
    d = get_dossier(ticker)
    return {
        "ticker": (ticker or "").upper(),
        "forecasts": d.get("forecasts") or {},
        "cid_version": CID_VERSION,
    }


def documents_view(ticker: str) -> dict[str, Any]:
    d = get_dossier(ticker)
    return {
        "ticker": (ticker or "").upper(),
        "documents": d.get("documents") or {},
        "announcements": (d.get("announcements") or [])[-40:],
        "latest_filing": d.get("latest_filing"),
        "latest_presentation": d.get("latest_presentation"),
        "latest_announcement": d.get("latest_announcement"),
        "cid_version": CID_VERSION,
    }


def production_dashboard() -> dict[str, Any]:
    store = get_cid_store()
    # Ensure tracked universe has shells
    for t in TRACKED_TICKERS:
        if not store.get(t):
            ensure_dossier(t)
    rows = store.summary_rows(limit=100)
    grades = {}
    for r in rows:
        g = r.get("coverage_grade") or "Insufficient"
        grades[g] = grades.get(g, 0) + 1
    return {
        "programme": "CID",
        "cid_version": CID_VERSION,
        "architecture_status": "v1.0.1 LOCKED",
        "enabled": is_cid_enabled(),
        "dossier_count": len(rows),
        "tracked_tickers": list(TRACKED_TICKERS),
        "grade_distribution": grades,
        "dossiers": rows,
        "answer_policy": "dossier_before_raw_apis",
        "not_an_engine": True,
    }


def warm_tracked(*, use_leo: bool = True) -> dict[str, Any]:
    """Validation helper — build dossiers for tracked tickers via LEO when requested."""
    packages = []
    for t in TRACKED_TICKERS:
        leo_pkg = None
        if use_leo:
            try:
                from leo.production import package_for_query

                leo_pkg = package_for_query(f"Should I buy {t}?", ticker=t, engine="cid_warm", record=False)
            except Exception:
                leo_pkg = None
        sif_pkg = (leo_pkg or {}).get("sector_intelligence") if isinstance(leo_pkg, dict) else None
        # Also pull SIF directly
        try:
            from sif.production import analyse_query

            sif_pkg = analyse_query(f"Should I buy {t}?", ticker=t, engine="cid", record=False) or sif_pkg
        except Exception:
            pass
        try:
            from academy.fapi.production import package_for_query as fapi_package

            fa = fapi_package(f"Should I buy {t}?", engine="cid", ticker=t, record=False)
        except Exception:
            fa = {}
        d = get_or_build(t, query=f"Should I buy {t}?", leo_pkg=leo_pkg, finance_academy=fa, sif_pkg=sif_pkg)
        packages.append(
            {
                "ticker": t,
                "coverage_score": d.get("coverage_score"),
                "coverage_grade": d.get("coverage_grade"),
                "sector_id": (d.get("sector_framework") or {}).get("sector_id"),
                "academy_concepts": len((d.get("finance_academy") or {}).get("active_concepts") or []),
                "timeline_events": len(d.get("evidence_timeline") or []),
                "documents": {
                    k: len(v or [])
                    for k, v in ((d.get("documents") or {}).items())
                },
                "sif_attached": bool((d.get("sector_framework") or {}).get("sector_id")),
                "academy_linked": bool((d.get("finance_academy") or {}).get("active_concepts")),
            }
        )
    return {
        "cid_version": CID_VERSION,
        "count": len(packages),
        "packages": packages,
        "pass": all(p["timeline_events"] > 0 and p["sif_attached"] for p in packages),
    }


def quality_gates() -> dict[str, Any]:
    warmed = warm_tracked(use_leo=True)
    checks = {
        "dossiers_created": all(p.get("ticker") for p in warmed["packages"]),
        "evidence_updates": all((p.get("timeline_events") or 0) > 0 for p in warmed["packages"]),
        "coverage_calculated": all(p.get("coverage_score") is not None for p in warmed["packages"]),
        "sif_attached": all(p.get("sif_attached") for p in warmed["packages"]),
        "academy_linked": all(p.get("academy_linked") for p in warmed["packages"]),
        "leo_updates_dossier": all((p.get("timeline_events") or 0) > 0 for p in warmed["packages"]),
    }
    return {
        "cid_version": CID_VERSION,
        "passed": all(checks.values()),
        "checks": checks,
        "packages": warmed["packages"],
    }


def _reasoning_hint(dossier: dict[str, Any]) -> str:
    grade = dossier.get("coverage_grade") or "Insufficient"
    sector = (dossier.get("sector_framework") or {}).get("sector_name") or (dossier.get("identity") or {}).get("sector")
    kpis = ((dossier.get("sector_kpis") or {}).get("priority_metrics") or [])[:6]
    miss = dossier.get("missing_evidence") or []
    parts = [
        f"CID {dossier.get('ticker')}: {grade} (score {dossier.get('coverage_score')}).",
    ]
    if sector:
        parts.append(f"Sector framework: {sector}.")
    if kpis:
        parts.append("Priority KPIs: " + ", ".join(kpis) + ".")
    if miss:
        parts.append("Missing: " + ", ".join(miss[:6]) + ".")
    parts.append("Reason from this dossier first — do not rebuild company context from raw APIs.")
    return " ".join(parts)
