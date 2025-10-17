// src/components/MarketsDashboards.jsx
import React, { useEffect, useState } from 'react';
import apiFetch from '../utils/apiFetch';
import { API_ORIGIN } from '../config';

/* small utils */
function fmt(n, d = 2) {
  if (n == null || !isFinite(n)) return '—';
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: d }).format(n);
}
function fmtInt(n) {
  if (n == null || !isFinite(n)) return '—';
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(n);
}
const noop = () => {};
function downloadCSV(filename, rows) {
  const csv = rows.map(r => r.map(v => (v == null ? '' : String(v))).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

/**
 * safeFetch
 * - Defensive wrapper around fetch
 * - opts.timeout (ms) supported
 * - accepts a custom fetchFn as third argument (use apiFetch to prefix /api -> API_ORIGIN)
 * - throws informative errors for non-2xx responses and for HTML responses
 * - returns parsed JSON when possible, otherwise returns text
 */
async function safeFetch(pathOrUrl, opts = {}, fetchFn = fetch) {
  const { timeout, ...fetchOpts } = opts;

  // Setup AbortController for timeout support
  const controller = new AbortController();
  let timeoutId = null;

  if (typeof timeout === 'number' && timeout > 0) {
    timeoutId = setTimeout(() => controller.abort(), timeout);
  }

  // ensure we respect caller-supplied signal if present by chaining signals
  if (fetchOpts.signal) {
    const callerSignal = fetchOpts.signal;
    const chained = new AbortController();

    const onAbort = () => chained.abort();
    callerSignal.addEventListener('abort', onAbort);
    controller.signal.addEventListener('abort', onAbort);

    fetchOpts.signal = chained.signal;
  } else {
    fetchOpts.signal = controller.signal;
  }

  let res;
  try {
    res = await fetchFn(pathOrUrl, fetchOpts);
  } catch (err) {
    if (err && err.name === 'AbortError') {
      throw new Error(`Request aborted (possible timeout ${timeout}ms)`);
    }
    throw err;
  } finally {
    if (timeoutId) clearTimeout(timeoutId);
  }

  // Safely read text body (some responses have no body)
  let text = '';
  try {
    text = await res.text();
  } catch (e) {
    text = '';
  }

  const ct = (res.headers.get('content-type') || '').toLowerCase();

  // Non-2xx responses -> throw with useful snippet
  if (!res.ok) {
    const snippet = text ? text.slice(0, 1000) : `${res.status} ${res.statusText}`;
    const err = new Error(`HTTP ${res.status}: ${snippet}`);
    // attach status for callers that want to handle status codes
    err.status = res.status;
    err.body = text;
    throw err;
  }

  // If content-type looks like HTML, treat as an unexpected response (helps catch HTML error pages)
  if (ct.includes('text/html') || ct.includes('application/xhtml+xml')) {
    const snippet = text ? text.slice(0, 1000) : 'HTML response';
    const err = new Error(`Unexpected HTML response: ${snippet}`);
    err.status = res.status;
    err.body = text;
    throw err;
  }

  // Prefer JSON parse for content-types that indicate JSON, or try parse as fallback.
  if (ct.includes('application/json') || ct.includes('+json')) {
    try {
      return JSON.parse(text);
    } catch (e) {
      // fall through and return raw text if parse fails
      return text;
    }
  }

  // Last resort: try to parse JSON then return text
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

/* normalize helpers - return data in shapes expected by UI */
function normalizeTrending(raw) {
  if (!raw) return { top_gainers: [], top_losers: [] };
  if (raw.trending_stocks) return raw.trending_stocks;
  if (raw.top_gainers || raw.top_losers) return { top_gainers: raw.top_gainers || [], top_losers: raw.top_losers || [] };
  if (raw.gainers || raw.losers) return { top_gainers: raw.gainers || [], top_losers: raw.losers || [] };
  if (Array.isArray(raw)) {
    const gainers = raw.filter(r => Number(r.percent_change ?? r.percent ?? 0) >= 0);
    const losers = raw.filter(r => Number(r.percent_change ?? r.percent ?? 0) < 0);
    return { top_gainers: gainers, top_losers: losers };
  }
  return { top_gainers: [], top_losers: [] };
}

function normalizeMostActive(raw) {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  if (raw.data && Array.isArray(raw.data)) return raw.data;
  if (raw.most_active && Array.isArray(raw.most_active)) return raw.most_active;
  const arr = Object.keys(raw || {}).reduce((acc, k) => (Array.isArray(raw[k]) ? acc.concat(raw[k]) : acc), []);
  return arr.length ? arr : [];
}

function normalizeCommodities(raw) {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  if (raw.data && Array.isArray(raw.data)) return raw.data;
  if (raw.commodities && Array.isArray(raw.commodities)) return raw.commodities;
  return Object.keys(raw || {}).map(k => raw[k]).flat().filter(Boolean);
}

function normalizeMutualFunds(raw) {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  if (typeof raw === 'object') {
    const out = [];
    Object.keys(raw).forEach(top => {
      const group = raw[top];
      if (!group || typeof group !== 'object') return;
      Object.keys(group).forEach(sub => {
        const list = group[sub];
        if (Array.isArray(list)) list.forEach(item => out.push({ ...item, category: top, subcategory: sub }));
      });
    });
    if (out.length) return out;
    Object.keys(raw).forEach(k => {
      const v = raw[k];
      if (Array.isArray(v)) v.forEach(i => out.push({ ...i, category: k }));
    });
    if (out.length) return out;
  }
  return [];
}

/* =========================================
   fetchApi with robust fallbacks
   - tries same-origin /api (via apiFetch helper)
   - then http://localhost:5000/api (absolute)
   - then /indianapi (legacy proxy path)
   - then API_ORIGIN (if provided)
========================================= */
async function fetchApiRaw(path, params = {}) {
  const qs = new URLSearchParams();
  Object.keys(params || {}).forEach(k => {
    const v = params[k];
    if (v !== undefined && v !== null && v !== '') qs.append(k, String(v));
  });
  const qstr = qs.toString() ? `?${qs.toString()}` : '';
  const rel = `/api/${path}${qstr}`; // will be prefixed by apiFetch in production
  const localAbs = `http://localhost:5000/api/${path}${qstr}`;
  const altLocal = `http://127.0.0.1:5000/api/${path}${qstr}`;
  const indianProxy = `/indianapi/${path}${qstr}`;
  const remote = API_ORIGIN ? `${API_ORIGIN.replace(/\/$/, '')}/api/${path}${qstr}` : null;

  const attempts = [rel, localAbs, altLocal, indianProxy];
  if (remote) attempts.push(remote);

  let lastErr = null;
  for (const url of attempts) {
    try {
      // call safeFetch with apiFetch as fetchFn so top-level /api gets converted in production
      return await safeFetch(url, { method: 'GET', credentials: 'same-origin', timeout: 8000 }, apiFetch);
    } catch (e) {
      lastErr = e;
      // continue
    }
  }
  throw lastErr || new Error('All fetch attempts failed');
}

async function fetchApi(req) {
  if (!req) throw new Error('No request specified');
  const isObj = typeof req === 'object' && req !== null;
  const path = isObj ? req.path : String(req);
  const params = isObj ? req.params || {} : {};
  const raw = await fetchApiRaw(path, params);
  if (path === 'trending') return normalizeTrending(raw);
  if (path === 'mutual_funds' || path === 'mutual_fund_search') return normalizeMutualFunds(raw);
  if (path === 'commodities') return normalizeCommodities(raw);
  if (path === 'NSE_most_active' || path === 'BSE_most_active') return normalizeMostActive(raw);
  if (path === 'news') {
    if (Array.isArray(raw)) return raw;
    if (raw.articles && Array.isArray(raw.articles)) return raw.articles;
    if (raw.data && Array.isArray(raw.data)) return raw.data;
    return raw;
  }
  return raw;
}

/* lightweight IndianAPI wrapper */
const IndianAPI = {
  ipo: () => fetchApi('ipo'),
  news: () => fetchApi('news'),
  trending: () => fetchApi('trending'),
  commodities: () => fetchApi('commodities'),
  mutual_funds: () => fetchApi('mutual_funds'),
  price_shockers: () => fetchApi('price_shockers'),
  fetch_52_week_high_low_data: () => fetchApi('fetch_52_week_high_low_data'),
  BSE_most_active: () => fetchApi('BSE_most_active'),
  NSE_most_active: () => fetchApi('NSE_most_active'),
  stock: (name) => fetchApi({ path: 'stock', params: { name } }),
  industry_search: (query) => fetchApi({ path: 'industry_search', params: { query } }),
  stock_forecasts: (opts) => fetchApi({ path: 'stock_forecasts', params: opts || {} }),
  historical_stats: (stock_name, stats) => fetchApi({ path: 'historical_stats', params: { stock_name, stats } }),
  mutual_fund_search: (query) => fetchApi({ path: 'mutual_fund_search', params: { query } }),
  stock_target_price: (stock_id) => fetchApi({ path: 'stock_target_price', params: { stock_id } }),
  clearCache: noop,
};

/* presentational components */
function MiniRow({ item, onClick }) {
  const pctVal = Number(item.percent_change ?? item.percent ?? item.percentChange ?? 0);
  const positive = pctVal >= 0;
  return (
    <div onClick={onClick} className="flex items-center justify-between py-2 border-b last:border-b-0 cursor-pointer hover:bg-slate-50" role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === 'Enter') onClick?.(); }}>
      <div className="min-w-0">
        <div className="text-sm font-medium truncate">{item.company_name || item.name || item.ticker || item.scheme_name || item.title || item.company}</div>
        <div className="text-xs text-gray-500 truncate">{item.ric || item.ticker_id || item.ticker || item.scheme_type || item.date || ''}</div>
      </div>
      <div className="text-right ml-4">
        <div className="text-sm font-semibold">{item.price ?? item.nav ?? item.last ?? item.latest_nav ?? '—'}</div>
        <div className={`text-xs ${positive ? 'text-emerald-600' : 'text-rose-600'}`}>{isFinite(pctVal) ? `${pctVal >= 0 ? '+' : ''}${pctVal}%` : '—'}</div>
      </div>
    </div>
  );
}
function PanelShell({ title, children }) {
  return (<div className="rounded-2xl border border-slate-200 p-4 bg-white shadow-sm"><div className="mb-2 text-sm text-slate-600 font-medium">{title}</div>{children}</div>);
}

function TrendingPanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  useEffect(() => {
    let canceled = false; setLoading(true); setErr(null);
    IndianAPI.trending()
      .then(j => { if (!canceled) setData(j); })
      .catch(e => { if (!canceled) setErr(e?.message || String(e)); })
      .finally(() => { if (!canceled) setLoading(false); });
    return () => { canceled = true; };
  }, []);
  return (
    <PanelShell title="Trending (Top gainers / losers)">
      {loading && <div className="text-sm text-slate-500">Loading…</div>}
      {err && <div className="text-sm text-rose-600 break-words">Error: {err}</div>}
      {!loading && !err && data && (
        <>
          <div className="text-xs text-slate-500 mb-2">Top Gainers</div>
          <div className="space-y-1">{(data.top_gainers || []).slice(0, 6).map(s => (<MiniRow key={s.ticker_id || s.ticker || s.ticker_id} item={s} onClick={() => window.location.assign(`/stock/${encodeURIComponent(s.ric || s.ticker_id || s.ticker)}`)} />))}</div>
          <div className="mt-3 text-xs text-slate-500 mb-2">Top Losers</div>
          <div className="space-y-1">{(data.top_losers || []).slice(0, 6).map(s => (<MiniRow key={s.ticker_id || s.ticker} item={s} onClick={() => window.location.assign(`/stock/${encodeURIComponent(s.ric || s.ticker_id || s.ticker)}`)} />))}</div>
        </>
      )}
    </PanelShell>
  );
}

function MostActivePanel({ which = 'BSE' }) {
  const [data, setData] = useState([]);
  useEffect(() => {
    let canceled = false;
    const endpoint = which === 'BSE' ? IndianAPI.BSE_most_active : IndianAPI.NSE_most_active;
    endpoint()
      .then(j => { if (!canceled) setData(Array.isArray(j) ? j : (j?.data || j?.most_active || j || [])); })
      .catch(e => { console.warn('MostActivePanel:', e?.message || e); if (!canceled) setData([]); });
    return () => { canceled = true; };
  }, [which]);
  return (
    <PanelShell title={`${which} — Most Active`}>
      <div className="space-y-1">
        {data.slice(0, 8).map(s => (<MiniRow key={s.ticker_id || s.ticker || s.ticker_id} item={s} onClick={() => window.location.assign(`/stock/${encodeURIComponent(s.ric || s.ticker_id || s.ticker)}`)} />))}
        {data.length === 0 && <div className="text-sm text-slate-500">No data</div>}
      </div>
    </PanelShell>
  );
}

function CommoditiesPanel() {
  const [data, setData] = useState([]);
  useEffect(() => {
    let canceled = false;
    IndianAPI.commodities()
      .then(j => { if (!canceled) setData(Array.isArray(j) ? j : (j?.data || j?.commodities || [])); })
      .catch(e => { console.warn('CommoditiesPanel', e?.message || e); if (!canceled) setData([]); });
    return () => { canceled = true; };
  }, []);
  return (
    <PanelShell title="Commodities">
      <div className="space-y-1">
        {data.slice(0, 8).map(c => (
          <div key={c.ticker || c.name} className="flex justify-between py-2 border-b last:border-b-0">
            <div>
              <div className="text-sm font-medium">{c.name || c.instrument || c.ticker}</div>
              <div className="text-xs text-gray-500">{c.exchange || c.market || ''}</div>
            </div>
            <div className="text-right ml-4">
              <div className="text-sm font-semibold">{c.price ?? c.last ?? '—'}</div>
              <div className={`text-xs ${Number(c.percent_change ?? c.change ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>{c.percent_change ?? c.change ?? '—'}</div>
            </div>
          </div>
        ))}
        {data.length === 0 && <div className="text-sm text-slate-500">No data</div>}
      </div>
    </PanelShell>
  );
}

function MutualFundsPanel() {
  const [data, setData] = useState([]);
  useEffect(() => {
    let canceled = false;
    IndianAPI.mutual_funds()
      .then(j => { if (!canceled) setData(Array.isArray(j) ? j : (Array.isArray(j?.data) ? j.data : Array.isArray(j?.mutual_funds) ? j.mutual_funds : (Array.isArray(j) ? j : []))); })
      .catch(e => { console.warn('MutualFundsPanel', e?.message || e); if (!canceled) setData([]); });
    return () => { canceled = true; };
  }, []);
  return (
    <PanelShell title="Mutual Funds">
      <div className="space-y-1">
        {data.slice(0, 8).map(m => (
          <div key={m.scheme_code || m.name || m.fund_name} className="flex justify-between py-2 border-b last:border-b-0">
            <div>
              <div className="text-sm font-medium truncate">{m.scheme_name ?? m.name ?? m.fund_name}</div>
              <div className="text-xs text-gray-500 truncate">{m.scheme_type ?? m.category ?? m.subcategory ?? ''}</div>
            </div>
            <div className="text-right ml-4">
              <div className="text-sm font-semibold">{m.nav ?? m.latest_nav ?? m.price ?? '—'}</div>
              <div className="text-xs text-gray-500">{m.date ?? ''}</div>
            </div>
          </div>
        ))}
        {data.length === 0 && <div className="text-sm text-slate-500">No data</div>}
      </div>
    </PanelShell>
  );
}

function StockForecastsPanel() {
  const [data, setData] = useState([]);
  useEffect(() => {
    let canceled = false;
    IndianAPI.stock_forecasts({ stock_id: '', measure_code: 'EPS', period_type: 'Annual', data_type: 'Actuals', age: 'Current' })
      .then(j => { if (!canceled) setData(j?.forecasts ?? j?.data ?? (Array.isArray(j) ? j : [])); })
      .catch(e => { console.warn('StockForecastsPanel', e?.message || e); if (!canceled) setData([]); });
    return () => { canceled = true; };
  }, []);
  return (
    <PanelShell title="Stock Forecasts">
      <div className="space-y-2">
        {data.slice(0, 8).map((f, i) => (
          <div key={f.ticker_id ?? i} className="py-2 border-b last:border-b-0">
            <div className="flex justify-between"><div className="text-sm font-medium">{f.company_name ?? f.ticker ?? f.symbol}</div><div className="text-xs text-gray-500">{f.horizon ?? f.period ?? ''}</div></div>
            <div className="text-xs text-slate-600">{f.summary ?? f.note ?? ''}</div>
          </div>
        ))}
        {data.length === 0 && <div className="text-sm text-slate-500">No forecasts</div>}
      </div>
    </PanelShell>
  );
}

function NewsPanel() {
  const [data, setData] = useState([]);
  useEffect(() => {
    let canceled = false;
    IndianAPI.news()
      .then(j => { if (!canceled) setData(Array.isArray(j) ? j : (j?.data || j?.news || j?.articles || [])); })
      .catch(e => { console.warn('NewsPanel', e?.message || e); if (!canceled) setData([]); });
    return () => { canceled = true; };
  }, []);
  return (
    <PanelShell title="Market News">
      <div className="space-y-2">
        {data.slice(0, 6).map((n, i) => (
          <div key={n.id ?? i} className="py-2 border-b last:border-b-0">
            <a className="text-sm font-medium" href={n.link ?? n.url ?? n.source_url ?? '#'} target="_blank" rel="noreferrer">{n.title ?? n.headline ?? n.name}</a>
            <div className="text-xs text-gray-500">{n.source ?? n.date ?? ''}</div>
          </div>
        ))}
        {data.length === 0 && <div className="text-sm text-slate-500">No news</div>}
      </div>
    </PanelShell>
  );
}

function IPOPanel() {
  const [data, setData] = useState([]);
  useEffect(() => {
    let canceled = false;
    IndianAPI.ipo()
      .then(j => { if (!canceled) setData(Array.isArray(j) ? j : (j?.data || j?.ipos || [])); })
      .catch(e => { console.warn('IPOPanel', e?.message || e); if (!canceled) setData([]); });
    return () => { canceled = true; };
  }, []);
  return (
    <PanelShell title="Upcoming IPOs">
      <div className="space-y-2">
        {data.slice(0, 6).map((ip, i) => (<div key={ip.ticker_id ?? i} className="py-2 border-b last:border-b-0"><div className="text-sm font-medium">{ip.company_name ?? ip.name}</div><div className="text-xs text-gray-500">{ip.listing_date ?? ip.date ?? ''}</div></div>))}
        {data.length === 0 && <div className="text-sm text-slate-500">No upcoming IPOs</div>}
      </div>
    </PanelShell>
  );
}

/* simplified MarketsView and export */
function MarketsView() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="rounded-2xl border border-slate-200 p-4 bg-white shadow-sm">
            <h3 className="text-lg font-semibold text-slate-800 mb-2">Markets — Snapshot (India)</h3>
            <p className="text-sm text-slate-500">Live snippets from IndianAPI: trending, most active, commodities, mutual funds and forecasts.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <NewsPanel />
            <StockForecastsPanel />
          </div>

          <IPOPanel />
        </div>

        <aside className="space-y-4">
          <TrendingPanel />
          <MostActivePanel which="BSE" />
          <MostActivePanel which="NSE" />
          <CommoditiesPanel />
          <MutualFundsPanel />
        </aside>
      </div>
    </div>
  );
}

function EconomicsView() {
  return (
    <div className="rounded-2xl border border-slate-200 p-6 bg-white shadow-sm">
      <h3 className="text-lg font-semibold">Economics — World Bank data</h3>
      <p className="text-sm text-slate-500">(Economics view omitted in this fixed file. Reuse your existing WB logic.)</p>
    </div>
  );
}

export default function G20WorldBankAndMarketsPro() {
  const [tab, setTab] = useState('markets');
  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">G20 — Economics & India Markets</h2>
          <p className="text-slate-600 text-sm">World Bank macro for G20 + India market panels (via IndianAPI).</p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => setTab('economics')} className={`px-4 py-2 rounded-xl border ${tab === 'economics' ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-800 border-slate-300 hover:bg-slate-50'}`}>Economics</button>
          <button type="button" onClick={() => setTab('markets')} className={`px-4 py-2 rounded-xl border ${tab === 'markets' ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-800 border-slate-300 hover:bg-slate-50'}`}>Markets (India)</button>
        </div>
      </header>
      {tab === 'economics' ? <EconomicsView /> : <MarketsView />}
    </div>
  );
}
