"""Complete Ask Pipeline runner — soft-wire integration only."""

from __future__ import annotations

import time
from typing import Any

from ask_pipeline.context import build_ask_context
from ask_pipeline.dag import execute_research_dag
from ask_pipeline.entities import resolve_ask_entities
from ask_pipeline.evidence import assemble_evidence
from ask_pipeline.gates import evaluate_gates
from ask_pipeline.intent import detect_intent
from ask_pipeline.answer_assembly import (
    AAE_VERSION,
    assemble_answer_plan,
    bind_reasoning_to_answer,
)
from ask_pipeline.intent_resolution import resolve_intent
from framework_selection import IFSE_VERSION, select_frameworks
from framework_selection import store as ifse_store
from institutional_playbooks import IAP_VERSION, select_playbook
from institutional_playbooks import store as iap_store
from institutional_evidence_graph import IEG_VERSION, build_evidence_graph
from institutional_evidence_graph import store as ieg_store
from institutional_analog_intelligence import IMAI_VERSION
from institutional_analog_intelligence.production import retrieve as retrieve_institutional_memory
from institutional_communication import ICE_VERSION, communicate_from_ask
from ask_pipeline.knowledge import retrieve_knowledge
from ask_pipeline.planner import run_planner
from ask_pipeline.policy import execution_policy
from ask_pipeline.recording import record_decision_quality, register_outcome
from ask_pipeline.schema import FREEZE_LOCKS, PIPELINE_VERSION, PROGRAMME
from ask_pipeline import store
from ask_pipeline.telemetry import build_telemetry
from observability.tracing import span as trace_span
from observability.tracing import traced as trace_run


@trace_run("agi.ask_pipeline", run_type="chain", tags=["agi", "ask_pipeline"])
def run_complete_ask(
    question: str,
    *,
    ticker_hint: str | None = None,
    session_id: str | None = None,
    conversation_id: str | None = None,
    entity_resolution_pack: dict[str, Any] | None = None,
    extra_packs: dict[str, Any] | None = None,
    academy: dict[str, Any] | None = None,
    requested_depth: str | None = None,
    requested_horizon: str | None = None,
    requested_asset: str | None = None,
    requested_portfolio: str | None = None,
    jurisdiction: str | None = None,
) -> dict[str, Any]:
    """Traverse the full institutional Ask pipeline for one question."""
    t0 = time.time()
    stages: dict[str, Any] = {}

    # S01 Context
    context = build_ask_context(
        question,
        session_id=session_id,
        conversation_id=conversation_id,
        ticker_hint=ticker_hint,
        requested_depth=requested_depth,
        requested_horizon=requested_horizon,
        requested_asset=requested_asset,
        requested_portfolio=requested_portfolio,
        jurisdiction=jurisdiction,
    )
    stages["context"] = {"status": "executed", "pipeline_id": context["pipeline_id"]}

    # ------------------------------------------------------------------
    # AGIB v3.4 Track A — Intent Resolution Layer (BEFORE IERE)
    # Language → Intent → Entities → Temporal → Question Type → Requirements
    # ------------------------------------------------------------------
    with trace_span(
        "intent_resolution",
        inputs={"question": question, "ticker_hint": ticker_hint},
        tags=["ask", "intent"],
    ) as _sp:
        irl = resolve_intent(question, ticker_hint=ticker_hint or context.get("ticker_hint"))
        _sp.end(
            outputs={
                "intent": irl.get("intent"),
                "confidence": irl.get("intent_confidence"),
                "question_type": irl.get("question_type"),
                "as_of": irl.get("as_of"),
                "concept_mode": irl.get("concept_mode"),
                "secondary_intent": irl.get("secondary_intent"),
                "rejected_intents": irl.get("rejected_intents"),
            }
        )
    stages["intent_resolution"] = {"status": "executed", **irl}
    context["intent_resolution"] = {
        "intent": irl.get("intent"),
        "question_type": irl.get("question_type"),
        "concept_mode": irl.get("concept_mode"),
        "as_of": irl.get("as_of"),
        "legacy_intent": irl.get("legacy_intent"),
    }
    context["as_of"] = irl.get("as_of")
    context["concept_mode"] = bool(irl.get("concept_mode"))

    # S02 Intent — prefer IRL; keep legacy detector as soft telemetry only
    legacy_intent = detect_intent(question)
    intent_rec = {
        "intent": irl.get("legacy_intent") or legacy_intent.get("intent") or "Unknown",
        "intent_v2": irl.get("intent"),
        "confidence": irl.get("intent_confidence"),
        "reasons": irl.get("intent_reasons") or [],
        "question_type_hint": irl.get("question_type"),
        "investment_recommendation": bool(irl.get("investment_recommendation")),
        "legacy_detector": legacy_intent,
        "source": "intent_resolution_layer",
    }
    context["intent"] = intent_rec["intent"]
    context["intent_v2"] = irl.get("intent")
    stages["intent"] = {"status": "executed", **intent_rec}

    # S03 Entities — Concept Mode clears pollution; else soft-merge IRL + legacy
    if irl.get("concept_mode"):
        entities_rec = {
            "primary": None,
            "entities": [],
            "soft_tags": irl.get("soft_tags") or [],
            "concept_mode": True,
            "count": 0,
            "entity_pollution_blocked": irl.get("entity_pollution_blocked"),
            "ignored_ticker_hint": irl.get("ignored_ticker_hint"),
            "source": "intent_resolution_layer",
        }
    else:
        entities_rec = resolve_ask_entities(
            question,
            ticker_hint=ticker_hint or context.get("ticker_hint"),
            entity_resolution_pack=entity_resolution_pack,
        )
        # Prefer IRL primary when present
        if irl.get("primary"):
            entities_rec["primary"] = irl["primary"]
            # Ensure IRL entities are present
            for e in irl.get("entities") or []:
                if not any(x.get("id") == e.get("id") for x in (entities_rec.get("entities") or [])):
                    entities_rec.setdefault("entities", []).append(e)
        entities_rec["concept_mode"] = False
        entities_rec["source"] = "intent_resolution_layer+legacy"
    context["entities"] = entities_rec.get("entities") or []
    stages["entities"] = {"status": "executed", **entities_rec}

    # S04 Query classification — IRL OVERRIDES classify_question (Track A exit gate)
    question_type = irl.get("question_type") or "education"
    legacy_cls: dict[str, Any] = {}
    try:
        from institutional_reasoning.evidence_contracts import classify_question

        legacy_cls = classify_question(question)
    except Exception as exc:
        legacy_cls = {"error": str(exc)[:120]}
    stages["query_classification"] = {
        "status": "executed",
        "question_type": question_type,
        "source": "intent_resolution_layer",
        "overrides_classify_question": True,
        "legacy_classify_question": legacy_cls,
        "intent_v2": irl.get("intent"),
    }

    primary = entities_rec.get("primary") or {}
    has_entity = bool(primary.get("entity_id")) and not irl.get("concept_mode")
    policy = execution_policy(
        intent=str(irl.get("intent") or intent_rec["intent"]),
        investment_recommendation=bool(intent_rec.get("investment_recommendation")),
        has_entity=has_entity,
        question_type=question_type,
        concept_mode=bool(irl.get("concept_mode")),
        as_of=irl.get("as_of"),
    )
    stages["policy"] = {"status": "executed", **policy}

    # S05 Knowledge (+ IERE) — inherits as_of + concept_mode
    with trace_span(
        "knowledge_retrieval",
        run_type="retriever",
        inputs={"intent": intent_rec["intent"], "as_of": irl.get("as_of")},
        tags=["ask", "knowledge"],
    ) as _sp:
        knowledge = retrieve_knowledge(
            intent=intent_rec["intent"],
            entities=context["entities"],
            soft_tags=entities_rec.get("soft_tags"),
            question=question,
            as_of=irl.get("as_of"),
            concept_mode=bool(irl.get("concept_mode")),
        )
        _sp.end(
            outputs={
                "ranked_evidence": len(((knowledge.get("iere") or {}).get("ranked_evidence") or [])),
                "as_of": knowledge.get("as_of"),
            }
        )
    stages["knowledge"] = knowledge

    # S06 Evidence — prefers IERE Evidence Packs when available; reasoning unchanged
    with trace_span(
        "evidence_assembly",
        run_type="retriever",
        inputs={"intent": intent_rec["intent"]},
        tags=["ask", "evidence"],
    ) as _sp:
        evidence = assemble_evidence(
            knowledge,
            intent=intent_rec["intent"],
            entities=context["entities"],
        )
        _sp.end(outputs={"packs": sorted((evidence.get("governance_packs") or {}).keys())})
    stages["evidence"] = evidence

    # ------------------------------------------------------------------
    # AGIB v3.4 Track B — Answer Assembly (AFTER evidence, BEFORE reasoning)
    # Classify → Order → Gaps → Skeleton → Confidence → Citations
    # Deterministic plan only — no LLM synthesis.
    # ------------------------------------------------------------------
    answer_assembly = assemble_answer_plan(
        question=question,
        intent_v2=str(irl.get("intent") or intent_rec.get("intent_v2") or "Unknown"),
        evidence=evidence,
        knowledge=knowledge,
        intent_resolution=irl,
    )
    stages["answer_assembly"] = {
        "status": "executed",
        "aae_version": answer_assembly.get("aae_version") or AAE_VERSION,
        "intent_v2": answer_assembly.get("intent_v2"),
        "item_count": (answer_assembly.get("metrics") or {}).get("item_count"),
        "gap_count": (answer_assembly.get("metrics") or {}).get("gap_count"),
        "confidence_band": (answer_assembly.get("confidence") or {}).get("band"),
        "coverage": (answer_assembly.get("gaps") or {}).get("coverage"),
        "section_order": (answer_assembly.get("skeleton") or {}).get("section_order"),
        "tell_reasoning": (answer_assembly.get("gaps") or {}).get("tell_reasoning"),
        "llm_used": False,
        "fabricated": False,
    }
    context["answer_plan"] = answer_assembly.get("answer_plan")

    # ------------------------------------------------------------------
    # AGIB v3.4 Track C — Framework Selection (AFTER assembly, BEFORE reasoning)
    # Deterministic multi-framework composition. Reasoning unchanged.
    # ------------------------------------------------------------------
    evidence_types_present: list[str] = []
    for item in ((knowledge.get("iere") or {}).get("ranked_evidence") or []):
        if isinstance(item, dict) and item.get("evidence_type"):
            evidence_types_present.append(str(item["evidence_type"]))
    with trace_span(
        "framework_selection",
        inputs={
            "intent_v2": str(irl.get("intent") or intent_rec.get("intent_v2") or "Unknown"),
            "question_type": question_type,
        },
        tags=["ask", "framework"],
    ) as _sp:
        framework_selection = select_frameworks(
            question=question,
            intent_v2=str(irl.get("intent") or intent_rec.get("intent_v2") or "Unknown"),
            question_type=question_type,
            entities=list(entities_rec.get("entities") or []),
            ticker_hint=None if irl.get("concept_mode") else ticker_hint,
            concept_mode=bool(irl.get("concept_mode")),
            as_of=irl.get("as_of"),
            answer_assembly=answer_assembly,
            evidence_types_present=evidence_types_present,
        )
        _sp.end(
            outputs={
                "framework_ids": framework_selection.get("framework_ids"),
                "sector": framework_selection.get("sector"),
                "confidence": (framework_selection.get("confidence") or {}).get("band"),
            }
        )
    ifse_store.record_selection(framework_selection)
    stages["framework_selection"] = {
        "status": "executed",
        "ifse_version": framework_selection.get("ifse_version") or IFSE_VERSION,
        "sector": framework_selection.get("sector"),
        "framework_ids": framework_selection.get("framework_ids"),
        "multi_framework": framework_selection.get("multi_framework"),
        "confidence_band": (framework_selection.get("confidence") or {}).get("band"),
        "confidence_pct": (framework_selection.get("confidence") or {}).get("pct"),
        "validation_passed": (framework_selection.get("validation") or {}).get("passed"),
        "forbidden_rejected": framework_selection.get("forbidden_rejected"),
        "llm_used": False,
        "fabricated": False,
    }
    context["framework_selection"] = {
        "framework_ids": framework_selection.get("framework_ids"),
        "sector": framework_selection.get("sector"),
        "confidence_pct": (framework_selection.get("confidence") or {}).get("pct"),
    }

    # ------------------------------------------------------------------
    # AGIB v3.5 — Institutional Analytical Playbooks (IAP)
    # AFTER framework selection, BEFORE reasoning. Guides reasoning; does not replace it.
    # ------------------------------------------------------------------
    with trace_span(
        "playbook_selection",
        inputs={"sector": framework_selection.get("sector")},
        tags=["ask", "playbook"],
    ) as _sp:
        playbook_selection = select_playbook(
            question=question,
            intent_v2=str(irl.get("intent") or intent_rec.get("intent_v2") or "Unknown"),
            question_type=question_type,
            entities=list(entities_rec.get("entities") or []),
            sector=framework_selection.get("sector"),
            framework_ids=list(framework_selection.get("framework_ids") or []),
            framework_selection=framework_selection,
            concept_mode=bool(irl.get("concept_mode")),
            as_of=irl.get("as_of"),
            answer_assembly=answer_assembly,
        )
        _sp.end(
            outputs={
                "playbook_id": playbook_selection.get("playbook_id"),
                "category": playbook_selection.get("category"),
            }
        )
    iap_store.record_selection(playbook_selection)
    stages["playbook_selection"] = {
        "status": "executed",
        "iap_version": playbook_selection.get("iap_version") or IAP_VERSION,
        "playbook_id": playbook_selection.get("playbook_id"),
        "category": playbook_selection.get("category"),
        "checklist_steps": ((playbook_selection.get("checklist") or {}).get("n_steps")),
        "procedure_steps": ((playbook_selection.get("procedure") or {}).get("n_steps")),
        "confidence_band": (playbook_selection.get("confidence") or {}).get("band"),
        "confidence_pct": (playbook_selection.get("confidence") or {}).get("pct"),
        "validation_passed": (playbook_selection.get("validation") or {}).get("passed"),
        "guides_reasoning": True,
        "reasoning_changed": False,
        "llm_used": False,
        "fabricated": False,
    }
    context["playbook_selection"] = {
        "playbook_id": playbook_selection.get("playbook_id"),
        "category": playbook_selection.get("category"),
        "confidence_pct": (playbook_selection.get("confidence") or {}).get("pct"),
    }

    # ------------------------------------------------------------------
    # AGIB v3.6 Phase 2 Sprint 2.1 — Institutional Evidence Graph (IEG)
    # AFTER playbook, BEFORE reasoning. Relationships over isolated facts.
    # ------------------------------------------------------------------
    hint = None if irl.get("concept_mode") else (
        (primary.get("entity_id") if primary else None)
        or (ticker_hint if not irl.get("entity_pollution_blocked") else None)
    )
    with trace_span(
        "evidence_graph",
        run_type="retriever",
        inputs={"ticker_hint": hint, "as_of": irl.get("as_of")},
        tags=["ask", "evidence_graph"],
    ) as _sp:
        evidence_graph = build_evidence_graph(
            question=question,
            entities=list(entities_rec.get("entities") or []),
            ticker_hint=hint,
            concept_mode=bool(irl.get("concept_mode")),
            as_of=irl.get("as_of"),
            evidence=evidence,
            knowledge=knowledge,
            playbook_selection=playbook_selection,
            framework_selection=framework_selection,
            intent_v2=str(irl.get("intent") or intent_rec.get("intent_v2") or "Unknown"),
        )
        _sp.end(
            outputs={
                "n_nodes": evidence_graph.get("n_nodes"),
                "n_edges": evidence_graph.get("n_edges"),
                "domain_coverage_pct": evidence_graph.get("domain_coverage_pct"),
            }
        )
    ieg_store.record(evidence_graph)

    # ------------------------------------------------------------------
    # AGI v3.5 Phase 3 Sprint 3.5 — Temporal Integrity Replay Guard (pre-analog)
    # AFTER Evidence Graph, BEFORE IMAI / reasoning. Soft-wire only.
    # ------------------------------------------------------------------
    from temporal_integrity.production import guard as tirc_guard

    with trace_span(
        "temporal_integrity.replay_guard.pre_analog",
        inputs={"as_of": irl.get("as_of")},
        tags=["ask", "tirc", "replay_guard"],
    ) as _sp:
        _tirc_pre = tirc_guard(
            as_of=irl.get("as_of"),
            evidence_graph=evidence_graph,
            stage="pre_analog",
        )
        _sp.end(outputs=_tirc_pre.get("report"))
    evidence_graph = _tirc_pre.get("evidence_graph") or evidence_graph

    stages["evidence_graph"] = {
        "status": "executed",
        "ieg_version": evidence_graph.get("ieg_version") or IEG_VERSION,
        "graph_id": evidence_graph.get("graph_id"),
        "entities": evidence_graph.get("entities"),
        "n_nodes": evidence_graph.get("n_nodes"),
        "n_edges": evidence_graph.get("n_edges"),
        "n_chains": len(evidence_graph.get("chains") or []),
        "domain_coverage_pct": evidence_graph.get("domain_coverage_pct"),
        "validation_passed": (evidence_graph.get("validation") or {}).get("passed"),
        "as_of": evidence_graph.get("as_of"),
        "guides_evidence": True,
        "reasoning_changed": False,
        "llm_used": False,
        "fabricated": False,
        "temporal_integrity": (_tirc_pre.get("report") or {}),
    }
    context["evidence_graph"] = {
        "graph_id": evidence_graph.get("graph_id"),
        "domain_coverage_pct": evidence_graph.get("domain_coverage_pct"),
        "n_nodes": evidence_graph.get("n_nodes"),
    }

    # ------------------------------------------------------------------
    # AGIB v3.6 Phase 2 Sprint 2.2 — Institutional Memory & Analog Intelligence
    # AFTER Evidence Graph, BEFORE reasoning. "Have we seen this before?"
    # Soft-wire only — never fabricates analogues; never replaces reasoning.
    # ------------------------------------------------------------------
    with trace_span(
        "institutional_analog_intelligence",
        run_type="retriever",
        inputs={"as_of": irl.get("as_of"), "top_k": 5},
        tags=["ask", "imai"],
    ) as _sp:
        institutional_memory = retrieve_institutional_memory(
            question=question,
            evidence_graph=evidence_graph,
            playbook=playbook_selection,
            as_of=irl.get("as_of"),
            top_k=5,
        )
        _sp.end(
            outputs={
                "have_we_seen_this_before": institutional_memory.get("have_we_seen_this_before"),
                "top_memory_ids": institutional_memory.get("top_memory_ids"),
                "regimes": institutional_memory.get("regimes"),
            }
        )

    # TIRC Replay Guard — post-analog surface / period integrity
    with trace_span(
        "temporal_integrity.replay_guard.post_analog",
        inputs={"as_of": irl.get("as_of")},
        tags=["ask", "tirc", "replay_guard"],
    ) as _sp:
        _tirc_post = tirc_guard(
            as_of=irl.get("as_of"),
            institutional_memory=institutional_memory,
            stage="post_analog",
        )
        _sp.end(outputs=_tirc_post.get("report"))
    institutional_memory = _tirc_post.get("institutional_memory") or institutional_memory
    stages["temporal_integrity"] = {
        "status": "executed",
        "tirc_version": (_tirc_post.get("tirc_version") or _tirc_pre.get("tirc_version")),
        "pre_analog": _tirc_pre.get("report"),
        "post_analog": _tirc_post.get("report"),
        "reasoning_changed": False,
        "knowledge_factory_changed": False,
        "fabricated": False,
    }

    stages["institutional_memory"] = {
        "status": "executed",
        "imai_version": institutional_memory.get("imai_version") or IMAI_VERSION,
        "have_we_seen_this_before": institutional_memory.get("have_we_seen_this_before"),
        "top_memory_ids": institutional_memory.get("top_memory_ids"),
        "scored_count": institutional_memory.get("scored_count"),
        "regimes": institutional_memory.get("regimes"),
        "quality_status": (institutional_memory.get("quality") or {}).get("status"),
        "as_of": institutional_memory.get("as_of"),
        "guides_memory": True,
        "reasoning_changed": False,
        "llm_used": False,
        "fabricated": False,
        "invented_analogues": False,
        "temporal_integrity": (_tirc_post.get("report") or {}),
    }
    context["institutional_memory"] = {
        "top_memory_ids": institutional_memory.get("top_memory_ids"),
        "have_we_seen_this_before": institutional_memory.get("have_we_seen_this_before"),
        "imai_version": institutional_memory.get("imai_version") or IMAI_VERSION,
    }

    # S07 Planner — no ticker in Concept Mode
    planner = run_planner(question, ticker_hint=hint, policy=policy)
    stages["planner"] = planner

    # S08 DAG (observability + dependency enforcement record)
    dag = execute_research_dag(
        policy=policy,
        planner=planner,
        knowledge=knowledge,
        evidence=evidence,
    )
    stages["dag"] = dag

    # Merge packs for reasoning
    packs = dict(extra_packs or {})
    for k, v in (evidence.get("governance_packs") or {}).items():
        if k not in packs or not packs.get(k):
            packs[k] = v
        else:
            # Prefer KF provenance markers alongside existing soft packs
            if isinstance(packs[k], dict) and isinstance(v, dict):
                packs[k] = {**packs[k], "knowledge_factory_overlay": v}
    # Soft overlay — reasoning may ignore; does not change governance internals
    packs["framework_selection"] = {
        "ifse_version": framework_selection.get("ifse_version"),
        "framework_ids": framework_selection.get("framework_ids"),
        "selected": framework_selection.get("selected"),
        "explanation": framework_selection.get("explanation"),
        "confidence": framework_selection.get("confidence"),
        "sector": framework_selection.get("sector"),
        "validation": framework_selection.get("validation"),
        "fabricated": False,
        "reasoning_changed": False,
    }
    # Soft overlay — checklist/procedure guide reasoning; governance may ignore
    packs["playbook_selection"] = {
        "iap_version": playbook_selection.get("iap_version"),
        "playbook_id": playbook_selection.get("playbook_id"),
        "playbook_name": playbook_selection.get("playbook_name"),
        "category": playbook_selection.get("category"),
        "checklist": playbook_selection.get("checklist"),
        "procedure": playbook_selection.get("procedure"),
        "common_mistakes": playbook_selection.get("common_mistakes"),
        "output_structure": playbook_selection.get("output_structure"),
        "evidence_required": playbook_selection.get("evidence_required"),
        "explanation": playbook_selection.get("explanation"),
        "confidence": playbook_selection.get("confidence"),
        "guides_reasoning": True,
        "reasoning_changed": False,
        "fabricated": False,
    }
    packs["evidence_graph"] = {
        "ieg_version": evidence_graph.get("ieg_version"),
        "graph_id": evidence_graph.get("graph_id"),
        "entities": evidence_graph.get("entities"),
        "n_nodes": evidence_graph.get("n_nodes"),
        "n_edges": evidence_graph.get("n_edges"),
        "chains": evidence_graph.get("chains"),
        "chain_bullets": evidence_graph.get("chain_bullets"),
        "surface_bullets": evidence_graph.get("surface_bullets"),
        "entity_trees": {
            k: {
                "coverage": v.get("coverage"),
                "filled_domains": (v.get("coverage") or {}).get("filled_domains"),
            }
            for k, v in (evidence_graph.get("entity_trees") or {}).items()
        },
        "domain_coverage_pct": evidence_graph.get("domain_coverage_pct"),
        "as_of": evidence_graph.get("as_of"),
        "missing_evidence_required": evidence_graph.get("missing_evidence_required"),
        "guides_evidence": True,
        "reasoning_changed": False,
        "fabricated": False,
    }
    packs["institutional_memory"] = {
        "imai_version": institutional_memory.get("imai_version") or IMAI_VERSION,
        "have_we_seen_this_before": institutional_memory.get("have_we_seen_this_before"),
        "top_memory_ids": institutional_memory.get("top_memory_ids"),
        "memories": institutional_memory.get("memories"),
        "surface_bullets": institutional_memory.get("surface_bullets"),
        "comparison": institutional_memory.get("comparison"),
        "regimes": institutional_memory.get("regimes"),
        "as_of": institutional_memory.get("as_of"),
        "quality": institutional_memory.get("quality"),
        "guides_memory": True,
        "reasoning_changed": False,
        "invented_analogues": False,
        "fabricated": False,
    }

    # S09 Reasoning (+ S10 portfolio via flags)
    governance: dict[str, Any] = {}
    try:
        from institutional_reasoning.execution_governance import govern_answer

        with trace_span(
            "reasoning.governance",
            inputs={
                "question_type": question_type,
                "packs": sorted(packs.keys()),
                "build_institutional_evidence": bool(policy.get("build_institutional_evidence")),
            },
            tags=["ask", "reasoning"],
        ) as _sp:
            governance = govern_answer(
                question,
                ticker_hint=hint,
                entity_resolution_pack=None if irl.get("concept_mode") else entity_resolution_pack,
                packs=packs,
                academy=academy,
                build_institutional_evidence=bool(policy.get("build_institutional_evidence")),
                build_portfolio_intelligence=bool(policy.get("build_portfolio_intelligence")),
                build_outcome_intelligence=bool(policy.get("build_outcome_intelligence")),
                question_type_override=question_type,
            )
            _sp.end(
                outputs={
                    "path": governance.get("path"),
                    "question_type": governance.get("question_type"),
                    "narrative_allowed": governance.get("narrative_allowed"),
                    "frameworks": len(governance.get("frameworks") or []),
                    "execution_ms": governance.get("execution_ms"),
                }
            )
        stages["governance"] = {
            "status": "executed",
            "run_id": governance.get("run_id"),
            "path": governance.get("path"),
            "question_type": governance.get("question_type"),
            "narrative_allowed": governance.get("narrative_allowed"),
            "validation": governance.get("validation"),
            "frameworks": len(governance.get("frameworks") or []),
            "has_ipi": bool(governance.get("ipi")),
            "execution_ms": governance.get("execution_ms"),
        }
        stages["portfolio"] = {
            "status": "executed" if governance.get("ipi") else (
                "skipped_by_policy" if not policy.get("run_portfolio") else "empty"
            ),
            "has_ipi": bool(governance.get("ipi")),
            "recommendation": governance.get("portfolio_recommendation"),
        }
    except Exception as exc:
        stages["governance"] = {"status": "error", "error": str(exc)[:200]}
        stages["portfolio"] = {
            "status": "skipped_by_policy" if not policy.get("run_portfolio") else "error",
            "error": str(exc)[:120],
        }

    # Track B — bind existing reasoning into the assembly skeleton (no new facts)
    bound = bind_reasoning_to_answer(answer_assembly, governance=governance)
    institutional_answer = bound.get("institutional_answer") or {}
    # Attach Framework Explanation Object (auditable; not shown by default)
    institutional_answer = {
        **institutional_answer,
        "framework_selection": {
            "framework_ids": framework_selection.get("framework_ids"),
            "selected": framework_selection.get("selected"),
            "explanation": framework_selection.get("explanation"),
            "confidence": framework_selection.get("confidence"),
            "ifse_version": framework_selection.get("ifse_version"),
        },
        "playbook_selection": {
            "playbook_id": playbook_selection.get("playbook_id"),
            "playbook_name": playbook_selection.get("playbook_name"),
            "category": playbook_selection.get("category"),
            "checklist": playbook_selection.get("checklist"),
            "procedure": playbook_selection.get("procedure"),
            "common_mistakes": playbook_selection.get("common_mistakes"),
            "output_structure": playbook_selection.get("output_structure"),
            "explanation": playbook_selection.get("explanation"),
            "confidence": playbook_selection.get("confidence"),
            "iap_version": playbook_selection.get("iap_version"),
            "guides_reasoning": True,
        },
        "evidence_graph": {
            "graph_id": evidence_graph.get("graph_id"),
            "entities": evidence_graph.get("entities"),
            "n_nodes": evidence_graph.get("n_nodes"),
            "n_edges": evidence_graph.get("n_edges"),
            "domain_coverage_pct": evidence_graph.get("domain_coverage_pct"),
            "chains": evidence_graph.get("chains"),
            "surface_bullets": evidence_graph.get("surface_bullets"),
            "as_of": evidence_graph.get("as_of"),
            "ieg_version": evidence_graph.get("ieg_version"),
            "guides_evidence": True,
        },
        "institutional_memory": {
            "imai_version": institutional_memory.get("imai_version") or IMAI_VERSION,
            "have_we_seen_this_before": institutional_memory.get("have_we_seen_this_before"),
            "top_memory_ids": institutional_memory.get("top_memory_ids"),
            "memories": institutional_memory.get("memories"),
            "surface_bullets": institutional_memory.get("surface_bullets"),
            "comparison": institutional_memory.get("comparison"),
            "regimes": institutional_memory.get("regimes"),
            "as_of": institutional_memory.get("as_of"),
            "guides_memory": True,
            "invented_analogues": False,
        },
    }
    stages["answer_binding"] = {
        "status": "executed",
        "governance_bound": bool(bound.get("governance_bound")),
        "governance_path": bound.get("governance_path"),
        "confidence_band": (institutional_answer.get("confidence") or {}).get("band"),
        "generic": bool(institutional_answer.get("generic")),
        "llm_used": False,
        "fabricated": False,
    }

    # ------------------------------------------------------------------
    # AGIB v3.4 Track D — Institutional Communication Engine (ICE)
    # Deterministic renderer of InstitutionalAnswer — no new reasoning.
    # ------------------------------------------------------------------
    with trace_span(
        "institutional_communication",
        inputs={"intent": irl.get("intent"), "path": governance.get("path")},
        tags=["ask", "ice"],
    ) as _sp:
        communication = communicate_from_ask(
            question=question,
            intent_resolution=irl,
            answer_assembly=answer_assembly,
            framework_selection=framework_selection,
            playbook_selection=playbook_selection,
            evidence_graph=evidence_graph,
            institutional_memory=institutional_memory,
            institutional_answer=institutional_answer,
            governance=governance,
            evidence=evidence,
            knowledge=knowledge,
            replay_id=context.get("replay_id"),
        )
        _sp.end(
            outputs={
                "template": communication.get("template"),
                "executive_summary": communication.get("executive_summary"),
                "answer_source": communication.get("answer_source"),
            }
        )
    stages["institutional_communication"] = {
        "status": "executed",
        "ice_version": communication.get("ice_version") or ICE_VERSION,
        "template": communication.get("template"),
        "framework_visible": communication.get("framework_visible"),
        "citation_density": communication.get("citation_density"),
        "narrative_style": communication.get("narrative_style"),
        "validation_passed": (communication.get("validation") or {}).get("passed"),
        "narrative_completeness": (communication.get("validation") or {}).get(
            "narrative_completeness"
        ),
        "generic_template": communication.get("generic_template"),
        "llm_used": False,
        "fabricated": False,
        "reasoning_changed": False,
    }
    # Prefer ICE text on the institutional answer surface
    institutional_answer = {
        **institutional_answer,
        "communication": {
            "template": communication.get("template"),
            "executive_summary": communication.get("executive_summary"),
            "section_order": communication.get("section_order"),
            "framework_visible": communication.get("framework_visible"),
            "ice_version": communication.get("ice_version"),
        },
    }

    # S11 DQ record
    dq = record_decision_quality(
        context=context,
        governance=governance,
        evidence=evidence,
        telemetry_latency_ms=int((time.time() - t0) * 1000),
    )
    stages["decision_quality"] = dq

    # S12 Outcome registration
    outcome = register_outcome(policy=policy, governance=governance)
    stages["outcome"] = outcome

    total_ms = int((time.time() - t0) * 1000)

    # Preliminary gates (telemetry filled next)
    stages["telemetry_pending"] = True
    gates = evaluate_gates(stages=stages, policy=policy, context=context)

    # S13 Telemetry
    telemetry = build_telemetry(
        context=context,
        stages=stages,
        policy=policy,
        gates=gates,
        total_ms=total_ms,
    )
    stages["telemetry"] = telemetry
    stages.pop("telemetry_pending", None)

    # Re-evaluate gates with telemetry present
    gates = evaluate_gates(stages=stages, policy=policy, context=context)

    # Persist
    store.put_context(context["pipeline_id"], context)
    execution = {
        "pipeline_id": context["pipeline_id"],
        "replay_id": context["replay_id"],
        "programme": PROGRAMME,
        "pipeline_version": PIPELINE_VERSION,
        "started_at": context["timestamp"],
        "finished_at": store.utc_now(),
        "latency_ms": total_ms,
        "intent": intent_rec["intent"],
        "question": context["question"],
        "stages": {
            k: (
                {sk: sv for sk, sv in v.items() if sk not in {"bag", "packs", "governance_packs", "plan", "knowledge", "evidence"}}
                if isinstance(v, dict)
                else v
            )
            for k, v in stages.items()
        },
        "institutionally_complete": gates.get("institutionally_complete"),
        "quality_gates": gates,
        "decision_id": dq.get("decision_id"),
        "outcome_decision_id": outcome.get("decision_id"),
        "freeze_locks": FREEZE_LOCKS,
        "fabricated": False,
    }
    # Keep full stage payloads for replay (separate)
    replay_payload = {
        "replay_id": context["replay_id"],
        "pipeline_id": context["pipeline_id"],
        "context": context,
        "intent": intent_rec,
        "intent_resolution": {
            "intent": irl.get("intent"),
            "question_type": irl.get("question_type"),
            "concept_mode": irl.get("concept_mode"),
            "as_of": irl.get("as_of"),
        },
        "entities": entities_rec,
        "policy": policy,
        "knowledge": knowledge,
        "evidence": evidence,
        "answer_assembly": answer_assembly,
        "framework_selection": framework_selection,
        "playbook_selection": playbook_selection,
        "evidence_graph": evidence_graph,
        "institutional_memory": institutional_memory,
        "institutional_answer": institutional_answer,
        "communication": communication,
        "planner": planner,
        "dag": dag,
        "governance": governance,
        "decision_quality": dq,
        "outcome": outcome,
        "telemetry": telemetry,
        "quality_gates": gates,
        "packs_keys": list(packs.keys()),
        "fabricated": False,
    }
    store.put_execution(context["pipeline_id"], execution)
    store.put_replay(context["replay_id"], replay_payload)

    return {
        "programme": PROGRAMME,
        "pipeline_version": PIPELINE_VERSION,
        "pipeline_id": context["pipeline_id"],
        "replay_id": context["replay_id"],
        "context": context,
        "intent_resolution": irl,
        "intent": intent_rec,
        "entities": entities_rec,
        "policy": policy,
        "knowledge": knowledge,
        "evidence": evidence,
        "answer_assembly": answer_assembly,
        "answer_assembly_version": AAE_VERSION,
        "framework_selection": framework_selection,
        "framework_selection_version": IFSE_VERSION,
        "playbook_selection": playbook_selection,
        "playbook_selection_version": IAP_VERSION,
        "evidence_graph": evidence_graph,
        "evidence_graph_version": IEG_VERSION,
        "institutional_memory": institutional_memory,
        "institutional_memory_version": IMAI_VERSION,
        "institutional_answer": institutional_answer,
        "communication": communication,
        "institutional_communication_version": ICE_VERSION,
        "answer": {
            "summary": communication.get("executive_summary"),
            "executive_summary": communication.get("executive_summary"),
            "why": communication.get("why") or [],
            "prose": communication.get("prose"),
            "template": communication.get("template"),
            "sections": communication.get("sections"),
            "source": "institutional_communication",
            "fabricated": False,
            "llm_used": False,
        },
        "planner": planner,
        "dag": dag,
        "governance": governance,
        "decision_quality": dq,
        "outcome": outcome,
        "telemetry": telemetry,
        "quality_gates": gates,
        "institutionally_complete": bool(gates.get("institutionally_complete")),
        "latency_ms": total_ms,
        "as_of": irl.get("as_of"),
        "concept_mode": bool(irl.get("concept_mode")),
        "freeze_locks": FREEZE_LOCKS,
        "fabricated": False,
        "reasoning_changed": False,
        "knowledge_factory_changed": False,
        "llm_synthesis_used": False,
    }
