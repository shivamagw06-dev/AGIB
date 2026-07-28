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
from institutional_communication import ICE_VERSION, communicate_from_ask
from ask_pipeline.knowledge import retrieve_knowledge
from ask_pipeline.planner import run_planner
from ask_pipeline.policy import execution_policy
from ask_pipeline.recording import record_decision_quality, register_outcome
from ask_pipeline.schema import FREEZE_LOCKS, PIPELINE_VERSION, PROGRAMME
from ask_pipeline import store
from ask_pipeline.telemetry import build_telemetry


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
    irl = resolve_intent(question, ticker_hint=ticker_hint or context.get("ticker_hint"))
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
    knowledge = retrieve_knowledge(
        intent=intent_rec["intent"],
        entities=context["entities"],
        soft_tags=entities_rec.get("soft_tags"),
        question=question,
        as_of=irl.get("as_of"),
        concept_mode=bool(irl.get("concept_mode")),
    )
    stages["knowledge"] = knowledge

    # S06 Evidence — prefers IERE Evidence Packs when available; reasoning unchanged
    evidence = assemble_evidence(
        knowledge,
        intent=intent_rec["intent"],
        entities=context["entities"],
    )
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

    # S07 Planner — no ticker in Concept Mode
    hint = None if irl.get("concept_mode") else (
        (primary.get("entity_id") if primary else None)
        or (ticker_hint if not irl.get("entity_pollution_blocked") else None)
    )
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

    # S09 Reasoning (+ S10 portfolio via flags)
    governance: dict[str, Any] = {}
    try:
        from institutional_reasoning.execution_governance import govern_answer

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
    communication = communicate_from_ask(
        question=question,
        intent_resolution=irl,
        answer_assembly=answer_assembly,
        framework_selection=framework_selection,
        institutional_answer=institutional_answer,
        governance=governance,
        evidence=evidence,
        knowledge=knowledge,
        replay_id=context.get("replay_id"),
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
