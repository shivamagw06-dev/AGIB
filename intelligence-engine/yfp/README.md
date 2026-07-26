# Yahoo Finance Institutional Provider (YFP V1)

**Not an engine.** Secondary MarketData provider adapter under the existing Provider Registry.

## Priority

```
Official Exchange → IndianAPI (10) → Finnhub (20) → FMP (30) → Yahoo (40)
```

Yahoo enriches; it never overwrites higher-confidence institutional fields in CID.

## Canonical only

Adapters map Yahoo modules into:

- `MarketDataQuote`
- `OHLCVSeries`
- `CorporateAction`
- `FundamentalSnapshot` (profile / ratios / statements / ownership as metrics)
- `CalendarEvent` (earnings / upgrades / SEC)
- `OptionChain` (store only)

Downstream engines never see Yahoo-native payloads.

## Flags

```
YAHOO_PROVIDER=true
YAHOO_PROFILE=true
YAHOO_FINANCIALS=true
YAHOO_EARNINGS=true
YAHOO_VALUATION=true
YAHOO_OWNERSHIP=true
YAHOO_OPTIONS=true
```

## Soft wiring

- `MarketDataClient.from_settings` registers Yahoo
- LEO source `yahoo` → evidence objects
- CID `get_or_build` / `yfp.enrich_cid` soft-merge
- Admin `/admin/yahoo-provider`
- API `/v1/yfp/*`
