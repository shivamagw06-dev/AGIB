"""Baseline v1.0 IAT Protocol — Parts A–G."""

from __future__ import annotations

from pathlib import Path

from institutional_evaluation_lab.iat.company_types import evaluate_company_types
from institutional_evaluation_lab.iat.production import health, protocol
from institutional_evaluation_lab.iat.protocol import PROTOCOL_VERSION, format_protocol_text
from institutional_evaluation_lab.iat.questions import QUESTION_BATTERY


def test_protocol_parts_a_through_g():
    pack = protocol()
    assert pack["protocol_version"] == PROTOCOL_VERSION
    assert set(pack["parts"]) == {"A", "B", "C", "D", "E", "F", "G"}
    assert pack["status"]["A"] == "PASS"
    assert pack["status"]["B"] == "PASS"
    assert pack["parts"]["A"]["actual_n"] == 200
    assert pack["parts"]["G"]["automated"] is False
    assert "human review" in (pack["parts"]["G"]["note"] or "").lower()


def test_question_battery_six_institutional_tests():
    assert len(QUESTION_BATTERY) == 6
    prompts = [q["prompt"] for q in QUESTION_BATTERY]
    assert "Can I buy this company today?" in prompts
    assert "Why is the gate failing?" in prompts
    assert not any(p.strip().lower() == "should i buy?" for p in prompts)


def test_company_types_include_difficult_cases():
    b = evaluate_company_types()
    assert b["status"] == "PASS"
    assert b["n_types_present"] == 16
    assert b["coverage"]["loss_making_growth"]["n"] >= 1
    assert b["coverage"]["consumer_internet"]["n"] >= 1
    assert b["coverage"]["psu_bank"]["n"] >= 1
    # No Capital Goods false-positive as IT
    it_examples = b["coverage"]["it"]["examples"]
    assert "ULTRACEMCO" not in it_examples
    assert "LT" not in it_examples or "TCS" in it_examples  # LT must not be sole IT exemplar via bug


def test_it_classifier_excludes_capital_goods():
    from institutional_evaluation_lab.iat.company_types import _classify_row

    tags = _classify_row({"ticker": "ULTRACEMCO", "sector": "Capital Goods", "name": "UltraTech", "profile": ""})
    assert "it" not in tags


def test_protocol_doc_exists():
    root = Path(__file__).resolve().parents[2]
    doc = root / "docs" / "AGIB_IAT_BASELINE_V1_PROTOCOL.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "Part G" in text
    assert "GOV-008" in text


def test_health_exposes_protocol():
    h = health()
    assert h["protocol_parts"] == ["A", "B", "C", "D", "E", "F", "G"]
    text = format_protocol_text()
    assert "Part A — Company Coverage" in text
    assert "Part G — Human review" in text
