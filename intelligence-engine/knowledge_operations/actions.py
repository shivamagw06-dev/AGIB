"""Operational actions for Knowledge Operations Center (audited)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from knowledge_operations.audit import record_audit


def run_action(
    action: str,
    *,
    ticker: Optional[str] = None,
    actor: Optional[str] = None,
    force: bool = False,
) -> Dict[str, Any]:
    a = str(action or "").strip().lower()
    t = (ticker or "").upper().strip() or None
    result: Dict[str, Any] = {"ok": False, "action": a}

    try:
        if a in {"run_cgl", "cgl"}:
            from continuous_gather_learn.orchestrator import run_cycle

            result = {"ok": True, "action": a, "result": run_cycle()}
        elif a in {"run_kil", "kil"}:
            from institutional_evidence.production import integrate_company_knowledge, run_kil_integration

            if t:
                result = {"ok": True, "action": a, "result": integrate_company_knowledge(t)}
            else:
                result = {"ok": True, "action": a, "result": run_kil_integration(None)}
        elif a in {"run_full_coverage", "full_coverage", "icf_tick"}:
            from institutional_coverage_factory.production import run_coverage_tick

            result = {
                "ok": True,
                "action": a,
                "result": run_coverage_tick(scope="TOP20", dispatch=True),
            }
        elif a in {"run_auto_repair", "auto_repair"} and t:
            from institutional_evidence.integration.repair.auto_repair import repair_missing_knowledge

            result = {"ok": True, "action": a, "result": repair_missing_knowledge(t)}
        elif a in {"run_research_refresh", "research_refresh"} and t:
            from institutional_evidence.research_pack.builder import build_institutional_research_pack

            pack = build_institutional_research_pack(t, auto_acquire=True)
            result = {
                "ok": True,
                "action": a,
                "result": {
                    "research_ready": pack.get("research_ready"),
                    "claim_safe": pack.get("claim_safe"),
                },
            }
        elif a in {"run_knowledge_validation", "validate"} and t:
            from institutional_evidence.production import validate_research_pack

            result = {"ok": True, "action": a, "result": validate_research_pack(t)}
        elif a in {"run_company_memory_refresh", "memory_refresh"} and t:
            from institutional_evidence.production import get_company_memory_bridge

            result = {"ok": True, "action": a, "result": get_company_memory_bridge(t)}
        elif a in {"run_research_readiness", "readiness"} and t:
            from institutional_evidence.production import get_research_readiness

            result = {"ok": True, "action": a, "result": get_research_readiness(t)}
        elif a in {"rebuild_knowledge_graph", "kg_rebuild"} and t:
            from institutional_evidence.production import get_evidence_graph

            result = {"ok": True, "action": a, "result": get_evidence_graph(t)}
        elif a in {"run_icf_dispatch", "dispatch"} and t:
            from institutional_coverage_factory.production import dispatch_company

            result = {"ok": True, "action": a, "result": dispatch_company(t)}
        elif a in {"run_coverage_scan", "coverage_scan"}:
            from institutional_coverage_factory.production import plan_coverage

            result = {
                "ok": True,
                "action": a,
                "result": plan_coverage(limit=20, scope="TOP20"),
            }
        elif a in {"run_institutional_coverage_check", "icc_check"} and t:
            from institutional_coverage_factory.production import icc_status_for

            result = {"ok": True, "action": a, "result": icc_status_for(t)}
        elif a in {"run_top20_audit", "top20_audit"}:
            from institutional_coverage_factory.production import coverage_dashboard

            result = {
                "ok": True,
                "action": a,
                "result": coverage_dashboard(scope="TOP20"),
            }
        elif a in {"run_kg_refresh", "knowledge_graph_refresh"} and t:
            from institutional_evidence.production import get_evidence_graph

            result = {"ok": True, "action": a, "result": get_evidence_graph(t)}
        else:
            result = {
                "ok": False,
                "action": a,
                "error": "unknown_or_ticker_required",
                "hint": "Pass ticker for company-scoped actions",
            }
    except Exception as exc:
        result = {"ok": False, "action": a, "error": str(exc)[:240]}

    audit = record_audit(
        a,
        actor=actor or "admin",
        ticker=t,
        research_updated=bool(result.get("ok")),
        details={"force": force, "ok": result.get("ok"), "error": result.get("error")},
    )
    result["audit"] = audit
    return result
