"""Build knowledge-only morning publications from soft-read knowledge."""

from __future__ import annotations

from typing import Any

from research_office import store
from research_office.publications.gates import validate_publication
from research_office.publications.registry import register_publication
from research_office.templates import knowledge as kn


def _obs(payload: dict[str, Any], label: str) -> list[str]:
    if payload.get("unavailable"):
        return [f"{label}: unavailable — transparent insufficiency"]
    keys = [k for k in payload.keys() if k not in {"fabricated", "error", "unavailable"}][:12]
    return [f"{label}: observed keys {keys}"] if keys else [f"{label}: empty snapshot"]


def _evidence_present(sources: list[dict[str, Any]], payloads: list[dict[str, Any]]) -> bool:
    """Provenanced KF soft-reads count as evidence attempts.

    Unavailable layers are transparent insufficiency inside the publication body,
    not a silent fabrication. Completely missing sources ⇒ evidence_missing.
    """
    if not sources:
        return False
    if any(s.get("provenance") for s in sources):
        return True
    return any(not (p or {}).get("unavailable") for p in payloads)


def build_all_morning_publications(*, scheduler_run_id: str | None = None) -> list[dict[str, Any]]:
    versions = kn.knowledge_versions()
    sched = kn.read_scheduler_context()
    iks = kn.read_iks_dashboard()
    coverage = kn.read_coverage()
    macro = kn.read_macro()
    gov = kn.read_government()
    industry = kn.read_industry()
    events = kn.read_corporate_events()
    alt = kn.read_alternative_data()
    exp = kn.read_expectations()
    company = kn.read_company_intelligence()

    pubs: list[dict[str, Any]] = []

    pubs.append(
        _publish(
            title="Market Morning Brief",
            publication_type="market_morning_brief",
            sections={
                "market_overview": _obs(iks, "institutional_knowledge_stack"),
                "global_context": _obs(macro, "macro"),
                "todays_agenda": _obs(sched, "scheduler"),
                "major_overnight_developments": _obs(events, "corporate_events"),
                "key_events": _obs(gov, "government"),
            },
            payloads=[iks, macro, sched, events, gov],
            source_names=[
                ("iks", iks),
                ("macro", macro),
                ("scheduler", sched),
                ("corporate_events", events),
                ("government", gov),
            ],
            coverage={"morning": coverage, "fabricated": False},
            versions=versions,
            scheduler_run_id=scheduler_run_id,
        )
    )

    pubs.append(
        _publish(
            title="Macro Intelligence Brief",
            publication_type="macro_intelligence_brief",
            sections={
                "macro_dashboard": _obs(macro, "macro_object"),
                "rates": ["Rates: see macro snapshot — no fabricated series"],
                "inflation": ["Inflation: see macro snapshot — UNKNOWN if absent"],
                "gdp": ["GDP: see macro snapshot — UNKNOWN if absent"],
                "liquidity": ["Liquidity: UNKNOWN unless present in macro object"],
                "credit": ["Credit: cross-ref alternative data bank credit if present"],
                "fx": ["FX: UNKNOWN unless present in macro object"],
                "alternative_data_changes": _obs(alt, "alternative_data"),
                "macro_observations": _obs(macro, "macro"),
            },
            payloads=[macro, alt],
            source_names=[("macro", macro), ("alternative_data", alt)],
            coverage={"fabricated": False},
            versions=versions,
            scheduler_run_id=scheduler_run_id,
        )
    )

    pubs.append(
        _publish(
            title="Government Intelligence Brief",
            publication_type="government_intelligence_brief",
            sections={
                "rbi": ["RBI: from government intelligence dashboard"],
                "budget": ["Budget: from government intelligence dashboard"],
                "sebi": ["SEBI: from government intelligence dashboard"],
                "gst": ["GST: from government intelligence dashboard"],
                "pli": ["PLI: from government intelligence dashboard"],
                "trade": ["Trade: from government intelligence dashboard"],
                "policy_changes": _obs(gov, "government"),
                "transmission_summary": [
                    "Transmission: descriptive only — no portfolio implications"
                ],
            },
            payloads=[gov],
            source_names=[("government", gov)],
            coverage={"fabricated": False},
            versions=versions,
            scheduler_run_id=scheduler_run_id,
        )
    )

    pubs.append(
        _publish(
            title="Sector Intelligence Report",
            publication_type="sector_intelligence_report",
            sections={
                "current_state": _obs(company, "company_intelligence"),
                "valuation": ["Valuation context: evidence-backed fields only; else UNKNOWN"],
                "historical_context": ["Historical: via KF/HD when available"],
                "alternative_data": _obs(alt, "alternative_data"),
                "macro_sensitivity": _obs(macro, "macro"),
                "government_impacts": _obs(gov, "government"),
                "key_observations": _obs(iks, "iks"),
            },
            payloads=[company, alt, macro, gov, iks],
            source_names=[
                ("company_intelligence", company),
                ("alternative_data", alt),
                ("macro", macro),
                ("government", gov),
            ],
            coverage={"fabricated": False},
            versions=versions,
            scheduler_run_id=scheduler_run_id,
        )
    )

    pubs.append(
        _publish(
            title="Industry Intelligence Report",
            publication_type="industry_intelligence_report",
            sections={
                "business_model_observations": _obs(industry, "industry"),
                "value_chain_developments": ["Value chain: from industry intelligence"],
                "cost_changes": ["Cost changes: UNKNOWN unless evidenced"],
                "supply_chain_changes": ["Supply chain: UNKNOWN unless evidenced"],
                "industry_cycles": ["Industry cycles: descriptive observations only"],
            },
            payloads=[industry],
            source_names=[("industry", industry)],
            coverage={"fabricated": False},
            versions=versions,
            scheduler_run_id=scheduler_run_id,
        )
    )

    pubs.append(
        _publish(
            title="Corporate Events Report",
            publication_type="corporate_events_report",
            sections={
                "results": ["Results: from corporate events intelligence"],
                "guidance": ["Guidance: from events / expectations layers"],
                "ceo_changes": ["CEO changes: timeline when present"],
                "buybacks": ["Buybacks: timeline when present"],
                "acquisitions": ["Acquisitions: timeline when present"],
                "contracts": ["Contracts: timeline when present"],
                "litigation": ["Litigation: timeline when present"],
                "regulatory_actions": ["Regulatory actions: timeline when present"],
                "timeline_updates": _obs(events, "corporate_events"),
            },
            payloads=[events],
            source_names=[("corporate_events", events)],
            coverage={"fabricated": False},
            versions=versions,
            scheduler_run_id=scheduler_run_id,
        )
    )

    pubs.append(
        _publish(
            title="Alternative Data Report",
            publication_type="alternative_data_report",
            sections={
                "upi": ["UPI: trend change only if dataset present"],
                "electricity": ["Electricity: trend change only if dataset present"],
                "rail_freight": ["Rail Freight: trend change only if dataset present"],
                "port_cargo": ["Port Cargo: trend change only if dataset present"],
                "gst": ["GST: trend change only if dataset present"],
                "vehicle_registrations": ["Vehicle Registrations: trend only if present"],
                "bank_credit": ["Bank Credit: trend only if present"],
                "rainfall": ["Rainfall: trend only if present"],
                "air_traffic": ["Air Traffic: trend only if present"],
                "trend_changes": _obs(alt, "alternative_data"),
            },
            payloads=[alt],
            source_names=[("alternative_data", alt)],
            coverage={"fabricated": False},
            versions=versions,
            scheduler_run_id=scheduler_run_id,
        )
    )

    pubs.append(
        _publish(
            title="Market Expectations Report",
            publication_type="market_expectations_report",
            sections={
                "guidance_changes": _obs(exp, "expectations"),
                "expectation_revisions": ["Revisions: from expectations intelligence"],
                "new_surprises": ["Surprises: from expectations intelligence"],
                "narrative_evolution": ["Narratives: descriptive only"],
                "expectation_gaps": ["Gaps: reality vs expectations — knowledge only"],
            },
            payloads=[exp],
            source_names=[("expectations", exp)],
            coverage={"fabricated": False},
            versions=versions,
            scheduler_run_id=scheduler_run_id,
        )
    )

    return pubs


def build_company_note(
    ticker: str,
    *,
    scheduler_run_id: str | None = None,
    trigger_reason: str = "new_evidence",
) -> dict[str, Any]:
    versions = kn.knowledge_versions()
    t = str(ticker or "").upper()
    bundle = kn.read_company_bundle(t)
    feed = kn.read_evidence_feed(t)
    gov = kn.read_government()
    macro = kn.read_macro()
    alt = kn.read_alternative_data()
    exp = kn.read_expectations()
    industry = kn.read_industry()

    insufficient = []
    for name, payload in (
        ("company_bundle", bundle),
        ("evidence_feed", feed),
        ("macro", macro),
        ("government", gov),
        ("alternative_data", alt),
        ("expectations", exp),
        ("industry", industry),
    ):
        if payload.get("unavailable") or payload.get("insufficient"):
            insufficient.append(name)

    return _publish(
        title=f"Company Research Note — {t}",
        publication_type="company_research_note",
        sections={
            "company": t,
            "summary": [f"Evidence-triggered note ({trigger_reason}) — no recommendation"],
            "evidence": _obs(feed, "evidence_feed"),
            "historical_context": ["Historical: from bundle/HD when present"],
            "sector_context": _obs(industry, "industry"),
            "macro_context": _obs(macro, "macro"),
            "government_context": _obs(gov, "government"),
            "alternative_data_context": _obs(alt, "alternative_data"),
            "expectation_context": _obs(exp, "expectations"),
            "transparent_insufficiency": insufficient or ["none_declared"],
            "bundle_keys": list(bundle.keys())[:20],
        },
        payloads=[bundle, feed, macro, gov, alt, exp, industry],
        source_names=[
            ("company_bundle", bundle),
            ("evidence_feed", feed),
            ("macro", macro),
            ("government", gov),
            ("alternative_data", alt),
            ("expectations", exp),
            ("industry", industry),
        ],
        coverage={"ticker": t, "fabricated": False},
        versions=versions,
        scheduler_run_id=scheduler_run_id,
        covered_entities=[t],
        evidence_pack_versions={"evidence_feed": (feed or {}).get("version") or versions["evidence_version"]},
    )


def _publish(
    *,
    title: str,
    publication_type: str,
    sections: dict[str, Any],
    payloads: list[dict[str, Any]],
    source_names: list[tuple[str, dict[str, Any]]],
    coverage: dict[str, Any],
    versions: dict[str, str],
    scheduler_run_id: str | None,
    covered_entities: list[str] | None = None,
    evidence_pack_versions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sources = [kn.source_ref(n, p) for n, p in source_names]
    body = {
        "as_of": store.utc_now(),
        "snapshot": {
            "publication_type": publication_type,
            "scheduler_run_id": scheduler_run_id,
            "knowledge_version": versions["knowledge_version"],
            "evidence_version": versions["evidence_version"],
        },
        "sections": sections,
        "recommendation": None,
        "knowledge_only": True,
    }
    evidence_present = _evidence_present(sources, payloads)
    # If all unavailable, still publish with insufficiency but gate fails
    validation = validate_publication(
        body=body,
        sources=sources,
        knowledge_version=versions.get("knowledge_version"),
        evidence_version=versions.get("evidence_version"),
        coverage=coverage,
        evidence_present=evidence_present,
    )
    return register_publication(
        title=title,
        publication_type=publication_type,
        body=body,
        knowledge_version=versions["knowledge_version"],
        evidence_version=versions["evidence_version"],
        evidence_pack_versions=evidence_pack_versions or {"soft_dashboard": versions["evidence_version"]},
        covered_entities=covered_entities or [],
        coverage=coverage,
        sources=sources,
        validation=validation,
        scheduler_run_id=scheduler_run_id,
    )
