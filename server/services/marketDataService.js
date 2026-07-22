/**
 * Unified market data service — Groww primary, NSE/IndianAPI fallback.
 * Provider-agnostic layer for frontend consumption.
 */

import { isGrowwConfigured, fetchGrowwTicker } from '../providers/groww.js';
import { fetchNseIndices, fetchCommodities, fetchTrending } from '../providers/fallback.js';
import { computeMarketOutlook, computeMarketPulse } from './marketOutlookEngine.js';

const CACHE = { ticker: null, tickerExpiry: 0, dashboard: null, dashboardExpiry: 0 };
const TICKER_TTL = 120_000;
const DASHBOARD_TTL = 180_000;

let tickerInflight = null;
let dashboardInflight = null;
let growwBackoffUntil = 0;

function findIndex(rows, ...names) {
  const set = new Set(names.map((n) => n.toUpperCase()));
  return rows.find((r) => set.has(String(r.name).toUpperCase())) || null;
}

function normalizeTrendingRow(row) {
  return {
    symbol: row.ticker || row.symbol || row.nse_code || row.company || '—',
    name: row.company || row.name || row.ticker || '—',
    price: row.current_price ?? row.price ?? row.ltp ?? null,
    change: row.percent_change ?? row.percentChange ?? row.change ?? null,
  };
}

export async function getTickerData(env = {}) {
  const now = Date.now();
  if (CACHE.ticker && now < CACHE.tickerExpiry) return CACHE.ticker;
  if (tickerInflight) return tickerInflight;

  tickerInflight = fetchTickerData(env).finally(() => {
    tickerInflight = null;
  });
  return tickerInflight;
}

async function fetchTickerData(env = {}) {
  const now = Date.now();
  const apiKey = env.indianApiKey || '';
  const baseUrl = env.indianApiBase || 'https://stock.indianapi.in';

  let rows = [];
  const growwAllowed = isGrowwConfigured() && now >= growwBackoffUntil;

  if (growwAllowed) {
    try {
      rows = await fetchGrowwTicker();
    } catch (err) {
      const msg = String(err?.message || err);
      console.warn('[marketData] Groww ticker failed:', msg);
      if (/rate limit|too many|429/i.test(msg)) {
        growwBackoffUntil = Date.now() + 5 * 60_000;
      }
    }
  }

  if (rows.length < 2) {
    const nseRows = await fetchNseIndices().catch(() => []);
    rows = [
      ...nseRows,
      ...rows.filter((r) => !nseRows.some((n) => n.name === r.name)),
    ];
  }

  const commodities = await fetchCommodities(apiKey, baseUrl).catch(() => []);

  const extraCommodities = [
    { id: 'usd-inr', name: 'USD/INR', price: null, change: null, percentChange: null, source: 'pending' },
    { id: 'gold', name: 'GOLD', price: null, change: null, percentChange: null, source: 'pending' },
    { id: 'silver', name: 'SILVER', price: null, change: null, percentChange: null, source: 'pending' },
    { id: 'brent', name: 'BRENT', price: null, change: null, percentChange: null, source: 'pending' },
    { id: 'gift-nifty', name: 'GIFT NIFTY', price: null, change: null, percentChange: null, source: 'pending' },
  ];

  for (const extra of extraCommodities) {
    const match = commodities.find(
      (c) => String(c.name).toUpperCase().includes(extra.name.split('/')[0])
    );
    if (match) rows.push(match);
    else rows.push(extra);
  }

  const result = {
    items: rows,
    source: isGrowwConfigured() ? 'groww+fallback' : 'fallback',
    updatedAt: new Date().toISOString(),
  };

  CACHE.ticker = result;
  CACHE.tickerExpiry = Date.now() + TICKER_TTL;
  return result;
}

export async function getDashboardData(env = {}) {
  const now = Date.now();
  if (CACHE.dashboard && now < CACHE.dashboardExpiry) return CACHE.dashboard;
  if (dashboardInflight) return dashboardInflight;

  dashboardInflight = fetchDashboardData(env).finally(() => {
    dashboardInflight = null;
  });
  return dashboardInflight;
}

async function fetchDashboardData(env = {}) {
  const apiKey = env.indianApiKey || '';
  const baseUrl = env.indianApiBase || 'https://stock.indianapi.in';

  const [ticker, trending] = await Promise.all([
    getTickerData(env),
    fetchTrending(apiKey, baseUrl),
  ]);

  const items = ticker.items || [];
  const nifty50 = findIndex(items, 'NIFTY 50', 'NIFTY');
  const bankNifty = findIndex(items, 'BANK NIFTY', 'NIFTY BANK');
  const vix = findIndex(items, 'INDIA VIX');
  const usdInr = findIndex(items, 'USD/INR');
  const gold = findIndex(items, 'GOLD');
  const brent = findIndex(items, 'BRENT');

  const gainers = (trending.gainers || []).map(normalizeTrendingRow);
  const losers = (trending.losers || []).map(normalizeTrendingRow);

  const outlookInputs = {
    indices: {
      nifty50: { percentChange: nifty50?.percentChange ?? nifty50?.change },
      bankNifty: { percentChange: bankNifty?.percentChange ?? bankNifty?.change },
      vix: { price: vix?.price, percentChange: vix?.percentChange },
    },
    breadth: {
      gainers: gainers.length,
      losers: losers.length,
    },
    commodities: {
      usdInr: { percentChange: usdInr?.percentChange },
      brent: { percentChange: brent?.percentChange },
      gold: { percentChange: gold?.percentChange },
    },
    sectors: { top: { name: 'Capital Goods' } },
  };

  const outlook = computeMarketOutlook(outlookInputs);
  const pulse = computeMarketPulse(outlook, outlookInputs);

  const result = {
    pulse,
    outlook,
    gainers,
    losers,
    breadth: {
      gainers: gainers.length,
      losers: losers.length,
      label: outlook.marketBreadth,
    },
    stocksInFocus: gainers.slice(0, 3).map((g) => g.symbol),
    upcomingResults: [],
    upcomingIpos: [],
    fiiDii: null,
    updatedAt: new Date().toISOString(),
  };

  CACHE.dashboard = result;
  CACHE.dashboardExpiry = Date.now() + DASHBOARD_TTL;
  return result;
}
