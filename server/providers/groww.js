/**
 * Groww Trading API provider — primary market data source.
 * Docs: https://groww.in/trade-api/docs/curl
 *
 * Auth: set GROWW_ACCESS_TOKEN (daily token from Groww dashboard)
 *   or GROWW_API_KEY + GROWW_API_SECRET for checksum flow.
 */

import crypto from 'crypto';

const GROWW_BASE = process.env.GROWW_API_BASE || 'https://api.groww.in/v1';

let cachedToken = null;
let tokenExpiry = 0;

async function ensureFetch() {
  if (typeof globalThis.fetch === 'function') return globalThis.fetch.bind(globalThis);
  const mod = await import('node-fetch');
  return mod.default;
}

function generateChecksum(secret, timestamp) {
  return crypto.createHash('sha256').update(secret + timestamp).digest('hex');
}

async function resolveAccessToken() {
  const direct = (process.env.GROWW_ACCESS_TOKEN || '').trim();
  if (direct) return direct;

  if (cachedToken && Date.now() < tokenExpiry) return cachedToken;

  const apiKey = (process.env.GROWW_API_KEY || '').trim();
  const apiSecret = (process.env.GROWW_API_SECRET || '').trim();
  if (!apiKey || !apiSecret) return null;

  const timestamp = Math.floor(Date.now() / 1000).toString();
  const checksum = generateChecksum(apiSecret, timestamp);
  const fetchFn = await ensureFetch();

  const resp = await fetchFn(`${GROWW_BASE}/token/api/access`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({ key_type: 'approval', checksum, timestamp }),
  });

  const json = await resp.json().catch(() => ({}));
  if (json?.token) {
    cachedToken = json.token;
    tokenExpiry = Date.now() + 23 * 60 * 60 * 1000;
    return cachedToken;
  }
  return null;
}

export function isGrowwConfigured() {
  return Boolean(
    (process.env.GROWW_ACCESS_TOKEN || '').trim() ||
      ((process.env.GROWW_API_KEY || '').trim() && (process.env.GROWW_API_SECRET || '').trim())
  );
}

async function growwRequest(path, params = {}) {
  const token = await resolveAccessToken();
  if (!token) throw new Error('Groww API not configured');

  const url = new URL(`${GROWW_BASE}${path}`);
  Object.entries(params).forEach(([k, v]) => {
    if (v != null && v !== '') url.searchParams.set(k, String(v));
  });

  const fetchFn = await ensureFetch();
  const resp = await fetchFn(url.toString(), {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/json',
      'X-API-VERSION': '1.0',
    },
  });

  const json = await resp.json().catch(() => ({}));
  if (json?.status === 'SUCCESS') return json.payload;
  throw new Error(json?.error?.message || `Groww request failed (${resp.status})`);
}

/** Batch LTP — up to 50 symbols per call */
export async function getLTP(exchangeSymbols, segment = 'CASH') {
  if (!exchangeSymbols?.length) return {};
  const payload = await growwRequest('/live-data/ltp', {
    segment,
    exchange_symbols: exchangeSymbols.join(','),
  });
  return payload || {};
}

/** Full quote for a single instrument */
export async function getQuote(exchange, segment, tradingSymbol) {
  return growwRequest('/live-data/quote', {
    exchange,
    segment,
    trading_symbol: tradingSymbol,
  });
}

/** Batch OHLC */
export async function getOHLC(exchangeSymbols, segment = 'CASH') {
  if (!exchangeSymbols?.length) return {};
  return growwRequest('/live-data/ohlc', {
    segment,
    exchange_symbols: exchangeSymbols.join(','),
  });
}

export const TICKER_INSTRUMENTS = [
  { id: 'nifty50', label: 'NIFTY 50', exchange: 'NSE', symbol: 'NIFTY', growwKey: 'NSE_NIFTY' },
  { id: 'banknifty', label: 'BANK NIFTY', exchange: 'NSE', symbol: 'BANKNIFTY', growwKey: 'NSE_BANKNIFTY' },
  { id: 'sensex', label: 'SENSEX', exchange: 'BSE', symbol: 'SENSEX', growwKey: 'BSE_SENSEX' },
  { id: 'vix', label: 'INDIA VIX', exchange: 'NSE', symbol: 'INDIA VIX', growwKey: 'NSE_INDIA VIX' },
];

/** Fetch normalized ticker rows from Groww */
export async function fetchGrowwTicker() {
  const instruments = TICKER_INSTRUMENTS;
  const keys = instruments.map((i) => i.growwKey);

  const [ltpMap, ...quotes] = await Promise.all([
    getLTP(keys).catch(() => ({})),
    ...instruments.map((inst) =>
      getQuote(inst.exchange, 'CASH', inst.symbol).catch(() => null)
    ),
  ]);

  return instruments.map((inst, idx) => {
    const quote = quotes[idx];
    const price = quote?.last_price ?? ltpMap[inst.growwKey] ?? null;
    const change = quote?.day_change ?? null;
    const percentChange = quote?.day_change_perc ?? null;
    return {
      id: inst.id,
      name: inst.label,
      price,
      change,
      percentChange,
      source: 'groww',
    };
  });
}
