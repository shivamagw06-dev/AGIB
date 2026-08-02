# Knowledge Dependency Map

Defines which intelligence layer depends on which. Later phases **consume** upstream DNA — they do not duplicate it.

```
Industry Intelligence          ← Phase 3.1 (Industry DNA — canonical)
        │
        ▼
Business Intelligence          ← Phase 3.0 (company model / moat / comparison)
        │                         consumes Industry DNA for industry economics,
        │                         KPIs, valuation methods, risks, Porter
        ▼
Investment Intelligence        ← later (thesis / valuation / decision)
        │                         consumes BI + Industry DNA
        ▼
Portfolio Intelligence         ← later (multi-name / risk / allocation)
                                  consumes Investment + Industry DNA
```

## Ask / KUL path (Phase 3.1.5)

```
Question
  → Knowledge Planner
  → Industry Intelligence Provider   (pure industry / KPI / valuation pedagogy)
  → Business Intelligence Provider   (company business model / moat / comparison)
  → CapIQ / IKL / Memory / KF
  → Evidence Fusion
  → Executive Composer
```

## Rules

1. **Industry DNA is canonical** for industry economics, KPIs, valuation methods, regulation, competition, cycles, and industry risks.
2. **Business Intelligence asks Industry Intelligence** (or overlays DNA via `template_for`) — it must not maintain a parallel industry doctrine.
3. **Investment / Portfolio** layers must depend downward; never re-author industry KPIs or valuation method maps.
4. **No parallel Ask routers** — providers register only inside KUL.
5. **Core v1.0 unchanged** — Industry / Business intelligence extend Core.

## Freeze implication

Phase 3.1 freezes only when Industry Acceptance, Industry Integration, Founder V3, and the production regression stack all pass — with zero hallucinations and zero framework leakage.
