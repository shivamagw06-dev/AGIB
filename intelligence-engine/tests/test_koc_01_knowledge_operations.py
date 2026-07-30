"""KOC-01 — Institutional Knowledge Operations Center tests."""

from __future__ import annotations

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_operations.schema import (
    DOCUMENT_UPLOAD_TYPES,
    KOC_VERSION,
    KOC_WORKSTREAM_ID,
    MISSION,
)
from knowledge_operations.production import (
    get_desk,
    get_missing_inbox,
    get_status,
    health,
    soft_slice_mission_control,
    upload_knowledge,
    get_audit,
    run_action,
)


def test_koc_identity():
    st = get_status()
    assert st["workstream_id"] == "KOC-01"
    assert KOC_VERSION.startswith("koc-01")
    assert health()["admin_only"] is True
    assert "institutional knowledge" in MISSION.lower()
    assert "annual_report" in DOCUMENT_UPLOAD_TYPES


def test_missing_inbox_prioritized():
    inbox = get_missing_inbox(scope="TOP20", limit=20)
    assert inbox["ok"] is True
    assert "Highest-Impact" in inbox["title"]
    assert inbox["workflow"].startswith("Clear the inbox")
    items = inbox.get("items") or []
    if len(items) >= 2:
        ranks = [i.get("priority_rank", 9) for i in items]
        assert ranks == sorted(ranks)


def test_desk_has_control_room_surfaces():
    desk = get_desk(scope="TOP20")
    assert desk["ok"] is True
    assert desk["workstream_id"] == KOC_WORKSTREAM_ID
    assert "kpis" in desk
    assert "missing_inbox" in desk
    assert "coverage_table" in desk
    assert "ingestion_timeline" in desk
    assert "daily_summary" in desk
    assert "collector_health" in desk
    assert "coverage_heatmap" in desk
    assert desk["security"]["never_overwrite"] is True
    assert desk["security"]["admin_only"] is True


def test_upload_is_append_only_and_audited():
    payload = base64.b64encode(b"%PDF-1.4 koc test document").decode("ascii")
    res = upload_knowledge(
        ticker="RELIANCE",
        document_type="investor_presentation",
        filename="reliance_q1_deck.pdf",
        content_base64=payload,
        actor="test_admin@agi.local",
    )
    assert res["ok"] is True
    assert res["upload"]["immutable"] is True
    assert res["upload"]["sha256"]
    assert res["audit"]["action"] == "upload_knowledge"
    assert res["audit"]["actor"] == "test_admin@agi.local"
    # Re-upload same bytes must not error (immutable path by hash)
    res2 = upload_knowledge(
        ticker="RELIANCE",
        document_type="investor_presentation",
        filename="reliance_q1_deck.pdf",
        content_base64=payload,
        actor="test_admin@agi.local",
    )
    assert res2["ok"] is True
    assert res2["upload"]["sha256"] == res["upload"]["sha256"]
    aud = get_audit(limit=10, ticker="RELIANCE")
    assert aud["count"] >= 1


def test_action_is_audited():
    out = run_action("run_research_readiness", ticker="RELIANCE", actor="test_admin")
    assert "audit" in out
    assert out["audit"]["action"] == "run_research_readiness"


def test_mission_control_soft_slice():
    slice_ = soft_slice_mission_control()
    assert slice_.get("status") == "ok"
    assert slice_["board"] == "Knowledge Operations"
    assert "missing_inbox_count" in slice_
