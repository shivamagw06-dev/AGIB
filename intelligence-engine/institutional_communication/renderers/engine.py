"""Deterministic ICE renderer — binds InstitutionalAnswer; no new reasoning."""

from __future__ import annotations

from typing import Any

from institutional_communication.citations.bind import render_sources_section
from institutional_communication.planner.plan import plan_communication
from institutional_communication.renderers.confidence import render_confidence_section
from institutional_communication.renderers.evidence import render_evidence_section
from institutional_communication.renderers.framework import render_framework_section
from institutional_communication.renderers.risk import render_risk_section
from institutional_communication.replay.section import render_replay_sections
from institutional_communication.schema import FREEZE_LOCKS, ICE_VERSION, MODULE_CODE, PROGRAMME
from institutional_communication.styles.institutional import bullet, clean_line
from institutional_communication.templates.catalog import get_template


def render_communication(institutional_answer: dict[str, Any]) -> dict[str, Any]:
    plan = plan_communication(institutional_answer)
    template = get_template(plan["template"])
    sections_out: dict[str, dict[str, Any]] = {}

    # Evidence before conclusions
    sections_out["evidence"] = render_evidence_section(institutional_answer)
    sections_out["framework_used"] = render_framework_section(institutional_answer)
    sections_out["risks"] = render_risk_section(institutional_answer)
    sections_out["confidence"] = render_confidence_section(institutional_answer)
    sections_out["sources"] = render_sources_section(institutional_answer)

    # Analysis from existing assembly / bound bullets only
    src_sections = institutional_answer.get("sections") or {}
    analysis_bullets = []
    for key in ("analysis", "conclusion", "executive_summary"):
        for b in (src_sections.get(key) or {}).get("bullets") or []:
            line = clean_line(str(b), max_len=240)
            if not line:
                continue
            # Drop governance scaffolding noise / generic markers
            low = line.lower()
            if low.startswith("governance path:"):
                continue
            if "business strength rated c" in low:
                continue
            if "valuation question blocked" in low:
                continue
            analysis_bullets.append(bullet(line))
    if not analysis_bullets:
        analysis_bullets.append(
            bullet(
                "Analysis limited to retrieved evidence and selected frameworks — "
                "no additional synthesis invented by the communication layer."
            )
        )
    # Evidence-id tags for first few evidence items
    for item in ((institutional_answer.get("evidence") or {}).get("items") or [])[:5]:
        eid = item.get("evidence_id")
        if eid:
            analysis_bullets.append(bullet(f"Supported by evidence id {eid}"))
    sections_out["analysis"] = {
        "section": "analysis",
        "title": "Analysis",
        "bullets": analysis_bullets[:14],
        "visible": True,
    }

    # Executive summary — framework-first / evidence-first per template lead
    exec_lines = _executive_summary(institutional_answer, plan, template, sections_out)
    sections_out["executive_summary"] = {
        "section": "executive_summary",
        "title": "Executive Summary",
        "bullets": exec_lines,
        "visible": True,
    }

    if plan["template"] == "historical_replay":
        sections_out.update(render_replay_sections(institutional_answer))

    # Ordered final text
    ordered_sections = []
    for name in template["sections"]:
        sec = sections_out.get(name)
        if not sec:
            continue
        ordered_sections.append(sec)

    prose_blocks = []
    for sec in ordered_sections:
        prose_blocks.append(sec.get("title") or sec.get("section"))
        prose_blocks.extend(sec.get("bullets") or [])
        prose_blocks.append("")

    executive_text = " ".join(
        clean_line(b.lstrip("- ").strip(), max_len=200)
        for b in (sections_out["executive_summary"].get("bullets") or [])[:4]
        if b
    )
    why = []
    for name in ("framework_used", "evidence", "analysis", "risks", "confidence"):
        for b in (sections_out.get(name) or {}).get("bullets") or []:
            why.append(b.lstrip("- ").strip())
            if len(why) >= 12:
                break
        if len(why) >= 12:
            break

    return {
        "ok": True,
        "ice_version": ICE_VERSION,
        "module": MODULE_CODE,
        "programme": PROGRAMME,
        "plan": plan,
        "template": template["id"],
        "template_title": template["title"],
        "sections": {s["section"]: s for s in ordered_sections},
        "section_order": [s["section"] for s in ordered_sections],
        "executive_summary": executive_text,
        "summary": executive_text,
        "why": why,
        "prose": "\n".join(prose_blocks).strip(),
        "framework_visible": bool((sections_out.get("framework_used") or {}).get("framework_ids")),
        "citation_density": plan.get("citation_density"),
        "narrative_style": plan.get("narrative_style"),
        "consumes_institutional_answer": True,
        "generic_template": False,
        "llm_used": False,
        "fabricated": False,
        "reasoning_changed": False,
        "governance_changed": False,
        "freeze_locks": FREEZE_LOCKS,
    }


def _executive_summary(
    institutional_answer: dict[str, Any],
    plan: dict[str, Any],
    template: dict[str, Any],
    sections_out: dict[str, dict[str, Any]],
) -> list[str]:
    intent = institutional_answer.get("intent_v2")
    lines = [
        bullet(f"Intent: {intent} · Template: {template.get('title')}"),
    ]
    fw_ids = ((institutional_answer.get("frameworks") or {}).get("framework_ids") or [])[:4]
    if fw_ids:
        lines.append(bullet(f"Frameworks applied: {', '.join(map(str, fw_ids))}"))
    expl = ((institutional_answer.get("frameworks") or {}).get("explanation") or {}).get("reason")
    if expl:
        lines.append(bullet(clean_line(str(expl), max_len=260)))

    if plan.get("as_of"):
        lines.append(bullet(f"Historical replay as_of={plan.get('as_of')} — current prices excluded."))

    n_ev = len(((institutional_answer.get("evidence") or {}).get("items") or []))
    lines.append(bullet(f"Evidence items bound: {n_ev}. Conclusions follow evidence and frameworks only."))

    band = (sections_out.get("confidence") or {}).get("band")
    if band:
        lines.append(bullet(f"Confidence: {band} (see Confidence section for calibration)."))

    # Concept mode hygiene
    if institutional_answer.get("concept_mode"):
        lines.append(bullet("Concept mode — no company entity forced into the narrative."))

    return lines
