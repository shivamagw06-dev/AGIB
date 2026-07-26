"""Investment Committee — meeting stages over analyst opinions only."""

from __future__ import annotations

from typing import Any

from institutional_analysts.base import as_list, pick_confidence, scrub_public


_ROLES = ["business", "financial", "valuation", "market", "sector", "macro", "risk", "management", "ownership"]

_STANCE_SCORE = {"Bullish": 1, "Neutral": 0, "Bearish": -1}


def _stance(op: dict[str, Any]) -> str:
    s = str(op.get("stance") or "Neutral")
    if s not in _STANCE_SCORE:
        return "Neutral"
    return s


def _minutes_label(stance: str) -> str:
    return {
        "Bullish": "Strong",
        "Neutral": "Neutral",
        "Bearish": "Cautious",
    }.get(stance, "Neutral")


def _conflict_pairs(stances: dict[str, str], opinions: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    biz, val = stances.get("business"), stances.get("valuation")
    if biz == "Bullish" and val == "Bearish":
        conflicts.append(
            {
                "topic": "Quality versus entry price",
                "left": {"analyst": "Business Analyst", "view": "Excellent franchise / high business quality"},
                "right": {"analyst": "Valuation Analyst", "view": "Entry price already looks rich"},
                "tension": "High quality, poor entry price",
            }
        )
    fin, risk = stances.get("financial"), stances.get("risk")
    if fin == "Bullish" and risk == "Bearish":
        conflicts.append(
            {
                "topic": "Improving numbers versus downside skew",
                "left": {"analyst": "Financial Analyst", "view": "Financial trajectory improving"},
                "right": {"analyst": "Risk Analyst", "view": "Downside risks still material"},
                "tension": "Better prints, elevated left-tail risk",
            }
        )
    mkt, val2 = stances.get("market"), stances.get("valuation")
    if mkt == "Bullish" and val2 == "Bearish":
        conflicts.append(
            {
                "topic": "Tape versus value",
                "left": {"analyst": "Market Analyst", "view": "Tape constructive"},
                "right": {"analyst": "Valuation Analyst", "view": "Multiples leave limited cushion"},
                "tension": "Momentum positive while valuation cushion is thin",
            }
        )
    mgmt, own = stances.get("management"), stances.get("ownership")
    if mgmt == "Bullish" and own == "Bearish":
        conflicts.append(
            {
                "topic": "Trust versus ownership signals",
                "left": {"analyst": "Management Analyst", "view": "Governance / execution trustable"},
                "right": {"analyst": "Ownership Analyst", "view": "Ownership trend less supportive"},
                "tension": "Trusted operators, weaker ownership alignment signals",
            }
        )

    # Generic opposing pairs if none of the templates fired but stances diverge hard
    if not conflicts:
        bulls = [r for r, s in stances.items() if s == "Bullish"]
        bears = [r for r, s in stances.items() if s == "Bearish"]
        if bulls and bears:
            b, r = bulls[0], bears[0]
            conflicts.append(
                {
                    "topic": f"{b.replace('_', ' ').title()} versus {r.replace('_', ' ').title()}",
                    "left": {
                        "analyst": (opinions.get(b) or {}).get("analyst") or b,
                        "view": scrub_public((opinions.get(b) or {}).get("summary"), limit=160),
                    },
                    "right": {
                        "analyst": (opinions.get(r) or {}).get("analyst") or r,
                        "view": scrub_public((opinions.get(r) or {}).get("summary"), limit=160),
                    },
                    "tension": "Specialists disagree on the balance of opportunity and risk",
                }
            )
    return conflicts[:5]


def _missing_evidence(opinions: dict[str, dict[str, Any]]) -> list[str]:
    asks: list[str] = []
    for role in _ROLES:
        op = opinions.get(role) or {}
        for q in as_list(op.get("unanswered_questions"), limit=2):
            if q and q not in asks:
                asks.append(q)
        conf = op.get("confidence") if isinstance(op.get("confidence"), dict) else {}
        cov = float(conf.get("coverage") or conf.get("overall") or 0.55)
        if cov < 0.55:
            label = (op.get("analyst") or role).replace("_", " ")
            asks.append(f"Fuller evidence pack for the {label} file")
    # Institutional phrasing — never "Coverage 73%"
    preferred = [
        "Updated quarterly results",
        "Latest management guidance",
        "Revised growth / demand outlook",
        "Clearer peer valuation triangulation",
    ]
    out = []
    for item in asks + preferred:
        if item not in out:
            out.append(item)
        if len(out) >= 6:
            break
    return out


def _committee_stance(stances: dict[str, str], conflicts: list[dict[str, Any]]) -> tuple[str, str]:
    weights = {
        "business": 1.2,
        "financial": 1.2,
        "valuation": 1.3,
        "risk": 1.1,
        "macro": 0.9,
        "sector": 0.9,
        "market": 0.7,
        "management": 0.9,
        "ownership": 0.7,
    }
    score = 0.0
    wsum = 0.0
    for role, stance in stances.items():
        w = weights.get(role, 1.0)
        score += _STANCE_SCORE.get(stance, 0) * w
        wsum += w
    avg = score / wsum if wsum else 0.0

    if avg >= 0.35:
        label = "Constructive"
    elif avg <= -0.35:
        label = "Cautious"
    else:
        label = "Neutral"

    biz, val, risk = stances.get("business"), stances.get("valuation"), stances.get("risk")
    if biz == "Bullish" and val == "Bearish":
        reason = "High-quality business but valuation already discounts much of the expected growth."
        label = "Constructive" if risk != "Bearish" else "Neutral"
    elif any(c.get("topic") == "Improving numbers versus downside skew" for c in conflicts):
        reason = "Financial trajectory is improving, yet the committee still prices a meaningful left tail."
    elif label == "Constructive":
        reason = "Specialist stances lean supportive across quality and financial trajectory."
    elif label == "Cautious":
        reason = "Downside and valuation concerns outweigh supportive franchise signals."
    else:
        reason = "Mixed specialist stances — wait for clearer confirmation before raising conviction."
    return label, reason


def aggregate(opinions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Never consumes raw APIs / dossiers / statements — opinions only."""
    present = {
        r: opinions[r]
        for r in _ROLES
        if isinstance(opinions.get(r), dict) and (opinions[r].get("summary") or opinions[r].get("headline"))
    }

    # Stage 1 — Consensus stances
    consensus_stances = {r: _stance(present[r]) if r in present else "Missing" for r in _ROLES}
    stage_1 = {r: consensus_stances[r] for r in _ROLES}

    # Stage 2 — Conflicts
    conflicts = _conflict_pairs({r: s for r, s in consensus_stances.items() if s != "Missing"}, present)

    # Stage 3 — Missing evidence (institutional asks, not coverage %)
    missing = []
    for r in _ROLES:
        if r not in present:
            missing.append(f"{r.replace('_', ' ').title()} opinion incomplete")
    missing.extend(_missing_evidence(present))
    # de-dupe preserve order
    seen = set()
    stage_3 = []
    for m in missing:
        if m not in seen:
            seen.add(m)
            stage_3.append(m)

    committee_stance, reason = _committee_stance(
        {r: s for r, s in consensus_stances.items() if s != "Missing"},
        conflicts,
    )

    disagreement_matrix = {
        "analyst_stances": {
            (present[r].get("analyst") if r in present else r.replace("_", " ").title()): consensus_stances[r]
            for r in _ROLES
        },
        "committee_stance": committee_stance,
        "reason": reason,
    }

    confs = []
    for op in present.values():
        c = op.get("confidence")
        if isinstance(c, dict):
            confs.append(float(c.get("overall") or 0.55))
        else:
            confs.append(float(c or 0.55))
    consensus_conf = pick_confidence(sum(confs) / len(confs) if confs else 0.55)

    readiness = "ready" if len(present) >= 7 and len(stage_3) <= 4 else "partial"
    if len(present) < 6:
        readiness = "not_ready"

    minutes = {
        "title": "Investment Committee Minutes",
        "business": _minutes_label(consensus_stances.get("business", "Neutral")),
        "financials": "Improving"
        if consensus_stances.get("financial") == "Bullish"
        else ("Soft" if consensus_stances.get("financial") == "Bearish" else "Stable"),
        "valuation": "Attractive"
        if consensus_stances.get("valuation") == "Bullish"
        else ("Rich" if consensus_stances.get("valuation") == "Bearish" else "Fair"),
        "market": _minutes_label(consensus_stances.get("market", "Neutral")),
        "sector": _minutes_label(consensus_stances.get("sector", "Neutral")),
        "macro": _minutes_label(consensus_stances.get("macro", "Neutral")),
        "risks": "Elevated" if consensus_stances.get("risk") == "Bearish" else "Contained",
        "management": _minutes_label(consensus_stances.get("management", "Neutral")),
        "ownership": _minutes_label(consensus_stances.get("ownership", "Neutral")),
        "decision": f"Remain {committee_stance.lower()}.",
        "follow_up": "Need confirmation after next earnings."
        if readiness != "ready"
        else "Maintain coverage; reassess on material evidence change.",
        "conflicts_noted": [c.get("tension") for c in conflicts if c.get("tension")],
        "missing_evidence_asks": stage_3[:4],
    }

    # Compact consensus blurbs for CIO — stances + one strength/weakness, not full analyst prose
    def _compact(role: str) -> str:
        op = present.get(role) or {}
        st = consensus_stances.get(role, "Missing")
        lead = (as_list(op.get("strengths"), limit=1) or as_list(op.get("weaknesses"), limit=1) or [""])[0]
        return scrub_public(f"{st}" + (f" — {lead}" if lead else ""), limit=180)

    return {
        "owner": "committee",
        "analyst": "Investment Committee",
        "question": "What is the coordinated institutional view?",
        "meeting": True,
        "stage_1_consensus": stage_1,
        "stage_2_conflicts": conflicts,
        "stage_3_missing_evidence": stage_3,
        "disagreement_matrix": disagreement_matrix,
        "minutes": minutes,
        "committee_summary": scrub_public(
            f"Committee meeting reviewed nine specialist opinions. Net stance: {committee_stance}. {reason}",
            limit=300,
        ),
        "consensus": {
            "business": _compact("business"),
            "financial": _compact("financial"),
            "valuation": _compact("valuation"),
            "market": _compact("market"),
            "sector": _compact("sector"),
            "macro": _compact("macro"),
            "risks": as_list(((present.get("risk") or {}).get("sections") or {}).get("business_risks"), limit=5)
            or as_list((present.get("risk") or {}).get("weaknesses"), limit=5)
            or ["Execution", "Earnings", "Multiple compression"],
            "management": _compact("management"),
            "ownership": _compact("ownership"),
        },
        "agreements": [
            f"{k.replace('_', ' ').title()}: {v}"
            for k, v in stage_1.items()
            if v in {"Bullish", "Neutral", "Bearish"}
        ][:6],
        "disagreements": [c.get("tension") for c in conflicts if c.get("tension")],
        "conflicts": conflicts,
        "missing_evidence": stage_3,
        "confidence": consensus_conf,
        "recommendation_readiness": readiness,
        "committee_stance": committee_stance,
        "committee_reason": reason,
        "opinions_count": len(present),
        "analyst_roles_present": list(present.keys()),
        # signals for CIO editor — structured, not prose copy
        "cio_signals": {
            "stances": stage_1,
            "committee_stance": committee_stance,
            "reason": reason,
            "conflicts": [{"topic": c.get("topic"), "tension": c.get("tension")} for c in conflicts],
            "missing_evidence": stage_3[:5],
            "risk_items": as_list(((present.get("risk") or {}).get("weaknesses")), limit=5),
            "what_changed": [
                {
                    "analyst": (present[r].get("analyst") if r in present else r),
                    "notes": ((present[r].get("what_changed") or {}).get("notes") if r in present else []),
                }
                for r in _ROLES
                if r in present and (present[r].get("what_changed") or {}).get("changed")
            ],
        },
    }
