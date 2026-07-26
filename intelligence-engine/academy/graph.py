"""Knowledge graph builder over Academy concepts and causal models."""

from __future__ import annotations

from typing import Any

from academy.causal_models import all_causal_models
from academy.knowledge_objects import all_knowledge_objects
from academy.mental_models import all_mental_models


def build_knowledge_graph() -> dict[str, Any]:
    concepts = all_knowledge_objects()
    nodes = [
        {
            "id": k.concept_id,
            "label": k.concept,
            "type": "concept",
            "tags": k.tags,
            "confidence": k.confidence,
        }
        for k in concepts
    ]
    edges: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    def add_edge(src: str, dst: str, rel: str) -> None:
        key = (src, dst, rel)
        if src == dst or key in seen:
            return
        seen.add(key)
        edges.append({"from": src, "to": dst, "type": rel})

    for k in concepts:
        rel = k.relationships
        for p in rel.parent:
            add_edge(p, k.concept_id, "parent_of")
        for c in rel.children:
            add_edge(k.concept_id, c, "parent_of")
        for d in rel.dependencies:
            add_edge(k.concept_id, d, "depends_on")
        for r in rel.related:
            add_edge(k.concept_id, r, "related")
        for o in rel.opposing:
            add_edge(k.concept_id, o, "opposes")
        for m in k.mental_models:
            add_edge(k.concept_id, m, "uses_mental_model")

    for cm in all_causal_models():
        nodes.append({"id": cm.model_id, "label": cm.name, "type": "causal_model"})
        for cid in cm.related_concepts:
            add_edge(cm.model_id, cid, "applies_concept")
        for i in range(len(cm.chain) - 1):
            edges.append(
                {
                    "from": f"{cm.model_id}:{i}:{cm.chain[i]}",
                    "to": f"{cm.model_id}:{i+1}:{cm.chain[i+1]}",
                    "type": "causes",
                    "causal_model": cm.model_id,
                }
            )

    for mm in all_mental_models():
        nodes.append({"id": mm.model_id, "label": mm.name, "type": "mental_model"})
        for cid in mm.related_concepts:
            add_edge(mm.model_id, cid, "frames")

    return {
        "nodes": nodes,
        "edges": edges,
        "counts": {
            "nodes": len(nodes),
            "edges": len(edges),
            "concepts": len(concepts),
            "causal_models": len(all_causal_models()),
            "mental_models": len(all_mental_models()),
        },
    }


def concept_neighborhood(concept_id: str) -> dict[str, Any]:
    graph = build_knowledge_graph()
    edges = [
        e
        for e in graph["edges"]
        if e.get("from") == concept_id or e.get("to") == concept_id or concept_id in str(e.get("from", ""))
    ]
    kos = {k.concept_id: k for k in all_knowledge_objects()}
    ko = kos.get(concept_id)
    return {
        "concept_id": concept_id,
        "concept": ko.to_dict() if ko else None,
        "edges": edges,
        "causal_models": [c.to_dict() for c in all_causal_models() if concept_id in c.related_concepts],
    }
