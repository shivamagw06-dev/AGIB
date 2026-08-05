# AGI Architecture Freeze v1.0

**Effective:** 2026-08-05  
**Status:** Active  
**Supersedes:** All prior architecture specifications as living design documents  

---

## Declaration

AGI's core architecture is **frozen at v1.0**.

From this date forward, work prioritizes **knowledge quality, coverage, research accuracy, performance, and user experience** — not new frameworks, constitutions, or orchestration layers.

---

## Stable components

Changes to these require **exceptional justification** and architecture review:

| Component | Module | Role |
|-----------|--------|------|
| **Knowledge Objects (KO)** | `institutional_knowledge_object` | Claim-centric institutional memory |
| **Knowledge Production Engine (KPE)** | `institutional_knowledge_factory` | Compile + Incremental modes |
| **Knowledge Runtime (KR)** | `institutional_knowledge_runtime` | Validation, selection, versioning |
| **Evidence Graph** | `institutional_evidence_graph` (in build) | Evidence → assertion edges |
| **Decision Memory** | `institutional_knowledge_factory/decision_memory` | Explainable evolution |
| **Research Workflow** | `research_workflow_framework` | Session orchestration |
| **Institutional Playbooks** | `institutional_playbook_framework` | Research methodology |
| **Ask Intelligence** | `ask_intelligence_constitution` | Response methodology |
| **Response Layer** | `response_constitution` | Institutional voice |

Legacy names (`IKO`, `IKF`, `IKR`, `IKC`) remain as aliases during migration.

---

## Canonical stack

```text
Evidence Sources
  ↓
Evidence Graph
  ↓
Knowledge Production Engine (KPE)
  ├── Compile Mode      (historical / backfill / rebuild)
  └── Incremental Mode  (filings / earnings / live updates)
  ↓
Knowledge Objects (KO)
  ↓
Knowledge Runtime (KR)
  ↓
Research Workflow
  ↓
Institutional Research Engine (IRE)   ← user-facing experience
  ↓
Response
```

---

## Knowledge Production Engine — two modes, one engine

| Mode | Entry point | Use case |
|------|-------------|----------|
| **Compile** | `compile_company()` | First population, rebuild, migration, repair |
| **Incremental** | `process_evidence()` | Earnings, filings, news, management changes |

There is **one production engine**. Not separate Factory and Compiler architectures.

---

## Governance rule

> **No new architectural component may be added unless an existing component demonstrably cannot solve the problem.**

---

## Future work priorities (in order)

1. **NIFTY 50 compilation** — 100% compiled, evidence-linked, Ask powered by KO
2. **Evidence Graph persistence** — durable evidence → assertion edges
3. **Decision Memory store** — durable version history
4. **Knowledge KPI dashboard** — product metrics, not module counts
5. **Expand universe** — NIFTY 500, then full market
6. **Institutional Research Engine (IRE)** — user experience over internal orchestration names

---

## Deprioritized (frozen)

- New constitutions or methodology documents
- New orchestration layers
- New runtime abstractions
- Namespace renames (gradual aliases only until Milestone 1 complete)

---

## Success metrics — Knowledge KPIs

Track product outcomes, not architecture artifacts:

```text
NIFTY 50 Compiled:           50/50
Knowledge Grade:             A-
Average Supported Claims:    18.4
Average Unknowns:            3.2
Average Contradictions:      0.8
Evidence Coverage:           94%
Stale Assertions:            2%
Last Refresh:                3h
```

---

## Milestone 1

**Institutional Knowledge Milestone 1 — NIFTY 50**

- [ ] 100% compiled
- [ ] Evidence linked
- [ ] Company DNA generated
- [ ] Investment thesis generated
- [ ] Monitoring active
- [ ] Ask powered entirely by Knowledge Objects

This milestone replaces "PR merged" as the definition of done.

---

## Namespace migration (phased)

| Current | Target | Phase |
|---------|--------|-------|
| `institutional_knowledge_object` | `knowledge/objects` | Post-Milestone 1 |
| `institutional_knowledge_factory` | `knowledge/production` | Post-Milestone 1 |
| `institutional_knowledge_runtime` | `knowledge/runtime` | Post-Milestone 1 |
| Investment OS (internal) | Institutional Research Engine (IRE) | UX naming |

**Do not big-bang rename.** Aliases and re-exports until Milestone 1 is demonstrated.

---

*Architecture is complete. AGI becomes smarter through knowledge quality, not more specifications.*
