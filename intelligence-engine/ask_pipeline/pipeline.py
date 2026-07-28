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
from ask_pipeline.intent_resolution import resolve_intent
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
    }
