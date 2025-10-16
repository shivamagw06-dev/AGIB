// src/components/G20WorldBankAndMarketsPro.jsx
import React, { useEffect, useMemo, useRef, useState } from 'react';

/* =========================================
   SMALL UTILS
========================================= */
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
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
}

/* =========================================
   G20 LIST (ISO2)
========================================= */
const G20 = [
  { code: 'IN', label: 'India' },
  { code: 'US', label: 'United States' },
  { code: 'CN', label: 'China' },
  { code: 'JP', label: 'Japan' },
  { code: 'DE', label: 'Germany' },
  { code: 'FR', label: 'France' },
  { code: 'IT', label: 'Italy' },
  { code: 'GB', label: 'United Kingdom' },
  { code: 'CA', label: 'Canada' },
  { code: 'AU', label: 'Australia' },
  { code: 'KR', label: 'South Korea' },
  { code: 'RU', label: 'Russia' },
  { code: 'BR', label: 'Brazil' },
  { code: 'MX', label: 'Mexico' },
  { code: 'ID', label: 'Indonesia' },
  { code: 'TR', label: 'Turkey' },
  { code: 'SA', label: 'Saudi Arabia' },
  { code: 'ZA', label: 'South Africa' },
  { code: 'AR', label: 'Argentina' },
  { code: 'EU', label: 'European Union' },
];

/* =========================================
   SAFE FETCH (defensive)
========================================= */
async function safeFetch(url, opts = {}) {
  try {
    const res = await fetch(url, opts);
    const ct = res.headers.get('content-type') || '';
    const text = await res.text().catch(() => '');
    if (!res.ok) {
      const snippet = text ? text.slice(0, 800) : `${res.status} ${res.statusText}`;
      throw new Error(`HTTP ${res.status}: ${snippet}`);
    }
    if (ct.includes('text/html') || ct.includes('application/xhtml+xml')) {
      const snippet = text ? text.slice(0, 1000) : 'HTML response';
      throw new Error(`Unexpected HTML response: ${snippet}`);
    }
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  } catch (e) {
    if (e?.name === 'AbortError') return null;
    throw e;
  }
}

/* =========================================
   WORLD BANK HELPERS (unchanged, defensive)
========================================= */
async function wbCountryMeta(iso2, signal) {
  const url = `https://api.worldbank.org/v2/country/${encodeURIComponent(iso2)}?format=json`;
  const j = await safeFetch(url, { signal });
  if (!Array.isArray(j) || !j[1] || !j[1][0]) return null;
  const row = j[1][0];
  return {
    name: row.name,
    region: row?.region?.value || null,
    incomeLevel: row?.incomeLevel?.value || null,
    capitalCity: row.capitalCity || null,
    latitude: row?.latitude || null,
    longitude: row?.longitude || null,
  };
}

async function wbLatest(iso2, indicator, signal) {
  const url = `https://api.worldbank.org/v2/country/${encodeURIComponent(iso2)}/indicator/${encodeURIComponent(indicator)}?format=json&per_page=500`;
  const j = await safeFetch(url, { signal });
  if (!Array.isArray(j)) return { date: null, value: null };
  const rows = Array.isArray(j[1]) ? j[1] : [];
  const found = rows.find(r => r && r.value != null);
  if (found) return { date: found.date, value: Number(found.value) };
  return { date: null, value: null };
}

async function wbSeries(iso2, indicator, n = 10, signal) {
  const url = `https://api.worldbank.org/v2/country/${encodeURIComponent(iso2)}/indicator/${encodeURIComponent(indicator)}?format=json&per_page=500`;
  const j = await safeFetch(url, { signal });
  if (!Array.isArray(j)) return { series: [], prev: null };
  const rows = (Array.isArray(j[1]) ? j[1] : []).filter(r => r && r.value != null);
  const lastNplus1 = rows.slice(0, n + 1).map(r => ({ date: Number(r.date), value: Number(r.value) })).reverse();
  const series = lastNplus1.slice(-n);
  const prev = lastNplus1.length > n ? lastNplus1[lastNplus1.length - n - 1] : null;
  return { series, prev };
}

/* Chosen indicators */
const IND = {
  GDP_GROWTH: 'NY.GDP.MKTP.KD.ZG',
  CPI_INFL: 'FP.CPI.TOTL.ZG',
  UNEMP: 'SL.UEM.TOTL.ZS',
  GDP_PCAP_USD: 'NY.GDP.PCAP.CD',
  CA_BAL_PCT: 'BN.CAB.XOKA.GD.ZS',
  EXPORTS_PCT: 'NE.EXP.GNFS.ZS',
  GDP_USD: 'NY.GDP.MKTP.CD',
  POP: 'SP.POP.TOTL',
  DEBT_PCT: 'GC.DOD.TOTL.GD.ZS',
  LIFE_EXP: 'SP.DYN.LE00.IN',
  LFPR: 'SL.TLF.CACT.ZS',
  GINI: 'SI.POV.GINI',
  SAVINGS_PCT: 'NY.GNS.ICTR.ZS',
};

/* =========================================
   WORLD BANK DOCUMENTS helpers (via /wds proxy)
========================================= */
async function wbDocFacets(countryName, signal) {
  try {
    const url = `/wds/api/v3/wds?format=json&rows=0&count_exact=${encodeURIComponent(countryName)}&fct=docty_exact`;
    const j = await safeFetch(url, { signal });
    const f = j?.facets || j?.fct || {};
    const obj = f?.docty_exact || {};
    const out = [];
    Object.keys(obj).forEach(k => {
      const v = obj[k];
      if (v && typeof v === 'object') out.push({ name: v.name ?? k, count: v.count ?? 0 });
      else if (typeof v === 'number') out.push({ name: k, count: v });
    });
    return out.sort((a, b) => (b.count ?? 0) - (a.count ?? 0));
  } catch (e) {
    console.warn('wbDocFacets error', e?.message || e);
    return [];
  }
}

async function wbDocsLatest({ countryName, rows = 8, docty, title }, signal) {
  try {
    const base = '/wds/api/v3/wds';
    const params = new URLSearchParams({
      format: 'json',
      rows: String(rows),
      count_exact: countryName,
      fl: 'display_title,docdt,docty,pdfurl,url',
      sort: 'docdt',
      order: 'desc',
    });
    if (docty) params.set('docty_exact', docty);
    if (title) params.set('display_title', title);
    const url = `${base}?${params.toString()}`;
    const j = await safeFetch(url, { signal });
    const maybe = j?.result || j?.results || j || {};
    const arr = [];
    Object.keys(maybe || {}).forEach(k => {
      const v = maybe[k];
      if (v && typeof v === 'object' && (v.display_title || v.docty)) {
        arr.push({
          title: v.display_title || v.repnme || v.docna || 'Untitled',
          date: v.docdt || null,
          type: v.docty || null,
          pdf: v.pdfurl || null,
          url: v.url || null,
        });
      }
    });
    return arr.sort((a, b) => (b.date || '').localeCompare(a.date || '')).slice(0, rows);
  } catch (e) {
    console.warn('wbDocsLatest error', e?.message || e);
    return [];
  }
}

/* =========================================
   SIMPLE SVG LINE CHART
========================================= */
function LineChart({ data, height = 200, pad = 30, valueDigits = 2 }) {
  const width = 420;
  if (!data || data.length < 2) return <div className="text-sm text-slate-500">Not enough data</div>;

  const xs = data.map(d => d.date), ys = data.map(d => d.value);
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const yMin = Math.min(...ys), yMax = Math.max(...ys);
  const xScale = (x) => pad + ((x - xMin) / Math.max(1, xMax - xMin)) * (width - pad * 2);
  const yScale = (y) => pad + (1 - (y - yMin) / Math.max(1e-6, (yMax - yMin))) * (height - pad * 2);

  const path = data.map((d, i) => `${i ? 'L' : 'M'} ${xScale(d.date)} ${yScale(d.value)}`).join(' ');

  const [hover, setHover] = useState(null);
  const svgRef = useRef(null);
  function onMove(e) {
    if (!svgRef.current) return;
    const pt = svgRef.current.createSVGPoint();
    pt.x = e.clientX; pt.y = e.clientY;
    const svgP = pt.matrixTransform(svgRef.current.getScreenCTM().inverse());
    const inv = (px) => Math.round(((px - pad) / (width - pad * 2)) * (xMax - xMin) + xMin);
    const yr = inv(svgP.x);
    let best = null, bestDist = Infinity;
    for (const d of data) {
      const dist = Math.abs(d.date - yr);
      if (dist < bestDist) { bestDist = dist; best = d; }
    }
    setHover(best);
  }

  return (
    <div className="relative">
      <svg ref={svgRef} viewBox={`0 0 ${width} ${height}`} className="w-full h-[220px]"
        onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
        <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} stroke="currentColor" className="text-slate-200" />
        <line x1={pad} y1={pad} x2={pad} y2={height - pad} stroke="currentColor" className="text-slate-200" />
        {[0.25, 0.5, 0.75].map((t, i) => (
          <line key={i} x1={pad} y1={pad + t * (height - pad * 2)} x2={width - pad} y2={pad + t * (height - pad * 2)}
                stroke="currentColor" className="text-slate-100" />
        ))}
        <text x={pad} y={height - pad + 12} className="fill-slate-400 text-[10px]">{xMin}</text>
        <text x={width - pad} y={height - pad + 12} textAnchor="end" className="fill-slate-400 text-[10px]">{xMax}</text>
        <text x={pad - 6} y={yScale(yMax)} textAnchor="end" className="fill-slate-400 text-[10px]">{fmt(yMax, valueDigits)}</text>
        <text x={pad - 6} y={yScale(yMin)} textAnchor="end" className="fill-slate-400 text-[10px]">{fmt(yMin, valueDigits)}</text>
        <path d={path} fill="none" stroke="currentColor" className="text-indigo-600" strokeWidth="2" />
        <circle cx={xScale(data[data.length - 1].date)} cy={yScale(data[data.length - 1].value)} r="3" fill="currentColor" className="text-indigo-600" />
        {hover && (
          <>
            <line x1={xScale(hover.date)} y1={pad} x2={xScale(hover.date)} y2={height - pad}
                  stroke="currentColor" className="text-slate-300" />
            <circle cx={xScale(hover.date)} cy={yScale(hover.value)} r="3" fill="currentColor" className="text-slate-700" />
          </>
        )}
      </svg>
      {hover && (
        <div className="absolute left-2 top-2 text-xs bg-white/90 backdrop-blur px-2 py-1 rounded border border-slate-200 shadow">
          <div className="font-medium">{hover.date}</div>
          <div>{fmt(hover.value, valueDigits)}</div>
        </div>
      )}
    </div>
  );
}

/* =========================================
   IndianAPI helper (robust)
   - tries /api/<path> first, then /indianapi/<path> with X-Api-Key header
   - supports { path, params } or 'path'
   - caching for GETs
========================================= */

const apiCache = {};

/** build querystring from params object */
function buildQuery(params = {}) {
  const s = new URLSearchParams();
  Object.keys(params || {}).forEach(k => {
    const v = params[k];
    if (v === undefined || v === null || v === '') return;
    s.append(k, String(v));
  });
  const qs = s.toString();
  return qs ? `?${qs}` : '';
}

/**
 * fetchApi accepts either:
 *  - 'trending' (string) => GET /api/trending (then fallback /indianapi/trending)
 *  - { path: 'stock', params: { name: 'Tata Steel' } } => GET /api/stock?name=...
 */
async function fetchApi(req) {
  if (!req) throw new Error('No request specified');
  const isObj = typeof req === 'object' && req !== null;
  const path = isObj ? req.path : String(req);
  const params = isObj ? req.params || {} : {};
  const cacheKey = `${path}${buildQuery(params)}`;

  if (apiCache[cacheKey]) return apiCache[cacheKey];

  // 1) try local backend (/api/)
  const apiUrl = `/api/${path}${buildQuery(params)}`;
  try {
    const r = await fetch(apiUrl, { method: 'GET' });
    const ct = r.headers.get('content-type') || '';
    const text = await r.text().catch(() => '');
    if (r.ok && !ct.includes('text/html')) {
      try {
        const j = JSON.parse(text);
        apiCache[cacheKey] = j;
        return j;
      } catch {
        apiCache[cacheKey] = text;
        return text;
      }
    }
    // if response is HTML, fall through to direct IndianAPI
    if (!r.ok) {
      const snippet = text ? text.slice(0, 800) : `${r.status} ${r.statusText}`;
      // continue to fallback
      // console.debug('Local backend returned error, falling back:', snippet);
    }
  } catch (e) {
    // console.debug('fetchApi /api fallback', e?.message || e);
    // try direct IndianAPI below
  }

  // 2) fallback to direct IndianAPI via /indianapi proxy and attach key if present
  // dev proxy should map /indianapi -> https://stock.indianapi.in
  const indianApiUrl = `/indianapi/${path}${buildQuery(params)}`;
  const key = import.meta.env?.VITE_INDIANAPI_KEY || '';
  try {
    const r = await fetch(indianApiUrl, { method: 'GET', headers: key ? { 'X-Api-Key': key } : {} });
    const ct = r.headers.get('content-type') || '';
    const text = await r.text().catch(() => '');
    if (!r.ok) {
      const snippet = text ? text.slice(0, 1000) : `${r.status} ${r.statusText}`;
      throw new Error(`IndianAPI ${path} failed: ${snippet}`);
    }
    if (ct.includes('text/html')) {
      const snippet = text ? text.slice(0, 1000) : 'HTML response from IndianAPI';
      throw new Error(`IndianAPI ${path} returned HTML (proxy misconfigured): ${snippet}`);
    }
    let j;
    try { j = JSON.parse(text); } catch { j = text; }
    apiCache[cacheKey] = j;
    return j;
  } catch (e) {
    throw new Error(`Failed to fetch ${path}: ${e?.message || String(e)}`);
  }
}

/* =========================================
   IndianAPI wrapper functions
========================================= */
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
  statement: (stock_name, stats) => fetchApi({ path: 'statement', params: { stock_name, stats } }),
  historical_data: (stock_name, period = '1m', filter = 'default') =>
    fetchApi({ path: 'historical_data', params: { stock_name, period, filter } }),
  industry_search: (query) => fetchApi({ path: 'industry_search', params: { query } }),
  stock_forecasts: ({ stock_id, measure_code, period_type, data_type, age }) =>
    fetchApi({ path: 'stock_forecasts', params: { stock_id, measure_code, period_type, data_type, age } }),
  historical_stats: (stock_name, stats) => fetchApi({ path: 'historical_stats', params: { stock_name, stats } }),
  corporate_actions: (stock_name) => fetchApi({ path: 'corporate_actions', params: { stock_name } }),
  mutual_fund_search: (query) => fetchApi({ path: 'mutual_fund_search', params: { query } }),
  stock_target_price: (stock_id) => fetchApi({ path: 'stock_target_price', params: { stock_id } }),
  mutual_funds_details: (stock_name) => fetchApi({ path: 'mutual_funds_details', params: { stock_name } }),
  recent_announcements: (stock_name) => fetchApi({ path: 'recent_announcements', params: { stock_name } }),
  clearCache: (keyPattern) => {
    if (!keyPattern) { Object.keys(apiCache).forEach(k => delete apiCache[k]); return; }
    const keys = Object.keys(apiCache).filter(k => k.includes(keyPattern));
    keys.forEach(k => delete apiCache[k]);
  }
};

/* =========================================
   UI: Panels
========================================= */

function MiniRow({ item, onClick }) {
  const pctVal = Number(item.percent_change ?? item.percent ?? item.percentChange ?? 0);
  const positive = pctVal >= 0;
  return (
    <div
      onClick={onClick}
      className="flex items-center justify-between py-2 border-b last:border-b-0 cursor-pointer hover:bg-slate-50"
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter') onClick?.(); }}
    >
      <div className="min-w-0">
        <div className="text-sm font-medium truncate">{item.company_name || item.name || item.ticker || item.scheme_name || item.title}</div>
        <div className="text-xs text-gray-500 truncate">{item.ric || item.ticker_id || item.ticker || item.scheme_type || item.date || ''}</div>
      </div>
      <div className="text-right ml-4">
        <div className="text-sm font-semibold">{item.price ?? item.nav ?? item.last ?? '—'}</div>
        <div className={`text-xs ${positive ? 'text-emerald-600' : 'text-rose-600'}`}>
          {isFinite(pctVal) ? `${pctVal >= 0 ? '+' : ''}${pctVal}%` : '—'}
        </div>
      </div>
    </div>
  );
}

function PanelShell({ title, children }) {
  return (
    <div className="rounded-2xl border border-slate-200 p-4 bg-white shadow-sm">
      <div className="mb-2 text-sm text-slate-600 font-medium">{title}</div>
      {children}
    </div>
  );
}

function TrendingPanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  useEffect(() => {
    let canceled = false;
    setLoading(true);
    IndianAPI.trending()
      .then(j => { if (!canceled) setData(j?.trending_stocks ?? j); })
      .catch(e => { if (!canceled) setErr(e.message || String(e)); })
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
          <div className="space-y-1">
            {(data.top_gainers || []).slice(0, 6).map(s => (
              <MiniRow key={s.ticker_id || s.ticker} item={s} onClick={() => window.location.assign(`/stock/${encodeURIComponent(s.ric || s.ticker_id || s.ticker)}`)} />
            ))}
          </div>
          <div className="mt-3 text-xs text-slate-500 mb-2">Top Losers</div>
          <div className="space-y-1">
            {(data.top_losers || []).slice(0, 6).map(s => (
              <MiniRow key={s.ticker_id || s.ticker} item={s} onClick={() => window.location.assign(`/stock/${encodeURIComponent(s.ric || s.ticker_id || s.ticker)}`)} />
            ))}
          </div>
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
      .then(j => { if (!canceled) setData(j?.data ?? j?.most_active ?? j ?? []); })
      .catch((e) => { console.warn('MostActivePanel:', e?.message || e); if (!canceled) setData([]); });
    return () => { canceled = true; };
  }, [which]);
  return (
    <PanelShell title={`${which} — Most Active`}>
      <div className="space-y-1">
        {data.slice(0, 8).map(s => (
          <MiniRow key={s.ticker_id || s.ticker} item={s} onClick={() => window.location.assign(`/stock/${encodeURIComponent(s.ric || s.ticker_id || s.ticker)}`)} />
        ))}
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
      .then(j => { if (!canceled) setData(j?.data ?? j?.commodities ?? j ?? []); })
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
              <div className={`text-xs ${Number(c.percent_change ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                {c.percent_change ?? c.change ?? '—'}
              </div>
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
      .then(j => { if (!canceled) setData(j?.data ?? j?.mutual_funds ?? j ?? []); })
      .catch(e => { console.warn('MutualFundsPanel', e?.message || e); if (!canceled) setData([]); });
    return () => { canceled = true; };
  }, []);
  return (
    <PanelShell title="Mutual Funds">
      <div className="space-y-1">
        {data.slice(0, 8).map(m => (
          <div key={m.scheme_code || m.name} className="flex justify-between py-2 border-b last:border-b-0">
            <div>
              <div className="text-sm font-medium truncate">{m.scheme_name ?? m.name}</div>
              <div className="text-xs text-gray-500 truncate">{m.scheme_type ?? m.category ?? ''}</div>
            </div>
            <div className="text-right ml-4">
              <div className="text-sm font-semibold">{m.nav ?? m.price ?? '—'}</div>
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
      .then(j => { if (!canceled) setData(j?.forecasts ?? j?.data ?? j ?? []); })
      .catch(e => { console.warn('StockForecastsPanel', e?.message || e); if (!canceled) setData([]); });
    return () => { canceled = true; };
  }, []);
  return (
    <PanelShell title="Stock Forecasts">
      <div className="space-y-2">
        {data.slice(0, 8).map((f, i) => (
          <div key={f.ticker_id ?? i} className="py-2 border-b last:border-b-0">
            <div className="flex justify-between">
              <div className="text-sm font-medium">{f.company_name ?? f.ticker ?? f.symbol}</div>
              <div className="text-xs text-gray-500">{f.horizon ?? f.period ?? ''}</div>
            </div>
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
      .then(j => { if (!canceled) setData(j?.data ?? j?.news ?? j ?? []); })
      .catch(e => { console.warn('NewsPanel', e?.message || e); if (!canceled) setData([]); });
    return () => { canceled = true; };
  }, []);
  return (
    <PanelShell title="Market News">
      <div className="space-y-2">
        {data.slice(0, 6).map((n, i) => (
          <div key={n.id ?? i} className="py-2 border-b last:border-b-0">
            <a className="text-sm font-medium" href={n.link ?? n.url ?? '#'} target="_blank" rel="noreferrer">
              {n.title ?? n.headline ?? n.name}
            </a>
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
      .then(j => { if (!canceled) setData(j?.data ?? j?.ipos ?? j ?? []); })
      .catch(e => { console.warn('IPOPanel', e?.message || e); if (!canceled) setData([]); });
    return () => { canceled = true; };
  }, []);
  return (
    <PanelShell title="Upcoming IPOs">
      <div className="space-y-2">
        {data.slice(0, 6).map((ip, i) => (
          <div key={ip.ticker_id ?? i} className="py-2 border-b last:border-b-0">
            <div className="text-sm font-medium">{ip.company_name ?? ip.name}</div>
            <div className="text-xs text-gray-500">{ip.listing_date ?? ip.date ?? ''}</div>
          </div>
        ))}
        {data.length === 0 && <div className="text-sm text-slate-500">No upcoming IPOs</div>}
      </div>
    </PanelShell>
  );
}

/* =========================================
   MARKETS view
========================================= */
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

/* =========================================
   MAIN PAGE — Economics / Markets Toggle
========================================= */
export default function G20WorldBankAndMarketsPro() {
  const [tab, setTab] = useState('economics'); // 'economics' | 'markets'
  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">G20 — Economics & India Markets</h2>
          <p className="text-slate-600 text-sm">World Bank macro for G20 + India market panels (via IndianAPI).</p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => setTab('economics')}
            className={`px-4 py-2 rounded-xl border ${tab==='economics' ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-800 border-slate-300 hover:bg-slate-50'}`}>
            Economics
          </button>
          <button type="button" onClick={() => setTab('markets')}
            className={`px-4 py-2 rounded-xl border ${tab==='markets' ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-800 border-slate-300 hover:bg-slate-50'}`}>
            Markets (India)
          </button>
        </div>
      </header>
      {tab === 'economics' ? <EconomicsView /> : <MarketsView />}
    </div>
  );
}

/* =========================================
   ECONOMICS VIEW (WB)
   (unchanged aside from safety guards)
========================================= */
function EconomicsView() {
  const [country, setCountry] = useState('IN'); // default India
  const countryLabel = useMemo(() => G20.find(c => c.code === country)?.label || 'India', [country]);
  const flagUrl = `https://flagcdn.com/${country.toLowerCase()}.svg`;

  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errs, setErrs] = useState({ meta: null, head: null, series: null, docs: null });

  // KPI store
  const [kpis, setKpis] = useState({
    gdpGrowth: { cur: null, prev: null }, cpi: { cur: null, prev: null }, unemp: { cur: null, prev: null },
    gdpPcap: { cur: null }, ca: { cur: null }, exp: { cur: null }, gdpUsd: { cur: null }, pop: { cur: null },
    debt: { cur: null }, life: { cur: null }, gini: { cur: null }, lfpr: { cur: null }, savings: { cur: null }
  });

  const [series, setSeries] = useState({
    gdpGrowth: [], cpi: [], unemp: [], debt: [], life: [], gini: [], lfpr: [], savings: []
  });

  const [docs, setDocs] = useState([]);
  const [docTypes, setDocTypes] = useState([]);
  const [filters, setFilters] = useState({ docty: '', title: '' });

  async function loadAll(iso2, label, signal) {
    setLoading(true);
    setErrs({ meta: null, head: null, series: null, docs: null });

    try {
      const m = await wbCountryMeta(iso2, signal);
      setMeta(m);
    } catch (e) {
      console.warn('wbCountryMeta error', e?.message || e);
      setMeta(null);
      setErrs(s => ({ ...s, meta: 'Country profile failed (WB).' }));
    }

    try {
      const [
        gdpGrowth, cpi, unemp, gdpPcap, caPct, expPct, gdpUsd, pop, debt, life, gini, lfpr, savings
      ] = await Promise.all([
        wbLatest(iso2, IND.GDP_GROWTH, signal),
        wbLatest(iso2, IND.CPI_INFL, signal),
        wbLatest(iso2, IND.UNEMP, signal),
        wbLatest(iso2, IND.GDP_PCAP_USD, signal),
        wbLatest(iso2, IND.CA_BAL_PCT, signal),
        wbLatest(iso2, IND.EXPORTS_PCT, signal),
        wbLatest(iso2, IND.GDP_USD, signal),
        wbLatest(iso2, IND.POP, signal),
        wbLatest(iso2, IND.DEBT_PCT, signal),
        wbLatest(iso2, IND.LIFE_EXP, signal),
        wbLatest(iso2, IND.GINI, signal),
        wbLatest(iso2, IND.LFPR, signal),
        wbLatest(iso2, IND.SAVINGS_PCT, signal),
      ]);

      const [s_gdp, s_cpi, s_un, s_debt, s_life, s_gini, s_lfpr, s_sav] = await Promise.all([
        wbSeries(iso2, IND.GDP_GROWTH, 10, signal),
        wbSeries(iso2, IND.CPI_INFL, 10, signal),
        wbSeries(iso2, IND.UNEMP, 10, signal),
        wbSeries(iso2, IND.DEBT_PCT, 10, signal),
        wbSeries(iso2, IND.LIFE_EXP, 10, signal),
        wbSeries(iso2, IND.GINI, 10, signal),
        wbSeries(iso2, IND.LFPR, 10, signal),
        wbSeries(iso2, IND.SAVINGS_PCT, 10, signal),
      ]);

      setKpis({
        gdpGrowth: { cur: gdpGrowth, prev: s_gdp.prev },
        cpi: { cur: cpi, prev: s_cpi.prev },
        unemp: { cur: unemp, prev: s_un.prev },
        gdpPcap: { cur: gdpPcap }, ca: { cur: caPct }, exp: { cur: expPct }, gdpUsd: { cur: gdpUsd }, pop: { cur: pop },
        debt: { cur: debt }, life: { cur: life }, gini: { cur: gini }, lfpr: { cur: lfpr }, savings: { cur: savings },
      });

      setSeries({
        gdpGrowth: s_gdp.series, cpi: s_cpi.series, unemp: s_un.series,
        debt: s_debt.series, life: s_life.series, gini: s_gini.series, lfpr: s_lfpr.series, savings: s_sav.series
      });
    } catch (e) {
      console.warn('Indicator fetch error', e?.message || e);
      setErrs(s => ({ ...s, head: 'Key indicators/series failed (World Bank).' }));
    }

    try {
      const cName = meta?.name || label;
      if (cName) {
        const dtypes = await wbDocFacets(cName, signal);
        setDocTypes(dtypes);
        const d = await wbDocsLatest({ countryName: cName, rows: 8, docty: filters.docty, title: filters.title }, signal);
        setDocs(d);
      } else {
        setDocTypes([]);
        setDocs([]);
      }
    } catch (e) {
      console.warn('Docs error', e?.message || e);
      setErrs(s => ({ ...s, docs: 'Documents failed (proxy?).' }));
      setDocTypes([]); setDocs([]);
    }

    setLoading(false);
  }

  useEffect(() => {
    const ctrl = new AbortController();
    loadAll(country, countryLabel, ctrl.signal).catch(() => {});
    return () => { try { ctrl.abort('cleanup'); } catch { ctrl.abort(); } };
  }, [country]);

  useEffect(() => {
    const ctrl = new AbortController();
    (async () => {
      try {
        const cName = meta?.name || countryLabel;
        if (cName) {
          const d = await wbDocsLatest({ countryName: cName, rows: 8, docty: filters.docty, title: filters.title }, ctrl.signal);
          setDocs(d);
        }
      } catch (e) {
        if (e?.name !== 'AbortError') setErrs(s => ({ ...s, docs: 'Documents failed.' }));
      }
    })();
    return () => { try { ctrl.abort('cleanup'); } catch { ctrl.abort(); } };
  }, [filters, meta, countryLabel]);

  const exportSeries = (title, data) => {
    const rows = [['Year', 'Value'], ...data.map(d => [d.date, d.value])];
    downloadCSV(`${(meta?.name || countryLabel).replace(/\s+/g,'_')}_${title.replace(/\s+/g,'_')}.csv`, rows);
  };

  return (
    <div className="space-y-8">
      {/* Country selector */}
      <section className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <img src={flagUrl} alt={`${countryLabel} flag`} className="h-6 w-8 rounded border border-slate-200" />
          <div className="flex items-center gap-2">
            <label className="text-sm text-slate-600">Country</label>
            <select
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="px-3 py-2 rounded-xl border border-slate-300 bg-white text-slate-800 shadow-sm"
            >
              {G20.map(c => <option key={c.code} value={c.code}>{c.label}</option>)}
            </select>
          </div>
        </div>
        {loading && <span className="text-sm text-slate-500">Loading…</span>}
      </section>

      {/* Overview */}
      <section className="rounded-2xl border border-slate-200 p-4 bg-white shadow-sm">
        <h3 className="text-lg font-semibold text-slate-800">{meta?.name || countryLabel} — Overview</h3>
        {errs.meta && <div className="text-amber-600 text-sm mt-2">{errs.meta}</div>}
        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-6 gap-4 mt-3">
          <InfoItem label="Region" value={meta?.region} />
          <InfoItem label="Income Level" value={meta?.incomeLevel} />
          <InfoItem label="Capital" value={meta?.capitalCity} />
          <InfoItem label="Population (latest)" value={fmtInt(kpis.pop.cur?.value)} foot={kpis.pop.cur?.date} />
          <InfoItem label="GDP (current USD)" value={`$${fmt(kpis.gdpUsd.cur?.value, 0)}`} foot={kpis.gdpUsd.cur?.date} />
          <InfoItem label="Coordinates" value={meta?.latitude && meta?.longitude ? `${meta.latitude}, ${meta.longitude}` : '—'} />
        </div>
      </section>

      {/* KPIs with trend */}
      <section className="space-y-3">
        <h3 className="text-lg font-semibold text-slate-800">Key Indicators (World Bank)</h3>
        {errs.head && <div className="text-amber-600 text-sm">{errs.head}</div>}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <KpiTrend label="Real GDP Growth (YoY)" cur={kpis.gdpGrowth.cur} prev={kpis.gdpGrowth.prev} unit="%" />
          <KpiTrend label="CPI Inflation (YoY)" cur={kpis.cpi.cur} prev={kpis.cpi.prev} unit="%" />
          <KpiTrend label="Unemployment Rate" cur={kpis.unemp.cur} prev={kpis.unemp.prev} unit="%" />
          <CardStat label="GDP per Capita (USD)" val={kpis.gdpPcap.cur?.value} prefix="$" year={kpis.gdpPcap.cur?.date} />
          <CardStat label="Current Account (% GDP)" val={kpis.ca.cur?.value} unit="%" year={kpis.ca.cur?.date} />
          <CardStat label="Exports (% GDP)" val={kpis.exp.cur?.value} unit="%" year={kpis.exp.cur?.date} />
          <CardStat label="Govt Debt (% GDP)" val={kpis.debt.cur?.value} unit="%" year={kpis.debt.cur?.date} />
          <CardStat label="Life Expectancy (yrs)" val={kpis.life.cur?.value} unit="" year={kpis.life.cur?.date} />
          <CardStat label="Gini (inequality)" val={kpis.gini.cur?.value} unit="" year={kpis.gini.cur?.date} />
          <CardStat label="LFPR (% 15+)" val={kpis.lfpr.cur?.value} unit="%" year={kpis.lfpr.cur?.date} />
          <CardStat label="Gross Savings (% GNI)" val={kpis.savings.cur?.value} unit="%" year={kpis.savings.cur?.date} />
        </div>
      </section>

      {/* Line Charts — 10y + CSV */}
      <section className="space-y-3">
        <h3 className="text-lg font-semibold text-slate-800">10-Year Time Series</h3>
        {errs.series && <div className="text-amber-600 text-sm">{errs.series}</div>}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <ChartCard title="GDP Growth (YoY, %)" data={series.gdpGrowth} digits={2} onExport={() => exportSeries('gdp_growth', series.gdpGrowth)} />
          <ChartCard title="CPI Inflation (YoY, %)" data={series.cpi} digits={2} onExport={() => exportSeries('cpi_inflation', series.cpi)} />
          <ChartCard title="Unemployment (% labor force)" data={series.unemp} digits={2} onExport={() => exportSeries('unemployment', series.unemp)} />
          <ChartCard title="Govt Debt (% GDP)" data={series.debt} digits={1} onExport={() => exportSeries('debt_pct_gdp', series.debt)} />
          <ChartCard title="Life Expectancy (yrs)" data={series.life} digits={1} onExport={() => exportSeries('life_expectancy', series.life)} />
          <ChartCard title="Savings (% GNI)" data={series.savings} digits={1} onExport={() => exportSeries('savings_pct_gni', series.savings)} />
        </div>
      </section>

      {/* Documents (search + type filter) */}
      <section className="space-y-3">
        <div className="flex items-end justify-between gap-3 flex-wrap">
          <h3 className="text-lg font-semibold text-slate-800">World Bank — Latest Documents</h3>
          <div className="flex items-center gap-2">
            <input
              placeholder="Filter title…"
              value={filters.title}
              onChange={(e) => setFilters(f => ({ ...f, title: e.target.value }))}
              className="px-3 py-2 rounded-xl border border-slate-300 bg-white text-slate-800 shadow-sm"
            />
            <select
              value={filters.docty}
              onChange={(e) => setFilters(f => ({ ...f, docty: e.target.value }))}
              className="px-3 py-2 rounded-xl border border-slate-300 bg-white text-slate-800 shadow-sm"
            >
              <option value="">All types</option>
              {docTypes.map((d, i) => <option key={i} value={d.name}>{d.name} ({d.count})</option>)}
            </select>
          </div>
        </div>
        {errs.docs && <div className="text-amber-600 text-sm">{errs.docs}</div>}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {docs.map((d, i) => (
            <article key={i} className="rounded-2xl border border-slate-200 p-4 bg-white shadow-sm">
              <div className="text-sm text-slate-500">{d.type || '—'} · {d.date || '—'}</div>
              <h4 className="mt-1 font-medium text-slate-900 line-clamp-2">{d.title}</h4>
              <div className="mt-2 flex items-center gap-3">
                {d.pdf && <a href={d.pdf} target="_blank" rel="noreferrer" className="text-indigo-700 hover:underline">PDF</a>}
                {d.url && <a href={d.url} target="_blank" rel="noreferrer" className="text-slate-700 hover:underline">Record</a>}
              </div>
            </article>
          ))}
          {docs.length === 0 && <div className="text-sm text-slate-500">No recent documents found.</div>}
        </div>
        <p className="text-xs text-slate-500">World Bank Documents are fetched via your Vite proxy at <code>/wds</code> (bypasses CORS).</p>
      </section>

      <p className="text-xs text-slate-500">Sources: World Bank Data API & Documents API; India market data via your backend proxy to IndianAPI.</p>
    </div>
  );
}

/* =========================================
   PRESENTATIONAL PARTS
========================================= */
function InfoItem({ label, value, foot }) {
  return (
    <div className="rounded-xl border border-slate-200 p-3">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-1 text-slate-900 font-medium">{value ?? '—'}</div>
      {foot && <div className="text-[11px] text-slate-500 mt-0.5">Year: {foot}</div>}
    </div>
  );
}

function CardStat({ label, val, unit = '', prefix = '', year }) {
  const showPct = unit === '%';
  return (
    <div className="rounded-2xl border border-slate-200 p-4 bg-white shadow-sm">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-2 text-2xl font-semibold text-slate-900">
        {val == null ? '—' : `${prefix}${fmt(val, 2)}${showPct ? '%' : ''}`}
      </div>
      <div className="mt-1 text-xs text-slate-500">Latest year: {year || '—'}</div>
    </div>
  );
}

function KpiTrend({ label, cur, prev, unit = '%' }) {
  const v = cur?.value ?? null, y = cur?.date ?? null;
  const pv = prev?.value ?? null, py = prev?.date ?? null;
  const diff = (v != null && pv != null) ? v - pv : null;
  const up = diff != null ? diff >= 0 : null;
  return (
    <div className="rounded-2xl border border-slate-200 p-4 bg-white shadow-sm">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-2 text-2xl font-semibold text-slate-900">
        {v == null ? '—' : `${fmt(v, 2)}${unit ? '%' : ''}`}
      </div>
      <div className="mt-1 text-xs text-slate-500">
        Latest year: {y || '—'}
        {diff != null && (
          <span className={`ml-2 inline-flex items-center rounded px-1.5 py-0.5 ${up ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}>
            {up ? '▲' : '▼'} {fmt(Math.abs(diff), 2)}{unit}
            {py && <span className="ml-1 text-slate-400">vs {py}</span>}
          </span>
        )}
      </div>
    </div>
  );
}

function ChartCard({ title, data, digits = 2, onExport }) {
  return (
    <div className="rounded-2xl border border-slate-200 p-4 bg-white shadow-sm">
      <div className="flex items-center justify-between">
        <div className="text-sm text-slate-500">{title}</div>
        <button
          type="button"
          onClick={onExport}
          className="text-xs px-2 py-1 rounded border border-slate-300 hover:bg-slate-50"
        >
          Download CSV
        </button>
      </div>
      <LineChart data={data} valueDigits={digits} />
      <div className="mt-2 text-[11px] text-slate-500">Last {data?.length || 0} observations</div>
    </div>
  );
}
