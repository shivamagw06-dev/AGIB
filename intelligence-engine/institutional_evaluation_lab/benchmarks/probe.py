"""Soft AGIB probe — measurement only; does not change reasoning internals."""

from __future__ import annotations

from typing import Any


def probe_question(
    question: dict[str, Any],
    *,
    mode: str = "soft",
) -> dict[str, Any]:
    """
    Execute AGIB soft layers for evaluation.

    mode=soft  — intent + frameworks + playbook + evidence graph + IMAI (fast nightly)
    mode=full  — complete ask pipeline (slow; sample use)
    """
    text = str(question.get("question") or "")
    ticker = question.get("ticker_hint")
    as_of = question.get("as_of")

    if mode == "full":
        from ask_pipeline.pipeline import run_complete_ask

        pipe = run_complete_ask(text, ticker_hint=ticker)
        return {
            "mode": "full",
            "question_id": question.get("question_id"),
            "intent_resolution": pipe.get("intent_resolution") or {},
            "framework_selection": pipe.get("framework_selection") or {},
            "playbook_selection": pipe.get("playbook_selection") or {},
            "evidence_graph": pipe.get("evidence_graph") or {},
            "institutional_memory": pipe.get("institutional_memory") or {},
            "communication": pipe.get("communication") or {},
            "governance": {
                "path": (pipe.get("governance") or {}).get("path"),
                "question_type": (pipe.get("governance") or {}).get("question_type"),
            },
            "latency_ms": pipe.get("latency_ms"),
            "reasoning_changed": pipe.get("reasoning_changed"),
            "fabricated": False,
        }

    # Soft structural probe
    from ask_pipeline.intent_resolution import resolve_intent
    from framework_selection import select_frameworks
    from institutional_analog_intelligence.production import retrieve as retrieve_memory
    from institutional_evidence_graph import build_evidence_graph
    from institutional_playbooks import select_playbook

    irl = resolve_intent(text, ticker_hint=ticker)
    if as_of and not irl.get("as_of"):
        irl = {**irl, "as_of": as_of}

    concept_mode = (
        question.get("concept_mode")
        if question.get("concept_mode") is not None
        else bool(irl.get("concept_mode"))
    )
    hint = None if concept_mode else ticker
    entities = [] if concept_mode else ([{"type": "company", "id": hint, "confidence": 0.99}] if hint else [])

    fs = select_frameworks(
        question=text,
        intent_v2=str(irl.get("intent") or "Unknown"),
        ticker_hint=hint,
        concept_mode=concept_mode,
        as_of=irl.get("as_of") or as_of,
        entities=entities or None,
    )
    pb = select_playbook(
        question=text,
        intent_v2=str(irl.get("intent") or "Unknown"),
        sector=fs.get("sector") or question.get("sector"),
        framework_ids=list(fs.get("framework_ids") or []),
        framework_selection=fs,
        concept_mode=concept_mode,
    )
    eg = build_evidence_graph(
        question=text,
        entities=entities or list(irl.get("entities") or []),
        ticker_hint=hint,
        concept_mode=concept_mode,
        as_of=irl.get("as_of") or as_of,
        playbook_selection=pb,
        framework_selection=fs,
        intent_v2=str(irl.get("intent") or "Unknown"),
    )
    # AGI TIRC — Replay Guard (soft probe mirrors Ask pipeline)
    from temporal_integrity.production import guard as tirc_guard

    _as_of = irl.get("as_of") or as_of
    _pre = tirc_guard(as_of=_as_of, evidence_graph=eg, stage="pre_analog")
    eg = _pre.get("evidence_graph") or eg
    im = retrieve_memory(
        question=text,
        evidence_graph=eg,
        playbook=pb,
        as_of=_as_of,
        top_k=5,
    )
    _post = tirc_guard(as_of=_as_of, institutional_memory=im, stage="post_analog")
    im = _post.get("institutional_memory") or im
    return {
        "mode": "soft",
        "question_id": question.get("question_id"),
        "intent_resolution": irl,
        "framework_selection": fs,
        "playbook_selection": pb,
        "evidence_graph": eg,
        "institutional_memory": im,
        "temporal_integrity": {
            "pre_analog": _pre.get("report"),
            "post_analog": _post.get("report"),
        },
        "communication": {},
        "governance": {},
        "latency_ms": None,
        "reasoning_changed": False,
        "fabricated": False,
    }
