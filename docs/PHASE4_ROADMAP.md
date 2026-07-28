# AGI Phase 4 — Institutional Judgment Roadmap

```text
COMPANY: AGI
BASELINE: v3.5 CERTIFIED (frozen)
UPDATED: 2026-07-28
```

| Sprint | Name | Status | Expected CIO lift |
|--------|------|--------|------------------:|
| **4.1** | Institutional Evidence Weighting (IEW) | ✓ Frozen v1.0.0 | +0.0 |
| **4.2** | Institutional Hypothesis Generation (IHG) | ✓ Frozen v1.0.0 | +0.0 |
| **4.3** | **Institutional Hypothesis Evaluation (IHE)** | ← Next | **+0.5 to +0.8** |
| **4.4** | Committee Reasoning | Planned | +0.3 |
| **4.5** | Confidence Calibration | Planned | +0.2 |

## Rename note

Sprint 4.3 was previously scoped as “Contradiction Resolution.”

It is renamed to **Institutional Hypothesis Evaluation Engine (IHE)** because the job is:

* compare hypotheses (pros / cons)
* score contradictions
* identify missing evidence
* reject weak explanations
* detect mutually exclusive explanations
* calculate confidence before reasoning concludes

That is hypothesis **evaluation**, not mere contradiction listing.

## Measurement

Before IHE lands, IEL reports **Hypothesis Quality Score (HQS)** — independent of CIO / overall pass weights — so Phase 4 judgment quality can be steered without conflating it with answer score.

## Do not

* Optimise frozen IEW / IHG profiles for benchmark chasing
* Replace reasoning internals
* Skip Hypothesis Space (Evidence → Conclusion is forbidden for analytical questions)
