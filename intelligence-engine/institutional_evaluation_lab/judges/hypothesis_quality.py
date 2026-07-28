"""Hypothesis Quality Score (HQS) — independent IEL metric for Phase 4.

Does NOT change CIO / overall pass weights. Measures the hypothesis layer:
  * plausibility of generated hypotheses
  * coverage of major explanation classes (when cues match)
  * avoidance of unsupported / fabricated hypotheses
  * retention of contradictory / rejected hypotheses
  * preferred hypothesis aligns with strongest weighted evidence

Deterministic only — no LLM grading.
"""

from __future__ import annotations

from typing import Any

HQS_VERSION = "hqs-v1.0.0"

# Component weights within HQS (sum = 1.0)
HQS_COMPONENT_WEIGHTS: dict[str, float] = {
    "plausibility": 0.25,
    "coverage": 0.20,
    "unsupported_avoided": 0.25,
    "contradiction_retention": 0.15,
    "preferred_evidence_alignment": 0.15,
}


def _hyp_pack(probe: dict[str, Any]) -> dict[str, Any]:
    return dict(probe.get("hypothesis_generation") or {})


def _iew_pack(probe: dict[str, Any]) -> dict[str, Any]:
    return dict(probe.get("evidence_weighting") or {})


def _score_plausibility(pack: dict[str, Any]) -> tuple[float, str]:
    if pack.get("insufficient_evidence"):
        # Correct institutional refusal is plausible
        if str((pack.get("hypotheses") or [{}])[0].get("hypothesis") or "").lower().startswith(
            "insufficient"
        ):
            return 100.0, "insufficient_evidence_gate"
        return 40.0, "insufficient_without_gate_label"
    hyps = [h for h in (pack.get("hypotheses") or []) if isinstance(h, dict)]
    n = len(hyps)
    if n == 0:
        return 0.0, "no_hypotheses"
    if pack.get("fabricated") is True or pack.get("llm_used") is True:
        return 0.0, "fabricated_or_llm"
    # 2–5 is the institutional band
    if 2 <= n <= 5:
        base = 100.0
    elif n == 1:
        base = 55.0
    else:
        base = 70.0
    # All must have text + category
    structured = all(h.get("hypothesis") and h.get("category") for h in hyps)
    if not structured:
        base *= 0.5
        return base, "missing_structure"
    return base, "ok"


def _score_coverage(question: dict[str, Any], pack: dict[str, Any]) -> tuple[float, str]:
    if pack.get("insufficient_evidence"):
        return 85.0, "coverage_n_a_insufficient"
    q = str(question.get("question") or "").lower()
    hyps = pack.get("hypotheses") or []
    keys = {str(h.get("template_key") or "") for h in hyps if isinstance(h, dict)}
    families = set(pack.get("families") or [])

    # Family-specific expected coverage floors (soft)
    expected_keys: list[str] = []
    if "margin" in q:
        expected_keys = ["input_cost_inflation", "pricing_pressure", "demand_weakness"]
        families.add("margin_decline")
    elif "after earnings" in q or "stock fell" in q or "shares fell" in q:
        expected_keys = ["guidance_disappointment", "valuation_rich", "margin_concern"]
    elif "premium" in q:
        expected_keys = ["higher_roe", "asset_quality", "deposit_franchise"]

    if not expected_keys:
        # Generic: at least 2 distinct categories
        cats = {str(h.get("category")) for h in hyps if isinstance(h, dict)}
        score = 100.0 if len(cats) >= 2 or len(hyps) >= 2 else 60.0
        return score, "generic_category_spread"

    hits = sum(1 for k in expected_keys if k in keys)
    rate = hits / max(1, len(expected_keys))
    # Credit family match even if template keys differ slightly
    if rate < 0.34 and families:
        rate = max(rate, 0.5)
    return round(100.0 * rate, 1), f"coverage_hits={hits}/{len(expected_keys)}"


def _score_unsupported_avoided(pack: dict[str, Any]) -> tuple[float, str]:
    if pack.get("fabricated") is True:
        return 0.0, "fabricated"
    if pack.get("llm_used") is True:
        return 0.0, "llm_used"
    hyps = [h for h in (pack.get("hypotheses") or []) if isinstance(h, dict)]
    if pack.get("insufficient_evidence"):
        return 100.0, "refused_to_invent"
    # Every non-insufficient hypothesis must cite supporting evidence ids
    unsupported = [
        h
        for h in hyps
        if h.get("status") != "InsufficientEvidence" and not (h.get("supporting_evidence") or [])
    ]
    if unsupported:
        return 20.0, f"unsupported_count={len(unsupported)}"
    return 100.0, "all_supported"


def _score_contradiction_retention(pack: dict[str, Any], iew: dict[str, Any]) -> tuple[float, str]:
    hyps = [h for h in (pack.get("hypotheses") or []) if isinstance(h, dict)]
    if pack.get("insufficient_evidence"):
        return 90.0, "n_a_insufficient"
    # Rejected retained
    rejected = [h for h in hyps if h.get("status") == "Rejected"]
    has_conflict_field = any(h.get("contradicting_evidence") for h in hyps)
    iew_conflicts = list(iew.get("conflicts") or [])
    score = 70.0
    notes: list[str] = []
    if rejected:
        # Must explain
        explained = all((h.get("reason") or h.get("reject_reason")) for h in rejected)
        score += 15.0 if explained else -20.0
        notes.append(f"rejected_retained={len(rejected)}")
    else:
        notes.append("no_rejected")
        score += 5.0
    if has_conflict_field:
        score += 15.0
        notes.append("conflict_evidence_linked")
    elif iew_conflicts:
        # IEW saw conflicts but IHG linked none — soft penalty
        score -= 10.0
        notes.append("iew_conflicts_unlinked")
    else:
        score += 10.0
        notes.append("no_conflicts_to_retain")
    return max(0.0, min(100.0, score)), ",".join(notes)


def _score_preferred_alignment(pack: dict[str, Any]) -> tuple[float, str]:
    hyps = [h for h in (pack.get("hypotheses") or []) if isinstance(h, dict)]
    if pack.get("insufficient_evidence") or not hyps:
        return 90.0, "n_a"
    if pack.get("forced_single_winner") is True:
        return 40.0, "forced_single_winner_violation"
    active = [h for h in hyps if h.get("status") not in {"Rejected", "InsufficientEvidence"}]
    pool = active or hyps
    best = max(pool, key=lambda h: float(h.get("overall_score") or 0.0))
    preferred = [h for h in hyps if h.get("status") in {"Preferred", "Contested"}]
    if not preferred:
        # All rejected — alignment N/A
        return 75.0, "no_preferred"
    # Top preferred/contested should be among strongest overall scores
    top_ids = {
        h.get("hypothesis_id")
        for h in sorted(pool, key=lambda h: -float(h.get("overall_score") or 0))[: max(1, len(preferred))]
    }
    aligned = all(h.get("hypothesis_id") in top_ids or float(h.get("overall_score") or 0) >= float(best.get("overall_score") or 0) - 1e-6 for h in preferred)
    # Plural contested with close shares is good
    if pack.get("outcome") == "contested" and pack.get("plural"):
        return (100.0 if aligned else 70.0), "contested_plural"
    if pack.get("outcome") == "preferred":
        pref = next((h for h in hyps if h.get("status") == "Preferred"), None)
        if pref and pref.get("hypothesis_id") == best.get("hypothesis_id"):
            return 100.0, "preferred_matches_strongest"
        return 55.0, "preferred_misaligned"
    return (90.0 if aligned else 60.0), "aligned" if aligned else "misaligned"


def judge_hypothesis_quality(question: dict[str, Any], probe: dict[str, Any]) -> dict[str, Any]:
    """Return HQS judgment. Independent of DIMENSION_WEIGHTS / CIO score."""
    pack = _hyp_pack(probe)
    iew = _iew_pack(probe)

    if not pack:
        # Soft path without IHG — neutral N/A (does not fail suite)
        return {
            "dimension": "hypothesis_quality",
            "passed": True,
            "score": None,
            "hqs": None,
            "n_a": True,
            "hqs_version": HQS_VERSION,
            "independent_of_cio": True,
            "root_cause": None,
            "note": "hypothesis_generation absent from probe",
        }

    components: dict[str, Any] = {}
    p_score, p_note = _score_plausibility(pack)
    c_score, c_note = _score_coverage(question, pack)
    u_score, u_note = _score_unsupported_avoided(pack)
    r_score, r_note = _score_contradiction_retention(pack, iew)
    a_score, a_note = _score_preferred_alignment(pack)

    components["plausibility"] = {"score": p_score, "note": p_note}
    components["coverage"] = {"score": c_score, "note": c_note}
    components["unsupported_avoided"] = {"score": u_score, "note": u_note}
    components["contradiction_retention"] = {"score": r_score, "note": r_note}
    components["preferred_evidence_alignment"] = {"score": a_score, "note": a_note}

    hqs = 0.0
    for name, w in HQS_COMPONENT_WEIGHTS.items():
        hqs += w * float(components[name]["score"])
    hqs = round(hqs, 2)
    passed = hqs >= 70.0

    root = None
    if not passed:
        # Pick weakest component
        worst = min(components.items(), key=lambda kv: float(kv[1]["score"]))
        root = f"hqs_weak_{worst[0]}"

    return {
        "dimension": "hypothesis_quality",
        "passed": passed,
        "score": hqs,  # for row dimensions display
        "hqs": hqs,
        "components": components,
        "n_hypotheses": pack.get("n_hypotheses"),
        "outcome": pack.get("outcome"),
        "plural": pack.get("plural"),
        "forced_single_winner": bool(pack.get("forced_single_winner")),
        "insufficient_evidence": bool(pack.get("insufficient_evidence")),
        "hqs_version": HQS_VERSION,
        "independent_of_cio": True,
        "n_a": False,
        "root_cause": root,
    }


def aggregate_hqs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Suite-level HQS summary from scored rows (reads dimensions.hypothesis_quality)."""
    scores: list[float] = []
    n_na = 0
    n_pass = 0
    n_fail = 0
    outcomes: dict[str, int] = {}
    for r in rows:
        j = ((r.get("dimensions") or {}).get("hypothesis_quality")) or r.get("hypothesis_quality") or {}
        if j.get("n_a") or j.get("hqs") is None and j.get("score") is None:
            n_na += 1
            continue
        s = j.get("hqs")
        if s is None:
            s = j.get("score")
        if s is None:
            n_na += 1
            continue
        scores.append(float(s))
        if j.get("passed"):
            n_pass += 1
        else:
            n_fail += 1
        oc = str(j.get("outcome") or "unknown")
        outcomes[oc] = outcomes.get(oc, 0) + 1
    n = len(scores)
    return {
        "hqs_version": HQS_VERSION,
        "independent_of_cio": True,
        "n_scored": n,
        "n_na": n_na,
        "mean_hqs": round(sum(scores) / n, 2) if n else None,
        "pass_pct": round(100.0 * n_pass / n, 2) if n else None,
        "passed": n_pass,
        "failed": n_fail,
        "outcomes": outcomes,
        "note": "HQS does not affect IEL overall / CIO score weights",
    }
