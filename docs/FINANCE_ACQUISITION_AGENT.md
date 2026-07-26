# Finance Acquisition Agent (FAA)

Upstream **live acquisition** layer for AGIB.

```text
FAA (Acquire) → FRE (Retrieve & Rank) → CAE → Ask AGI
```

## Responsibility split

| Layer | Job |
|-------|-----|
| **FAA** | Discover, download, parse, dedupe, index into FRE |
| **FRE** | Hybrid search, rerank, evidence validation, graph |
| **CAE** | Assemble context for reasoning |
| **Ask AGI** | Present the answer |

FAA never answers and never reasons.

## Enable live downloads

On Render → `intelligence-engine`:

```text
FAA_LIVE_FETCH=true
```

Optional search providers (any one):

```text
TAVILY_API_KEY=
SERPAPI_API_KEY=
EXA_API_KEY=
BING_SEARCH_API_KEY=
GOOGLE_CSE_API_KEY=
GOOGLE_CSE_ID=
```

## Test

```bash
# Discover only
curl -H "Authorization: Bearer $TOKEN" \
  "$ENGINE/v1/faa/discover?q=Should%20I%20buy%20Reliance%3F"

# Acquire + index into FRE
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "$ENGINE/v1/faa/acquire?q=Should%20I%20buy%20Reliance%3F"

# FRE query now includes acquisition block
curl -H "Authorization: Bearer $TOKEN" \
  "$ENGINE/v1/fre/query?q=Should%20I%20buy%20Reliance%3F"
```

Look for:

```json
{
  "acquisition": {
    "programme": "FAA",
    "live_fetch": true,
    "fetched": 3,
    "indexed_to_fre": 3
  },
  "top_sources": [
    {
      "url": "https://www.ril.com/...",
      "metadata": { "faa_live_fetch": true }
    }
  ]
}
```

If `live_fetch` is false, FAA is still running the acquisition pipeline in offline/stub mode.
