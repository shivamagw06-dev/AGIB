"""Phase 2 programme registry — must not claim to replace Baseline v1.0."""

from __future__ import annotations

from pathlib import Path

from phase2_investment_intelligence.production import health, programme
from phase2_investment_intelligence.schema import FROZEN_BASELINE_LOCKS, SUCCESS_CRITERIA
from phase2_investment_intelligence.workstreams import WORKSTREAMS, workstream_board


def test_phase2_health_respects_baseline_freeze():
    h = health()
    assert h["baseline"]["status"] == "FROZEN"
    assert h["replaces_baseline"] is False
    assert h["extends_intelligence"] is True
    assert FROZEN_BASELINE_LOCKS["decision_engine_contracts"] == "frozen"
    assert FROZEN_BASELINE_LOCKS["institutional_gate"] == "frozen"
    assert FROZEN_BASELINE_LOCKS["institutional_acceptance_test"] == "frozen"
    assert "unknown_drift_zero" in SUCCESS_CRITERIA
    assert "iat_continues_to_pass" in SUCCESS_CRITERIA


def test_workstreams_cover_p21_to_p26():
    ids = {w["id"] for w in WORKSTREAMS}
    assert ids == {"P2.1", "P2.2", "P2.3", "P2.4", "P2.5", "P2.6"}
    board = workstream_board()
    assert board["recommended_first_build"][0] == "P2.6"
    assert "P2.1" in board["recommended_first_build"]


def test_programme_doc_exists():
    root = Path(__file__).resolve().parents[2]
    doc = root / "docs" / "PHASE2_INSTITUTIONAL_INVESTMENT_INTELLIGENCE_PROGRAMME.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "Institutional Investment Intelligence Programme" in text
    assert "P2.1 Earnings Intelligence" in text
    assert "AGIB Institutional Baseline v1.0" in text
    assert "Do NOT modify" in text or "MUST NOT be modified" in text or "Do **not**" in text


def test_programme_pipeline_ends_with_iat():
    pack = programme()
    assert pack["pipeline"][-1] == "Institutional Acceptance Test"
    assert "redesign_decision_engine" in pack["prohibited"]
