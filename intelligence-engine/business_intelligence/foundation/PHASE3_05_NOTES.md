# Phase 3.0.5 — Business Intelligence Integration

## Objective

Wire the Phase 3.0 BI Foundation into Ask **through KUL**, the same lifecycle
pattern as Financial Foundations → Phase 2.5 integration. Engine acceptance
(100/100) is necessary but not sufficient; product validation requires KUL
routing + live integration suite + founder/regression gates.

## What changed

1. **KUL provider** `business_intelligence` wraps `foundation.analyse`
2. **Query planner** detects business / moat / unit-economics / comparison /
   business-risk / growth intents deterministically
3. **Knowledge planner** uses a BI-first menu (BI → CapIQ → memory → IKL → KF →
   CGL → legacy) for business-shaped questions; industry pedagogy without a
   ticker uses BI → KF → concepts (no generic retrieval default)
4. **Fusion** prefers BI summaries for business-typed questions
5. **Hard provider** — BI can short-circuit Ask via `answer_for_ask` (still
   after coverage / recommendation / unknown-entity policies in `UiService`)
6. Foundation `ask_wired: true` via `knowledge_unification.providers.business_intelligence`

## What did **not** change

- No parallel Ask short-circuit bypassing KUL
- Recommendation policy, coverage policy, executive composer unchanged
- CapIQ pedagogy false-bind guards preserved
- Industry Intelligence remains a later phase

## Acceptance

```bash
cd intelligence-engine
python3 -m ask_product_test.run_bi_integration_acceptance_v1
```

~28 questions · gate ≥90% · `/workspace/artifacts/bi_integration_acceptance_v1.json`

Assertions: BI selected, KUL plan includes BI, not legacy-only, direct answer
first, no hallucination / false CapIQ binds, evidence fusion when company-bound.

## Remaining before Phase 3 freeze

1. ✅ Engine acceptance (100/100)
2. ⏳ This integration suite green
3. ⏳ Founder Evaluation rerun
4. ⏳ Production regression (Golden 5, Coverage, AFI, Recommendation Policy)

Only after those pass: freeze Business Intelligence Foundation → Industry Intelligence.
