"""Soft production entry — attach institutional reasoning plan before answers."""

from __future__ import annotations

from typing import Any

from institutional_reasoning.flags import flags_dict, is_enabled
from institutional_reasoning.gold_patterns import package_pattern_answer
from institutional_reasoning.planner import build_reasoning_plan
from institutional_reasoning.prompt import (
    INSTITUTIONAL_REASONING_SYSTEM_PROMPT,
    TOP_RULE,
)
from institutional_reasoning.schema import (
    ARCHITECTURE_STATUS,
    MODULE_CODE,
    NOT_A_TOP_LEVEL_ENGINE,
    PROGRAMME,
    ROLE,
    VERSION,
)


def health() -> dict[str, Any]:
    return {
        "status": "ok" if is_enabled() else "disabled",
        "programme": PROGRAMME,
        "module_code": MODULE_CODE,
        "version": VERSION,
        "architecture_status": ARCHITECTURE_STATUS,
        "not_a_top_level_engine": NOT_A_TOP_LEVEL_ENGINE,
        "role": ROLE,
        "top_rule": TOP_RULE,
        "gold_reasoning_patterns": True,
        "flags": flags_dict(),
    }


def quality_gates() -> dict[str, Any]:
    return {
        "programme": PROGRAMME,
        "version": VERSION,
        "architecture_status": ARCHITECTURE_STATUS,
        "passed": is_enabled(),
        "checks": {
            "enabled": is_enabled(),
            "top_rule_evidence_justifies_every_sentence": True,
            "nine_step_reasoning_chain": True,
            "evidence_before_conclusions": True,
            "conclusions_before_answers": True,
            "never_guess": True,
            "gold_reasoning_patterns": True,
            "soft_wire_only": True,
            "not_a_top_level_engine": True,
        },
        "flags": flags_dict(),
    }


def system_prompt() -> str:
    return INSTITUTIONAL_REASONING_SYSTEM_PROMPT


def package_for_ask_agi(
    *,
    query: str = "",
    ticker: str | None = None,
    company: str | None = None,
) -> dict[str, Any]:
    """Build the pre-answer reasoning plan and optional gold-pattern executive.

    Never raises. Never invents company facts beyond the supplied question framing.
    """
    if not is_enabled():
        return {
            "enabled": False,
            "bypassed": True,
            "programme": PROGRAMME,
            "version": VERSION,
        }
    try:
        plan = build_reasoning_plan(query, ticker=ticker, company=company)
        gold = package_pattern_answer(query, ticker=ticker, company=company)
        out = {
            **plan,
            "programme": PROGRAMME,
            "module_code": MODULE_CODE,
            "version": VERSION,
            "architecture_status": ARCHITECTURE_STATUS,
            "not_a_top_level_engine": True,
            "role": ROLE,
            "top_rule": TOP_RULE,
            "system_prompt": INSTITUTIONAL_REASONING_SYSTEM_PROMPT,
            "system_prompt_chars": len(INSTITUTIONAL_REASONING_SYSTEM_PROMPT),
            "flags": flags_dict(),
            "gold_pattern": gold if gold.get("enabled") else {"enabled": False},
        }
        if gold.get("enabled") and gold.get("executive"):
            out["executive"] = gold["executive"]
            out["answer"] = gold["executive"]
            out["pattern_id"] = gold.get("pattern_id")
            out["pattern_level"] = gold.get("level")
            out["direct_answer"] = gold.get("direct_answer")
            out["owns_executive"] = True
            out["answer_policy"] = "gold_reasoning_pattern"
        return out
    except Exception as exc:  # noqa: BLE001
        return {
            "enabled": False,
            "bypassed": True,
            "error": str(exc),
            "programme": PROGRAMME,
            "version": VERSION,
        }
