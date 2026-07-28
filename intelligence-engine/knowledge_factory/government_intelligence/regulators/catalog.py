"""Statutory regulators and authorities registry."""

from __future__ import annotations

from typing import Any

REGULATORS: dict[str, dict[str, Any]] = {
    "RBI": {
        "body_id": "RBI",
        "name": "Reserve Bank of India",
        "kind": "regulator",
        "jurisdiction": "India",
        "responsibilities": [
            "Monetary policy",
            "Banking regulation",
            "Liquidity management",
            "FX reserves / intervention",
            "Payment systems oversight",
        ],
        "industries_covered": ["banks", "nbfc", "payments", "all_credit"],
        "market_relevance": "Critical",
        "policy_categories": ["monetary", "industry_regulation"],
        "relationships": {"parent": "GOI", "instruments": ["repo", "sdf", "msf", "crr", "slr", "omo", "vrrr"]},
    },
    "SEBI": {
        "body_id": "SEBI",
        "name": "Securities and Exchange Board of India",
        "kind": "regulator",
        "jurisdiction": "India",
        "responsibilities": [
            "Securities markets regulation",
            "Listing / LODR",
            "Mutual funds / AIF / PMS",
            "Takeovers / buybacks / IPO process",
        ],
        "industries_covered": ["capital_markets", "all_listed"],
        "market_relevance": "Critical",
        "policy_categories": ["securities_regulation"],
        "relationships": {"parent": "GOI"},
    },
    "MCA": {
        "body_id": "MCA",
        "name": "Ministry of Corporate Affairs",
        "kind": "authority",
        "jurisdiction": "India",
        "responsibilities": [
            "Companies Act administration",
            "Corporate filings",
            "Director / auditor rules",
            "Financial reporting framework liaison",
        ],
        "industries_covered": ["all_companies"],
        "market_relevance": "High",
        "policy_categories": ["corporate_law"],
        "relationships": {"parent": "GOI"},
    },
    "GST_COUNCIL": {
        "body_id": "GST_COUNCIL",
        "name": "GST Council",
        "kind": "statutory_body",
        "jurisdiction": "India",
        "responsibilities": ["GST rate setting", "Exemptions", "GST law recommendations"],
        "industries_covered": ["all_taxable_goods_services"],
        "market_relevance": "Critical",
        "policy_categories": ["tax_gst"],
        "relationships": {"parent": "GOI", "linked": ["MOF"]},
    },
    "IRDAI": {
        "body_id": "IRDAI",
        "name": "Insurance Regulatory and Development Authority of India",
        "kind": "regulator",
        "jurisdiction": "India",
        "responsibilities": ["Insurance regulation", "Solvency", "Product approvals"],
        "industries_covered": ["insurance"],
        "market_relevance": "High",
        "policy_categories": ["industry_regulation"],
        "relationships": {"parent": "GOI"},
    },
    "TRAI": {
        "body_id": "TRAI",
        "name": "Telecom Regulatory Authority of India",
        "kind": "regulator",
        "jurisdiction": "India",
        "responsibilities": ["Telecom tariffs / QoS / spectrum policy inputs"],
        "industries_covered": ["telecom"],
        "market_relevance": "High",
        "policy_categories": ["industry_regulation"],
        "relationships": {"parent": "GOI"},
    },
    "CCI": {
        "body_id": "CCI",
        "name": "Competition Commission of India",
        "kind": "statutory_body",
        "jurisdiction": "India",
        "responsibilities": ["Competition / combination approvals", "Anti-competitive conduct"],
        "industries_covered": ["all"],
        "market_relevance": "High",
        "policy_categories": ["statutory", "industry_regulation"],
        "relationships": {"parent": "GOI"},
    },
    "NCLT": {
        "body_id": "NCLT",
        "name": "National Company Law Tribunal",
        "kind": "authority",
        "jurisdiction": "India",
        "responsibilities": ["Insolvency / company law adjudication"],
        "industries_covered": ["all_companies"],
        "market_relevance": "High",
        "policy_categories": ["corporate_law"],
        "relationships": {"parent": "GOI", "linked": ["MCA"]},
    },
}


def list_regulators() -> list[dict[str, Any]]:
    return [dict(v, fabricated=False, political_opinion=False) for v in REGULATORS.values()]
