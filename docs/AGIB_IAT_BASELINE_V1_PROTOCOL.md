# AGIB Institutional Acceptance Test — Baseline v1.0 Protocol

```text
OBJECTIVE:  Determine whether AGIB today performs like an institutional research platform.
BASELINE:   AGIB Institutional Baseline v1.0 (FROZEN)
SUITE:      Golden 200 + Question Battery + Governance + Ops + Human Review
STATUS:     PROTOCOL v1.0
```

This protocol **extends** the automated IAT (`institutional_evaluation_lab.iat`) with institutional question coverage and a human-review lane (Part G). It does **not** modify Constitution, Governance Spec, Decision Engine, or Gate thresholds.

---

## Part A — Company Coverage

| Universe | Count | Golden bucket |
| --- | ---: | --- |
| Nifty 50 | 50 | `nifty_50` |
| Nifty Next 50 | 50 | `nifty_next_50` |
| Midcap 150 (sample) | 50 | `midcap` |
| Smallcap 250 (sample) | 25 | `smallcap` |
| Special situations | 25 | `special_situation` |
| **Total** | **200** | Phase 1 Golden Universe v1.0 |

Composition is frozen (`composition_sha256` pinned). Editing tickers requires an explicit Golden v1.1 + IAT.

---

## Part B — Company Types

Difficult cases must be present in the 200. Minimum type coverage:

| Type | Intent |
| --- | --- |
| Large private bank | Franchise + credit quality |
| PSU bank | Policy / asset-quality overlay |
| NBFC | Liability / ALM sensitivity |
| FMCG | Brand / pricing power |
| IT | Export / margin franchise |
| Power | Regulated / cycle |
| Defence | Order-book / policy |
| Auto | Cycle / product |
| Cement | Commodity / regional |
| Pharma | Pipeline / regulation |
| Insurance | Embedded value / float |
| Consumer internet | Path-to-profit / unit economics |
| Loss-making growth company | Gate honesty under incomplete earnings |
| Cyclical commodity | Cycle timing vs quality |
| Holding company | SOTP / look-through (Golden v1.0 uses RELIANCE / GRASIM / ADANIENT as structure proxies) |
| Conglomerate | Segment complexity |

Automated check: `iat.company_types.evaluate_company_types()` maps Golden 200 → types via sector/profile heuristics and flags gaps.

---

## Part C — Questions

Do **not** ask only “Should I buy?”

| ID | Institutional question |
| --- | --- |
| **Test 1** | Can I buy this company today? |
| **Test 2** | Is this suitable for a long-term institutional portfolio? |
| **Test 3** | What is the investment thesis? |
| **Test 4** | What evidence prevents a recommendation? |
| **Test 5** | What would change your view? |
| **Test 6** | Why is the gate failing? |

For each company in scope, the suite records answers (or gate-withheld states) for all six tests. Soft smoke may run a stratified sample; official certification expects the full Golden 200 × 6 question matrix (or documented sampling plan with CI bounds).

---

## Part D — Evaluation (per company)

Score / report for every company:

| Dimension | Field |
| --- | --- |
| Business Quality | `company_quality` / business layer |
| Financial Quality | `financial_quality` |
| Management | management layer |
| Valuation | `valuation` |
| Macro | `macro` |
| Ownership | ownership coverage / pack |
| Technical | `technical` |
| Risk | `risk` |
| Opportunity | `investment_opportunity` / market opportunity |
| Readiness | `recommendation_readiness` + `institutional_readiness` |
| Confidence | analytical / evidence confidence |

These remain **separate concepts** — quality ≠ opportunity ≠ readiness ≠ confidence.

---

## Part E — Governance

Verify on the release under test:

| Check | Rule |
| --- | --- |
| Constitution | Enforced / stamped |
| GOV-001 | Readiness &lt; 80% ⇒ High Conviction prohibited |
| GOV-002 | Missing live price ⇒ valuation stale / unavailable |
| GOV-003 | Missing mandatory financials ⇒ thesis INCONCLUSIVE |
| GOV-004 | Missing ownership ⇒ readiness reduced |
| GOV-005 | Material filing pending ⇒ recommendation withheld |
| GOV-006 | Company Quality not reduced solely for missing data |
| GOV-007 | Editorial cannot override INCONCLUSIVE gate |
| GOV-008 | Recommendation includes evidence lineage |

Critical failures must be **0** for baseline qualification.

---

## Part F — Operational

Measure across the run:

| Metric | Intent |
| --- | --- |
| Runtime | Avg + p95 per company / release |
| Memory | Process / worker peak (ops note) |
| Coverage | Evidence + universe coverage |
| Freshness | Price / packs within SLA |
| Replay | Deterministic replay from stored inputs |
| Determinism | Replay match on compare fields |

---

## Part G — Institutional usefulness (human review)

Automated PASS/FAIL cannot certify research usefulness. For a stratified sample (minimum: 1 per Part B type, ≥20 names), reviewers score:

| Question | Review focus |
| --- | --- |
| Did the analysis actually help? | Decision usefulness |
| Was the thesis logical? | Causal coherence |
| Was the reasoning coherent? | Internal consistency |
| Were risks identified? | Left-tail honesty |
| Were missing evidence items correct? | Gate honesty |
| Was valuation sensible? | Multiple / method sanity |

**Scale:** `Helpful` / `Partial` / `Not helpful` (+ free-text).  
Part G does **not** alone freeze the baseline; it is required for institutional sign-off alongside automated Parts A–F PASS.

---

## Certification rule

```text
Automated Parts A–F PASS
        +
Part G human review completed (stratified sample)
        +
UNKNOWN drift = 0 (when comparing releases)
        │
        ▼
Eligible for Baseline freeze / re-affirmation
```

Machine entrypoints:

```bash
PYTHONPATH=. python -m institutional_evaluation_lab.iat --release PR309 --freeze
PYTHONPATH=. python -m institutional_evaluation_lab.iat --protocol
PYTHONPATH=. python -m institutional_evaluation_lab.iat --protocol-report --release PR309
```

APIs:

- `GET /institutional-evaluation-lab/iat/protocol`
- `POST /institutional-evaluation-lab/iat` (existing automated exam)
