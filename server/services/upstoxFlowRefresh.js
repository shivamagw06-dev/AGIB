/**
 * Upstox FII/DII → warehouse ingest via Market Intelligence Engine.
 * Shared by API route and daily EOD scheduler.
 */

export async function refreshUpstoxInstitutionalFlows({
  // Upstox market-insights FII/DII expects segment form NSE_EQ|CASH (not bare NSE_EQ).
  dataType = 'NSE_EQ|CASH',
  interval = '1D',
  date = undefined,
} = {}) {
  const { getMarketFiiDii } = await import('../providers/upstox.js');
  const pack = await getMarketFiiDii({ dataType, interval });

  const engineBase = process.env.AGIB_INTELLIGENCE_ENGINE_URL || process.env.INTELLIGENCE_ENGINE_URL;
  const token = process.env.AGIB_SERVICE_TOKEN || process.env.INTELLIGENCE_ENGINE_TOKEN;
  if (!engineBase || !token) {
    return {
      ok: false,
      status: 503,
      error: 'intelligence_engine_not_configured',
      upstox: pack,
      warehouse: null,
    };
  }

  const ingest = await fetch(`${String(engineBase).replace(/\/$/, '')}/v1/market-intelligence/flows/ingest`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      'X-AGI-Intelligence-Token': token,
    },
    body: JSON.stringify({ ...pack, date }),
    signal: AbortSignal.timeout(120_000),
  });

  const text = await ingest.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: String(text || '').slice(0, 400) };
  }

  return {
    ok: ingest.ok,
    status: ingest.status,
    upstox: pack,
    warehouse: data,
    error: ingest.ok ? null : data?.error || `ingest_http_${ingest.status}`,
  };
}
