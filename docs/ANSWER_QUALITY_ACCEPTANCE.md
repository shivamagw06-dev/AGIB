# AGI Answer Quality Acceptance v1.0 (Phase 4.0)

**Runner:** `ask_product_test/run_answer_quality_acceptance_v1.py`
**Status:** not yet certified — **90.4%** against a 95% target with 25 open defects.

Core Platform Acceptance proves AGI answers *safely*: right route, right
entity, no hallucination, no recommendation leakage. It does not prove AGI
answers *well*. This suite measures institutional depth, company specificity,
evidence quality, research depth and executive communication, and fails
answers that are technically correct but generic.

## Shape

500 questions, 50 per section, scored on nine weighted dimensions rather than
routing and length.

| Dimension | Weight |
|---|---|
| Answers the actual question | 20 |
| Company specificity | 15 |
| Evidence quality | 15 |
| Financial reasoning | 15 |
| Industry specificity | 10 |
| Executive communication | 10 |
| Research depth | 10 |
| Boilerplate penalty | 5 |
| Honest uncertainty | 5 |

A case passes at ≥70 quality with no automatic fail. Automatic fails:
boilerplate, generic investment thesis, generic research answer, industry
refusal, wrong evidence, company answered generically, recommendation leakage,
unexpected refusal.

**Boilerplate detection** compares answers to the same template across
different companies; similarity ≥0.85 fails both. Axis Bank, ICICI Bank and
SBI cannot share one thesis.

## Current result

```
452/500 (90.4%)  target 95%  decision=FAIL

A Company Intelligence     80%   F Research Intelligence     94%
B Financial Intelligence   92%   G Consensus Intelligence    88%
C Business Intelligence    96%   H Knowledge Fusion          72%
D Industry Intelligence    92%   I Executive Communication   90%
E Investment Intelligence  90%   J Impossible Questions     100%

boilerplate 8 · generic thesis 3 · generic research 1 · industry refusal 0
wrong evidence 5 · company answered generically 6 · recommendation leakage 0
```

Baseline before the fixes below was **53.3%**.

## Product defects this suite found and fixed

1. **Provider names leaked into answers.** Every fused answer carried
   "Sources fused: industry_intelligence, business_intelligence, capiq_ikt…".
   Internal plumbing now stays in diagnostics.
2. **Company questions were answered with industry templates.** "Explain Axis
   Bank" led with "For banks, enterprise value is primarily driven by NIM,
   CASA…" — true of every bank, so about none. A company-bound answer must now
   mention the company, otherwise fusion picks the first provider summary that
   does.
3. **Industry pedagogy was refused for want of an entity.** "How are banks
   valued?" and "What KPIs matter for telecom?" hit the unknown-entity policy.
   Industry pedagogy is now a first-class route.
4. **Research questions were answered with company profiles.** "What did Axis
   Bank's annual report say?" returned a business description as if it were
   the report. When research memory holds no filed document, the answer now
   says so before offering what is on file.
5. **"What does X do?" refused for every company.** The canonical registry bind
   was gated behind a bare-stem guard. Since the resolver only binds exact or
   unambiguous names, that guard is gone.

## Remaining work to certify

- **Knowledge Fusion (72%)** — multi-provider questions still lean on one
  provider instead of composing identity, business, industry, consensus and
  research into one view.
- **Investment thesis depth** — companies without a curated thesis fall back to
  consensus plus industry DNA, so bank theses read alike. Three still trip the
  generic-thesis gate and several cluster as boilerplate.
- **Financial reasoning (33%)** — concept answers state definitions without
  the causal chain the dimension looks for.
- **Industry specificity (56%)** — company answers rarely carry the industry's
  own KPI vocabulary.

## Artifacts

`artifacts/answer_quality_acceptance_v1.{json,md,html}` — section heatmap,
quality gates, dimension averages, weakest companies, boilerplate clusters and
the worst 50 answers with text.

## Pipeline

Registered after Core Platform Acceptance:

```
production regression → core platform acceptance → answer quality acceptance
```
