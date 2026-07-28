# Institutional Government & Regulatory Intelligence (IGRI) — AGIB v2.0 Sprint 3

## Role

Soft Knowledge Factory package that maps **Indian government & regulatory policy** to sectors, industries, companies, macro, corporate events, and portfolio context.

**Never** political opinion. **Never** policy forecasts. **Never** fabricate.

## Dependency

```
Company Intelligence → Corporate Events → Government & Regulatory Intelligence → …
```

## Freeze locks

Do not modify Phase 1–7 reasoning, framework selection, evidence contracts, committees, governance, learning, Decision Quality, KF architecture, Universe / Company / Corporate Event Intelligence.

## Modules

1. Government Registry (ministries / regulators)
2. RBI Intelligence
3. Union Budget
4. SEBI Intelligence
5. MCA Intelligence
6. GST Intelligence
7. PLI Intelligence
8. Trade Policy
9. Industry Regulation
10. State Government framework (extensible)

## Point-in-time

Every policy stores `announcement_date`, `effective_date`, `available_from`.

Replay: `available_from <= as_of`.

## APIs (read-only)

`/v1/government/{dashboard,policies,policy/{id},search,rbi,sebi,budget,gst,pli,trade,timeline}`
