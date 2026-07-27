"""Phase 1 — Evidence-First Execution Governance.

Pipeline (no engine replaced, nothing bypassed):

    Question → Classification → Entity Resolution → Evidence Contract
      → Framework Selection → Evidence Validation → Framework Execution
      → Committee → Editorial → Telemetry

Editorial is never allowed before framework execution.
Architecture v1.0.1 LOCKED — soft helper under institutional_reasoning.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from institutional_reasoning.evidence_contracts import (
    CONTRACTS_VERSION,
    EDUCATION_TYPES,
    classify_question,
    clarification_required,
    contract_for,
    forbidden_claim_hits,
    resolve_entities,
)
from institutional_reasoning.evidence_validation import VALIDATION_VERSION, validate_contract

GOVERNANCE_VERSION = "execution-governance-v1.0.0"

# Framework requirement → contract evidence field (single source of truth).
FRAMEWORK_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "rel_val_damodaran": {
        "name": "Damodaran Relative Valuation",
        "author": "Damodaran",
        "version": "1.0.0",
        "requires": ("current_pe", "peer_pe"),
        "produces": ("premium_discount", "confidence"),
        "invalid_for_entity_types": (),
    },
    "hist_multiples": {
        "name": "Historical Multiples Percentile",
        "author": "Institutional",
        "version": "1.0.0",
        "requires": ("current_pe", "historical_pe", "historical_percentile"),
        "produces": ("historical_percentile", "confidence"),
        "invalid_for_entity_types": (),
    },
    "margin_of_safety": {
        "name": "Graham Margin of Safety",
        "author": "Graham",
        "version": "1.0.0",
        "requires": ("current_pe", "historical_pe"),
        "produces": ("mos_pct", "confidence"),
        "invalid_for_entity_types": (),
    },
    "dcf_applicability": {
        "name": "DCF Applicability Test",
        "author": "Damodaran",
        "version": "1.0.0",
        "requires": (),
        "produces": ("applicable", "reason"),
        "invalid_for_entity_types": ("Index",),
        "invalid_for_sectors": ("bank", "insurance", "nbfc"),
    },
    "peer_comparison": {
        "name": "Peer Comparison",
        "author": "Institutional",
        "version": "1.0.0",
        "requires": ("peer_set", "comparable_metrics"),
        "produces": ("peer_rank", "confidence"),
    },
    "business_quality_roic": {
        "name": "ROIC Quality Assessment",
        "author": "Institutional",
        "version": "1.0.0",
        "requires": ("roic", "margins"),
        "produces": ("quality_grade", "confidence"),
    },
}

FRAMEWORKS_BY_TYPE: dict[str, tuple[str, ...]] = {
    "valuation": ("rel_val_damodaran", "hist_multiples", "margin_of_safety", "dcf_applicability"),
    "investment_decision": (
        "rel_val_damodaran",
        "hist_multiples",
        "margin_of_safety",
        "business_quality_roic",
    ),
    "comparison": ("peer_comparison", "rel_val_damodaran"),
    "business_quality": ("business_quality_roic",),
    "financial_quality": (),
    "portfolio": (),
    "macro": (),
    "sector": (),
    "risk": (),
    "forecast": (),
    "education": (),
}


def select_frameworks_for(question_type: str) -> list[dict[str, Any]]:
    ids = FRAMEWORKS_BY_TYPE.get(str(question_type or "").lower(), ())
    out: list[dict[str, Any]] = []
    for fid in ids:
        spec = FRAMEWORK_REQUIREMENTS.get(fid)
        if not spec:
            continue
        out.append({"framework_id": fid, **spec})
    return out


def _execute_framework(
    spec: dict[str, Any],
    *,
    validation: dict[str, Any],
    entity: dict[str, Any] | None,
) -> dict[str, Any]:
    """Structured framework result — never prose."""
    fid = spec["framework_id"]
    observed = set(validation.get("observed") or [])
    rejected = validation.get("rejected") or {}
    entity_type = str((entity or {}).get("entity_type") or "")

    # Applicability first — a rejected method must not be forced.
    invalid_types = tuple(spec.get("invalid_for_entity_types") or ())
    if entity_type and entity_type in invalid_types:
        return {
            "framework_id": fid,
            "name": spec.get("name"),
            "author": spec.get("author"),
            "framework_version": spec.get("version"),
            "status": "not_applicable",
            "outputs": {"applicable": False, "reason": f"{spec.get('name')} invalid for {entity_type}"},
            "required_evidence": list(spec.get("requires") or ()),
            "missing_evidence": [],
            "confidence": None,
        }

    required = tuple(spec.get("requires") or ())
    missing = [r for r in required if r not in observed]
    if missing:
        return {
            "framework_id": fid,
            "name": spec.get("name"),
            "author": spec.get("author"),
            "framework_version": spec.get("version"),
            "status": "insufficient_evidence",
            "outputs": {},
            "required_evidence": list(required),
            "missing_evidence": missing,
            "rejection_reasons": {m: rejected.get(m, "not_found") for m in missing},
            "confidence": None,
        }

    verdict_map = {v["field"]: v for v in validation.get("field_verdicts") or []}
    outputs: dict[str, Any] = {}
    confidence = 0.6 + 0.1 * min(len(required), 3)

    def num(field_name: str) -> float | None:
        v = (verdict_map.get(field_name) or {}).get("value")
        try:
            return float(v)
        except Exception:
            return None

    if fid == "rel_val_damodaran":
        cur, peer = num("current_pe"), num("peer_pe")
        if cur is not None and peer:
            outputs["premium_discount_pct"] = round((cur / peer - 1) * 100, 2)
            outputs["current_pe"] = cur
            outputs["peer_pe"] = peer
    elif fid == "hist_multiples":
        cur, hist, pct = num("current_pe"), num("historical_pe"), num("historical_percentile")
        if cur is not None and hist:
            outputs["vs_history_pct"] = round((cur / hist - 1) * 100, 2)
        if pct is not None:
            outputs["historical_percentile"] = pct
        outputs["current_pe"] = cur
        outputs["historical_pe"] = hist
    elif fid == "margin_of_safety":
        cur, hist = num("current_pe"), num("historical_pe")
        if cur and hist:
            outputs["implied_mos_pct"] = round((hist / cur - 1) * 100, 2)
    elif fid == "dcf_applicability":
        outputs["applicable"] = True
        outputs["reason"] = "cash-flow forecastable entity"
    elif fid == "peer_comparison":
        outputs["peer_set_present"] = True
    elif fid == "business_quality_roic":
        outputs["roic"] = num("roic")

    return {
        "framework_id": fid,
        "name": spec.get("name"),
        "author": spec.get("author"),
        "framework_version": spec.get("version"),
        "status": "executed",
        "outputs": outputs,
        "required_evidence": list(required),
        "missing_evidence": [],
        "confidence": round(min(confidence, 0.95), 2),
        "provenance": validation.get("provenance") or [],
    }


def _committee(results: list[dict[str, Any]], *, question_type: str) -> dict[str, Any]:
    """Committee consumes only framework outputs; cannot invent or override."""
    executed = [r for r in results if r["status"] == "executed"]
    insufficient = [r for r in results if r["status"] == "insufficient_evidence"]
    not_applicable = [r for r in results if r["status"] == "not_applicable"]

    findings: list[str] = []
    disagreements: list[str] = []

    hist = next((r for r in executed if r["framework_id"] == "hist_multiples"), None)
    rel = next((r for r in executed if r["framework_id"] == "rel_val_damodaran"), None)

    if hist:
        pctile = hist["outputs"].get("historical_percentile")
        vs_hist = hist["outputs"].get("vs_history_pct")
        if pctile is not None:
            findings.append(
                f"Historical multiples: {pctile:.0f}th percentile versus own history."
            )
        elif vs_hist is not None:
            findings.append(f"Historical multiples: {vs_hist:+.1f}% versus historical average.")
    if rel:
        prem = rel["outputs"].get("premium_discount_pct")
        if prem is not None:
            findings.append(
                f"Relative valuation: {prem:+.1f}% versus peer multiple "
                f"({rel['outputs'].get('current_pe')} vs {rel['outputs'].get('peer_pe')})."
            )

    # Explicit disagreement handling (Test 5)
    if hist and rel:
        h_rich = (hist["outputs"].get("historical_percentile") or 0) >= 70 or (
            hist["outputs"].get("vs_history_pct") or 0
        ) > 10
        r_cheap = (rel["outputs"].get("premium_discount_pct") or 0) < -5
        h_cheap = (hist["outputs"].get("historical_percentile") or 100) <= 30 or (
            hist["outputs"].get("vs_history_pct") or 0
        ) < -10
        r_rich = (rel["outputs"].get("premium_discount_pct") or 0) > 5
        if (h_rich and r_cheap) or (h_cheap and r_rich):
            disagreements.append(
                "Frameworks disagree: own-history and peer-relative valuation point in "
                "opposite directions. Both readings are reported; neither is suppressed."
            )

    for r in insufficient:
        findings.append(
            f"{r['name']}: insufficient evidence (missing {', '.join(r['missing_evidence'][:4])})."
        )
    for r in not_applicable:
        findings.append(f"{r['name']}: not applicable — {r['outputs'].get('reason')}.")

    contract = contract_for(question_type)
    can_conclude = bool(executed) and not insufficient
    partial = bool(executed) and bool(insufficient)

    if not executed:
        conclusion = (
            "Insufficient evidence: no required framework could execute. "
            "No valuation, quality or decision conclusion is issued."
        )
        stance = "Insufficient evidence"
    elif partial:
        missing_names = sorted({m for r in insufficient for m in r["missing_evidence"]})
        conclusion = (
            "Partial evidence only. "
            + " ".join(findings)
            + f" Missing: {', '.join(missing_names[:6])}. "
            "A full conclusion is withheld."
        )
        stance = "Partial evidence"
    else:
        conclusion = " ".join(findings) or "Frameworks executed."
        stance = "Evidence-supported"

    if disagreements:
        conclusion = conclusion + " " + " ".join(disagreements)

    return {
        "stance": stance,
        "conclusion": conclusion,
        "findings": findings,
        "disagreements": disagreements,
        "executed_count": len(executed),
        "insufficient_count": len(insufficient),
        "not_applicable_count": len(not_applicable),
        "can_conclude": can_conclude,
        "forbidden_claims": list(contract.forbidden_claims),
    }


def govern_answer(
    question: str,
    *,
    ticker_hint: str | None = None,
    entity_resolution_pack: dict[str, Any] | None = None,
    packs: dict[str, dict[str, Any]] | None = None,
    academy: dict[str, Any] | None = None,
    build_institutional_evidence: bool = True,
) -> dict[str, Any]:
    """Run the full governed pipeline; returns structured governance record."""
    started = time.time()
    run_id = f"fer_{uuid.uuid4().hex[:16]}"
    classification = classify_question(question)
    qtype = classification["question_type"]
    contract = contract_for(qtype)

    # Education path bypasses evidence contract + frameworks + committee.
    if qtype in EDUCATION_TYPES:
        return {
            "run_id": run_id,
            "governance_version": GOVERNANCE_VERSION,
            "question": str(question or "")[:500],
            "question_type": qtype,
            "classification": classification,
            "path": "education",
            "entity": None,
            "contract": contract.to_dict(),
            "validation": None,
            "frameworks": [],
            "committee": None,
            "narrative_allowed": True,
            "editorial_mode": "explain_academy",
            "academy_available": bool(academy),
            "execution_ms": int((time.time() - started) * 1000),
        }

    entities = resolve_entities(
        question,
        ticker_hint=ticker_hint,
        entity_resolution_pack=entity_resolution_pack,
    )
    clarify = clarification_required(classification, entities)
    if clarify.get("required"):
        return {
            "run_id": run_id,
            "governance_version": GOVERNANCE_VERSION,
            "question": str(question or "")[:500],
            "question_type": qtype,
            "classification": classification,
            "path": "clarification",
            "entity": entities.get("primary"),
            "entity_resolution": entities,
            "contract": contract.to_dict(),
            "validation": None,
            "frameworks": [],
            "committee": {
                "stance": "Clarification required",
                "conclusion": clarify.get("message"),
                "can_conclude": False,
            },
            "narrative_allowed": False,
            "editorial_mode": "clarify_only",
            "clarification": clarify,
            "execution_ms": int((time.time() - started) * 1000),
        }

    primary = entities.get("primary") or {}
    entity_id = primary.get("entity_id")

    # Phase 2 — Institutional Evidence Pack binding.
    # Frameworks consume validated packs; they never fetch.
    packs = dict(packs or {})
    if build_institutional_evidence:
        try:
            from institutional_reasoning.institutional_evidence.production import (
                package_for_governance,
            )

            ie_pkg = package_for_governance(
                entity_id,
                entity_name=primary.get("entity_name"),
                entity_type=primary.get("entity_type"),
                existing_packs=packs,
            )
            if ie_pkg.get("found"):
                packs["institutional_evidence"] = ie_pkg
        except Exception:
            pass

    validation = validate_contract(
        question_type=qtype,
        entity_id=entity_id,
        packs=packs,
    )
    specs = select_frameworks_for(qtype)
    results = [
        _execute_framework(spec, validation=validation, entity=primary) for spec in specs
    ]
    committee = _committee(results, question_type=qtype)

    executed_any = any(r["status"] == "executed" for r in results)
    # Contract completeness governs narrative permission for gated types.
    narrative_allowed = bool(executed_any and validation.get("complete"))
    if not specs:
        # Types without executable frameworks yet: allow narrative only with contract coverage
        narrative_allowed = bool(validation.get("complete"))

    return {
        "run_id": run_id,
        "governance_version": GOVERNANCE_VERSION,
        "question": str(question or "")[:500],
        "question_type": qtype,
        "classification": classification,
        "path": "research",
        "entity": primary or None,
        "entity_resolution": entities,
        "contract": contract.to_dict(),
        "contract_version": CONTRACTS_VERSION,
        "validation_version": VALIDATION_VERSION,
        "validation": validation,
        "frameworks": results,
        "committee": committee,
        "narrative_allowed": narrative_allowed,
        "editorial_mode": "explain_only" if narrative_allowed else "report_insufficient",
        "missing_evidence": validation.get("missing") or [],
        "institutional_evidence": (packs.get("institutional_evidence") or {}),
        "execution_ms": int((time.time() - started) * 1000),
    }


def governed_executive(record: dict[str, Any]) -> str:
    """Executive text derived only from framework/committee outputs."""
    committee = record.get("committee") or {}
    if record.get("path") == "clarification":
        return str(committee.get("conclusion") or "Clarification required.")
    if record.get("path") == "education":
        return ""
    return str(committee.get("conclusion") or "Insufficient evidence.")


def enforce_editorial(
    *,
    text: str | None,
    record: dict[str, Any],
) -> dict[str, Any]:
    """Editorial may explain, never invent. Strip unsupported forbidden claims."""
    if record.get("path") == "education":
        return {"text": text, "blocked": False, "violations": []}
    qtype = str(record.get("question_type") or "")
    allowed = bool(record.get("narrative_allowed"))
    violations = forbidden_claim_hits(text or "", qtype)
    if allowed or not violations:
        return {"text": text, "blocked": False, "violations": violations}
    return {
        "text": governed_executive(record),
        "blocked": True,
        "violations": violations,
        "reason": "forbidden_claim_without_executed_framework",
    }


def telemetry_rows(record: dict[str, Any], *, answer_id: str | None = None) -> list[dict[str, Any]]:
    """One immutable row per framework attempt (never updated)."""
    rows: list[dict[str, Any]] = []
    validation = record.get("validation") or {}
    entity = record.get("entity") or {}
    committee = record.get("committee") or {}
    frameworks = record.get("frameworks") or []
    base = {
        "run_id": record.get("run_id"),
        "question": record.get("question"),
        "question_type": record.get("question_type"),
        "question_confidence": (record.get("classification") or {}).get("confidence"),
        "entity_id": entity.get("entity_id"),
        "entity_name": entity.get("entity_name"),
        "entity_type": entity.get("entity_type"),
        "entity_confidence": entity.get("confidence"),
        "evidence_contract_version": record.get("contract_version"),
        "validation_version": record.get("validation_version"),
        "evidence_provenance": validation.get("provenance") or [],
        "committee_stance": committee.get("stance"),
        "committee_conclusion": (committee.get("conclusion") or "")[:2000],
        "narrative_allowed": record.get("narrative_allowed"),
        "answer_id": answer_id,
        "execution_ms": record.get("execution_ms"),
        "governance_version": record.get("governance_version"),
        "path": record.get("path"),
    }
    if not frameworks:
        rows.append(
            {
                **base,
                "framework_id": None,
                "framework_name": None,
                "framework_version": None,
                "required_evidence": validation.get("required") or [],
                "observed_evidence": validation.get("observed") or [],
                "missing_evidence": validation.get("missing") or [],
                "validation_result": validation or {},
                "execution_status": record.get("path") or "no_frameworks",
                "failure_reason": (record.get("clarification") or {}).get("reason"),
                "confidence": None,
                "outputs": {},
            }
        )
        return rows
    for fw in frameworks:
        rows.append(
            {
                **base,
                "framework_id": fw.get("framework_id"),
                "framework_name": fw.get("name"),
                "framework_version": fw.get("framework_version"),
                "required_evidence": fw.get("required_evidence") or [],
                "observed_evidence": validation.get("observed") or [],
                "missing_evidence": fw.get("missing_evidence") or [],
                "validation_result": {
                    "coverage": validation.get("coverage"),
                    "complete": validation.get("complete"),
                    "rejected": validation.get("rejected") or {},
                    "field_verdicts": validation.get("field_verdicts") or [],
                },
                "execution_status": fw.get("status"),
                "failure_reason": (
                    ", ".join(f"{k}:{v}" for k, v in (fw.get("rejection_reasons") or {}).items())
                    or (fw.get("outputs") or {}).get("reason")
                ),
                "confidence": fw.get("confidence"),
                "outputs": fw.get("outputs") or {},
            }
        )
    return rows
