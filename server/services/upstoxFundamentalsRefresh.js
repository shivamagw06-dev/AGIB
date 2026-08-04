/**
 * Phase 7.4E — Upstox Institutional Fundamentals Integration (UIFI).
 *
 * Node fetches Upstox; intelligence-engine normalises → DQIV → warehouse.
 * Products never call Upstox from this path.
 */

import { loadIsinUniverse } from './upstoxValuationRatiosRefresh.js';

const DATASETS = Object.freeze([
  'profile',
  'income-statement',
  'balance-sheet',
  'cash-flow',
  'share-holdings',
  'competitors',
  'corporate-actions',
]);

function engineConfig() {
  let baseUrl = (process.env.AGIB_INTELLIGENCE_ENGINE_URL || process.env.INTELLIGENCE_ENGINE_URL || '').replace(/\/$/, '');
  if (baseUrl && !/^https?:\/\//i.test(baseUrl)) baseUrl = `https://${baseUrl}`;
  const token = (process.env.AGIB_SERVICE_TOKEN || process.env.INTELLIGENCE_ENGINE_TOKEN || '').trim();
  return { baseUrl, token };
}

async function engineFetch(path, { method = 'GET', body = null, timeoutMs = 180_000 } = {}) {
  const { baseUrl, token } = engineConfig();
  if (!baseUrl || !token) {
    return { ok: false, status: 503, data: { error: 'intelligence_engine_not_configured' } };
  }
  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      'X-AGI-Intelligence-Token': token,
    },
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(timeoutMs),
  });
  const text = await response.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: String(text || '').slice(0, 400) };
  }
  return { ok: response.ok, status: response.status, data };
}

function pickIsinCompanies(rows, { limit = 40, symbols = null } = {}) {
  const want = Array.isArray(symbols) && symbols.length
    ? new Set(symbols.map((s) => String(s).toUpperCase()))
    : null;
  const out = [];
  const seen = new Set();
  for (const row of rows || []) {
    const symbol = String(row.symbol || '').trim().toUpperCase();
    const isin = String(row.isin || '').trim().toUpperCase();
    if (!symbol || !isin || seen.has(isin)) continue;
    if (want && !want.has(symbol)) continue;
    seen.add(isin);
    out.push({
      symbol,
      isin,
      company_id: row.company_id || symbol,
      instrument_key: row.instrument_key || `NSE_EQ|${isin}`,
      sector: row.sector || null,
      industry: row.industry || null,
    });
    if (out.length >= limit) break;
  }
  return out;
}

function buildIsinMap(rows) {
  const map = {};
  for (const row of rows || []) {
    const isin = String(row.isin || '').trim().toUpperCase();
    const symbol = String(row.symbol || '').trim().toUpperCase();
    if (isin && symbol) map[isin] = symbol;
  }
  return map;
}

/**
 * Refresh one fundamentals dataset for a batch of ISIN-mapped companies.
 */
export async function refreshUpstoxFundamentals({
  dataset = 'profile',
  limit = Number(process.env.UIFI_BATCH || 40),
  concurrency = Number(process.env.UIFI_CONCURRENCY || 3),
  symbols = null,
} = {}) {
  const ds = String(dataset || '').trim().toLowerCase();
  if (!DATASETS.includes(ds) && ds !== 'statements') {
    return { ok: false, status: 400, error: `unsupported_dataset:${ds}`, datasets: DATASETS };
  }

  const { getFundamentals, getCompetitors, isUpstoxConfigured } = await import('../providers/upstox.js');
  if (!isUpstoxConfigured()) {
    return { ok: false, status: 503, error: 'upstox_not_configured' };
  }

  const universe = await loadIsinUniverse({ limit: Math.max(limit * 5, 5000) });
  const companies = pickIsinCompanies(universe, { limit, symbols });
  if (!companies.length) {
    return { ok: false, status: 404, error: 'no_isin_universe', dataset: ds };
  }

  const isinMap = buildIsinMap(universe);
  const batch = [];
  const errors = [];
  let cursor = 0;

  async function worker() {
    while (cursor < companies.length) {
      const idx = cursor;
      cursor += 1;
      const company = companies[idx];
      try {
        if (ds === 'statements') {
          const [income, balance, cash] = await Promise.all([
            getFundamentals(company.isin, 'income-statement'),
            getFundamentals(company.isin, 'balance-sheet'),
            getFundamentals(company.isin, 'cash-flow'),
          ]);
          batch.push({
            symbol: company.symbol,
            isin: company.isin,
            company_id: company.company_id,
            instrument_key: company.instrument_key,
            dataset: 'statements',
            'income-statement': income,
            'balance-sheet': balance,
            'cash-flow': cash,
          });
        } else if (ds === 'competitors') {
          const key = company.instrument_key || `NSE_EQ|${company.isin}`;
          const json = await getCompetitors(key);
          batch.push({
            symbol: company.symbol,
            isin: company.isin,
            instrument_key: key,
            sector: company.sector,
            industry: company.industry,
            isin_map: isinMap,
            data: json?.data || json,
          });
        } else {
          const json = await getFundamentals(company.isin, ds);
          batch.push({
            symbol: company.symbol,
            isin: company.isin,
            company_id: company.company_id,
            instrument_key: company.instrument_key,
            data: json?.data || json,
            units_in: json?.data?.units_in,
          });
        }
      } catch (err) {
        errors.push({
          symbol: company.symbol,
          isin: company.isin,
          dataset: ds,
          error: err?.message || String(err),
          status: err?.status || null,
        });
      }
    }
  }

  await Promise.all(Array.from({ length: Math.max(1, concurrency) }, () => worker()));

  if (!batch.length) {
    return {
      ok: false,
      status: 502,
      error: 'upstox_fundamentals_empty',
      dataset: ds,
      attempted: companies.length,
      errors: errors.slice(0, 20),
    };
  }

  const ingestDataset = ds === 'statements' ? 'statements' : ds;
  const ingest = await engineFetch('/v1/upstox-fundamentals/ingest', {
    method: 'POST',
    body: {
      dataset: ingestDataset,
      companies: batch,
      actor: `uifi_${ingestDataset.replace(/-/g, '_')}`,
    },
  });

  return {
    ok: Boolean(ingest?.ok && ingest?.data?.ok !== false),
    status: ingest?.status,
    dataset: ds,
    attempted: companies.length,
    fetched: batch.length,
    errors: errors.slice(0, 20),
    ingest: ingest?.data || ingest,
  };
}

export async function getUifiCoverage() {
  const result = await engineFetch('/v1/upstox-fundamentals/coverage');
  return result.data || { ok: false, error: 'coverage_unavailable' };
}

export async function getUifiFailures() {
  const result = await engineFetch('/v1/upstox-fundamentals/failures');
  return result.data || { ok: false, error: 'failures_unavailable' };
}

export { DATASETS };
