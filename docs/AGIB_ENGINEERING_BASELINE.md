# AGIB Engineering Baseline — Release Certification Status

## Status

```text
ENGINEERING BASELINE FROZEN: NO
BOARD VERDICT: NOT CERTIFIED
DATE: 2026-07-28
COMMIT MEASURED: 581f1363
```

This document records the **attempted** AGIB v3.5 engineering baseline after Framework Optimisation + Intent Optimisation. Because certification gates failed, these metrics are a **certification measurement record**, not an official frozen baseline that future PRs must beat as a certified floor.

When gates clear, re-run this certification and flip the banner to:

```text
ENGINEERING BASELINE FROZEN: YES
BOARD VERDICT: CERTIFIED
```

## Measured reference (full path, 1,025)

| Metric | Value |
|--------|------:|
| IEL pass | 98.44% |
| Mean score | 90.18 |
| Intent | 99.8% |
| Framework | 97.76% |
| Playbook | 99.61% |
| Evidence graph hit | 100% |
| IMAI hit | 91.32% |
| Historical replay accuracy | 73.21% |
| Future leakage | 15 |
| Hallucinated evidence | 0 |
| CIO-25 pass | 100% |
| CIO structural /10 | 8.95 |
| Last CIO examiner /10 | 8.12 (post-IMAI) |

## What is already strong

- Overall IEL above 98%
- Framework accuracy above 97%
- Portfolio intent_mismatch RCI clusters cleared (Sprint 3.4 hold)
- CIO-25 soft/full IEL pass 100%
- Zero hallucinated-evidence failures / reasoning regressions on this run

## What blocks freeze

1. Point-in-time / future leakage on historical replay questions  
2. Replay accuracy below 100% on the historical suite  
3. Two frozen CIO prompts mis-intent as Industry (Q11, Q16)

## Rule for future work

Until `CERTIFIED`:

- Do not claim a frozen v3.5 engineering baseline.
- Prefer integrity fixes (replay leakage) over new analytical depth modules.
- Every PR may still compare against this measurement record, but the official freeze is deferred.
