"""Module 11 — Institutional Evidence Pack.

What every framework receives. Frameworks consume packs — never raw APIs.
"""

from __future__ import annotations

from typing import Any

from institutional_reasoning.institutional_evidence.accounting_quality import (
    produce_accounting_quality,
)
from institutional_reasoning.institutional_evidence.business_quality import (
    produce_business_quality,
)
from institutional_reasoning.institutional_evidence.dcf import produce_dcf_intelligence
from institutional_reasoning.institutional_evidence.historical import (
    produce_historical_intelligence,
)
from institutional_reasoning.institutional_evidence.peer import produce_peer_intelligence
from institutional_reasoning.institutional_evidence.provenance import (
    metric_provenance,
    now_iso,
)
from institutional_reasoning.institutional_evidence.quality import (
    MIN_FRAMEWORK_SCORE,
    pack_score,
    score_metric,
)
from institutional_reasoning.institutional_evidence.sector import produce_sector_intelligence

PACK_VERSION = "institutional-evidence-pack-v1.0.0"


def _current_pe_from_packs(
    entity_id: str,
    packs: dict[str, dict[str, Any]] | None,
) -> float | None:
    """Soft extract current PE from existing DVC/YFP/CID packs without fetching."""
    if not packs:
        return None
    eid = str(entity_id).upper()
    aliases = ("trailing_pe", "current_pe", "pe", "forward_pe", "pe_ratio")

    def walk(node: Any, depth: int = 0) -> float | None:
        if depth > 5 or node is None:
            return None
        if isinstance(node, dict):
            ent = None
            for k in ("symbol", "ticker", "entity_id", "company_symbol"):
                if node.get(k):
                    ent = str(node[k]).upper()
                    break
            # DVC field shape
            if node.get("field") in aliases and node.get("value") is not None:
                if not ent or ent == eid:
                    try:
                        v = float(node["value"])
                        if v > 0:
                            return v
                    except Exception:
                        pass
            for key, val in node.items():
                kl = str(key).lower()
                if kl in aliases and isinstance(val, (int, float)) and val > 0:
                    if not ent or ent == eid:
                        return float(val)
                found = walk(val, depth + 1)
                if found is not None:
                    return found
        elif isinstance(node, list):
            for item in node[:40]:
                found = walk(item, depth + 1)
                if found is not None:
                    return found
        return None

    for pack in packs.values():
        found = walk(pack)
        if found is not None:
            return found
    return None


def _field_envelope(
    *,
    field: str,
    value: Any,
    entity_id: str,
    provider: str,
    method: str,
    quality: dict[str, Any],
    as_of: str,
    data_class: str = "institutional_seed",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Emit contract field only when quality ≥ framework threshold."""
    if value is None:
        return None
    if not quality.get("accept_for_framework"):
        return None
    return metric_provenance(
        field=field,
        value=value,
        entity_id=entity_id,
        provider=provider,
        method=method,
        validated=True,
        quality=quality.get("score"),
        as_of=as_of,
        data_class=data_class,
        extra=extra,
    )


def build_institutional_pack(
    entity_id: str,
    *,
    entity_name: str | None = None,
    entity_type: str | None = None,
    existing_packs: dict[str, dict[str, Any]] | None = None,
    dcf_inputs: dict[str, Any] | None = None,
    financials: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble the Institutional Evidence Pack for one entity."""
    eid = str(entity_id or "").upper()
    as_of = now_iso()
    current_pe = _current_pe_from_packs(eid, existing_packs)

    hist = produce_historical_intelligence(eid, current_pe=current_pe)
    # If no live current PE, use latest series point (transparent seed).
    if current_pe is None:
        current_pe = hist.get("current_pe")

    peer = produce_peer_intelligence(eid, current_pe=current_pe)
    sector = produce_sector_intelligence(eid)
    bq = produce_business_quality(eid)
    aq = produce_accounting_quality(eid, financials=financials)
    dcf = produce_dcf_intelligence(eid, inputs=dcf_inputs, entity_type=entity_type)

    pe_quality = hist.get("quality") or score_metric(
        value=hist.get("historical_pe"),
        entity_id=eid,
        metric_entity=eid,
        provider="historical_engine",
        as_of=as_of,
        series_n=0,
        validated=False,
    )
    cur_quality = score_metric(
        value=current_pe,
        entity_id=eid,
        metric_entity=eid,
        provider="institutional_seed" if current_pe is not None else "missing",
        as_of=as_of,
        series_n=int((hist.get("pe") or {}).get("analytics", {}).get("n") or 0),
        expected_n=10,
        data_class="institutional_seed",
        validated=current_pe is not None,
        consistency_ok=True,
    )
    pct_quality = score_metric(
        value=hist.get("historical_percentile"),
        entity_id=eid,
        metric_entity=eid,
        provider="historical_analytics",
        as_of=as_of,
        series_n=int((hist.get("pe") or {}).get("analytics", {}).get("n") or 0),
        expected_n=10,
        data_class="institutional_seed",
        validated=hist.get("historical_percentile") is not None,
        consistency_ok=True,
    )
    peer_quality = peer.get("quality") or {"score": 0, "accept_for_framework": False}
    sector_quality = sector.get("quality") or {"score": 0, "accept_for_framework": False}

    validated_fields: dict[str, Any] = {}
    for env in (
        _field_envelope(
            field="current_pe",
            value=current_pe,
            entity_id=eid,
            provider=cur_quality.get("components") and "institutional_evidence" or "missing",
            method="latest_or_dvc",
            quality=cur_quality,
            as_of=as_of,
        ),
        _field_envelope(
            field="historical_pe",
            value=hist.get("historical_pe"),
            entity_id=eid,
            provider="historical_engine",
            method="series_average",
            quality=pe_quality,
            as_of=as_of,
        ),
        _field_envelope(
            field="historical_percentile",
            value=hist.get("historical_percentile"),
            entity_id=eid,
            provider="historical_analytics",
            method="series_percentile",
            quality=pct_quality,
            as_of=as_of,
        ),
        _field_envelope(
            field="peer_pe",
            value=peer.get("peer_pe"),
            entity_id=eid,
            provider="peer_engine",
            method="universe_median",
            quality=peer_quality,
            as_of=as_of,
            extra={"universe": peer.get("peer_universe")},
        ),
        _field_envelope(
            field="sector_pe",
            value=sector.get("sector_pe"),
            entity_id=eid,
            provider="sector_engine",
            method="index_or_peer_median",
            quality=sector_quality,
            as_of=as_of,
        ),
    ):
        if env:
            validated_fields[env["field"]] = env

    # Optional quality metrics for business/financial contracts
    if bq.get("roic") is not None:
        rq = score_metric(
            value=bq["roic"],
            entity_id=eid,
            metric_entity=eid,
            provider="business_quality",
            as_of=as_of,
            series_n=5,
            data_class="institutional_seed",
            validated=True,
        )
        env = _field_envelope(
            field="roic",
            value=bq["roic"],
            entity_id=eid,
            provider="business_quality",
            method="series_latest",
            quality=rq,
            as_of=as_of,
        )
        if env:
            validated_fields["roic"] = env
    if bq.get("margins") is not None:
        mq = score_metric(
            value=bq["margins"],
            entity_id=eid,
            metric_entity=eid,
            provider="business_quality",
            as_of=as_of,
            series_n=5,
            data_class="institutional_seed",
            validated=True,
        )
        env = _field_envelope(
            field="operating_margin",
            value=bq["margins"],
            entity_id=eid,
            provider="business_quality",
            method="series_latest",
            quality=mq,
            as_of=as_of,
        )
        if env:
            validated_fields["operating_margin"] = env
            validated_fields["margins"] = env

    scores = [
        cur_quality,
        pe_quality,
        pct_quality,
        peer_quality,
        sector_quality,
    ]
    evidence_score = pack_score(scores)
    coverage = round(
        len([f for f in ("current_pe", "historical_pe", "historical_percentile", "peer_pe") if f in validated_fields])
        / 4.0,
        4,
    )

    summary = {
        "company": entity_name or eid,
        "entity_id": eid,
        "entity_type": entity_type,
        "current_pe": current_pe,
        "historical_pe": hist.get("historical_pe"),
        "historical_percentile": hist.get("historical_percentile"),
        "peer_median": peer.get("peer_pe"),
        "sector_pe": sector.get("sector_pe"),
        "roic": bq.get("roic"),
        "revenue_growth": (bq.get("summaries") or {}).get("Revenue_Growth", {}).get("latest"),
        "fcf_margin": (bq.get("summaries") or {}).get("FCF", {}).get("latest"),
        "evidence_quality": evidence_score,
        "coverage": round(coverage * 100, 1),
    }

    return {
        "pack_version": PACK_VERSION,
        "entity_id": eid,
        "symbol": eid,
        "entity_name": entity_name or eid,
        "entity_type": entity_type,
        "as_of": as_of,
        "summary": summary,
        "validated": validated_fields,
        # Flat aliases for evidence_validation walk
        "current_pe": current_pe if "current_pe" in validated_fields else None,
        "historical_pe": hist.get("historical_pe") if "historical_pe" in validated_fields else None,
        "historical_percentile": (
            hist.get("historical_percentile") if "historical_percentile" in validated_fields else None
        ),
        "peer_pe": peer.get("peer_pe") if "peer_pe" in validated_fields else None,
        "peer_median_pe": peer.get("peer_pe") if "peer_pe" in validated_fields else None,
        "sector_pe": sector.get("sector_pe") if "sector_pe" in validated_fields else None,
        "roic": bq.get("roic"),
        "operating_margin": bq.get("margins"),
        "revenue_growth": (bq.get("summaries") or {}).get("Revenue_Growth", {}).get("latest"),
        "modules": {
            "historical": hist,
            "peer": peer,
            "sector": sector,
            "business_quality": bq,
            "accounting_quality": aq,
            "dcf": dcf,
        },
        "evidence_score": evidence_score,
        "coverage": coverage,
        "min_framework_score": MIN_FRAMEWORK_SCORE,
        "accepted_for_frameworks": evidence_score >= MIN_FRAMEWORK_SCORE and coverage >= 0.75,
        "insufficient_fields": [
            f
            for f in ("current_pe", "historical_pe", "historical_percentile", "peer_pe")
            if f not in validated_fields
        ],
    }
