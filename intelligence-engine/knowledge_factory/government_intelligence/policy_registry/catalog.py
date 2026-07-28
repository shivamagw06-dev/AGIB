"""Policy domain index — maps domains to seed policy families."""

from __future__ import annotations

from typing import Any

DOMAIN_INDEX: dict[str, dict[str, Any]] = {
    "rbi": {"label": "RBI Intelligence", "body": "RBI", "policy_type": "monetary"},
    "budget": {"label": "Union Budget", "body": "MOF", "policy_type": "fiscal_budget"},
    "sebi": {"label": "SEBI Intelligence", "body": "SEBI", "policy_type": "securities_regulation"},
    "mca": {"label": "MCA Intelligence", "body": "MCA", "policy_type": "corporate_law"},
    "gst": {"label": "GST Intelligence", "body": "GST_COUNCIL", "policy_type": "tax_gst"},
    "pli": {"label": "PLI Intelligence", "body": "DPIIT", "policy_type": "pli_industrial"},
    "trade": {"label": "Trade Policy", "body": "MOC", "policy_type": "trade"},
    "industry": {"label": "Industry Regulation", "body": "GOI", "policy_type": "industry_regulation"},
    "state": {"label": "State Government Framework", "body": "GOI", "policy_type": "state_policy"},
}


def list_domain_ids() -> list[str]:
    return list(DOMAIN_INDEX.keys())
