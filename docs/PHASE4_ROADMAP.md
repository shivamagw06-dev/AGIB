# AGI Phase 4 — Institutional Judgment Roadmap

```text
COMPANY: AGI
BASELINE: v3.5 CERTIFIED (frozen)
UPDATED: 2026-07-28
STATUS: Phase 4 judgment stack complete (pending ICC certification freeze)
```

| Sprint | Name | Status | Expected CIO lift |
|--------|------|--------|------------------:|
| **4.1** | Institutional Evidence Weighting (IEW) | ✓ Frozen v1.0.0 | +0.0 |
| **4.2** | Institutional Hypothesis Generation (IHG) | ✓ Frozen v1.0.0 | +0.0 |
| **4.3** | Institutional Hypothesis Evaluation (IHE) | ✓ Frozen v1.0.0 | +0.5 to +0.8 |
| **4.4** | Institutional Committee Reasoning (ICR) | ✓ Frozen v1.0.0 | +0.3 |
| **4.5** | **Institutional Confidence Calibration (ICC)** | ✓ Implemented v1.0.0 | **+0.2** |

## Complete judgment stack

```text
Evidence → Weighting → Hypotheses → Evaluation → Committee → Confidence → Reasoning → ICE
```

Confidence is no longer a subjective label. It is a deterministic, explainable, replay-safe outcome of institutional analysis.

## Measurement (all independent of CIO)

| Metric | Measures |
|--------|----------|
| **HQS** | Hypothesis generation + evaluation quality |
| **CQS** | Committee deliberation quality |
| **CFQS** | Confidence calibration quality |

## After Sprint 4.5

1. Run full certification: IEL 1,025 · CIO-25 · HQS · CQS · CFQS · RCI · LangSmith
2. Freeze IEW / IHG / IHE / ICR / ICC as **v1.0.0**
3. **Do not** add more judgment layers
4. Begin **Phase 5** — how AGI makes and manages investment decisions over time

## Do not

* Optimise frozen Phase 4 profiles for benchmark chasing
* Replace reasoning internals
* Manually assign or LLM-inflate confidence
* Treat confidence as optimism
