# Production Release Gate — AGI Core v1.0

**Status:** Permanent (frozen baseline)  
**Owner:** Core Platform  
**Policy:** Every PR must PASS this gate before merge.

See `docs/AGI_CORE_V1_0.md` and `ask_product_test/agi_core_v1_0.py`.

## Run

```bash
cd intelligence-engine
ASK_TEST_MODE=inprocess python3 -m ask_product_test.run_production_regression_v1
```

AFI is included by default (merge-sufficient). Local iteration only:

```bash
PROD_REGRESSION_QUICK=1 python3 -m ask_product_test.run_production_regression_v1
```

Writes `artifacts/production_regression_v1.json` (override with `ASK_TEST_ARTIFACTS`).

## Permanent suite order

```text
Founder Evaluation V2
        ↓
Golden Founder 5
        ↓
Golden Business 20
        ↓
Financial Intelligence Acceptance (AFI)
        ↓
Business Intelligence Acceptance
        ↓
Business Integration
        ↓
Coverage Acceptance
        ↓
Concept Acceptance
        ↓
Knowledge Unification
        ↓
Recommendation Policy
        ↓
Unknown Entity
        ↓
PASS → Merge
```

## Targets

| Suite | Target |
|---|---|
| Founder Evaluation V2 | ≥95% |
| Golden Founder 5 | 5/5 |
| Golden Business 20 | 20/20 |
| AFI | ≥95% overall |
| BI Acceptance | 100% |
| Business Integration | 100% |
| Coverage | PR-scoped PASS |
| Concept | 100% |
| KUL | 100% |
| Recommendation Policy | PASS |
| Unknown Entity | PASS |
| Hallucinations | 0 |

`agi_core_v1_ready` / `merge_allowed` is true only when the full gate
(including AFI + Coverage) passes.

## CI

`.github/workflows/production-regression.yml` runs this gate on every
`pull_request` and on pushes to `main` / `cursor/**`.
