"""Soft collectors — curated seeds + registry catalogs only. Never infer policy."""

from __future__ import annotations

from typing import Any

from knowledge_factory.government_intelligence.fixtures.seeds import all_policy_seeds
from knowledge_factory.government_intelligence.ministry_registry.catalog import list_ministries
from knowledge_factory.government_intelligence.regulators.catalog import list_regulators


def collect_government_context() -> dict[str, Any]:
    return {
        "ministries": list_ministries(),
        "regulators": list_regulators(),
        "policy_seeds": all_policy_seeds(),
        "sources_priority": [
            "government_of_india",
            "rbi",
            "sebi",
            "mca",
            "gst_council",
            "pib",
            "ministry_websites",
            "official_gazette",
            "official_notifications",
            "parliamentary_documents",
        ],
        "never_infer_policy": True,
        "never_fabricate": True,
    }
