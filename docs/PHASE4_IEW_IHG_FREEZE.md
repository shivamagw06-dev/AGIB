# Phase 4 Freeze — IEW v1.0.0 + IHG v1.0.0

```text
COMPANY: AGI
DATE: 2026-07-28
STATUS: FROZEN — do not optimise
```

## Frozen modules

| Module | Version | Role |
|--------|---------|------|
| **IEW** | `institutional-evidence-weighting-v1.0.0` | Evidence priority before reasoning |
| **Weight profile** | `iew-weight-profile-v1.0.0` | Deterministic scorecard |
| **IHG** | `institutional-hypothesis-generation-v1.0.0` | Hypothesis Space before reasoning |
| **Hypothesis catalog** | `ihg-hypothesis-catalog-v1.0.0` | Deterministic templates |

## Why freeze

Sprints 4.1 and 4.2 build **machinery**, not accuracy lift.

Observed (soft IEL):

| Sprint | CIO / IEL lift |
|--------|---------------:|
| IEW | ~0 |
| IHG | ~0 |

That is expected: reasoning does not yet **evaluate** competing hypotheses.

## Rule

Do **not** tune IEW caps or IHG catalogs to chase IEL/CIO points.

Evolve judgment in:

1. **HQS** measurement (IEL independent metric)
2. **Sprint 4.3 — Institutional Hypothesis Evaluation Engine (IHE)**

## Pipeline (frozen segment)

```text
… → IEW (frozen) → IHG (frozen) → [IHE next] → Reasoning → ICE
```
