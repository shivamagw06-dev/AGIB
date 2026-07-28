"""Read-only soft aggregation for Mission Control — never mutates research or house views."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from mission_control.flags import flags_dict, is_enabled
from mission_control.schema import (
    ARCHITECTURE_NODES,
    COPILOT_PROMPTS,
    MISSION_CONTROL_VERSION,
    PLATFORMS,
    PROGRAMME,
    PROGRAMME_SHORT,
)
from mission_control import store as mc_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _status_norm(v: Any) -> str:
    s = str(getattr(v, "value", v) or "unknown").lower()
    if s in {"ok", "healthy", "health", "pass", "passed", "green"}:
        return "Healthy"
    if s in {"warning", "warn", "stale", "degraded", "yellow"}:
        return "Warning"
    if s in {"critical", "fail", "failed", "error", "red"}:
        return "Critical"
    if s in {"offline", "disabled", "down"}:
        return "Offline"
    if s in {"unknown", "none", ""}:
        return "Unknown"
    return s.title() if s else "Unknown"


def _soft(fn, default=None):
    try:
        return fn()
    except Exception:
        return default if default is not None else {}


def _soft_institutional_intelligence() -> dict[str, Any]:
    """Soft-read Sprints 1–7 KPIs for Mission Control. Never mutates KF/IDQ stores here."""
    out: dict[str, Any] = {
        "decision_coverage": {},
        "historical_depth": None,
        "sector_intelligence": None,
        "macro_intelligence": None,
        "decision_quality": None,
        "roadmap_next": None,
        "sources": [],
    }
    try:
        from knowledge_factory.coverage import decision_coverage, NIFTY_100, NIFTY_500, TARGET_20
        from institutional_reasoning.fundamentals.universe import NIFTY_50

        t20 = decision_coverage(TARGET_20)
        n50 = decision_coverage(NIFTY_50)
        n100 = decision_coverage(NIFTY_100)
        n500 = decision_coverage(NIFTY_500)
        idc_pct = n500.get("decision_coverage_pct")
        try:
            from knowledge_factory.institutional_depth import institutional_decision_coverage

            idc = institutional_decision_coverage(NIFTY_500)
            idc_pct = idc.get("institutional_decision_coverage_pct")
        except Exception:
            pass
        out["decision_coverage"] = {
            "target_20": t20.get("decision_coverage_pct"),
            "nifty_50": n50.get("decision_coverage_pct"),
            "nifty_100": n100.get("decision_coverage_pct"),
            "nifty_500": n500.get("decision_coverage_pct"),
            "institutional_decision_coverage": idc_pct,
        }
        out["sources"].append("knowledge_factory.coverage")
        out["roadmap_next"] = (
            "tier_3_midcap_thematic"
            if (n500.get("decision_coverage_pct") or 0) >= 100
            else "nifty_500"
        )
    except Exception:
        pass
    try:
        from universe_intelligence.dashboard import universe_health

        uh = universe_health(universe_id="NIFTY_500", ensure=False)
        out["universe_intelligence"] = {
            "avg_ici": (uh.get("coverage") or {}).get("avg_ici"),
            "institutional_coverage_pct": (uh.get("coverage") or {}).get("institutional_coverage_pct"),
            "failure_count": uh.get("failure_count"),
            "stale_count": uh.get("stale_count"),
            "north_star": uh.get("north_star"),
        }
        out["sources"].append("universe_intelligence")
        if (uh.get("coverage") or {}).get("institutional_coverage_pct") == 100.0:
            out["roadmap_next"] = "tier_3_midcap_thematic"
    except Exception:
        out["universe_intelligence"] = None
    try:
        from knowledge_factory.company_intelligence.dashboard import company_intelligence_dashboard

        ci = company_intelligence_dashboard(ensure=False)
        out["company_intelligence"] = {
            "institutional_company_coverage_pct": ci.get("institutional_company_coverage_pct"),
            "average_intelligence_score": ci.get("average_intelligence_score"),
            "unknown_fields": ci.get("unknown_fields"),
            "north_star": ci.get("north_star"),
            "layer_label": ci.get("layer_label"),
        }
        out["sources"].append("company_intelligence")
        if (ci.get("institutional_company_coverage_pct") or 0) >= 100:
            out["roadmap_next"] = "company_intelligence_depth_enrichment"
    except Exception:
        out["company_intelligence"] = None
    try:
        from knowledge_factory.corporate_events.dashboard import corporate_events_dashboard

        ce = corporate_events_dashboard(ensure=False)
        out["corporate_events"] = {
            "coverage_pct": ce.get("coverage_pct"),
            "corporate_events": ce.get("corporate_events"),
            "critical_events": ce.get("critical_events"),
            "timeline_completeness_avg": ce.get("timeline_completeness_avg"),
            "north_star": ce.get("north_star"),
        }
        out["sources"].append("corporate_events")
        if (ce.get("coverage_pct") or 0) >= 100:
            out["roadmap_next"] = "government_regulatory_intelligence"
    except Exception:
        out["corporate_events"] = None
    try:
        from knowledge_factory.government_intelligence.dashboard import government_dashboard

        gov = government_dashboard(ensure=False)
        out["government_intelligence"] = {
            "coverage_pct": gov.get("coverage_pct"),
            "policy_count": gov.get("policy_count"),
            "high_impact_policies": gov.get("high_impact_policies"),
            "replay_status": gov.get("replay_status"),
            "north_star": gov.get("north_star"),
        }
        out["sources"].append("government_intelligence")
        if (gov.get("coverage_pct") or 0) >= 100:
            out["roadmap_next"] = "industry_value_chain_intelligence"
    except Exception:
        out["government_intelligence"] = None
    try:
        from knowledge_factory.industry_intelligence.dashboards import industry_dashboard

        ind = industry_dashboard(ensure=False)
        out["industry_intelligence"] = {
            "institutional_ready_pct": ind.get("institutional_ready_pct"),
            "industry_coverage": ind.get("industry_coverage"),
            "industry_intelligence_score": ind.get("industry_intelligence_score"),
            "companies_mapped": ind.get("companies_mapped"),
            "north_star": ind.get("north_star"),
            "future_roadmap": ind.get("future_roadmap"),
        }
        out["sources"].append("industry_intelligence")
        if (ind.get("institutional_ready_pct") or 0) >= 100 and (ind.get("companies_mapped") or 0) >= 500:
            out["roadmap_next"] = "economic_relationship_intelligence"
    except Exception:
        out["industry_intelligence"] = None
    try:
        from knowledge_factory.economic_relationship_intelligence.dashboards import (
            relationship_dashboard,
        )

        rel = relationship_dashboard(ensure=False)
        cov = rel.get("economic_relationship_coverage") or {}
        out["economic_relationship_intelligence"] = {
            "relationships": cov.get("relationships"),
            "commodities": cov.get("commodities"),
            "institutional_ready_pct": cov.get("institutional_ready_pct"),
            "company_relationships": rel.get("company_relationships"),
            "north_star": rel.get("north_star"),
        }
        out["sources"].append("economic_relationship_intelligence")
        if (cov.get("institutional_ready_pct") or 0) >= 100 and (cov.get("relationships") or 0) >= 50:
            out["roadmap_next"] = "alternative_data_intelligence"
    except Exception:
        out["economic_relationship_intelligence"] = None
    try:
        from knowledge_factory.alternative_data_intelligence.dashboards import (
            alternative_data_dashboard,
        )

        alt = alternative_data_dashboard(ensure=False)
        acov = alt.get("alternative_data_coverage") or {}
        out["alternative_data_intelligence"] = {
            "datasets": acov.get("datasets"),
            "observations": acov.get("observations"),
            "institutional_ready_pct": acov.get("institutional_ready_pct"),
            "economic_momentum": alt.get("economic_momentum"),
            "north_star": alt.get("north_star"),
            "delivery_phase": alt.get("delivery_phase"),
        }
        out["sources"].append("alternative_data_intelligence")
        if (acov.get("institutional_ready_pct") or 0) >= 100 and (acov.get("datasets") or 0) >= 10:
            out["roadmap_next"] = "market_expectations_intelligence"
    except Exception:
        out["alternative_data_intelligence"] = None
    try:
        from knowledge_factory.market_expectations_intelligence.dashboards import (
            expectations_dashboard,
        )

        exp = expectations_dashboard(ensure=False)
        ecov = exp.get("expectation_dashboard") or {}
        out["market_expectations_intelligence"] = {
            "expectations": ecov.get("expectations"),
            "revisions": ecov.get("revisions"),
            "surprises": ecov.get("surprises"),
            "narratives": ecov.get("narratives"),
            "institutional_ready_pct": ecov.get("institutional_ready_pct"),
            "north_star": exp.get("north_star"),
            "delivery_phase": exp.get("delivery_phase"),
            "principle": exp.get("principle"),
        }
        out["sources"].append("market_expectations_intelligence")
        if (ecov.get("surprises") or 0) >= 1 and (ecov.get("narratives") or 0) >= 10:
            out["roadmap_next"] = "knowledge_stack_complete"
    except Exception:
        out["market_expectations_intelligence"] = None
    # Unified Institutional Knowledge Stack board (soft orchestration).
    try:
        from knowledge_factory.institutional_knowledge_stack.production import dashboard as iks_dash

        iks = iks_dash(ensure=False)
        out["institutional_knowledge_stack"] = {
            "summary": iks.get("summary"),
            "reality": {
                k: {"status": v.get("status")} for k, v in (iks.get("reality") or {}).items()
            },
            "expectations": {
                k: {"status": v.get("status")} for k, v in (iks.get("expectations") or {}).items()
            },
            "roadmap_next": iks.get("roadmap_next"),
            "north_star": iks.get("north_star"),
        }
        out["sources"].append("institutional_knowledge_stack")
        if (iks.get("summary") or {}).get("stack_complete"):
            out["roadmap_next"] = "knowledge_stack_complete"
    except Exception:
        out["institutional_knowledge_stack"] = None
    # AGIB v2.1 Institutional Scheduler — soft ops heartbeat.
    try:
        from institutional_scheduler.production import dashboard as sched_dash
        from institutional_scheduler.production import status as sched_status

        st = sched_status()
        dash = sched_dash()
        out["institutional_scheduler"] = {
            "state": st.get("state"),
            "system_ready": st.get("system_ready"),
            "current_workflow": st.get("current_workflow"),
            "current_run_id": st.get("current_run_id"),
            "ready_status": (dash.get("ready_status") or {}),
            "mission_control_ops": dash.get("mission_control_ops"),
            "north_star": dash.get("north_star"),
        }
        out["sources"].append("institutional_scheduler")
        out["system_ready"] = bool(st.get("system_ready"))
    except Exception:
        out["institutional_scheduler"] = None
    # AGIB v2.1 Ask Pipeline board (soft observability).
    try:
        from ask_pipeline.production import dashboard as ask_dash

        ad = ask_dash()
        out["ask_pipeline"] = {
            "questions_today": ad.get("questions_today"),
            "average_latency_ms": ad.get("average_latency_ms"),
            "pipeline_coverage": ad.get("pipeline_coverage"),
            "evidence_coverage_avg": ad.get("evidence_coverage_avg"),
            "decision_records": ad.get("decision_records"),
            "outcome_registered": ad.get("outcome_registered"),
            "replay_ready": ad.get("replay_ready"),
            "north_star": ad.get("north_star"),
        }
        out["sources"].append("ask_pipeline")
    except Exception:
        out["ask_pipeline"] = None
    # AGIB v2.2 Institutional Research Office — soft research desk board.
    try:
        from research_office.production import dashboard as ro_dash
        from research_office.production import health as ro_health

        rd = ro_dash()
        rh = ro_health()
        out["research_office"] = {
            "status": (rh.get("office_status") or {}).get("state"),
            "ready_for_users": rd.get("ready_for_users"),
            "morning_publications": len(rd.get("todays_publications") or []),
            "research_queue_follow_ups": len((rd.get("outstanding_reviews") or [])),
            "outstanding_research": len(rd.get("outstanding_reviews") or []),
            "missing_coverage": len(rd.get("missing_evidence") or []),
            "publication_health": rd.get("validation"),
            "north_star": rd.get("north_star"),
        }
        out["sources"].append("research_office")
    except Exception:
        out["research_office"] = None
    # AGIB v3.0 LIDI — live institutional data soft board.
    try:
        from live_data.production import dashboard as lidi_dash
        from live_data.production import health as lidi_health
        from live_data.production import status as lidi_status

        ls = lidi_status()
        ld = lidi_dash()
        lh = lidi_health()
        out["live_institutional_data"] = {
            "state": ls.get("state"),
            "collectors_operational": ls.get("collectors_operational"),
            "collectors_total": ls.get("collectors_total"),
            "validation_failures": ld.get("validation_failures"),
            "fallback_usage": ld.get("fallback_usage"),
            "missing_data": ld.get("missing_data"),
            "fixture_collectors_disabled": ls.get("fixture_collectors_disabled"),
            "north_star": ld.get("north_star"),
            "health": lh.get("status"),
        }
        out["sources"].append("live_institutional_data")
    except Exception:
        out["live_institutional_data"] = None
    # AGIB v3.0 LIDI Track 2 — collector certification board (soft).
    try:
        from live_data.production_verify import certification as lidi_cert
        from live_data.production_verify import health_dashboard as lidi_health_dash
        from live_data.production_verify import report_status as lidi_report_status

        cert = lidi_cert()
        hd = lidi_health_dash()
        rs = lidi_report_status()
        out["live_collector_activation"] = {
            "version": cert.get("version"),
            "certification_summary": cert.get("summary"),
            "dashboard_rows": len(hd.get("rows") or []),
            "readiness_score": (rs.get("readiness") or {}).get("score"),
            "last_verification_run_id": rs.get("last_run_id"),
            "north_star": hd.get("north_star"),
            "all_certified": (cert.get("summary") or {}).get("all_certified"),
        }
        out["sources"].append("live_collector_activation")
    except Exception:
        out["live_collector_activation"] = None
    # AGIB v3.1 IDI — institutional documents soft board.
    try:
        from knowledge_factory.institutional_documents.production import dashboard as idi_dash
        from knowledge_factory.institutional_documents.production import health as idi_health

        idh = idi_health()
        idd = idi_dash()
        out["institutional_documents"] = {
            "status": idh.get("status"),
            "version": idh.get("version"),
            "documents": idd.get("documents"),
            "companies_updated": len(idd.get("companies_updated") or []),
            "knowledge_objects_created": idd.get("knowledge_objects_created"),
            "validation_failures": idd.get("validation_failures"),
            "replay_status": idd.get("replay_status"),
            "north_star": idd.get("north_star"),
        }
        out["sources"].append("institutional_documents")
    except Exception:
        out["institutional_documents"] = None
    # AGIB v3.2 IERE — institutional evidence retrieval soft board.
    try:
        from evidence_retrieval.production import dashboard as iere_dash
        from evidence_retrieval.production import health as iere_health

        ih = iere_health()
        idash = iere_dash()
        out["evidence_retrieval"] = {
            "status": ih.get("status"),
            "version": ih.get("version"),
            "evidence_coverage": idash.get("evidence_coverage"),
            "evidence_freshness": idash.get("evidence_freshness"),
            "retrieval_latency_ms": idash.get("retrieval_latency_ms"),
            "citation_coverage": idash.get("citation_coverage"),
            "replay_health": idash.get("replay_health"),
            "knowledge_completeness": idash.get("knowledge_completeness"),
            "evidence_confidence": idash.get("evidence_confidence"),
            "north_star": idash.get("north_star"),
        }
        out["sources"].append("evidence_retrieval")
    except Exception:
        out["evidence_retrieval"] = None
    # AGIB v3.4 Track C — IFSE soft board
    try:
        from framework_selection.production import dashboard as ifse_dash
        from framework_selection.production import health as ifse_health

        fh = ifse_health()
        fd = ifse_dash()
        out["framework_selection"] = {
            "status": fh.get("status"),
            "version": fh.get("ifse_version"),
            "selection_count": fd.get("selection_count"),
            "wrong_framework_rate": fd.get("wrong_framework_rate"),
            "multi_framework_usage": fd.get("multi_framework_usage"),
            "confidence_distribution": fd.get("confidence_distribution"),
            "framework_coverage": fd.get("framework_coverage"),
            "framework_accuracy": fd.get("framework_accuracy"),
        }
        out["sources"].append("framework_selection")
    except Exception:
        out["framework_selection"] = None
    # AGIB v3.4 Track D — ICE soft board
    try:
        from institutional_communication.production import dashboard as ice_dash
        from institutional_communication.production import health as ice_health

        ih = ice_health()
        idash = ice_dash()
        out["institutional_communication"] = {
            "status": ih.get("status"),
            "version": ih.get("ice_version"),
            "communication_style": idash.get("communication_style"),
            "template_used": idash.get("template_used"),
            "framework_visibility": idash.get("framework_visibility"),
            "citation_density": idash.get("citation_density"),
            "narrative_completeness": idash.get("narrative_completeness"),
            "confidence_quality": idash.get("confidence_quality"),
            "generic_template_rate": idash.get("generic_template_rate"),
        }
        out["sources"].append("institutional_communication")
    except Exception:
        out["institutional_communication"] = None
    # AGIB v3.5 — IAP soft board
    try:
        from institutional_playbooks.production import dashboard as iap_dash
        from institutional_playbooks.production import health as iap_health

        ph = iap_health()
        pdash = iap_dash()
        out["institutional_playbooks"] = {
            "status": ph.get("status"),
            "version": ph.get("iap_version"),
            "registry_n": pdash.get("registry_n"),
            "category_counts": pdash.get("category_counts"),
            "target_met": pdash.get("target_met"),
            "recent_n": pdash.get("recent_n"),
            "guides_reasoning": True,
        }
        out["sources"].append("institutional_playbooks")
    except Exception:
        out["institutional_playbooks"] = None
    # AGIB v3.6 Phase 2 — IEG soft board
    try:
        from institutional_evidence_graph.production import dashboard as ieg_dash
        from institutional_evidence_graph.production import health as ieg_health

        eh = ieg_health()
        edash = ieg_dash()
        out["institutional_evidence_graph"] = {
            "status": eh.get("status"),
            "version": eh.get("ieg_version"),
            "n_domains": edash.get("n_domains"),
            "avg_domain_coverage_pct": edash.get("avg_domain_coverage_pct"),
            "recent_n": edash.get("recent_n"),
            "guides_evidence": True,
        }
        out["sources"].append("institutional_evidence_graph")
    except Exception:
        out["institutional_evidence_graph"] = None
    # AGIB v3.6 Phase 2 Sprint 2.2 — IMAI soft board
    try:
        from institutional_analog_intelligence.production import board as imai_board
        from institutional_analog_intelligence.production import status as imai_status

        mh = imai_status()
        mdash = imai_board()
        out["institutional_analog_intelligence"] = {
            "status": mh.get("status"),
            "version": mh.get("version"),
            "memory_count": mh.get("memory_count"),
            "memory_hits": mdash.get("memory_hits"),
            "analog_accuracy": mdash.get("analog_accuracy"),
            "regime_coverage": mdash.get("regime_coverage"),
            "historical_coverage": mdash.get("historical_coverage"),
            "replay_coverage": mdash.get("replay_coverage"),
            "guides_memory": True,
            "distinct_from_ilm": True,
        }
        out["sources"].append("institutional_analog_intelligence")
    except Exception:
        out["institutional_analog_intelligence"] = None
    # AGIB Phase 3 Sprint 3.1 — IEL soft board
    try:
        from institutional_evaluation_lab.production import board as iel_board
        from institutional_evaluation_lab.production import status as iel_status

        ih = iel_status()
        idash = iel_board()
        latest = idash.get("latest_run") or {}
        out["institutional_evaluation_lab"] = {
            "status": ih.get("status"),
            "version": ih.get("version"),
            "catalogue_all": (ih.get("catalogue") or {}).get("all"),
            "meets_1000_plus": (ih.get("catalogue") or {}).get("meets_1000_plus"),
            "latest_pass_pct": latest.get("pass_pct"),
            "latest_mean_score": latest.get("mean_score"),
            "quality_targets": ih.get("quality_targets"),
            "measurement_only": True,
        }
        out["sources"].append("institutional_evaluation_lab")
    except Exception:
        out["institutional_evaluation_lab"] = None
    # AGIB Phase 3 Sprint 3.2 — RCI soft board
    try:
        from root_cause_intelligence.production import board as rci_board
        from root_cause_intelligence.production import status as rci_status

        rh = rci_status()
        rdash = rci_board()
        out["root_cause_intelligence"] = {
            "status": rh.get("status"),
            "version": rh.get("version"),
            "n_failures": rdash.get("n_failures"),
            "n_clusters": rdash.get("n_clusters"),
            "iel_pass_pct": rdash.get("iel_pass_pct"),
            "top_cluster": ((rdash.get("top_10") or [{}])[0]).get("impact_statement"),
            "recommended_pr_count": len(rdash.get("recommended_prs") or []),
            "gaps": rdash.get("gaps"),
            "measurement_driven": True,
        }
        out["sources"].append("root_cause_intelligence")
    except Exception:
        out["root_cause_intelligence"] = None
    # Patch Intelligence — human-in-the-loop briefs
    try:
        from patch_intelligence.production import status as pi_status
        from root_cause_intelligence import store as rci_store

        ph = pi_status()
        latest = rci_store.latest() or {}
        pi = latest.get("patch_intelligence") or {}
        out["patch_intelligence"] = {
            "status": ph.get("status"),
            "version": ph.get("version"),
            "n_briefs": pi.get("n_briefs"),
            "highest_roi": (pi.get("highest_roi") or {}).get("recommended_title"),
            "never_writes_code_automatically": True,
        }
        out["sources"].append("patch_intelligence")
    except Exception:
        out["patch_intelligence"] = None
    # AGI Phase 3 Sprint 3.5 — Temporal Integrity & Replay Certification
    try:
        from temporal_integrity.production import dashboard as tirc_dashboard
        from temporal_integrity.production import status as tirc_status

        th = tirc_status()
        td = tirc_dashboard()
        out["temporal_integrity"] = {
            "company": th.get("company"),
            "status": th.get("status"),
            "version": th.get("version"),
            "replay_health": td.get("replay_health"),
            "certification_status": td.get("certification_status"),
            "future_leakage_count": td.get("future_leakage_count"),
            "replay_accuracy_pct": td.get("replay_accuracy_pct"),
            "objects_rejected": td.get("objects_rejected"),
            "institutional_guarantee": td.get("institutional_guarantee"),
        }
        out["sources"].append("temporal_integrity")
    except Exception:
        out["temporal_integrity"] = None
    # AGI Observability — LangSmith tracing status (read-only)
    try:
        from observability.production import dashboard as obs_dashboard

        od = obs_dashboard()
        out["observability"] = {
            "provider": "langsmith",
            "enabled": od.get("enabled"),
            "project": od.get("project"),
            "api_key_present": od.get("api_key_present"),
            "sdk_available": od.get("sdk_available"),
            "traced_stages": od.get("n_traced_stages"),
            "observability_only": True,
        }
        out["sources"].append("observability")
    except Exception:
        out["observability"] = None
    # AGI Phase 4 Sprint 4.1 — Institutional Evidence Weighting Engine
    try:
        from institutional_evidence_weighting.production import dashboard as iew_dashboard
        from institutional_evidence_weighting.production import status as iew_status

        ih = iew_status()
        idash = iew_dashboard()
        out["institutional_evidence_weighting"] = {
            "company": ih.get("company"),
            "status": ih.get("status"),
            "version": ih.get("version"),
            "weight_version": idash.get("weight_version"),
            "average_weight": idash.get("average_weight"),
            "dominant_sources": idash.get("dominant_sources"),
            "n_recent_runs": idash.get("n_recent_runs"),
            "replay_status": idash.get("replay_status"),
            "llm_used": False,
        }
        out["sources"].append("institutional_evidence_weighting")
    except Exception:
        out["institutional_evidence_weighting"] = None
    # AGI Phase 4 Sprint 4.2 — Institutional Hypothesis Generation Engine
    try:
        from institutional_hypothesis_generation.production import dashboard as ihg_dashboard
        from institutional_hypothesis_generation.production import status as ihg_status

        hh = ihg_status()
        hd = ihg_dashboard()
        out["institutional_hypothesis_generation"] = {
            "company": hh.get("company"),
            "status": hh.get("status"),
            "version": hh.get("version"),
            "hypothesis_version": hd.get("hypothesis_version"),
            "average_hypotheses": hd.get("average_hypotheses"),
            "rejected_hypotheses": hd.get("rejected_hypotheses"),
            "winning_hypothesis": hd.get("winning_hypothesis"),
            "hypothesis_confidence": hd.get("hypothesis_confidence"),
            "evidence_support": hd.get("evidence_support"),
            "conflict_score": hd.get("conflict_score"),
            "plural": hd.get("plural"),
            "forced_single_winner": False,
            "llm_used": False,
        }
        out["sources"].append("institutional_hypothesis_generation")
    except Exception:
        out["institutional_hypothesis_generation"] = None
    # AGI Phase 4 Sprint 4.3 — Institutional Hypothesis Evaluation Engine
    try:
        from institutional_hypothesis_evaluation.production import dashboard as ihe_dashboard
        from institutional_hypothesis_evaluation.production import status as ihe_status

        eh = ihe_status()
        ed = ihe_dashboard()
        out["institutional_hypothesis_evaluation"] = {
            "company": eh.get("company"),
            "status": eh.get("status"),
            "version": eh.get("version"),
            "evaluation_version": ed.get("evaluation_version"),
            "preferred_hypotheses": ed.get("preferred_hypotheses"),
            "rejected_hypotheses": ed.get("rejected_hypotheses"),
            "average_support": ed.get("average_support"),
            "average_conflict": ed.get("average_conflict"),
            "coverage": ed.get("coverage"),
            "missing_evidence_frequency": ed.get("missing_evidence_frequency"),
            "outcome": ed.get("outcome"),
            "plural": ed.get("plural"),
            "forced_single_winner": False,
            "llm_used": False,
        }
        out["sources"].append("institutional_hypothesis_evaluation")
    except Exception:
        out["institutional_hypothesis_evaluation"] = None
    # AGI Phase 4 Sprint 4.4 — Institutional Committee Reasoning (ICR)
    try:
        from institutional_committee_reasoning.production import dashboard as icr_dashboard
        from institutional_committee_reasoning.production import status as icr_status

        ch = icr_status()
        cd = icr_dashboard()
        out["institutional_committee_reasoning"] = {
            "company": ch.get("company"),
            "status": ch.get("status"),
            "version": ch.get("version"),
            "committee_version": cd.get("committee_version"),
            "bull_base_bear_distribution": cd.get("bull_base_bear_distribution"),
            "average_confidence": cd.get("average_confidence"),
            "probability_distribution": cd.get("probability_distribution"),
            "unresolved_disagreements": cd.get("unresolved_disagreements"),
            "missing_evidence": cd.get("missing_evidence"),
            "dominant_assumptions": cd.get("dominant_assumptions"),
            "historical_analogue_usage": cd.get("historical_analogue_usage"),
            "preferred_case": cd.get("preferred_case"),
            "voting_engine": False,
            "llm_used": False,
        }
        out["sources"].append("institutional_committee_reasoning")
    except Exception:
        out["institutional_committee_reasoning"] = None
    # AGI Phase 4 Sprint 4.5 — Institutional Confidence Calibration (ICC)
    try:
        from institutional_confidence_calibration.production import dashboard as icc_dashboard
        from institutional_confidence_calibration.production import status as icc_status

        fh = icc_status()
        fd = icc_dashboard()
        out["institutional_confidence_calibration"] = {
            "company": fh.get("company"),
            "status": fh.get("status"),
            "version": fh.get("version"),
            "confidence_version": fd.get("confidence_version"),
            "average_confidence": fd.get("average_confidence"),
            "confidence_distribution": fd.get("confidence_distribution"),
            "top_uncertainty_drivers": fd.get("top_uncertainty_drivers"),
            "evidence_penalties": fd.get("evidence_penalties"),
            "committee_agreement": fd.get("committee_agreement"),
            "missing_evidence": fd.get("missing_evidence"),
            "historical_analogue_quality": fd.get("historical_analogue_quality"),
            "framework_consistency": fd.get("framework_consistency"),
            "latest_confidence": fd.get("latest_confidence"),
            "latest_reason": fd.get("latest_reason"),
            "llm_used": False,
            "manually_assigned": False,
            "phase4_complete": True,
        }
        out["sources"].append("institutional_confidence_calibration")
    except Exception:
        out["institutional_confidence_calibration"] = None
    # AGI v4.0 Phase 5 Sprint 5.1 — Institutional Investment Thesis Engine
    try:
        from institutional_investment_thesis.production import dashboard as ite_dashboard
        from institutional_investment_thesis.production import status as ite_status

        th = ite_status()
        td = ite_dashboard()
        out["institutional_investment_thesis"] = {
            "company": th.get("company"),
            "status": th.get("status"),
            "version": th.get("version"),
            "release": th.get("release"),
            "n_theses": td.get("n_theses"),
            "n_active": td.get("n_active"),
            "n_watch": td.get("n_watch"),
            "lifecycle_distribution": td.get("lifecycle_distribution"),
            "decision_distribution": td.get("decision_distribution"),
            "average_confidence_active": td.get("average_confidence_active"),
            "waiting_for_earnings_review": td.get("waiting_for_earnings_review"),
            "confidence_dropped_gt_10": td.get("confidence_dropped_gt_10"),
            "buy_sell": False,
            "judgment_stack_modified": False,
            "llm_used": False,
        }
        out["sources"].append("institutional_investment_thesis")
    except Exception:
        out["institutional_investment_thesis"] = None
    # AGI v4.0 Phase 5 Sprint 5.2 — Institutional Decision Office
    try:
        from institutional_decision_office.production import dashboard as ido_dashboard
        from institutional_decision_office.production import status as ido_status

        dh = ido_status()
        dd = ido_dashboard()
        out["institutional_decision_office"] = {
            "company": dh.get("company"),
            "status": dh.get("status"),
            "version": dh.get("version"),
            "release": dh.get("release"),
            "n_decisions": dd.get("n_decisions"),
            "decision_distribution": dd.get("decision_distribution"),
            "lifecycle_distribution": dd.get("lifecycle_distribution"),
            "n_wait": dd.get("n_wait"),
            "n_monitor": dd.get("n_monitor"),
            "n_approve": dd.get("n_approve"),
            "n_escalate": dd.get("n_escalate"),
            "review_after_earnings": dd.get("review_after_earnings"),
            "orders": False,
            "buy_sell": False,
            "execution": False,
            "judgment_stack_modified": False,
            "llm_used": False,
        }
        out["sources"].append("institutional_decision_office")
    except Exception:
        out["institutional_decision_office"] = None
    try:
        from knowledge_factory.production import historical_depth_coverage

        hd = historical_depth_coverage()
        out["historical_depth"] = {
            "average_history_years": hd.get("average_history_years"),
            "companies_gt_20y_pct": hd.get("companies_gt_20y_pct"),
            "point_in_time_integrity": hd.get("point_in_time_integrity"),
        }
        out["sources"].append("historical_depth")
    except Exception:
        pass
    try:
        from knowledge_factory.production import sector_intelligence_coverage

        isi = sector_intelligence_coverage()
        out["sector_intelligence"] = {
            "sector_coverage_pct": isi.get("sector_coverage_pct"),
            "playbook_coverage_pct": isi.get("playbook_coverage_pct"),
            "status": isi.get("status"),
        }
        out["sources"].append("sector_intelligence")
    except Exception:
        pass
    try:
        from knowledge_factory.production import macro_intelligence_coverage

        imi = macro_intelligence_coverage()
        kpi = imi.get("kpi") or imi
        out["macro_intelligence"] = {
            "coverage": kpi.get("coverage"),
            "status": imi.get("status"),
            "regime_coverage": kpi.get("regime_coverage"),
        }
        out["sources"].append("macro_intelligence")
    except Exception:
        pass
    try:
        from decision_quality.production import dashboard as idq_dashboard

        idq = idq_dashboard()
        kpi = idq.get("kpi") or {}
        out["decision_quality"] = {
            "coverage": kpi.get("coverage") or kpi.get("institutional_decision_quality"),
            "status": idq.get("status"),
            "hall_fame": (kpi.get("counts") or {}).get("hall_fame"),
            "hall_shame": (kpi.get("counts") or {}).get("hall_shame"),
        }
        out["sources"].append("decision_quality")
    except Exception:
        pass
    return out


def _platform_card(name: str, *, status: str = "Unknown", **extra: Any) -> dict[str, Any]:
    return {
        "name": name,
        "current_status": _status_norm(status),
        "last_run": extra.get("last_run"),
        "last_success": extra.get("last_success"),
        "last_failure": extra.get("last_failure"),
        "runtime": extra.get("runtime"),
        "average_response_time": extra.get("average_response_time"),
        "coverage": extra.get("coverage"),
        "knowledge_count": extra.get("knowledge_count"),
        "error_count": extra.get("error_count") or 0,
        "warnings": extra.get("warnings") or 0,
        "dependencies": extra.get("dependencies") or [],
        "health_score": extra.get("health_score"),
        "details": extra.get("details") or {},
        "read_only": True,
    }


def build_mission_control(*, ioc_service: Any | None = None) -> dict[str, Any]:
    if not is_enabled():
        return {
            "enabled": False,
            "programme": PROGRAMME,
            "version": MISSION_CONTROL_VERSION,
            "bypassed": True,
            "read_only": True,
        }

    # Soft pulls — never raise into the cockpit
    ioc = {}
    if ioc_service is not None:
        try:
            from app.aws.adapters import dump, soft

            ioc = dump(soft(ioc_service.dashboard)) or {}
        except Exception:
            ioc = _soft(lambda: ioc_service.dashboard().model_dump(mode="json") if hasattr(ioc_service.dashboard(), "model_dump") else {})
    if not ioc:
        ioc = _soft(lambda: __import__("app.ioc.service", fromlist=["IocService"]).IocService().dashboard().model_dump(mode="json"))

    cms = _soft(lambda: __import__("company_monitor.production", fromlist=["dashboard"]).dashboard())
    io = _soft(lambda: __import__("investment_office.production", fromlist=["dashboard"]).dashboard())
    ca = _soft(lambda: __import__("company_analysis.production", fromlist=["dashboard"]).dashboard())
    books = _soft(lambda: __import__("academy.books.production", fromlist=["dashboard"]).dashboard())
    try:
        from company_monitor import store as cms_store

        cms_changes = list(cms_store.list_changes(limit=40) or [])
        cms_alerts = list(cms_store.list_alerts(40) or [])
        cms_reviews = list(cms_store.list_reviews(40) or [])
    except Exception:
        cms_changes, cms_alerts, cms_reviews = [], [], []

    dvc = _soft(lambda: __import__("dvc.production", fromlist=["production_dashboard"]).production_dashboard())
    if not dvc:
        dvc = _soft(lambda: __import__("dvc.production", fromlist=["dashboard"]).dashboard())
    ecp = _soft(lambda: __import__("ecp.production", fromlist=["production_dashboard"]).production_dashboard())
    if not ecp:
        ecp = _soft(lambda: __import__("ecp.production", fromlist=["dashboard"]).dashboard())

    leo_h = _soft(lambda: __import__("leo.production", fromlist=["health"]).health() if hasattr(__import__("leo.production", fromlist=["health"]), "health") else {})
    if not leo_h:
        leo_h = _soft(lambda: {"status": "soft", "programme": "LEO"})

    cid_h = _soft(lambda: __import__("cid.production", fromlist=["is_cid_enabled"]).is_cid_enabled())
    sif_h = _soft(lambda: __import__("sif.production", fromlist=["quality_gates"]).quality_gates())

    overall_ioc = _status_norm(ioc.get("overall_health") or ioc.get("status") or ioc.get("overall"))
    coverage = (io.get("coverage_dashboard") or cms.get("coverage") or {})
    knowledge = io.get("knowledge_growth") or {
        "books_learned": books.get("books_successfully_ingested"),
        "concepts_added": books.get("concept_count"),
        "frameworks_added": books.get("framework_count"),
        "companies_updated": (cms.get("metrics") or {}).get("companies_monitored"),
    }

    # SECTION 1 — Executive Status
    exec_status = {
        "agi_status": overall_ioc if overall_ioc != "Unknown" else ("Healthy" if is_enabled() else "Offline"),
        "research_grade": coverage.get("research_grade") or "B",
        "knowledge_grade": coverage.get("knowledge_grade") or "B",
        "data_grade": str(coverage.get("data_grade") or overall_ioc or "ok"),
        "coverage": coverage.get("coverage_pct") or (cms.get("coverage") or {}).get("financial_channel_pct") or 55,
        "system_confidence": None,
        "companies_covered": (cms.get("metrics") or {}).get("companies_monitored") or len(cms.get("companies_monitored") or []),
        "companies_monitored": (cms.get("metrics") or {}).get("companies_monitored") or 0,
        "questions_answered_today": None,
        "last_successful_learning": books.get("latest_ingestion_report", {}).get("books_version")
        if isinstance(books.get("latest_ingestion_report"), dict)
        else None,
        "last_deployment": None,
        "last_health_check": _now(),
        "sources": ["ioc", "investment_office", "company_monitor", "academy.books"],
    }

    # Soft Institutional Stack (FIL→FDI→MII→EIL→PIL) — additive platform cards
    stack_irs = _soft(
        lambda: __import__(
            "institutional_stack.production", fromlist=["soft_slice_for_mission_control"]
        ).soft_slice_for_mission_control()
    )
    stack_dash = _soft(
        lambda: __import__("institutional_stack.production", fromlist=["dashboard"]).dashboard()
    )
    stack_slice = (stack_irs or {}).get("institutional_stack") or {}
    stack_layers = (stack_dash or {}).get("layer_health") or {}

    # SECTION 2 — Platform Status
    ioc_platforms = ioc.get("platform_status") or {}
    platforms = [
        _platform_card("Knowledge Foundation", status=ioc_platforms.get("kip") or "soft", dependencies=["KIP"], health_score=70),
        _platform_card("CID", status="Healthy" if cid_h else "Warning", dependencies=["LEO", "SIF"], knowledge_count=None),
        _platform_card(
            "Academy",
            status="Healthy" if books.get("enabled", True) else "Offline",
            knowledge_count=books.get("concept_count"),
            coverage=books.get("coverage"),
            dependencies=["FAPI", "Books"],
            health_score=85 if books.get("concept_count") else 60,
        ),
        _platform_card("Financial Intelligence", status="soft", dependencies=["CID", "YFP", "DVC"]),
        _platform_card(
            "Company Analysis",
            status="Healthy" if ca.get("enabled", True) else "Offline",
            knowledge_count=(ca.get("metrics") or {}).get("reports"),
            dependencies=["CID", "Academy", "SIF"],
        ),
        _platform_card(
            "Company Monitor",
            status="Healthy" if cms.get("enabled", True) else "Offline",
            knowledge_count=(cms.get("metrics") or {}).get("change_events"),
            error_count=(cms.get("metrics") or {}).get("critical_alerts") or 0,
            dependencies=["LEO", "CID", "Company Analysis"],
        ),
        _platform_card(
            "Investment Office",
            status="Healthy" if io.get("enabled", True) else "Offline",
            dependencies=["CMS", "CA", "IOC", "Academy"],
            health_score=80,
        ),
        _platform_card("KIP", status=ioc_platforms.get("kip") or "soft", dependencies=["store"]),
        _platform_card("RSP", status=ioc_platforms.get("rsp") or "soft"),
        _platform_card("RMS", status=ioc_platforms.get("rms") or "soft"),
        _platform_card("IOC", status=overall_ioc, dependencies=["engines", "providers"]),
        _platform_card("DVC", status="Healthy" if (dvc.get("enabled") is not False) else "Offline", details=dvc.get("metrics") or dvc),
        _platform_card("ECP", status="Healthy" if (ecp.get("enabled") is not False) else "Offline", details=ecp.get("metrics") or ecp),
        _platform_card("Ask AGI", status="soft", dependencies=["IRP", "CAE", "IO", "CMS"]),
        _platform_card(
            "Filing Intelligence",
            status="Healthy" if (stack_layers.get("filing_intelligence") or {}).get("enabled", True) else "Offline",
            dependencies=["Official Filings"],
            details=stack_layers.get("filing_intelligence") or {},
        ),
        _platform_card(
            "Filing Diff",
            status="Healthy" if (stack_layers.get("filing_diff") or {}).get("enabled", True) else "Offline",
            dependencies=["FIL"],
            details=stack_layers.get("filing_diff") or {},
        ),
        _platform_card(
            "Management Intelligence",
            status="Healthy" if (stack_layers.get("management_intelligence") or {}).get("enabled", True) else "Offline",
            dependencies=["FIL", "FDI"],
            details=stack_layers.get("management_intelligence") or {},
        ),
        _platform_card(
            "Accounting Intelligence",
            status="Healthy" if (stack_layers.get("accounting_intelligence") or {}).get("enabled", True) else "Offline",
            dependencies=["FIL", "FDI", "MII"],
            details=stack_layers.get("accounting_intelligence") or {},
        ),
        _platform_card(
            "Portfolio Intelligence",
            status="Healthy" if (stack_layers.get("portfolio_intelligence") or {}).get("enabled", True) else "Offline",
            dependencies=["Investment Committee", "MII", "ACI"],
            details=stack_layers.get("portfolio_intelligence") or {},
        ),
        _platform_card(
            "Peer Intelligence",
            status="Healthy" if (stack_layers.get("peer_intelligence") or {}).get("enabled", True) else "Offline",
            dependencies=["FIL"],
            details=stack_layers.get("peer_intelligence") or {},
        ),
        _platform_card(
            "Evidence Intelligence",
            status="Healthy" if (stack_layers.get("evidence_intelligence") or {}).get("enabled", True) else "Offline",
            dependencies=["FIL", "PIL"],
            details=stack_layers.get("evidence_intelligence") or {},
        ),
        _platform_card(
            "Institutional Stack",
            status="Healthy" if stack_slice.get("enabled", True) else "Offline",
            dependencies=["FIL", "FDI", "MII", "ACI", "PIO", "EIL", "PIL"],
            knowledge_count=stack_slice.get("seed_documents"),
            details=stack_slice,
        ),
    ]

    # SECTION 3 — Engine Status
    engine_status = ioc.get("engine_status") or {}
    engines = []
    for name in ("LEO", "IRP", "RSP", "KIP", "DVC", "ECP", "Financial Intelligence", "Company Analysis", "Company Monitor", "Investment Office"):
        key = name.lower().replace(" ", "_")
        st = engine_status.get(key) or engine_status.get(name.lower())
        if name == "LEO":
            st = st or leo_h.get("status") or "soft"
        if name == "Company Monitor":
            st = "Healthy" if cms.get("enabled", True) else "Disabled"
        if name == "Company Analysis":
            st = "Healthy" if ca.get("enabled", True) else "Disabled"
        if name == "Investment Office":
            st = "Healthy" if io.get("enabled", True) else "Disabled"
        engines.append(
            {
                "name": name,
                "status": _status_norm(st or "soft"),
                "last_execution": None,
                "execution_time": None,
                "queue": None,
                "failures": 0,
                "retries": 0,
                "memory_usage": None,
                "cpu_usage": None,
                "read_only": True,
            }
        )

    # SECTION 4 — API / Provider Status
    providers = []
    for p in ioc.get("provider_health") or ioc.get("providers") or []:
        if not isinstance(p, dict):
            # pydantic dump may already be dict
            try:
                p = p.model_dump(mode="json") if hasattr(p, "model_dump") else {"provider_id": str(p), "status": "unknown"}
            except Exception:
                p = {"provider_id": str(p), "status": "unknown"}
        st = _status_norm(p.get("status"))
        colour = "Green" if st == "Healthy" else "Yellow" if st == "Warning" else "Red"
        providers.append(
            {
                "name": p.get("provider_id") or p.get("name") or "provider",
                "status": st,
                "colour": colour,
                "latency": p.get("latency"),
                "requests_today": None,
                "success_rate": None,
                "failure_rate": None,
                "last_error": p.get("last_error"),
                "rate_limit": None,
                "quota_usage": None,
                "remaining_quota": None,
                "last_successful_request": None,
                "average_response_time": None,
                "provider_confidence": "configured" if p.get("configured") else "unknown",
                "circuit_state": p.get("circuit_state"),
                "capabilities": p.get("capabilities") or [],
            }
        )
    # Ensure named providers appear even if IOC sparse
    known = {p["name"].lower() for p in providers}
    for label in (
        "Yahoo Finance",
        "Indian API",
        "Finnhub",
        "FMP",
        "OpenAI",
        "Supabase",
        "Render",
        "Hostinger",
        "SMTP",
        "Email",
        "GitHub",
        "Scheduler",
        "Redis",
    ):
        if label.lower() not in known and not any(label.lower().split()[0] in k for k in known):
            providers.append(
                {
                    "name": label,
                    "status": "Unknown",
                    "colour": "Yellow",
                    "latency": None,
                    "last_error": None,
                    "provider_confidence": "not_probed",
                    "note": "Soft placeholder — IOC provider probe when configured",
                }
            )

    # SECTION 5 — Knowledge Growth
    # research_learned / last_5_days_* are soft-enriched by Node from CMS learn events.
    knowledge_growth = {
        "windows": ["Last Hour", "Last 24 Hours", "Last 5 Days", "Last 7 Days"],
        "research_learned": None,
        "companies_updated": knowledge.get("companies_updated"),
        "books_learned": knowledge.get("books_learned") or books.get("books_successfully_ingested"),
        "concepts_added": knowledge.get("concepts_added") or books.get("concept_count"),
        "frameworks_added": knowledge.get("frameworks_added") or books.get("framework_count"),
        "formulas_added": knowledge.get("formulas_added") or books.get("formula_count"),
        "financial_statements_updated": None,
        "valuation_updates": None,
        "research_notes": None,
        "cid_updates": None,
        "knowledge_foundation_updates": None,
        "prediction_evaluations": None,
        "house_view_reviews": len(cms_reviews),
        "last_5_days_summary": None,
        "last_5_days_highlights": [],
        "last_5_days": [],
        "sources": ["academy.books", "company_monitor", "investment_office", "cms_article_learning"],
    }

    # SECTION 6 — Coverage (+ soft Institutional Intelligence from Sprints 1–7)
    institutional = _soft_institutional_intelligence()
    dc = institutional.get("decision_coverage") or {}
    coverage_dash = {
        "overall_coverage": dc.get("nifty_100") or coverage.get("coverage_pct") or exec_status["coverage"],
        "nifty_50": dc.get("nifty_50"),
        "nifty_next_50": None,
        "nifty_100": dc.get("nifty_100"),
        "nifty_500": dc.get("nifty_500"),
        "target_20": dc.get("target_20"),
        "us_coverage": None,
        "sector_coverage": (institutional.get("sector_intelligence") or {}).get("sector_coverage_pct")
        or coverage.get("sector_coverage"),
        "company_coverage": exec_status["companies_covered"],
        "research_coverage": coverage.get("research_coverage"),
        "academy_coverage": coverage.get("academy_coverage"),
        "financial_coverage": coverage.get("financial_coverage") or (cms.get("coverage") or {}).get("financial_channel_pct"),
        "valuation_coverage": coverage.get("valuation_coverage"),
        "prediction_coverage": None,
        "historical_depth": institutional.get("historical_depth"),
        "macro_intelligence": institutional.get("macro_intelligence"),
        "decision_quality": institutional.get("decision_quality"),
        "roadmap_next": institutional.get("roadmap_next"),
        "below_threshold": coverage.get("below_threshold") or cms_reviews[:10],
        "sources": [
            "investment_office",
            "company_monitor",
            "knowledge_factory.coverage",
            "historical_depth",
            "sector_intelligence",
            "macro_intelligence",
            "decision_quality",
            "evidence_retrieval",
        ],
        "institutional_intelligence": institutional,
        "evidence_retrieval": institutional.get("evidence_retrieval"),
    }

    # SECTION 7 — Company Monitor
    company_monitor = {
        "companies_monitored": (cms.get("metrics") or {}).get("companies_monitored") or 0,
        "critical_alerts": len([a for a in cms_alerts if a.get("significance") == "Critical"]),
        "high_alerts": len([a for a in cms_alerts if a.get("significance") == "High"]),
        "medium_alerts": len([a for a in cms_alerts if a.get("significance") == "Medium"]),
        "low_alerts": len([a for a in cms_alerts if a.get("significance") == "Low"]),
        "companies_needing_review": len(cms_reviews),
        "companies_updated_today": len(cms.get("companies_monitored") or []),
        "latest_company_changes": cms_changes[:20],
        "latest_earnings_processed": [c for c in cms_changes if "revenue" in str(c.get("change_type") or "")][:10],
        "latest_filings_processed": [],
        "sources": ["company_monitor"],
    }

    # SECTION 8 — Research Pipeline
    research_pipeline = {
        **(ioc.get("research_pipeline") or {}),
        "research_drafts": list(ioc.get("publication_queue") or [])[:20],
        "internal_review": [],
        "compliance_review": [],
        "approved": [],
        "publishing_today": (io.get("research_pipeline") or {}).get("publishing_today") or [],
        "published_today": (io.get("research_pipeline") or {}).get("recently_published") or [],
        "failed_publishing": [],
        "research_queue": io.get("todays_research_queue") or [],
        "sources": ["ioc", "rms", "investment_office"],
    }

    # SECTION 9 — Predictions
    pred = io.get("prediction_review") or {}
    prediction_intelligence = {
        "predictions_created": len(pred.get("predictions_due") or []),
        "predictions_due": pred.get("predictions_due") or [],
        "predictions_correct": pred.get("predictions_correct") or [],
        "predictions_incorrect": pred.get("predictions_incorrect") or [],
        "prediction_accuracy": pred.get("prediction_accuracy"),
        "confidence_trend": pred.get("confidence_changes") or [],
        "house_view_reviews": pred.get("house_view_reviews_required") or cms_reviews,
        "sources": ["investment_office", "company_monitor"],
    }

    # SECTION 10 — Data Quality
    data_quality = {
        "research_grade": exec_status["research_grade"],
        "knowledge_grade": exec_status["knowledge_grade"],
        "market_data_grade": _status_norm((ioc.get("data_freshness") or {}).get("market_data")),
        "financial_statement_grade": None,
        "valuation_grade": None,
        "sector_intelligence_grade": "pass" if (sif_h or {}).get("passed") else "soft",
        "academy_grade": "B" if books.get("concept_count") else "C",
        "evidence_quality": None,
        "average_confidence": None,
        "missing_data": coverage_dash.get("below_threshold") or [],
        "dvc": dvc.get("metrics") or dvc,
        "ecp": ecp.get("metrics") or ecp,
        "sources": ["ioc", "dvc", "ecp", "sif", "academy"],
    }

    # SECTION 11 — Company Analysis
    ca_reports = ca.get("latest_reports") or []
    company_analysis = {
        "companies_analysed": (ca.get("metrics") or {}).get("reports") or len(ca_reports),
        "financial_intelligence_complete": None,
        "business_quality_complete": sum(1 for r in ca_reports if r.get("business_quality_score") is not None),
        "valuation_complete": None,
        "sector_intelligence_complete": None,
        "bull_base_bear_generated": None,
        "recommendation_readiness": [r.get("gate") for r in ca_reports][:12],
        "companies_missing_analysis": [],
        "latest_reports": ca_reports[:12],
        "sources": ["company_analysis"],
    }

    # SECTION 12 — Academy
    academy = {
        "books": books.get("books_successfully_ingested") or len(books.get("books") or []),
        "courses": None,
        "concepts": books.get("concept_count"),
        "frameworks": books.get("framework_count"),
        "formulas": books.get("formula_count"),
        "knowledge_objects": (books.get("concept_count") or 0)
        + (books.get("framework_count") or 0)
        + (books.get("formula_count") or 0),
        "graph_nodes": books.get("concept_count"),
        "graph_relationships": books.get("graph_edges"),
        "recently_learned": [
            b.get("title")
            for b in (books.get("books") or [])
            if (b or {}).get("source_format") != "seed"
        ][:12],
        "most_used_concepts": books.get("most_used_concepts") or [],
        "most_referenced_frameworks": [],
        "sources": ["academy.books"],
    }

    # SECTION 13 — CID
    cid = {
        "company_dossiers": "soft",
        "updated_today": None,
        "coverage": "see CID admin",
        "average_confidence": None,
        "documents": None,
        "timelines": None,
        "financial_histories": None,
        "valuation_histories": None,
        "knowledge_links": None,
        "companies_missing_cid": [],
        "enabled": bool(cid_h),
        "sources": ["cid"],
    }

    # SECTION 14 — System Health
    system_health = {
        "frontend": "soft",
        "backend": "soft",
        "fastapi": overall_ioc,
        "database": "soft",
        "authentication": "soft",
        "email": "soft",
        "scheduler": "soft",
        "storage": "soft",
        "background_jobs": "soft",
        "queue": (ioc.get("pipeline_status") or {}),
        "cache": "soft",
        "memory": None,
        "cpu": None,
        "disk": None,
        "network": None,
        "ioc": ioc,
        "components": ioc.get("components") or [],
        "sources": ["ioc"],
        "note": "Deep infra metrics soft — IOC is system-of-record for ops probes",
    }

    # SECTION 15 — Live Event Stream
    events = []
    for c in cms_changes[:15]:
        events.append(
            {
                "at": c.get("detected_at") or _now(),
                "type": "company_change",
                "message": f"{c.get('ticker')}: {c.get('detail') or c.get('change_type')}",
                "significance": c.get("significance"),
                "ref": c,
            }
        )
    if books.get("concept_count"):
        events.append(
            {
                "at": _now(),
                "type": "academy",
                "message": f"Academy knowledge objects: {books.get('concept_count')} concepts / {books.get('framework_count')} frameworks",
            }
        )
    for r in cms_reviews[:5]:
        events.append(
            {
                "at": r.get("suggested_at") or _now(),
                "type": "house_view_review",
                "message": f"{r.get('ticker')}: House View review suggested",
                "ref": r,
            }
        )
    for fail in (ioc.get("latest_failures") or [])[:8]:
        if isinstance(fail, dict):
            events.append(
                {
                    "at": fail.get("checked_at") or _now(),
                    "type": "ioc_failure",
                    "message": f"{fail.get('component')}: {fail.get('status')}",
                    "ref": fail,
                }
            )
    events.sort(key=lambda e: str(e.get("at") or ""), reverse=True)

    # SECTION 16 — Executive Copilot
    unhealthy_apis = [p for p in providers if p.get("status") in {"Critical", "Offline", "Warning"}]
    attention = io.get("companies_requiring_attention") or []
    answers = {
        COPILOT_PROMPTS[0]: f"{len(ioc.get('latest_failures') or [])} IOC failure/warning components; CMS critical={company_monitor['critical_alerts']}.",
        COPILOT_PROMPTS[1]: f"{len(unhealthy_apis)} providers not Healthy (incl. soft unknowns).",
        COPILOT_PROMPTS[2]: f"{len(attention)} companies on IO attention list; {company_monitor['companies_needing_review']} HV reviews.",
        COPILOT_PROMPTS[3]: f"Books learned={knowledge_growth['books_learned']}; concepts={knowledge_growth['concepts_added']}; HV reviews={knowledge_growth['house_view_reviews']}.",
        COPILOT_PROMPTS[4]: "See Platform Status error_count / IOC latest_failures for highest-error surfaces.",
        COPILOT_PROMPTS[5]: f"Research queue length={len(research_pipeline.get('research_queue') or [])}.",
        COPILOT_PROMPTS[6]: "Research Grade is aggregated from IO coverage — investigate RMS queues and published counts.",
        COPILOT_PROMPTS[7]: "Inspect provider latency / circuit_state in API Status (IOC provider probes).",
        COPILOT_PROMPTS[8]: f"AGI status={exec_status['agi_status']}; coverage={exec_status['coverage']}%; monitored={exec_status['companies_monitored']}; events={len(events)}.",
    }
    copilot = {"prompts": list(COPILOT_PROMPTS), "answers": answers, "read_only": True}

    # SECTION 17 — Architecture Map
    node_status = {
        "Providers": _status_norm(overall_ioc),
        "MarketDataClient": _status_norm((ioc.get("platform_status") or {}).get("market_data")),
        "DVC": _platform_card("DVC", status="Healthy" if dvc else "Unknown")["current_status"],
        "ECP": _platform_card("ECP", status="Healthy" if ecp else "Unknown")["current_status"],
        "LEO": _status_norm(leo_h.get("status") or "soft"),
        "CID": "Healthy" if cid_h else "Warning",
        "Knowledge Foundation": _status_norm((ioc.get("platform_status") or {}).get("kip")),
        "Evidence Retrieval": (
            "Healthy"
            if (institutional.get("evidence_retrieval") or {}).get("status") == "ok"
            else "Warning"
            if institutional.get("evidence_retrieval")
            else "Unknown"
        ),
        "Academy": "Healthy" if books.get("enabled", True) else "Offline",
        "Financial Intelligence": "soft",
        "Company Analysis": "Healthy" if ca.get("enabled", True) else "Offline",
        "Company Monitor": "Healthy" if cms.get("enabled", True) else "Offline",
        "Investment Office": "Healthy" if io.get("enabled", True) else "Offline",
        "IRP": "soft",
        "Ask AGI": "soft",
    }
    def _node_id(label: str) -> str:
        return label.lower().replace(" ", "_").replace("/", "_")

    architecture_map = {
        "nodes": [
            {
                "id": _node_id(n),
                "label": n,
                "status": node_status.get(n, "Unknown"),
                "colour": "Green"
                if node_status.get(n) == "Healthy"
                else "Yellow"
                if node_status.get(n) in {"Warning", "Unknown", "soft", "Soft"}
                else "Red",
                "health": node_status.get(n, "Unknown"),
                "dependencies": [],
                "performance": None,
                "coverage": None,
                "logs": [],
            }
            for n in ARCHITECTURE_NODES
        ],
        "edges": [
            {
                "from": _node_id(ARCHITECTURE_NODES[i]),
                "to": _node_id(ARCHITECTURE_NODES[i + 1]),
            }
            for i in range(len(ARCHITECTURE_NODES) - 1)
        ],
        "read_only": True,
    }

    # SECTION 18 — Alerts Centre
    ack = mc_store.acknowledged_ids()
    alerts = []
    for a in cms_alerts:
        aid = f"cms:{a.get('ticker')}:{a.get('change_type')}:{a.get('detected_at')}"
        alerts.append(
            {
                "id": aid,
                "category": "Critical Alerts" if a.get("significance") == "Critical" else "System Alerts",
                "message": a.get("detail") or a.get("change_type"),
                "ticker": a.get("ticker"),
                "significance": a.get("significance"),
                "acknowledged": aid in ack,
            }
        )
    for r in cms_reviews:
        aid = f"hvr:{r.get('ticker')}:{r.get('suggested_at')}"
        alerts.append(
            {
                "id": aid,
                "category": "Prediction Alerts",
                "message": r.get("action") or "House View review",
                "ticker": r.get("ticker"),
                "acknowledged": aid in ack,
            }
        )
    for fail in (ioc.get("alerts") or [])[:20]:
        if isinstance(fail, dict):
            aid = f"ioc:{fail.get('id') or fail.get('component') or fail.get('message')}"
            alerts.append(
                {
                    "id": aid,
                    "category": "API Alerts",
                    "message": fail.get("message") or fail.get("title") or str(fail)[:160],
                    "acknowledged": aid in ack,
                }
            )

    # SECTION 19 — Deployment Centre
    deployment = {
        "current_version": MISSION_CONTROL_VERSION,
        "git_commit": None,
        "current_branch": None,
        "last_deployment": None,
        "deployment_duration": None,
        "rollback_available": None,
        "environment": "development",
        "note": "Populate from deploy metadata when available — read-only",
        "sources": ["mission_control"],
    }
    try:
        import subprocess

        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True, timeout=2).strip()
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True, timeout=2).strip()
        deployment["current_branch"] = branch
        deployment["git_commit"] = commit
    except Exception:
        pass

    # SECTION 20 — Performance Analytics (soft placeholders + whatever IOC has)
    performance = {
        "average_api_response": None,
        "average_ask_agi_response": None,
        "average_research_generation_time": None,
        "average_company_analysis_time": None,
        "average_cid_refresh_time": None,
        "average_learning_time": None,
        "daily_questions": None,
        "daily_learning": knowledge_growth.get("concepts_added"),
        "daily_research": len(research_pipeline.get("published_today") or []),
        "charts": {"hours_24": [], "days_7": [], "days_30": []},
        "sources": ["ioc", "soft"],
        "note": "Detailed perf series reserved — no fabricated charts",
    }

    desk = {
        "enabled": True,
        "programme": PROGRAMME,
        "layer": PROGRAMME_SHORT,
        "version": MISSION_CONTROL_VERSION,
        "architecture_status": "v1.0.1 LOCKED",
        "read_only": True,
        "never_modifies_research": True,
        "never_changes_house_views": True,
        "never_changes_recommendations": True,
        "not_an_engine": True,
        "not_client_facing": True,
        "flags": flags_dict(),
        "generated_at": _now(),
        "platforms_catalog": list(PLATFORMS),
        "executive_status": exec_status,
        "platform_status": platforms,
        "engine_status": engines,
        "api_status": providers,
        "knowledge_growth": knowledge_growth,
        "coverage_dashboard": coverage_dash,
        "company_monitor": company_monitor,
        "research_pipeline": research_pipeline,
        "prediction_intelligence": prediction_intelligence,
        "data_quality": data_quality,
        "company_analysis": company_analysis,
        "academy": academy,
        "cid": cid,
        "system_health": system_health,
        "live_event_stream": events[:40],
        "executive_copilot": copilot,
        "architecture_map": architecture_map,
        "alerts_centre": alerts[:60],
        "deployment_centre": deployment,
        "performance_analytics": performance,
        "answer_policy": "mission_control_read_only_diagnostics",
    }
    return desk
