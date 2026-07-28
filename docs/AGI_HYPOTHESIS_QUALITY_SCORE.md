# Hypothesis Quality Score (HQS) — IEL Independent Metric

```text
COMPANY: AGI
METRIC: hypothesis_quality / HQS
VERSION: hqs-v1.0.0
INDEPENDENT_OF_CIO: YES
```

## Why

IEW + IHG are infrastructure. CIO may not move until **IHE** evaluates hypotheses.

HQS measures the hypothesis layer **on its own** so Phase 4 can be steered before Sprint 4.3.

## Components

| Component | Weight | Measures |
|-----------|-------:|----------|
| Plausibility | 0.25 | 2–5 hypotheses or correct Insufficient Evidence gate; structured; no LLM/fabricated |
| Coverage | 0.20 | Major explanation classes for the question family |
| Unsupported avoided | 0.25 | Every hypothesis has supporting evidence ids; refusal when empty |
| Contradiction retention | 0.15 | Rejected kept with reasons; conflict evidence linked |
| Preferred ↔ evidence alignment | 0.15 | Preferred/Contested match strongest overall scores; no forced single winner |

## Suite fields

```text
aggregate.hypothesis_quality.mean_hqs
aggregate.hypothesis_quality.pass_pct
summary.hypothesis_quality_score
row.hqs
row.dimensions.hypothesis_quality
```

## Critical rule

HQS is **not** in `DIMENSION_WEIGHTS`. It must not change IEL overall pass % or CIO scoring.
