# Full Production Regression v1 — Phase 3.0 freeze gate

## Run

```bash
cd intelligence-engine
ASK_TEST_MODE=inprocess python3 -m ask_product_test.run_production_regression_v1 --with-afi
```

Quick iteration (skip Coverage + AFI):

```bash
PROD_REGRESSION_QUICK=1 python3 -m ask_product_test.run_production_regression_v1
```

Writes `/workspace/artifacts/production_regression_v1.json`.

## Suites and targets

| Suite | Target | Module |
|---|---|---|
| BI Acceptance | 100% | `run_bi_acceptance_v1` |
| Business Integration | 100% | `run_bi_integration_acceptance_v1` |
| Golden Business 20 | 20/20 | `run_golden_business_20` |
| Golden Founder 5 | 5/5 | `run_golden_founder_5` |
| Founder Evaluation V2 | ≥95% | `run_founder_evaluation_v2` |
| KUL Acceptance | PASS | `run_kul_acceptance_v1` |
| Concept Acceptance | PASS | `run_concept_acceptance_v1` |
| Coverage Acceptance | PR-scoped PASS | `run_coverage_acceptance_v1` |
| Recommendation Policy | PASS | `run_recommendation_policy_acceptance_v1` |
| Unknown Entity | PASS | `run_unknown_entity_acceptance_v1` |
| AFI | ≥95% overall | `run_afi_acceptance_v1` |

`phase3_freeze_ready` is true only when the full gate (including AFI + Coverage) passes.

## Permanent business regression

`golden_business_20` must run on every release. Categories: Business Models, Moats,
Competition, Unit Economics, Management, Growth, Risks, Industry Structure.
