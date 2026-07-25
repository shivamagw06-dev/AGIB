/**
 * Yahoo Finance chart fallback for Indian cash indices.
 * Used when Groww / NSE are unavailable (common on cloud hosts that block NSE).
 */

async function ensureFetch() {
  if (typeof globalThis.fetch === 'function') return globalThis.fetch.bind(globalThis);
  const mod = await import('node-fetch');
  return mod.default;
}

/** Snapshot labels used by the Investment Office Market Snapshot. */
export const YAHOO_INDEX_MAP = [
  { symbol: '^NSEI', name: 'NIFTY' },
  { symbol: '^NSEBANK', name: 'BANK NIFTY' },
  { symbol: '^BSESN', name: 'SENSEX' },
  { symbol: 'NIFTY_MIDCAP_100.NS', name: 'MIDCAP' },
  { symbol: '^CNXSC', name: 'SMALLCAP' },
  { symbol: '^INDIAVIX', name: 'VIX' },
];

function pctFromCloses(price, prevClose) {
  const last = Number(price);
  const prev = Number(prevClose);
  if (!Number.isFinite(last) || !Number.isFinite(prev) || prev === 0) return null;
  return ((last - prev) / prev) * 100;
}

async function fetchYahooSymbol(fetchFn, symbol) {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1d&range=5d`;
  const resp = await fetchFn(url, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      'User-Agent': 'Mozilla/5.0 (compatible; AGIB-UI/1.0)',
    },
    signal: AbortSignal.timeout(10_000),
  });
  if (!resp.ok) return null;
  const json = await resp.json().catch(() => null);
  const result = json?.chart?.result?.[0];
  const meta = result?.meta;
  if (!meta) return null;

  const closes = (result?.indicators?.quote?.[0]?.close || []).filter((x) => x != null);
  const price = Number(meta.regularMarketPrice ?? closes.at(-1));
  const prevClose = Number(closes.length >= 2 ? closes.at(-2) : meta.chartPreviousClose);
  if (!Number.isFinite(price)) return null;

  return {
    price,
    percentChange: pctFromCloses(price, prevClose),
    source: 'yahoo',
  };
}

/**
 * @returns {Promise<Array<{ name: string, price: number, percentChange: number|null, source: string }>>}
 */
export async function fetchYahooIndices(wantedNames = null) {
  const fetchFn = await ensureFetch();
  const allow = wantedNames
    ? new Set([...wantedNames].map((n) => String(n).toUpperCase()))
    : null;

  const targets = YAHOO_INDEX_MAP.filter((row) => !allow || allow.has(row.name));
  const settled = await Promise.allSettled(
    targets.map(async (row) => {
      const quote = await fetchYahooSymbol(fetchFn, row.symbol);
      if (!quote) return null;
      return {
        name: row.name,
        price: quote.price,
        percentChange: quote.percentChange,
        source: 'yahoo',
      };
    })
  );

  return settled
    .map((r) => (r.status === 'fulfilled' ? r.value : null))
    .filter(Boolean);
}
