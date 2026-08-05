# AGI Institutional Knowledge Factory (IKF) v1.0

**Document type:** Engineering Specification  
**Layer:** Knowledge Production Layer  
**Status:** Core Intelligence System  

---

## Mission

The **Institutional Knowledge Factory (IKF)** continuously transforms raw financial information into validated institutional knowledge.

AGI does not become smarter because it has more data. AGI becomes smarter because it continuously converts evidence into institutional knowledge.

IKF is the permanent knowledge production system.

---

## Purpose

IKF answers one question:

> How does AGI continuously improve its understanding of every listed company?

```text
Raw Evidence
  ↓
Knowledge Assertions
  ↓
Institutional Knowledge Objects (IKO)
  ↓
Research Intelligence
  ↓
Investment Intelligence
```

---

## Position in architecture

```text
Evidence Sources
  ↓
Institutional Knowledge Factory (IKF)     ← this spec (production)
  ↓
Evidence Graph (refs)
  ↓
Institutional Knowledge Runtime (IKR)     ← validation at consumption
  ↓
Institutional Knowledge Objects (IKO)
  ↓
Research Workflows → Ask → Investment OS
```

IKF **writes** knowledge (via approved writers). IKR **validates** knowledge at read time. LLMs are never writers.

---

## Input sources

| Source type | Trust baseline |
|-------------|----------------|
| `annual_report` | 90 |
| `quarterly_results` | 85 |
| `investor_presentation` | 80 |
| `conference_call` | 75 |
| `corporate_filing` | 88 |
| `exchange_announcement` | 82 |
| `shareholding_data` | 85 |
| `financial_statement` | 90 |
| `consensus_estimate` | 70 |
| `historical_price` | 75 |
| `corporate_action` | 85 |
| `macro_data` | 80 |
| `sector_data` | 78 |
| `alternative_data` | 65 |
| `analyst_research` | 72 |

Every source receives: `source_id`, `timestamp`, `trust_score`, `coverage`, `freshness`.

---

## Knowledge pipeline

```text
1. Collect
2. Normalize
3. Extract
4. Identify Claims
5. Validate Evidence
6. Resolve Contradictions
7. Update Assertions
8. Update Company DNA
9. Update Monitoring
10. Version Decision Memory
11. Notify Research Workflows
```

Implementation: `institutional_knowledge_factory/pipeline.py`

---

## Claim generation

IKF never stores raw documents as knowledge. It extracts institutional assertions.

Every assertion must contain:

- Statement  
- Evidence refs  
- Confidence  
- Dependencies  
- Monitoring rules  
- Review date  

Assertions without evidence remain `UNKNOWN`.

---

## Company DNA update

Company DNA is never rewritten. It evolves.

Every update records:

- Previous assertion  
- New assertion  
- Evidence added / removed  
- Reason  
- Timestamp  
- Confidence change  
- Impact  

Implementation uses IKR `update_assertion()` with writer `evidence_pipeline`.

---

## Thesis engine

Every company maintains:

- Current thesis  
- Bull thesis  
- Bear thesis  
- Key assumptions  
- Unknowns  
- Invalidation conditions  

When assertions change → re-evaluate investment thesis.

---

## Decision memory

Stores:

- Previous thesis  
- Assertion changes  
- Evidence changes  
- Research conclusions  

Every decision becomes explainable.

---

## Monitoring engine

Assertions define monitoring triggers. Threshold breach → `SUPPORTED` → `UNDER_REVIEW`.

Delegates status transitions to IKR monitoring evaluation.

---

## Knowledge quality

Every company receives measured (not assumed) quality:

| Metric | Description |
|--------|-------------|
| `knowledge_coverage` | Claims with non-UNKNOWN state |
| `assertion_coverage` | Required claims addressed |
| `evidence_coverage` | Claims with evidence refs |
| `freshness` | Average evidence freshness |
| `contradiction_count` | Active contradictions |
| `unknown_count` | Unresearched claims |
| `data_quality` | Source trust weighted score |
| `review_status` | healthy / needs_review / stale |

---

## Institutional review

IKF continuously surfaces:

- What do we now know?  
- What changed?  
- What became stronger / weaker / uncertain?  
- What should be monitored?  
- What research should be updated?  

---

## Outputs

- Updated Company DNA (IKO)  
- Updated assertions  
- Updated monitoring rules  
- Updated investment thesis  
- Updated decision memory  
- Evidence graph delta  
- Research notifications  

---

## Public API

| Method | Purpose |
|--------|---------|
| `process_evidence(entity_id, evidence_items)` | Run full factory pipeline |
| `normalize_source(raw)` | Normalize input source |
| `extract_claims(normalized)` | Identify claims from evidence |
| `update_company_dna(iko, updates)` | Append-only DNA evolution |
| `evaluate_thesis(iko, changes)` | Re-evaluate thesis |
| `record_decision_memory(...)` | Version decision trail |
| `compute_knowledge_quality(iko)` | Quality metrics |
| `institutional_review(iko, changes)` | Review questions |
| `apply_ikf(out, **kwargs)` | Soft-wire into answer pipeline |

---

## Writers

| Writer | Role |
|--------|------|
| `evidence_pipeline` | Primary IKF writer |
| `workflow_completion` | Post-research updates |
| `monitoring_engine` | Status/monitoring only |
| **LLM** | **Never** |

---

## Acceptance tests

| Test | Pass |
|------|------|
| Evidence normalized | ✓ |
| Claims extracted | ✓ |
| Assertions validated | ✓ |
| Company DNA updated (append-only) | ✓ |
| Thesis re-evaluated on change | ✓ |
| Decision memory versioned | ✓ |
| Knowledge quality computed | ✓ |
| Institutional review generated | ✓ |
| Research notifications emitted | ✓ |

---

## Non-goals

IKF does **not**:

- Generate prose for users  
- Perform valuation or forecasting  
- Issue recommendations  
- Store raw documents as knowledge  
- Use LLMs as writers  

---

## What comes next (build, not spec)

1. **Evidence Graph** — persistent evidence → assertion edges  
2. **Populate Company DNA** — NIFTY 50 high-quality assertions  
3. **Decision Memory store** — durable version history  
4. **Wire Ask** — assemble responses from validated assertions  
5. **Expand universe** — full Indian market  

*This is the last product intelligence specification. Next artifacts are build implementations.*
