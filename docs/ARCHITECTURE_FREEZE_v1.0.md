# AGI Architecture Freeze v1.0 (Final)

**Effective:** 2026-08-05  
**Status:** Active — Final  
**Supersedes:** All prior architecture specifications  

---

## Declaration

AGI's core architecture is **frozen at v1.0**.

Future work prioritizes **knowledge quality, coverage, research accuracy, performance, and user experience** — not new frameworks, constitutions, or orchestration layers.

---

## Final frozen architecture

```text
Raw Data
    │
    ▼
Collectors
    │
    ▼
Knowledge Production Engine (KPE)
    ├── Compile Mode
    ├── Incremental Mode
    ├── Evidence Graph          ← KPE-owned infrastructure
    ├── Assertion Compiler      ← KPE sub-component
    └── Knowledge KPIs
    │
    ▼
Knowledge Objects (KO)
    │
    ▼
Knowledge Runtime (KR)
    │
    ▼
Research Workflow
    │
    ▼
Institutional Research Engine (IRE)
    │
    ▼
Ask / Workspace / APIs
```

---

## Component ownership

| Component | Owns | Never owns |
|-----------|------|----------|
| **Evidence Graph** | Evidence nodes, assertion links, provenance | Business logic, research conclusions, direct app queries |
| **KPE** | Compilation, extraction, graph writes, KO generation | User responses |
| **Knowledge Objects** | Canonical institutional understanding | Raw documents |
| **Knowledge Runtime** | Validation, dependency resolution, monitoring | Compilation, raw evidence storage |
| **IRE** | Research orchestration and presentation | Knowledge persistence |

### Evidence Graph rules

- **KPE owns Evidence Graph writes** (`institutional_knowledge_factory/evidence_graph.py`)
- **KR reads validated assertions**, resolving refs via graph pack — never stores raw evidence
- **IRE assembles research from Knowledge Objects**, not from the graph
- Applications **never query the Evidence Graph directly**
- Legacy `institutional_evidence_graph` module is telemetry only — not the canonical graph

---

## Engineering rule

Every new feature must answer:

> **Which existing component owns this responsibility?**

| If the answer is… | Then… |
|-------------------|-------|
| KPE, KR, KO, or IRE | Extend that component |
| None (demonstrably) | Only then consider a new component — requires architecture review |

---

## Stable components

| Component | Module |
|-----------|--------|
| **Knowledge Objects (KO)** | `institutional_knowledge_object` |
| **Knowledge Production Engine (KPE)** | `institutional_knowledge_factory` |
| **Evidence Graph (KPE infra)** | `institutional_knowledge_factory/evidence_graph.py` |
| **Assertion Compiler (KPE infra)** | `institutional_knowledge_factory/assertion_compiler.py` |
| **Knowledge Runtime (KR)** | `institutional_knowledge_runtime` |
| **Decision Memory** | `institutional_knowledge_factory/decision_memory` |
| **Research Workflow** | `research_workflow_framework` |
| **Institutional Research Engine (IRE)** | User-facing (internal orchestration TBD) |

Legacy names (`IKO`, `IKF`, `IKR`) remain as aliases during migration.

---

## Milestone 1 — NIFTY 50 Institutional Knowledge

**Definition of done** (replaces "PR merged"):

| Criterion | Target |
|-----------|--------|
| Companies compiled | 50/50 |
| Supported assertions per company | ≥ 10 |
| Evidence linked to every supported assertion | 100% |
| DNA sections populated | Business, Management, Financial, Valuation, Risk, Investment Thesis |
| Knowledge maturity grade | Computed per company |
| Monitoring rules | Active per company |
| Ask responses | Generated primarily from compiled KO + KR validation |

---

## Knowledge KPIs (product metrics)

```text
NIFTY 50 Compiled:              50/50
Knowledge Grade:                  A-
Average Supported Assertions:     ≥ 10
Average Unknowns:                 ≤ 5
Average Contradictions:           ≤ 1
Evidence Coverage:                ≥ 90%
Stale Assertions:                 ≤ 5%
Last Refresh:                     < 24h
```

---

## Execution priorities (post-freeze)

1. NIFTY 50 compilation (`compile_universe`)
2. Wire Ask to assemble from compiled Knowledge Objects
3. Decision Memory durable store
4. Expand to NIFTY 500, then full market
5. Phased namespace migration (aliases only until Milestone 1)

---

## Deprioritized (frozen)

- New constitutions or methodology documents
- New orchestration layers
- Evidence Graph as standalone application layer
- Big-bang renames

---

*Architecture is complete. AGI becomes smarter through knowledge quality, not more specifications.*
