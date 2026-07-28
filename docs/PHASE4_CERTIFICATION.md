# AGI Phase 4 — Certification Gate

```text
COMPANY: AGI
PROGRAMME: Phase 4 Analytical Depth
STATUS: Ready for certification freeze after ICC merge
DATE: 2026-07-28
```

## Judgment stack (freeze as v1.0.0 after certification)

| Module | Version | Role |
|--------|---------|------|
| IEW | institutional-evidence-weighting-v1.0.0 | Evidence priority |
| IHG | institutional-hypothesis-generation-v1.0.0 | Hypothesis space |
| IHE | institutional-hypothesis-evaluation-v1.0.0 | Hypothesis judgment |
| ICR | institutional-committee-reasoning-v1.0.0 | Committee deliberation |
| ICC | institutional-confidence-calibration-v1.0.0 | Emergent confidence |

```text
Evidence → Weighting → Hypotheses → Evaluation → Committee → Confidence → Reasoning → ICE
```

## Certification programme

1. IEL institutional_1000 (soft + hard as available)
2. Frozen CIO-25
3. HQS · CQS · CFQS (independent)
4. Root Cause Intelligence cluster review
5. LangSmith end-to-end trace review
6. Replay / temporal integrity regression

## Soft baseline at ICC landing

| Metric | Value |
|--------|------:|
| IEL 1000 pass % | 99.9 |
| CIO-25 pass % | 100 |
| HQS mean | 95.85 |
| CQS mean | 95.89 |
| CFQS mean | 100.0 |
| Reasoning changed | No |

## Rule after freeze

**Do not add more judgment layers.**

Phase 5 shifts from *how AGI thinks* to *how AGI makes and manages investment decisions over time*.
