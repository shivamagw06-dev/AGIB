"""Bind evidence before conclusions — map to evidence IDs / docs / replay."""

from __future__ import annotations

from typing import Any

from institutional_communication.styles.institutional import bullet, clean_line


def render_evidence_section(institutional_answer: dict[str, Any]) -> dict[str, Any]:
    ev = institutional_answer.get("evidence") or {}
    items = list(ev.get("items") or [])
    lines: list[str] = []
    bindings: list[dict[str, Any]] = []

    for item in items[:12]:
        eid = item.get("evidence_id") or "unknown"
        title = clean_line(item.get("title") or item.get("evidence_type") or eid, max_len=160)
        src = item.get("source") or "unspecified"
        doc = item.get("document_id")
        domain = item.get("domain") or item.get("evidence_type")
        bit = f"[{eid}] {title} (source={src}"
        if doc:
            bit += f"; doc={doc}"
        if domain:
            bit += f"; type={domain}"
        bit += ")"
        lines.append(bullet(bit))
        bindings.append(
            {
                "evidence_id": eid,
                "document_id": doc,
                "source": src,
                "knowledge_object": item.get("evidence_type"),
                "available_from": item.get("available_from"),
                "replay_id": (institutional_answer.get("replay") or {}).get("retrieval_id"),
            }
        )

    if not lines:
        lines.append(bullet("No ranked evidence items were available in the InstitutionalAnswer object."))

    ranked = ev.get("iere_ranked_count")
    if ranked is not None:
        lines.insert(0, bullet(f"IERE ranked evidence count: {ranked}"))

    return {
        "section": "evidence",
        "title": "Evidence",
        "bullets": lines,
        "bindings": bindings,
        "visible": True,
    }
