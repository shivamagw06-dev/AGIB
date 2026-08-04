/**
 * Upstox key-ratios → warehouse.valuation_ratios via intelligence engine.
 * Resolves ISIN from company_master; never uses ticker for the Upstox call.
 */

function engineConfig() {
  let baseUrl = (process.env.AGIB_INTELLIGENCE_ENGINE_URL || process.env.INTELLIGENCE_ENGINE_URL || '').replace(/\/$/, '');
  if (baseUrl && !/^https?:\/\//i.test(baseUrl)) baseUrl = `https://${baseUrl}`;
  const token = (process.env.AGIB_SERVICE_TOKEN || process.env.INTELLIGENCE_ENGINE_TOKEN || '').trim();
  return { baseUrl, token };
}

async function engineFetch(path, { method = 'GET', body = null, timeoutMs = 120_000 } = {}) {
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

/**
 * Load companies with ISINs from warehouse company_master.
 */
export async function loadIsinUniverse({ limit = 500 } = {}) {
  const result = await engineFetch(
    `/v1/warehouse/tab/company_master?limit=${Math.max(1, Number(limit) || 500)}`
  );
  const rows = result.data?.rows || result.data?.data || [];
  return Array.isArray(rows) ? rows : [];
}

function pickIsinCompanies(rows, { limit = 200 } = {}) {
  const out = [];
  const seen = new Set();
  for (const row of rows || []) {
    const symbol = String(row.symbol || '').trim().toUpperCase();
    const isin = String(row.isin || '').trim().toUpperCase();
    if (!symbol || !isin || seen.has(isin)) continue;
    if (!/^IN[A-Z0-9]{10}$/.test(isin) && !/^INE[A-Z0-9]{9}$/.test(isin)) continue;
    seen.add(isin);
    out.push({
      symbol,
      isin,
      company_id: row.company_id || symbol,
      instrument_key: row.instrument_key || `NSE_EQ|${isin}`,
      sector: row.sector || null,
    });
    if (out.length >= limit) break;
  }
  return out;
}

/**
 * Fetch Upstox key-ratios for a company list and ingest into warehouse.
 */
export async function refreshUpstoxValuationRatios({
  limit = Number(process.env.UPSTOX_VALUATION_BATCH || 80),
  concurrency = Number(process.env.UPSTOX_VALUATION_CONCURRENCY || 4),
  symbols = null,
} = {}) {
  const { getFundamentals, isUpstoxConfigured } = await import('../providers/upstox.js');
  if (!isUpstoxConfigured()) {
    return { ok: false, status: 503, error: 'upstox_not_configured' };
  }

  let companies = [];
  if (Array.isArray(symbols) && symbols.length) {
    // Resolve ISINs for explicit symbols from warehouse master.
    const all = await loadIsinUniverse({ limit: 5000 });
    const want = new Set(symbols.map((s) => String(s).toUpperCase()));
    companies = pickIsinCompanies(all.filter((r) => want.has(String(r.symbol || '').toUpperCase())), {
      limit: symbols.length,
    });
  } else {
    const all = await loadIsinUniverse({ limit: Math.max(limit * 3, 500) });
    companies = pickIsinCompanies(all, { limit });
  }

  if (!companies.length) {
    return { ok: false, status: 404, error: 'no_isin_universe', fetched: 0, ingested: 0 };
  }

  const reportedDate = new Date().toISOString().slice(0, 10);
  const batch = [];
  const errors = [];
  let cursor = 0;

  async function worker() {
    while (cursor < companies.length) {
      const idx = cursor;
      cursor += 1;
      const company = companies[idx];
      try {
        const json = await getFundamentals(company.isin, 'key-ratios');
        batch.push({
          symbol: company.symbol,
          isin: company.isin,
          company_id: company.company_id,
          instrument_key: company.instrument_key,
          reported_date: reportedDate,
          data: json?.data || json,
        });
      } catch (err) {
        errors.push({
          symbol: company.symbol,
          isin: company.isin,
          error: err?.message || String(err),
          status: err?.status || null,
        });
      }
    }
  }

  const workers = Array.from({ length: Math.max(1, concurrency) }, () => worker());
  await Promise.all(workers);

  if (!batch.length) {
    return {
      ok: false,
      status: 502,
      error: 'upstox_key_ratios_empty',
      attempted: companies.length,
      errors: errors.slice(0, 20),
    };
  }

  const ingest = await engineFetch('/v1/valuation-ratios/ingest', {
    method: 'POST',
    body: {
      companies: batch,
      actor: 'upstox_valuation_ratios_refresh',
      sync_valuation: true,
    },
    timeoutMs: 180_000,
  });

  return {
    ok: ingest.ok,
    status: ingest.status,
    attempted: companies.length,
    fetched: batch.length,
    failed: errors.length,
    errors: errors.slice(0, 20),
    warehouse: ingest.data,
    error: ingest.ok ? null : ingest.data?.error || `ingest_http_${ingest.status}`,
  };
}
