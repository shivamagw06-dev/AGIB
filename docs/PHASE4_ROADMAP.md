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
| **4.3** | Institutional Hypothesis Evaluation (IHE) | ✓ Frozen v1.0.0 | +0.5 to +0.8 |
| **4.4** | **Institutional Committee Reasoning (ICR)** | ✓ Implemented v1.0.0 | **+0.3** |
| **4.5** | Confidence Calibration | ← Next | +0.2 |

## Design note (Sprint 4.4)

ICR is **not a voting engine**.

Bull / Base / Bear are **roles within the committee**:

* **Bull** — strongest evidence-supported upside interpretation
* **Base** — best supported by the current balance of evidence
* **Bear** — strongest evidence-supported downside interpretation

Reasoning consumes an `InstitutionalCommitteeReport`, not raw hypothesis reports alone.

## Measurement

IEL reports:

* **HQS** — Hypothesis Quality Score (independent of CIO)
* **CQS** — Committee Quality Score (independent of CIO and HQS)

so Phase 4 judgment quality can be steered without conflating answer score.

## Do not

* Optimise frozen IEW / IHG / IHE profiles for benchmark chasing
* Replace reasoning internals
* Fabricate consensus or force three cases when evidence does not support them
* Treat probabilities as forecasts (they are relative support)
