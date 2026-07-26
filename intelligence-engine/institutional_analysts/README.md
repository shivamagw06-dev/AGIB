# Institutional Analyst Framework (IAF V1.1)

Answer Construction orchestration only. **Not an engine.**

## Locked architecture

Does **not** redesign CID, LEO, IRP, Company Analysis, Financial Intelligence,
Company Monitor, Knowledge Foundation, Academy, DVC, ECP, MarketDataClient, or providers.

No new data. No new intelligence. Ownership of existing intelligence only.

## Flow

```text
Question
  → Research Planner (assigns mandates)
  → 9 Specialist Analysts (structured opinions + memory)
  → Investment Committee meeting
        Stage 1 Consensus
        Stage 2 Conflicts
        Stage 3 Missing Evidence
        Disagreement Matrix + Minutes
  → Chief Investment Officer (editor)
  → Institutional Report
```

## Analyst contract

Each analyst has mandate metadata:

- Mandate
- Primary Question
- Primary Inputs
- Outputs
- Never (out-of-domain)

Each opinion is a **structured object**:

```json
{
  "summary": "...",
  "stance": "Bullish|Neutral|Bearish",
  "strengths": [],
  "weaknesses": [],
  "evidence": [],
  "unanswered_questions": [],
  "confidence": {
    "evidence": 0.0,
    "knowledge": 0.0,
    "freshness": 0.0,
    "coverage": 0.0,
    "overall": 0.0
  },
  "what_changed": null
}
```

Domain guards strip out-of-mandate vocabulary (e.g. Business never discusses PE).

## Committee

Behaves like a meeting — not a merge:

1. Consensus stances per analyst
2. Conflicts (e.g. high quality vs rich entry)
3. Missing evidence asks in institutional language (never “Coverage 73%”)
4. Disagreement Matrix → committee stance + reason
5. Investment Committee Minutes (historical memory)

## CIO

Editor, not summariser:

- Never repeats analyst wording
- Never names engines / providers / subsystems
- Writes institutional prose from committee signals only

## Flags

`institutional_analysts`, `ask_agi_iaf`
