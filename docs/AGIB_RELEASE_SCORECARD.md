# AGIB v3.5 — Release Scorecard

**Verdict: NOT CERTIFIED**  
**Commit:** `581f1363` · **Date:** 2026-07-28 · **Mode:** full path · **N:** 1,025

## Headline

| KPI | Target | Observed | Gate |
|-----|-------:|---------:|:----:|
| IEL pass | ≥98% | 98.44% | ✓ |
| Intent accuracy | 100% | 99.8% | ✗ |
| Framework accuracy | ≥97% | 97.76% | ✓ |
| Replay (historical) | 100% | 73.21% | ✗ |
| Future leakage | 0 | 15 | ✗ |
| Hallucinated evidence | 0 | 0 | ✓ |
| Reasoning regression | 0 | 0 | ✓ |
| Communication regression | 0 | 0 | ✓ |
| CIO-25 pass | 100% | 100% | ✓ |

## Layer health

| Layer | Hit / accuracy |
|-------|---------------:|
| Intent (1025) | 99.8% |
| Framework | 97.76% |
| Playbook | 99.61% |
| Evidence graph | 100% hit |
| IMAI | 91.32% hit |
| Confidence bands | 100% |
| Unsupported claims | 100% pass |
| Hallucinated evidence | 100% pass |

## CIO frozen exam

| | Value |
|--|------:|
| IEL pass | 100% |
| Structural /10 | 8.95 |
| Last examiner (IMAI) | 8.12 |
| IMAI hit | 80% |
| ICE source | 100% |

## Failing gates (priority)

1. Future leakage (15) — critical integrity  
2. Replay historical accuracy 73.21% — critical integrity  
3. Intent 99.8% (CIO-Q11, CIO-Q16) — high

## Baseline freeze

**ENGINEERING BASELINE FROZEN: NO**
