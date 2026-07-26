"""Smoke tests for Finance Academy Validation Audit harness."""

from __future__ import annotations

from academy.audit.harness import run_audit, static_engine_import_audit, write_report


def test_static_engine_import_audit_finds_no_production_wiring():
    audit = static_engine_import_audit()
    assert audit["verdict"] == "NO_LOCKED_ENGINE_IMPORTS_ACADEMY"
    assert "ve" in audit["engines_with_zero_academy_imports"]
    assert "ui" in audit["engines_with_zero_academy_imports"]
    assert "irp" in audit["engines_with_zero_academy_imports"]


def test_run_audit_fails_success_criteria_until_wired(tmp_path):
    evidence = run_audit()
    assert evidence["inventory"]["concept_count"] >= 100
    assert evidence["exam_suite"]["passed"] == evidence["exam_suite"]["total"]
    assert evidence["final_verdict"]["overall_pass"] is False
    assert evidence["final_verdict"]["success_criteria"]["engines_consume_rather_than_bypass"] is False
    assert evidence["scores"]["knowledge_extraction"] == 100
    assert evidence["scores"]["knowledge_usage"] < 50
    assert len(evidence["concept_usage_table"]) == evidence["inventory"]["concept_count"]
    assert evidence["graph_traversal"]["production_traversal_by_ask_agi"] is False
    assert evidence["ab_test"]["material_change_in_ask_agi"] is False

    paths = write_report(evidence, tmp_path)
    md = paths["markdown"].read_text()
    assert "Part 1 — Knowledge usage" in md
    assert "Part 6 — Retrieval audit" in md
    assert "FAIL for production deployment" in md
