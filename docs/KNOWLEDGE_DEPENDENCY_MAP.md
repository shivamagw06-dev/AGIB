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
Investment Intelligence        ← Phase 3.2 (thesis / quality / scenarios / committee)
        │                         consumes BI + Industry DNA; no BUY/SELL
        ▼
Portfolio Intelligence         ← later (multi-name / risk / allocation)
                                  consumes Investment + Industry DNA
```

## Ask / KUL path

```
Question
  → Knowledge Planner
  → Industry Intelligence Provider   (pure industry / KPI / valuation pedagogy)
  → Business Intelligence Provider   (company business model / moat / comparison)
  → Investment Intelligence Provider (thesis / quality / catalysts / scenarios)  ← after 3.2 acceptance
  → CapIQ / IKL / Memory / KF
  → Evidence Fusion
  → Executive Composer
```

## Rules

1. **Industry DNA is canonical** for industry economics, KPIs, valuation methods, regulation, competition, cycles, and industry risks.
2. **Business Intelligence asks Industry Intelligence** (or overlays DNA via `template_for`) — it must not maintain a parallel industry doctrine.
3. **Investment Intelligence consumes BI + Industry DNA** — never re-authors industry KPIs or valuation method maps; never issues BUY/SELL.
4. **Portfolio** layers must depend downward on Investment Intelligence.
5. **No parallel Ask routers** — providers register only inside KUL.
6. **Core unchanged** — higher layers extend Core.

## Freeze implication

Phase 3.2 freezes only when Investment Acceptance (300), Investment Integration, Founder V4, and the production regression stack all pass — with zero hallucinations, zero recommendation leakage, and zero framework leakage.
