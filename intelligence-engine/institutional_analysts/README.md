# Institutional Analyst Framework (IAF V1)

Answer Construction orchestration only. **Not an engine.**

## Locked architecture

Does **not** redesign CID, LEO, IRP, Company Analysis, Financial Intelligence,
Company Monitor, Knowledge Foundation, Academy, DVC, ECP, MarketDataClient, or providers.

No new data. No new intelligence. Ownership of existing intelligence only.

## Flow

```text
Question
  → Research Planner
  → Business / Financial / Valuation / Market / Sector / Macro / Risk / Management / Ownership Analysts
  → Investment Committee
  → Chief Investment Officer
  → Institutional Report
```

## Rules

- Each analyst answers **one** question and must not repeat another analyst.
- Analysts only **read** existing packs; they never call providers.
- Committee reads **analyst opinions only** (never raw APIs / CID / statements).
- CIO reads **committee summary only**.
- User-facing copy must never expose internal engine, provider, or API names.

## Package layout

```text
institutional_analysts/
  business/ financial/ valuation/ market/ sector/ macro/
  risk/ management/ ownership/
  committee/
  cio/
  production.py   # planner → analysts → committee → CIO
```

## Soft-wire

`answer_construction.production.package_for_ask_agi` soft-calls IAF, then applies
Answer Construction V3 policy. Flags: `institutional_analysts`, `ask_agi_iaf`.
