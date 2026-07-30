# RH-01 — AGI Release Health

The single screen before every release.

## Scorecard

| Row | Meaning |
| --- | --- |
| Build | Product + core packages present / importable |
| Unit Tests | Curated pytest smoke (CW / IST / IBS / E2E) |
| Integration | IST · IBS · E2E · CW health OK |
| IST | 2/2 (IST-01 + IST-02) |
| IBS | 39/39 |
| E2E | 1/1 |
| Average Benchmark | IBS suite average |
| Hallucinations | Must be 0 |
| Broken Provenance | Must be 0 |
| Regression | Must not fall vs previous suite |
| Performance | E2E latency gate |
| Ready for Release | YES only if every gate passes |

## How to access

1. **Admin UI (primary)** — [/admin/release-health](/admin/release-health)  
   Also in Admin nav: **Release Health** (near the top).
2. **Product Settings** — [/agi/settings](/agi/settings) → Open Release Health
3. **API**
   - `GET /api/intelligence/release-health/dashboard`
   - `POST /api/intelligence/release-health/run`
4. **CLI**
   ```bash
   cd intelligence-engine
   PYTHONPATH=. python3 -m release_health --run
   ```

## Ready for Release = YES

Means Build, Unit Tests, Integration, IST 2/2, IBS 39/39, E2E 1/1, average ≥ 85, zero hallucinations, zero broken provenance, no regression, performance PASS.
