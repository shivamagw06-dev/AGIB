# AGIB Phase 3 — Quality Programme Roadmap

Operating rule: **no features because they sound useful**.  
Every sprint starts with a measured weakness and ends with a measurable improvement.

## Status

| Phase | Focus | Status |
|-------|-------|--------|
| Architecture | Platform structure | ✓ |
| Knowledge | Knowledge Factory domains | ✓ |
| Evidence | IERE + Evidence Graph | ✓ |
| Communication | ICE + Playbooks + Memory | ✓ |
| **Quality Engineering** | Evaluation → reasoning depth | **In progress** |

CIO frozen exam (post-IMAI): **8.12 / 10**

## Sprint sequence

| Sprint | Capability | Exit metric |
|--------|------------|-------------|
| **3.1 IEL** ✅ | Institutional Evaluation Lab | 1000+ Q suite + nightly judge + dashboard |
| **3.2 RCI** ✅ | Root Cause Intelligence | Top-10 clusters + recommended PRs |
| **3.3 FO** ✅ | Framework Optimisation + Patch Intelligence | Framework accuracy ≥96% (target 98%) |
| **3.4 IO** ✅ | Intent Optimisation | Intent accuracy ≥99% (**100.0%**; IEL **98.4%**) |
| **Release Cert v3.5** ⛔ | Baseline freeze (measure-only) | **NOT CERTIFIED** — future_leakage / replay / intent 99.8% |
| 3.5 | Evidence Weighting | Explicit source hierarchy in answers |
| 3.6 | Hypothesis Engine | Multi-hypothesis before conclusion |
| 3.7 | Contradiction Resolution | Reconcile conflicting signals |
| 3.8 | Committee Reasoning | Bull / Base / Bear on important Qs |
| 3.9 | Production Certification | Live collectors 100% / 7-day cert |

## Parallel production track

BSE → RBI → IR Parser → 7-Day Certification

## Stopping condition (not “all modules done”)

| Metric | Target | Latest (post Sprint 3.4 soft) |
|--------|-------:|------------------------------:|
| CIO benchmark | ≥9.0/10 | 8.12 (frozen exam; routing soft 100%) |
| IEL 1,025-question pass rate | ≥95% | **98.4%** |
| Framework accuracy | ≥98% | 97.7% |
| Intent accuracy | ≥99% | **100.0%** |
| Hallucinated evidence | 0 | 0 |
| Replay correctness | 100% | remaining `future_leakage` RCI cluster |
| Live collector certification | 100% | pending production track |

**Release certification (2026-07-28, commit `581f1363`):** **NOT CERTIFIED**.  
IEL full 1,025 pass **98.44%**, framework **97.76%**, intent **99.8%**, CIO-25 pass **100%**, but **future_leakage=15** and historical replay **73.21%** block freeze.  
See `docs/AGIB_RELEASE_CERTIFICATION_v3_5.md`. Do **not** start depth sprints as if the baseline were frozen — clear integrity gates first.

## Tool roles (when purchased)

| Tool | Role |
|------|------|
| Claude Code | Large implementation sprints |
| Cursor Ultra | Day-to-day coding |
| ChatGPT | Architecture / roadmap reviews |
| LangSmith | Nightly evaluation + experiment tracking |
| Firecrawl | Institutional document ingestion |
| Exa | Research discovery / evidence expansion |
