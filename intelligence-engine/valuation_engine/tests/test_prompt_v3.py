"""UVE Institutional System Prompt V3 — institutional valuation voice."""

from __future__ import annotations

from valuation_engine.prompt import (
    OUTPUT_SECTIONS,
    UVE_INSTITUTIONAL_SYSTEM_PROMPT_V3,
    UVE_PROMPT_VERSION,
    VALUATION_FRAMEWORKS,
    is_valuation_question,
    prompt_catalog,
    system_prompt,
)


def test_prompt_catalog_surface():
    cat = prompt_catalog()
    assert cat["ok"] is True
    assert cat["version"] == UVE_PROMPT_VERSION
    assert cat["prompt_id"] == "uve_institutional_system_prompt_v3"
    assert len(cat["output_sections"]) == 25
    assert "banks" in cat["valuation_frameworks"]


def test_system_prompt_is_uve_v3():
    assert system_prompt() == UVE_INSTITUTIONAL_SYSTEM_PROMPT_V3
    assert "Unified Valuation Engine" in system_prompt()
    assert len(system_prompt()) > 2000


def test_no_buy_sell_or_price_targets():
    low = system_prompt().lower()
    assert "never recommend buy or sell" in low
    assert "never predict future prices" in low
    assert "never issue buy or sell" in low


def test_output_sections_match_spec():
    assert OUTPUT_SECTIONS[0] == "Executive Summary"
    assert OUTPUT_SECTIONS[-1] == "Suggested Follow-up Questions"
    assert "Plain English Explanation" in OUTPUT_SECTIONS
    assert "Risk Matrix" in OUTPUT_SECTIONS
    assert "Scenario Analysis" in OUTPUT_SECTIONS


def test_valuation_frameworks_banks_use_pb():
    assert VALUATION_FRAMEWORKS["banks"]["primary"] == "Price-to-Book"
    assert "deployable" in VALUATION_FRAMEWORKS["banks"]["note"].lower()


def test_is_valuation_question_detection():
    assert is_valuation_question("Is Reliance Industries currently expensive or cheap?")
    assert is_valuation_question("Explain HDFC Bank P/B versus history and peers")
    assert not is_valuation_question("What is the RBI repo rate outlook?")


def test_institutional_reasoning_selects_uve_for_valuation():
    from institutional_reasoning.production import system_prompt_for

    uve = system_prompt_for(query="Is Infosys expensive versus peers and history?", family_id=None)
    assert "Unified Valuation Engine" in uve
    generic = system_prompt_for(query="What is the RBI repo rate?", family_id="macro")
    assert "Agarwal Intelligence Grid" in generic or "AIG" in generic
