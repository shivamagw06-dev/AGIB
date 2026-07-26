"""Business Analyst historical memory — views, accuracy, lessons."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _as_confidence(value: Any) -> float:
    if isinstance(value, dict):
        for key in ("overall", "evidence", "knowledge"):
            if value.get(key) is not None:
                try:
                    return float(value.get(key))
                except Exception:
                    continue
        return 0.0
    try:
        return float(value or 0.0)
    except Exception:
        return 0.0


def extract_prior_view(memory_snapshot: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    snap = memory_snapshot if isinstance(memory_snapshot, dict) else {}
    has_prior = bool(snap)
    return {
        "has_prior": has_prior,
        "prior_stance": (snap.get("prior_stance") or snap.get("stance") or "") if has_prior else "",
        "prior_quality_grade": snap.get("prior_quality_grade") or snap.get("quality_grade"),
        "prior_moat_durability": snap.get("prior_moat_durability") or snap.get("moat_durability"),
        "prior_confidence": _as_confidence(snap.get("prior_confidence") if "prior_confidence" in snap else snap.get("confidence")),
        "prediction_history": list(snap.get("prediction_history") or [])[:8],
        "accuracy": snap.get("accuracy"),
        "lessons_learned": list(snap.get("lessons_learned") or [])[:6],
    }


def compare_views(
    *,
    current_stance: str,
    current_quality_grade: str,
    current_moat_durability: str,
    current_confidence: float,
    prior: Dict[str, Any],
) -> Dict[str, Any]:
    if not prior.get("has_prior"):
        return {
            "what_changed": [],
            "view_stable": True,
            "confidence_delta": 0.0,
            "prior_stance": None,
            "current_stance": current_stance,
        }

    changes: List[str] = []
    prior_stance = str(prior.get("prior_stance") or "")
    if current_stance and prior_stance and current_stance != prior_stance:
        changes.append(f"Stance shifted from {prior_stance} to {current_stance}")

    prior_grade = prior.get("prior_quality_grade")
    if prior_grade and current_quality_grade and str(prior_grade) != str(current_quality_grade):
        changes.append(f"Business quality grade moved from {prior_grade} to {current_quality_grade}")

    prior_moat = prior.get("prior_moat_durability")
    if prior_moat and current_moat_durability and str(prior_moat) != str(current_moat_durability):
        changes.append(f"Moat durability reassessment: {prior_moat} → {current_moat_durability}")

    prior_conf = float(prior.get("prior_confidence") or 0.0)
    delta = round(float(current_confidence or 0.0) - prior_conf, 3)
    if abs(delta) >= 0.08:
        direction = "up" if delta > 0 else "down"
        changes.append(f"Confidence {direction} by {abs(delta):.2f}")

    return {
        "what_changed": changes,
        "view_stable": len(changes) == 0,
        "confidence_delta": delta,
        "prior_stance": prior_stance or None,
        "current_stance": current_stance,
    }


def build_memory_record(
    *,
    company: str,
    stance: str,
    quality_grade: str,
    moat_durability: str,
    confidence: float,
    opinion_summary: str,
    comparison: Dict[str, Any],
    prior: Dict[str, Any],
) -> Dict[str, Any]:
    history = list(prior.get("prediction_history") or [])
    history.append(
        {
            "company": company,
            "stance": stance,
            "quality_grade": quality_grade,
            "moat_durability": moat_durability,
            "confidence": confidence,
        }
    )
    lessons = list(prior.get("lessons_learned") or [])
    if comparison.get("what_changed"):
        lessons.append(
            f"Updated view on {company or 'subject'}: {'; '.join(comparison.get('what_changed')[:2])}"
        )
    return {
        "stance": stance,
        "quality_grade": quality_grade,
        "moat_durability": moat_durability,
        "confidence": confidence,
        "opinion_summary": opinion_summary,
        "prediction_history": history[-12:],
        "accuracy": prior.get("accuracy"),
        "changes_in_view": list(comparison.get("what_changed") or []),
        "lessons_learned": lessons[-8:],
    }
