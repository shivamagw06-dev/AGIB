# AGIB v3.5 — Release Certification (Baseline Freeze Attempt)

**Board:** Independent Institutional Certification Board  
**Exercise:** Release Certification — measure only  
**Date:** 2026-07-28  
**Commit under test:** `581f1363` (post Framework Optimisation + Intent Optimisation)  
**Product changes in this exercise:** **None**

---

## Board verdict

# NOT CERTIFIED

Official engineering baseline is **not frozen**.

Failing gates (engineering priority order):

1. **Future Leakage = 0** — observed **15** (`future_leakage` on historical_replay / GEN-REP)
2. **Replay = 100%** — historical replay accuracy **73.21%** (56 replay questions)
3. **Intent Accuracy = 100%** — full 1,025 suite **99.8%** (fails: `CIO-Q11`, `CIO-Q16` only)

All other certification gates **passed**.

---

## Scope (honoured)

| Constraint | Status |
|------------|--------|
| No code / architecture / reasoning changes | ✓ |
| No framework / intent / playbook / KF changes | ✓ |
| No evaluation harness redesign | ✓ |
| Measure only | ✓ |
| Full 1,025 questions (CIO-25 + institutional 1,000) | ✓ |
| Frozen CIO prompts unchanged | ✓ |
| Full execution path (`mode=full`) | ✓ |

Execution path verified per question:

Intent → Evidence → Playbooks → Evidence Graph → IMAI → Reasoning → ICE → Answer assembly

---

## IEL — full suite (1,025)

| Metric | Observed | Gate |
|--------|---------:|------|
| Overall pass % | **98.44** | ≥98 ✓ |
| Mean score | **90.18** | — |
| Intent accuracy | **99.8** | =100 ✗ |
| Framework accuracy | **97.76** | ≥97 ✓ |
| Playbook accuracy | **99.61** | — |
| Evidence graph hit rate | **100.0** | — |
| Analog intelligence hit rate | **91.32** | — |
| Replay (all dims) | **98.54** | — |
| Replay (historical_replay only) | **73.21** | =100 ✗ |
| Future leakage count | **15** | =0 ✗ |
| Hallucinated evidence failures | **0** | =0 ✓ |
| Unsupported / fabricated | **0** | ✓ |
| Reasoning regression | **0** | ✓ |
| Communication regression | **0** | ✓ |
| Latency (suite wall) | ~172 s full / ~7.5 s soft | — |

Soft reference (same commit, nightly probe): institutional_1000 pass **98.4%**, intent **100.0%**, framework **97.7%**.

### Trajectory (IEL institutional routing era)

| Milestone | Pass % | Intent | Framework |
|-----------|-------:|-------:|----------:|
| IEL baseline (3.1) | 88.2 | 84.7 | 75.3 |
| Framework Opt (3.3) | 92.6 | 84.7 | 96.3 |
| Intent Opt (3.4) | 98.4 | 100.0* | 97.7 |
| **Release cert full 1025** | **98.44** | **99.8** | **97.76** |

\*institutional_1000 soft; full 1025 includes two CIO intent misses.

---

## CIO-25 — frozen exam

| Metric | Observed | Gate |
|--------|---------:|------|
| IEL full pass % | **100.0** | =100 ✓ |
| IEL mean score | 87.58 | — |
| Structural composite /10 | **8.95** | measure |
| Last examiner score (post-IMAI) | **8.12** | historical |
| Intent match rate | 92.0% | (Q11, Q16) |
| Playbook present | 100% | — |
| Evidence graph hit | 100% | — |
| IMAI hit / visible | 80% / 80% | same as post-IMAI KPI |
| ICE answer source | 100% | — |
| Future leakage (IEL replay dim) | 0 on CIO suite | ✓ |

### Examiner trajectory (historical, unchanged prompts)

| Version | CIO Score |
|---------|----------:|
| Baseline | 3.66 |
| A+B+C+D | 6.26 |
| +IAP | 7.54 |
| +IEG | 7.82 |
| +IMAI | **8.12** |
| FO / IO | routing soft 100% (examiner not re-run) |
| Release cert structural | **8.95** (deterministic KPI rubric; not examiner narrative) |

Intent mismatches on frozen gold: **CIO-Q11** (got Industry; expect Macro/Government/CrossDomain), **CIO-Q16** (got Industry; expect CrossDomain/Macro).

---

## Root Cause Intelligence (post-cert run)

Dominant remaining clusters: **`future_leakage` × historical_replay**.

Portfolio **`intent_mismatch` clusters remain cleared** (Sprint 3.4 hold).

| Priority | Root cause | Expected ROI if fixed |
|--------:|------------|------------------------|
| 1 | future_leakage | Unlock Replay 100% + Future Leakage 0; ~+1.5pp IEL |
| 2 | CIO intent Industry collapse (Q11/Q16) | Intent 99.8% → 100% on 1,025 |
| 3 | framework_mismatch EXPECTATIONS | Framework → ≥98% |

---

## Gate register

| Gate | Pass? |
|------|:-----:|
| IEL ≥ 98% | ✓ |
| Intent accuracy 100% | ✗ |
| Framework ≥ 97% | ✓ |
| Replay 100% | ✗ |
| Future leakage 0 | ✗ |
| Hallucinated evidence 0 | ✓ |
| Reasoning regression 0 | ✓ |
| Communication regression 0 | ✓ |
| CIO-25 100% pass | ✓ |
| No new intent_mismatch RCI clusters | ✓ |
| No regression vs prior IEL certification | ✓ |

---

## Artifacts

- `docs/AGIB_IEL_FROZEN_BASELINE.json`
- `docs/AGIB_CIO_FROZEN_BASELINE.json`
- `docs/AGIB_RCI_FROZEN_BASELINE.json`
- `docs/AGIB_RELEASE_SCORECARD.md`
- `docs/AGIB_ENGINEERING_BASELINE.md`
- `docs/AGIB_MISSION_CONTROL_RELEASE_BOARD.json`
- `intelligence-engine/mission_control/data/release_certification_v35.json`

---

## Board instruction

Do **not** mark `ENGINEERING BASELINE FROZEN` until the three failing gates clear.

Next engineering work must target those gates (replay integrity first). Do not start Evidence Weighting / Hypothesis / Contradiction as if the baseline were certified.
