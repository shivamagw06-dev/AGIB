# AGI Phase 5 — Institutional Investment Office (AGI v4.0)

```text
COMPANY: AGI
RELEASE: AGI v4.0
FOUNDATION: AGI v3.6 Institutional Judgment (FROZEN)
STATUS: Sprint 5.4 IMO implemented
UPDATED: 2026-07-28
```

## Architecture

```text
Research Office
        │
        ▼
Investment Office
        │
 ┌──────┼────────┐
 ▼      ▼        ▼
Thesis Decision Portfolio
        │
        ▼
Monitoring (IMO)
        │
        ▼
Learning (5.5)
```

## Sprint sequence

| Sprint | Module | Status |
|--------|--------|--------|
| 5.1 | Investment Thesis (ITE) | ✓ |
| 5.2 | Decision Office (IDO) | ✓ |
| 5.3 | Portfolio Office (IPO) | ✓ |
| **5.4** | **Institutional Monitoring Office (IMO)** | ✓ v1.0.0 |
| 5.5 | Institutional Learning Office | ← Next |

## Independent metrics

IEL → HQS → CQS → CFQS → ITQS → DQS → PQS → **MQS**

## Hard rules

* Consume v3.6 judgment — do not modify it  
* Ideas ≠ positions ≠ orders ≠ execution  
* MonitoringEvents recommend review — they do not mutate thesis/decision/portfolio  
* Relative ranking over absolute “good company” calls  

## After Sprint 5.5

Declare **AGI v4.0 Investment Office** complete and spend a release cycle on
performance, UX, live integrations, observability, production hardening, and
institutional workflow validation — before adding more conceptual Office layers.
