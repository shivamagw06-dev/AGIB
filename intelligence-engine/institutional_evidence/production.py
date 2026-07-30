"""IEP-01 production façades."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .flags import iep_flags, is_iep_enabled
from .schema import (
    GUIDING_PRINCIPLE,
    IEP_PRODUCT,
    IEP_SPEC,
    IEP_VERSION,
    IEP_WORKSTREAM_ID,
    PHASE1_TOP20,
    PHASE1_UNIVERSE,
    RESEARCH_READY_THRESHOLD,
)


def get_iep_status() -> Dict[str, Any]:
    return {
        "ok": True,
        "workstream_id": IEP_WORKSTREAM_ID,
        "product": IEP_PRODUCT,
        "version": IEP_VERSION,
        "spec": IEP_SPEC,
        "enabled": is_iep_enabled(),
        "flags": iep_flags(),
        "guiding_principle": GUIDING_PRINCIPLE,
        "phase1_universe_size": len(PHASE1_UNIVERSE),
        "research_ready_threshold": RESEARCH_READY_THRESHOLD,
        "pipeline": [
            "Raw Data",
            "Canonical Evidence",
            "Company Memory",
            "Knowledge Graph",
            "Financial Intelligence",
            "Decision Engine",
            "Research Note",
        ],
        "anti_pipeline": ["Raw Data", "LLM", "Research Note"],
    }


def get_research_pack(ticker: str, **kwargs: Any) -> Dict[str, Any]:
    from .research_pack.builder import build_institutional_research_pack

    return build_institutional_research_pack(ticker, **kwargs)


def get_research_readiness(ticker: str) -> Dict[str, Any]:
    pack = get_research_pack(ticker)
    return {
        "ok": True,
        "ticker": str(ticker).upper(),
        "readiness": pack.get("research_readiness"),
        "claim_safe": pack.get("claim_safe"),
        "research_ready": pack.get("research_ready"),
    }


def validate_research_pack(ticker: str = "", pack: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    from .validator.pack_validator import validate_research_pack_dict, ci_gate_failures

    p = pack if isinstance(pack, dict) else get_research_pack(ticker)
    v = validate_research_pack_dict(p)
    return {**v, "ci_gates": ci_gate_failures(p), "ticker": p.get("ticker")}


def orchestrate_research(ticker: str, **kwargs: Any) -> Dict[str, Any]:
    from .orchestrator.workflow import orchestrate_company_research

    return orchestrate_company_research(ticker, **kwargs)


def get_evidence_registry(ticker: str) -> Dict[str, Any]:
    from .registry.store import get_registry_for_ticker

    return get_registry_for_ticker(ticker)


def get_canonical_statements(ticker: str) -> Dict[str, Any]:
    from .canonical.statements import build_canonical_statements

    return build_canonical_statements(ticker)


def get_company_memory_bridge(ticker: str) -> Dict[str, Any]:
    from .canonical.statements import build_canonical_statements
    from .registry.store import get_registry_for_ticker
    from .company_memory_bridge.bridge import build_company_memory_view

    can = build_canonical_statements(ticker)
    reg = get_registry_for_ticker(ticker)
    return build_company_memory_view(ticker, canonical=can, registry=reg)


def get_phase1_coverage() -> Dict[str, Any]:
    rows = []
    ready_n = 0
    statements_n = 0
    complete_ev_n = 0
    for c in PHASE1_TOP20:
        t = c["ticker"]
        try:
            pack = get_research_pack(t, auto_acquire=True)
            ready = bool(pack.get("research_ready"))
            pub = bool((pack.get("financials") or {}).get("published"))
            ev_n = ((pack.get("evidence") or {}).get("registry") or {}).get("evidence_count") or 0
            if ready:
                ready_n += 1
            if pub:
                statements_n += 1
            if ev_n >= 2:
                complete_ev_n += 1
            rows.append(
                {
                    "ticker": t,
                    "company": c["company"],
                    "sector": c["sector"],
                    "research_ready": ready,
                    "claim_safe": pack.get("claim_safe"),
                    "readiness_score": (pack.get("research_readiness") or {}).get("score"),
                    "statements_published": pub,
                    "period_count": (pack.get("financials") or {}).get("period_count") or 0,
                    "evidence_count": ev_n,
                    "status": (pack.get("research_readiness") or {}).get("status"),
                }
            )
        except Exception as exc:
            rows.append({"ticker": t, "company": c["company"], "error": str(exc), "research_ready": False})
    n = max(1, len(PHASE1_TOP20))
    return {
        "ok": True,
        "phase": 1,
        "universe": "top_20_india_cross_sector",
        "companies": rows,
        "summary": {
            "total": len(PHASE1_TOP20),
            "with_canonical_statements": statements_n,
            "with_complete_evidence": complete_ev_n,
            "research_ready_pct": round(100.0 * ready_n / n, 2),
            "research_ready_count": ready_n,
        },
        "scale_rule": "Do NOT scale to Nifty 500 until Top-20 reaches institutional quality",
    }


def get_success_metrics() -> Dict[str, Any]:
    cov = get_phase1_coverage()
    summary = cov.get("summary") or {}
    block_rate = 100.0 - float(summary.get("research_ready_pct") or 0)
    return {
        "ok": True,
        "metrics": {
            "companies_with_canonical_statements": summary.get("with_canonical_statements"),
            "companies_with_complete_evidence": summary.get("with_complete_evidence"),
            "research_ready_pct": summary.get("research_ready_pct"),
            "recommendation_block_rate_proxy_pct": round(block_rate, 2),
            "phase1_total": summary.get("total"),
        },
        "tracked": [
            "Companies with canonical statements",
            "Companies with complete evidence",
            "Research Ready %",
            "Primary citation coverage",
            "Missing evidence count",
            "Recommendation block rate",
            "Average analyst corrections",
            "Evidence freshness SLA",
            "Research publication success",
        ],
        "coverage": cov,
    }


def get_evidence_center_board() -> Dict[str, Any]:
    status = get_iep_status()
    metrics = get_success_metrics()
    return {
        "ok": True,
        "board": "Evidence Center",
        "workstream_id": IEP_WORKSTREAM_ID,
        "status": status,
        "metrics": metrics.get("metrics"),
        "phase1_summary": (metrics.get("coverage") or {}).get("summary"),
        "design_principles": [
            "No research without evidence",
            "No recommendation without canonical financial statements",
            "No narrative without lineage",
            "Every material claim maps to primary evidence",
            "Missing evidence blocks publication",
            "Every downstream engine consumes a single canonical Research Pack",
        ],
    }


def soft_slice_mission_control() -> Dict[str, Any]:
    """Mission Control Evidence Center soft slice — cheap; never scans Top-20 live."""
    try:
        return {
            "status": "ok" if is_iep_enabled() else "disabled",
            "workstream_id": IEP_WORKSTREAM_ID,
            "product": IEP_PRODUCT,
            "version": IEP_VERSION,
            "companies_with_canonical_statements": None,
            "companies_with_complete_evidence": None,
            "research_ready_pct": None,
            "research_ready_count": None,
            "phase1_total": len(PHASE1_TOP20),
            "recommendation_block_rate_proxy_pct": None,
            "threshold": RESEARCH_READY_THRESHOLD,
            "guiding_principle": GUIDING_PRINCIPLE,
            "board": "Evidence Center",
            "note": "Call /api/intelligence/iep/phase1 or /iep/metrics for live coverage",
            "flags": iep_flags(),
        }
    except Exception as exc:
        return {
            "status": "error",
            "workstream_id": IEP_WORKSTREAM_ID,
            "error": str(exc)[:240],
        }


def health() -> Dict[str, Any]:
    return get_iep_status()


# Gate façades
def check_writer_gate(ticker: str, **kwargs: Any) -> Dict[str, Any]:
    from .gates import gate_research_writer

    return gate_research_writer(ticker, **kwargs)


def check_decision_gate(ticker: str, recommendation: str, **kwargs: Any) -> Dict[str, Any]:
    from .gates import gate_decision_recommendation

    return gate_decision_recommendation(ticker, recommendation, **kwargs)


def check_publish_gate(ticker: str, **kwargs: Any) -> Dict[str, Any]:
    from .gates import gate_publishing

    return gate_publishing(ticker, **kwargs)
