# AGI Editorial Excellence Program v1.0

**Document type:** Editorial Engineering Specification  
**Layer:** Institutional Research Engine (IRE)  
**Status:** Execution Program  
**Architecture:** Freeze v1.0 — communication improvement only  

---

## Purpose

Continuously improve the quality of AGI's written research through systematic review, benchmarking, and refinement.

This program does **not** add intelligence engines, constitutions, or orchestration layers. It improves **communication only**.

---

## Mission

AGI should produce research that an institutional investor would willingly forward to an investment committee without editing.

The objective is not to write more. The objective is to **communicate better**.

Every iteration should improve:

- Clarity
- Prioritization
- Institutional tone
- Narrative flow
- Investor usefulness

---

## Success metric

The question after every answer:

> "Would a portfolio manager forward this response without editing?"

| Rating | Meaning |
|--------|---------|
| YES | Forward as-is |
| MINOR_EDITS | Small polish only |
| MAJOR_EDITS | Substantial rework |
| REWRITE | Not committee-ready |

**Success requires >90% YES** on the benchmark dataset.

---

## Pipeline

```text
Research
  ↓
Response Planning (IWC)
  ↓
Institutional Writing (IWC)
  ↓
Editorial Review (this program)
  ↓
Rule Improvement
  ↓
Future Responses Improve
```

The constitution remains stable. Editorial rules evolve.

---

## Implementation

| Package | Role |
|---------|------|
| `intelligence-engine/editorial_excellence/` | Scorecard, rules, workspace, reports, production wiring |
| `intelligence-engine/institutional_writing_benchmark/` | 500-question benchmark registry + Hall of Fame |
| `intelligence-engine/answer_construction/production.py` | Applies editorial review after IWC |

### Production wiring

```python
apply_institutional_writing_constitution(out, ...)
apply_editorial_excellence(out, query=..., benchmark_id=...)
```

---

## Benchmark dataset

Location: `institutional_writing_benchmark/registry.py`

- **500** real investment questions (`IWB_001` … `IWB_500`)
- **13** categories: investment assessment, valuation, earnings, peer comparison, business quality, management, capital allocation, risks, competitive position, sector analysis, macro, portfolio construction, monitoring

Each benchmark stores:

- Question
- Expected response structure
- Editorial notes
- Latest score (populated by review loop)
- Revision history

---

## Editorial scorecard

Twelve dimensions scored 0–100:

1. Clarity  
2. Institutional tone  
3. Narrative flow  
4. Prioritization  
5. Evidence integration  
6. Explanation quality  
7. Handling of uncertainty  
8. Investor usefulness  
9. Executive summary quality  
10. Investment debate quality  
11. Questions before you decide  
12. Overall editorial score  

Pass threshold: **≥90**.

---

## Editorial review workspace

Internal-only workspace per response (`editorial_excellence/workspace.py`):

- Question and current response excerpt  
- Editorial score and forward rating  
- Reviewer notes  
- Weak sentences  
- Suggested improvements  
- Applicable editorial rules  
- Previous versions / improved version  

---

## Editorial rules

Append-only rules in `editorial_excellence/rules.py`. Examples:

| ID | Rule |
|----|------|
| ER-001 | Executive Summary must explain why this matters |
| ER-014 | Never classify without reasoning |
| ER-021 | Evidence bullets must vary sentence structure |
| ER-034 | Research Conclusion must identify remaining uncertainty |

Rules improve writing. They never modify reasoning.

---

## Style guide

**Prefer:** "The central investment debate…", "Current evidence indicates…", "The primary uncertainty…"

**Avoid:** good company, strong buy, cheap stock, bullish, bearish, marketing language

---

## Quality gates

A response cannot pass unless:

- Executive Summary exists  
- Investment Debate exists  
- Evidence supports conclusions  
- Key uncertainties explained  
- Research Conclusion complete  
- Questions Before You Decide included  
- No prohibited recommendation language  
- Editorial score ≥ 90  

---

## Hall of Fame

Location: `institutional_writing_benchmark/hall_of_fame/`

- **100** best responses (first 100 benchmark IDs)  
- Re-run on every writing-layer improvement  
- Compare old vs new editorial score  
- Keep new version only if objectively better  
- Prevents regressions while improving quality  

---

## Weekly and monthly review

**Weekly** (`editorial_excellence/reports.py`): review up to 100 benchmark responses — top improvements, common weaknesses, score trend.

**Monthly:** average scores, forward-without-editing %, most improved / weakest response, most common editorial issue.

No architecture changes. Only editorial refinement.

---

## Final principle

> Architecture creates capability.  
> Knowledge creates intelligence.  
> Editorial excellence creates trust.

From this point onward, sprints should improve institutional research **communication** rather than the number of architectural components.
