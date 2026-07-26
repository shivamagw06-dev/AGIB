# Institutional Regression Suite (IRS) V1

**Primary question:** Did this pull request make AGIB smarter?

**Architecture status:** v1.0.1 LOCKED  
Soft final gate after Certification (ACS). No engine / UI / provider / ACS / Academy redesign.

## Architecture position

Books → Academy → Analysts → Committee → CIO → Research Writer → **ACS** → **IRS** → Release Report → Production

## Frozen golden set

`golden_set/v1/` is **immutable**. Never edit prior versions; create `v2/` for changes.

## Merge policy

Blocked if Overall IQ decreases, core reasoning decreases, critical hallucinations rise, analyst drift rises, certification fails, recommendation policy violated, or golden benchmark floor fails.

## APIs

- `GET /v1/academy/regression/health`
- `GET /v1/academy/regression/dashboard`
- `POST /v1/academy/regression/run`
- `POST /v1/academy/regression/gate`
- `GET /v1/academy/regression/quality-gates`
- `GET /v1/academy/regression/history`
- `GET /admin/regression` — soft admin surface

## Flag

`institutional_regression_suite` / `INSTITUTIONAL_REGRESSION_SUITE`
