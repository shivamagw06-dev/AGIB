/**
 * Fallback market data — NSE indices + IndianAPI commodities.
 * Used when Groww is unavailable or for instruments Groww doesn't cover.
 */

const INDEX_NAMES = ['NIFTY 50', 'NIFTY BANK', 'INDIA VIX'];

async function ensureFetch() {
  if (typeof globalThis.fetch === 'function') return globalThis.fetch.bind(globalThis);
  const mod = await import('node-fetch');
  return mod.default;
}

export async function fetchNseIndices() {
  const fetchFn = await ensureFetch();
  const resp = await fetchFn('https://www.nseindia.com/api/allIndices', {
    headers: {
      Accept: 'application/json',
      'User-Agent': 'Mozilla/5.0 (compatible; AGIB-Proxy/1.0)',
      Referer: 'https://www.nseindia.com/',
    },
  });
  const text = await resp.text().catch(() => '');
  if (!resp.ok || !text) return [];

  const payload = JSON.parse(text);
  const rows = Array.isArray(payload?.data) ? payload.data : [];
  const wanted = new Set(INDEX_NAMES.map((n) => n.toUpperCase()));

  return rows
    .filter((row) => {
      const name = String(row.index || row.indexSymbol || '').trim().toUpperCase();
      return wanted.has(name);
    })
    .map((row) => ({
      id: String(row.index || row.indexSymbol).toLowerCase().replace(/\s+/g, '-'),
      name: row.index || row.indexSymbol,
      price: row.last ?? row.previousClose ?? null,
      change: row.variation ?? null,
      percentChange: row.percentChange ?? null,
      source: 'nse',
    }));
}

export async function fetchCommodities(apiKey, baseUrl) {
  if (!apiKey) return [];
  const fetchFn = await ensureFetch();
  try {
    const resp = await fetchFn(`${baseUrl}/commodities`, {
      headers: { Accept: 'application/json', 'x-api-key': apiKey },
    });
    const json = await resp.json().catch(() => ({}));
    const items = json?.data || json?.commodities || json || [];
    const list = Array.isArray(items) ? items : [];

    const map = {
      gold: 'GOLD',
      silver: 'SILVER',
      brent: 'BRENT',
      'usd/inr': 'USD/INR',
      usdinr: 'USD/INR',
    };

    return list
      .filter((c) => {
        const key = String(c.name || c.commodity || c.symbol || '').toLowerCase();
        return Object.keys(map).some((k) => key.includes(k));
      })
      .slice(0, 4)
      .map((c) => ({
        id: String(c.name || c.commodity).toLowerCase().replace(/\s+/g, '-'),
        name: map[String(c.name || c.commodity).toLowerCase()] || c.name || c.commodity,
        price: c.price ?? c.last ?? c.value ?? null,
        change: c.change ?? null,
        percentChange: c.percent_change ?? c.percentChange ?? null,
        source: 'indianapi',
      }));
  } catch {
    return [];
  }
}

export async function fetchTrending(apiKey, baseUrl) {
  if (!apiKey) return { gainers: [], losers: [] };
  const fetchFn = await ensureFetch();
  try {
    const resp = await fetchFn(`${baseUrl}/trending`, {
      headers: { Accept: 'application/json', 'x-api-key': apiKey },
    });
    const json = await resp.json().catch(() => ({}));
    const trending = json?.trending_stocks || json?.data?.trending_stocks || json?.data || json || {};
    const gainers = (trending.top_gainers || trending.gainers || []).slice(0, 5);
    const losers = (trending.top_losers || trending.losers || []).slice(0, 5);
    return { gainers, losers, raw: trending };
  } catch {
    return { gainers: [], losers: [] };
  }
}
