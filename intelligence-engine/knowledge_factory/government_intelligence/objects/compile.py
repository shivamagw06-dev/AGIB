"""Compile Government & Regulatory Intelligence pack."""

from __future__ import annotations

from typing import Any

from knowledge_factory.government_intelligence import store as igri_store
from knowledge_factory.government_intelligence.collectors.soft import collect_government_context
from knowledge_factory.government_intelligence.coverage import compute_coverage_level
from knowledge_factory.government_intelligence.producers.core import produce_all
from knowledge_factory.government_intelligence.schema import FREEZE_LOCKS, IGRI_VERSION, LAYER, PROGRAMME
from knowledge_factory.government_intelligence.timeline.build import build_policy_timeline
from knowledge_factory.government_intelligence.validators.gates import validate_pack


def compile_government_intelligence(*, persist: bool = True) -> dict[str, Any]:
    ctx = collect_government_context()
    produced = produce_all(ctx)
    bodies = produced["bodies"]
    policies = produced["policies"]
    timeline = build_policy_timeline(policies)
    quality = validate_pack(bodies=bodies, policies=policies, timeline=timeline)
    level = compute_coverage_level(
        bodies=bodies, policies=policies, timeline=timeline, quality=quality
    )

    # Per-policy validation stamp
    from knowledge_factory.government_intelligence.validators.gates import validate_policy

    for p in policies:
        p["validation"] = validate_policy(p)

    pack = {
        "kind": "government_intelligence_pack",
        "igri_version": IGRI_VERSION,
        "programme": PROGRAMME,
        "layer": LAYER,
        "registry": {
            "bodies": bodies,
            "body_count": len(bodies),
        },
        "policies": policies,
        "policy_count": len(policies),
        "timeline": timeline,
        "domains": sorted({str(p.get("domain") or "") for p in policies}),
        "quality": quality,
        "coverage_level": level["coverage_level"],
        "coverage_level_name": level["coverage_level_name"],
        "complete": level["complete"],
        "institutional_ready": bool(quality.get("institutional_ready")),
        "freeze_locks": FREEZE_LOCKS,
        "architecture_status": "SOFT_GOVERNMENT_REGULATORY_INTELLIGENCE",
        "not_a_reasoning_engine": True,
        "political_opinion": False,
        "policy_forecast": False,
        "fabricated": False,
    }
    if persist:
        for b in bodies:
            igri_store.put_body(b)
        for p in policies:
            igri_store.put_policy(p)
        igri_store.put_timeline(timeline)
    return pack
