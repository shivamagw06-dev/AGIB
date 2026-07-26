# FAA — Finance Acquisition Agent v1.0

Upstream **live evidence acquisition** layer for AGIB.

```text
FAA (Acquire) → FRE (Retrieve & Rank) → CAE (Assemble) → Ask AGI (Answer)
```

FAA never reasons and never answers users. It only:

1. Discovers public documents  
2. Downloads them (when live fetch is enabled)  
3. Parses / cleans  
4. Stores / dedupes by URL + SHA256  
5. Indexes into FRE  

## Four services

| Service | Responsibility |
|---------|----------------|
| Discovery | Intelligent task plan + connector routing |
| Fetch | HTTP/PDF/search download + cache |
| Processing | Clean text → FRE document objects |
| Index | Push into FRE chunk/embed/index |

## Connectors

- Company IR  
- NSE / BSE  
- SEBI / RBI / Government  
- Trusted news  
- Search API adapters: Tavily, SerpAPI, Exa, Bing, Google CSE  

## Live fetch

Default: `FAA_LIVE_FETCH=false` (offline-safe CI).

Enable on Render `intelligence-engine`:

```text
FAA_LIVE_FETCH=true
TAVILY_API_KEY=...   # optional
```

## APIs

`/v1/faa/health|dashboard|discover|acquire|connectors|jobs|consult|scheduler`

Node BFF: `/api/intelligence/faa/*`
