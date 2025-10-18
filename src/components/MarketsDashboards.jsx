// src/components/MarketsDashboard.jsx
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { API_ORIGIN } from '../config'; // keep existing config

/* ---------------- utilities ---------------- */
function fmtNum(n, d = 2) {
  if (n === null || n === undefined || n === '' || !isFinite(Number(n))) return '—';
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: d }).format(Number(n));
}
function fmtPct(n) {
  if (n === null || n === undefined || n === '' || !isFinite(Number(n))) return '—';
  const v = Number(n);
  return `${v >= 0 ? '+' : ''}${v}%`;
}
function safeGet(obj, ...keys) {
  let cur = obj;
  for (const k of keys) {
    if (!cur) return undefined;
    cur = cur[k];
  }
  return cur;
}
function csvDownload(filename, rows) {
  const esc = v => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const csv = rows.map(r => r.map(esc).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
}

/* ---------- fetch helper (robust, informative) ---------- */
async function apiFetch(path, params = {}, opts = {}) {
  const qs = new URLSearchParams();
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') qs.append(k, String(v));
  });
  const qstr = qs.toString() ? `?${qs.toString()}` : '';

  const candidates = [];
  if (typeof API_ORIGIN === 'string' && API_ORIGIN) {
    const base = API_ORIGIN.replace(/\/$/, '');
    candidates.push(`${base}/api/${path}${qstr}`);
  }
  candidates.push(`/api/${path}${qstr}`);
  candidates.push(`/indianapi/${path}${qstr}`);
  candidates.push(`http://localhost:5000/api/${path}${qstr}`);
  candidates.push(`http://127.0.0.1:5000/api/${path}${qstr}`);

  let lastErr = null;
  for (const url of candidates) {
    try {
      const controller = new AbortController();
      const timeout = opts.timeout || 8000;
      const t = setTimeout(() => controller.abort(), timeout);
      const res = await fetch(url, { credentials: 'same-origin', signal: controller.signal, headers: { Accept: 'application/json, text/plain, */*' } });
      clearTimeout(t);
      const ct = res.headers.get ? (res.headers.get('content-type') || '') : '';
      const text = await res.text().catch(() => '');
      if (!res.ok) {
        // construct informative error with server body snippet
        const snippet = text ? text.slice(0, 200) : res.statusText;
        const err = new Error(`HTTP ${res.status} from ${url}: ${snippet}`);
        err.status = res.status; err.body = text; err.url = url;
        throw err;
      }
      // try parse JSON, otherwise return text
      if (ct.toLowerCase().includes('json') || ct.toLowerCase().includes('+json')) {
        try { return JSON.parse(text); } catch (parseErr) { return text; }
      }
      try { return JSON.parse(text); } catch { return text; }
    } catch (err) {
      lastErr = err;
      // try next candidate silently (we capture in DebugPanel)
    }
  }
  throw lastErr || new Error('All API fetch attempts failed');
}

/* Simple throttle to prevent flooding API for same key */
const fetchThrottleMap = new Map();
async function fetchThrottle(key, fn, ms = 600) {
  const now = Date.now();
  const prev = fetchThrottleMap.get(key) || 0;
  if (now - prev < ms) {
    await new Promise(r => setTimeout(r, ms - (now - prev)));
  }
  fetchThrottleMap.set(key, Date.now());
  return fn();
}

/* ---------- DebugPanel (handy during dev) ---------- */
function DebugPanel({ visible = true }) {
  const [out, setOut] = useState([]);
  const append = (label, v) => setOut(o => [...o, { label, v }]);
  useEffect(() => {
    if (!visible) return;
    (async () => {
      const base = (typeof API_ORIGIN === 'string' && API_ORIGIN) ? API_ORIGIN.replace(/\/$/, '') : window.location.origin;
      const checks = [
        { url: `${base}/api/trending`, label: 'trending (remote)' },
        { url: `/api/trending`, label: 'trending (relative)' },
        { url: `/api/_debug_env`, label: '_debug_env (relative)' },
        { url: `/indianapi/trending`, label: '/indianapi/trending (proxy)' },
      ];
      for (const c of checks) {
        try {
          const res = await fetch(c.url, { credentials: 'same-origin' });
          const ct = res.headers.get && res.headers.get('content-type') || '';
          const text = await res.text().catch(() => '');
          let body = text;
          if (ct.includes('json')) {
            try { body = JSON.parse(text); } catch {}
          }
          append(c.label, { status: res.status, ok: res.ok, body: (typeof body === 'string' ? body.slice(0, 1000) : body), type: typeof body });
        } catch (err) {
          append(c.label, { error: String(err) });
        }
      }
    })();
  }, [visible]);
  if (!visible) return null;
  return (
    <div className="rounded p-3 bg-white border text-xs mb-4">
      <div className="font-semibold mb-2">Diagnostics</div>
      <div className="max-h-40 overflow-auto">
        {out.map((r, i) => (
          <div key={i} className="mb-2">
            <div className="text-slate-700">{r.label} — {r.v.error ? 'ERR' : `HTTP ${r.v.status}`}</div>
            <div className="text-[11px] text-slate-500">type: {r.v.type ?? typeof r.v.body}</div>
            <pre className="text-[11px] text-slate-500 whitespace-pre-wrap">{typeof r.v.body === 'string' ? r.v.body : JSON.stringify(r.v.body, null, 2)}</pre>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------- Basic UI components ---------- */

function Sparkline({ values = [], width = 200, height = 40 }) {
  if (!values || values.length === 0) return <div className="text-xs text-slate-400">No data</div>;
  const nums = values.map(v => Number(v[1] ?? v));
  const min = Math.min(...nums);
  const max = Math.max(...nums);
  const range = max - min || 1;
  const stepX = width / Math.max(1, nums.length - 1);
  const points = nums.map((n, i) => `${i * stepX},${height - ((n - min) / range) * height}`).join(' ');
  const last = nums[nums.length - 1];
  const color = last >= nums[0] ? '#059669' : '#ef4444';
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="block">
      <polyline fill="none" stroke={color} strokeWidth="1.6" points={points} />
    </svg>
  );
}

/* ---------- Panels: Stock search + details ---------- */

function StockDetails({ stock, onViewDeeper }) {
  if (!stock) return (
    <div className="rounded-2xl border p-4 bg-white text-sm text-slate-500">No stock selected — search above to view details.</div>
  );

  const tickerId = stock.tickerId || stock.ticker_id || stock.ticker || stock.ric || stock.ticker;
  const name = stock.companyName || stock.company_name || stock.commonName || stock.name || 'Company';
  const priceObj = stock.currentPrice || stock.current_price || stock.price || {};
  const price = (typeof priceObj === 'object') ? (priceObj.NSE ?? priceObj.BSE ?? priceObj.latest ?? priceObj.value ?? priceObj) : priceObj;
  const pct = stock.percentChange ?? stock.percent_change ?? stock.percent ?? 0;
  const metrics = stock.keyMetrics || stock.key_metrics || stock.stockDetailsReusableData || {};
  const yearHigh = stock.yearHigh ?? stock.year_high;
  const yearLow = stock.yearLow ?? stock.year_low;

  return (
    <div className="rounded-2xl border p-4 bg-white">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="text-lg font-semibold truncate">{name} <span className="text-sm text-slate-400">({tickerId})</span></div>
          <div className="text-sm text-slate-500 mt-1">{stock.industry ?? stock.mgIndustry ?? ''}</div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-semibold">{fmtNum(price)}</div>
          <div className={`text-sm ${Number(pct) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>{fmtPct(pct)}</div>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4 text-xs text-slate-600">
        <div>PE: {fmtNum(metrics.pe_ratio ?? metrics.pe ?? metrics.PE)}</div>
        <div>PB: {fmtNum(metrics.pb_ratio ?? metrics.pb ?? metrics.PB)}</div>
        <div>Div Yld: {fmtNum(metrics.dividend_yield ?? metrics.dividendYield ?? metrics.div_yield)}</div>
        <div>Mkt Cap: {fmtNum(metrics.market_cap ?? metrics.mktcap ?? metrics.marketCap, 0)}</div>
        <div>52wk High: {fmtNum(yearHigh)}</div>
        <div>52wk Low: {fmtNum(yearLow)}</div>
        <div className="col-span-2 text-right">
          <button onClick={() => onViewDeeper && onViewDeeper(tickerId)} className="px-3 py-1 rounded-md bg-slate-800 text-white text-sm">View deeper</button>
        </div>
      </div>
    </div>
  );
}

/* ---------- Main MarketsDashboard component ---------- */
export default function MarketsDashboard() {
  const [query, setQuery] = useState('');
  const [stock, setStock] = useState(null);
  const [selectedTicker, setSelectedTicker] = useState(null);
  const [loadingMap, setLoadingMap] = useState({});
  const [errorMap, setErrorMap] = useState({});
  const [trending, setTrending] = useState(null);
  const [nseActive, setNseActive] = useState(null);
  const [bseActive, setBseActive] = useState(null);
  const [commodities, setCommodities] = useState(null);
  const [mutualFunds, setMutualFunds] = useState(null);
  const [priceShockers, setPriceShockers] = useState(null);
  const [ipos, setIpos] = useState(null);
  const [news, setNews] = useState(null);
  const [historical, setHistorical] = useState(null);
  const [forecasts, setForecasts] = useState(null);
  const [targetPrice, setTargetPrice] = useState(null);
  const [macro, setMacro] = useState(null); // World Bank macro
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  const setLoading = useCallback((k, v) => setLoadingMap(m => ({ ...m, [k]: v })), []);
  const setError = useCallback((k, v) => setErrorMap(m => ({ ...m, [k]: v })), []);

  /* ---------- fetch many panels on mount (limit frequency) ---------- */
  useEffect(() => {
    // helper to safely coerce array-like responses
    const toArray = (data) => {
      if (!data) return [];
      if (Array.isArray(data)) return data;
      // sometimes api returns object with keys being items
      if (typeof data === 'object') {
        // if object has keys like trending_stocks -> check nested
        if (data.trending_stocks) return toArray(data.trending_stocks.top_gainers || data.trending_stocks.topLosers || data.trending_stocks);
        // if object is keyed by categories (mutual funds), return object values
        const vals = Object.values(data);
        // If values are arrays and first entry looks like items, flatten first useful array
        if (vals.length === 0) return [];
        const firstArr = vals.find(v => Array.isArray(v));
        if (firstArr) return firstArr;
        // fallback: return values as items
        return vals;
      }
      // if string, return empty
      return [];
    };

    (async () => {
      setLoading('trending', true); setError('trending', null);
      try {
        const j = await fetchThrottle('trending', () => apiFetch('trending'));
        if (!mountedRef.current) return;
        setTrending(j || null);
      } catch (err) {
        if (!mountedRef.current) return;
        setError('trending', err.message || String(err));
      } finally {
        if (mountedRef.current) setLoading('trending', false);
      }
    })();

    (async () => {
      setLoading('nse', true); setError('nse', null);
      try {
        const j = await fetchThrottle('nse', () => apiFetch('NSE_most_active'));
        if (!mountedRef.current) return;
        setNseActive(j || null);
      } catch (err) {
        if (!mountedRef.current) return;
        setError('nse', err.message || String(err));
      } finally {
        if (mountedRef.current) setLoading('nse', false);
      }
    })();

    (async () => {
      setLoading('bse', true); setError('bse', null);
      try {
        const j = await fetchThrottle('bse', () => apiFetch('BSE_most_active'));
        if (!mountedRef.current) return;
        setBseActive(j || null);
      } catch (err) {
        if (!mountedRef.current) return;
        setError('bse', err.message || String(err));
      } finally {
        if (mountedRef.current) setLoading('bse', false);
      }
    })();

    (async () => {
      setLoading('commod', true); setError('commod', null);
      try {
        const j = await fetchThrottle('commod', () => apiFetch('commodities'));
        if (!mountedRef.current) return;
        setCommodities(j || null);
      } catch (err) {
        if (!mountedRef.current) return;
        setError('commod', err.message || String(err));
      } finally {
        if (mountedRef.current) setLoading('commod', false);
      }
    })();

    (async () => {
      setLoading('mf', true); setError('mf', null);
      try {
        const j = await fetchThrottle('mf', () => apiFetch('mutual_funds'));
        if (!mountedRef.current) return;
        setMutualFunds(j || null);
      } catch (err) {
        if (!mountedRef.current) return;
        setError('mf', err.message || String(err));
      } finally {
        if (mountedRef.current) setLoading('mf', false);
      }
    })();

    (async () => {
      setLoading('shock', true); setError('shock', null);
      try {
        const j = await fetchThrottle('shock', () => apiFetch('price_shockers'));
        if (!mountedRef.current) return;
        setPriceShockers(j || null);
      } catch (err) {
        if (!mountedRef.current) return;
        setError('shock', err.message || String(err));
      } finally {
        if (mountedRef.current) setLoading('shock', false);
      }
    })();

    (async () => {
      setLoading('ipo', true); setError('ipo', null);
      try {
        const j = await fetchThrottle('ipo', () => apiFetch('ipo'));
        if (!mountedRef.current) return;
        setIpos(j || null);
      } catch (err) {
        if (!mountedRef.current) return;
        setError('ipo', err.message || String(err));
      } finally {
        if (mountedRef.current) setLoading('ipo', false);
      }
    })();

    (async () => {
      setLoading('news', true); setError('news', null);
      try {
        const j = await fetchThrottle('news', () => apiFetch('news'));
        if (!mountedRef.current) return;
        setNews(j || null);
      } catch (err) {
        if (!mountedRef.current) return;
        setError('news', err.message || String(err));
      } finally {
        if (mountedRef.current) setLoading('news', false);
      }
    })();

    // World Bank macro (fetch directly from worldbank API)
    (async () => {
      setLoading('macro', true); setError('macro', null);
      try {
        const resp = await fetch('https://api.worldbank.org/v2/country/IN/indicator/NY.GDP.MKTP.CD?format=json&per_page=1&date=2020:2024');
        const txt = await resp.text();
        let body = null;
        try { body = JSON.parse(txt); } catch { body = txt; }
        if (!mountedRef.current) return;
        setMacro(body);
      } catch (err) {
        if (!mountedRef.current) return;
        setError('macro', String(err));
      } finally {
        if (mountedRef.current) setLoading('macro', false);
      }
    })();

  }, []);

  /* ---------- search for a stock by name (calls /stock?name=) ---------- */
  const handleSearch = useCallback(async (q) => {
    const qtrim = (q || query || '').trim();
    if (!qtrim) return;
    setLoading('stockSearch', true); setError('stockSearch', null);
    setStock(null);
    try {
      const data = await apiFetch('stock', { name: qtrim });
      // unify array/object: many APIs return either array or single object
      const chosen = Array.isArray(data) ? data[0] : data;
      if (!chosen) {
        setError('stockSearch', 'No stock data returned');
        return;
      }
      setStock(chosen || null);
      setSelectedTicker(chosen?.tickerId || chosen?.ticker || chosen?.ric || null);

      // historical (guarded)
      if (chosen?.tickerId || chosen?.ticker || chosen?.companyName) {
        const stockNameParam = (chosen.tickerId || chosen.ticker || chosen.companyName || qtrim);
        setLoading('historical', true); setError('historical', null);
        try {
          const hist = await apiFetch('historical_data', { stock_name: stockNameParam, period: '1yr', filter: 'price' });
          if (mountedRef.current) setHistorical(hist || null);
        } catch (err) {
          if (mountedRef.current) setError('historical', err.message || String(err));
        } finally {
          if (mountedRef.current) setLoading('historical', false);
        }

        if (chosen.tickerId || chosen.ticker) {
          const id = chosen.tickerId || chosen.ticker;
          setLoading('forecasts', true); setError('forecasts', null);
          try {
            const f = await apiFetch('stock_forecasts', { stock_id: id, measure_code: 'EPS', period_type: 'Annual', data_type: 'Actuals', age: 'Current' });
            if (mountedRef.current) setForecasts(f || null);
          } catch (err) {
            if (mountedRef.current) setError('forecasts', err.message || String(err));
          } finally { if (mountedRef.current) setLoading('forecasts', false); }

          setLoading('target', true); setError('target', null);
          try {
            const t = await apiFetch('stock_target_price', { stock_id: id });
            if (mountedRef.current) setTargetPrice(t || null);
          } catch (err) {
            if (mountedRef.current) setError('target', err.message || String(err));
          } finally { if (mountedRef.current) setLoading('target', false); }
        }
      }
    } catch (err) {
      setError('stockSearch', err.message || String(err));
    } finally {
      setLoading('stockSearch', false);
    }
  }, [query]);

  /* ---------- helper to render trending list ---------- */
  const renderList = (items = [], labelKey = 'company_name', valueKey = 'percent_change') => {
    if (!items) return <div className="text-xs text-slate-500">No data</div>;
    // coerce to array - support object keyed responses
    let arr = [];
    if (Array.isArray(items)) arr = items;
    else if (typeof items === 'object') {
      // if the object contains arrays, prefer those
      const nested = Object.values(items).find(v => Array.isArray(v));
      if (nested) arr = nested;
      else arr = Object.values(items);
    } else {
      return <div className="text-xs text-slate-500">No data</div>;
    }
    if (!arr || arr.length === 0) return <div className="text-xs text-slate-500">No data</div>;
    return arr.slice(0, 6).map((it, i) => {
      const label = (it && (it[labelKey] ?? it.name ?? it.ticker ?? it.company ?? '—')) || '—';
      const pct = Number(it?.[valueKey] ?? it?.percent ?? 0);
      return (
        <div key={i} className="flex justify-between py-1">
          <div className="truncate text-sm">{label}</div>
          <div className={`text-xs ${pct >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>{fmtPct(pct)}</div>
        </div>
      );
    });
  };

  function handleViewDeeper(ticker) {
    if (!ticker) return;
    const path = `/sections/markets?ticker=${encodeURIComponent(ticker)}`;
    window.open(path, '_blank');
  }

  const topGainers = trending?.trending_stocks?.top_gainers || trending?.top_gainers || (Array.isArray(trending) ? trending : []);
  const topLosers = trending?.trending_stocks?.top_losers || trending?.top_losers || [];

  const historicalRows = useMemo(() => {
    const ds = historical?.datasets && Array.isArray(historical.datasets) ? historical.datasets.find(d => /price/i.test(d.metric || d.label || '')) || historical.datasets[0] : null;
    const vals = ds?.values || [];
    return [['date', 'price'], ...vals.map(r => [r[0], r[1]])];
  }, [historical]);

  /* ---------- UI ---------- */
  return (
    <div className="space-y-6">
      <DebugPanel visible={true} />

      <div className="rounded-2xl border p-4 bg-white flex gap-3 items-center">
        <input type="text" placeholder="Search stock by name or symbol (e.g. Reliance, TCS)" value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') handleSearch(); }} className="flex-1 border rounded-xl px-4 py-3" />
        <button onClick={() => handleSearch()} className="px-4 py-2 rounded-xl bg-slate-800 text-white">Search</button>
        <button onClick={() => { if (selectedTicker) window.open(`/sections/markets?ticker=${selectedTicker}`, '_blank'); }} className="px-3 py-2 rounded-xl border">Open detail</button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <StockDetails stock={stock} onViewDeeper={handleViewDeeper} />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-2xl border p-4 bg-white">
              <div className="text-sm font-medium text-slate-700 mb-2">Analyst Recommendation</div>
              {loadingMap['target'] && <div className="text-sm text-slate-500">Loading…</div>}
              {!loadingMap['target'] && errorMap['target'] && <div className="text-sm text-rose-600">{errorMap['target']}</div>}
              {!loadingMap['target'] && targetPrice && (
                <>
                  <div className="text-lg font-semibold">{(() => {
                    const rec = targetPrice.recommendation;
                    const mean = rec?.PreliminaryMean ?? rec?.UnverifiedMean ?? rec?.Mean ?? (typeof rec === 'number' ? rec : null);
                    if (mean == null) return 'N/A';
                    const m = Number(mean);
                    if (m <= 1.5) return 'Buy';
                    if (m <= 2.5) return 'Outperform';
                    if (m <= 3.5) return 'Hold';
                    if (m <= 4.5) return 'Underperform';
                    return 'Sell';
                  })()}</div>
                  <div className="text-xs text-slate-500 mt-1">Estimates: {targetPrice.priceTarget?.NumberOfEstimates ?? targetPrice.priceTarget?.NumberOfAnalysts ?? '—'}</div>
                  <div className="mt-3 text-xs text-slate-600">{targetPrice.priceTarget ? `Mean: ${fmtNum(targetPrice.priceTarget.Mean)} High: ${fmtNum(targetPrice.priceTarget.High)} Low: ${fmtNum(targetPrice.priceTarget.Low)}` : 'No analyst target available.'}</div>
                </>
              )}
            </div>

            <div className="rounded-2xl border p-4 bg-white">
              <div className="text-sm font-medium text-slate-700 mb-2">Forecasts (EPS sample)</div>
              {loadingMap['forecasts'] && <div className="text-sm text-slate-500">Loading…</div>}
              {!loadingMap['forecasts'] && errorMap['forecasts'] && <div className="text-sm text-rose-600">{errorMap['forecasts']}</div>}
              {!loadingMap['forecasts'] && forecasts && Array.isArray(forecasts) && forecasts.length > 0 && (
                <div className="space-y-1 text-xs text-slate-600">
                  {forecasts.slice(0, 4).map((fs, i) => (<div key={i}><strong>{fs.period ?? fs.horizon ?? fs.label ?? fs.date ?? '—'}</strong>: {fs.value ?? fs.summary ?? JSON.stringify(fs)}</div>))}
                </div>
              )}
              {!loadingMap['forecasts'] && forecasts && !Array.isArray(forecasts) && typeof forecasts === 'object' && (
                <div className="text-xs text-slate-600">{JSON.stringify(forecasts)}</div>
              )}
              {!loadingMap['forecasts'] && !forecasts && <div className="text-xs text-slate-500">No forecasts available</div>}
            </div>
          </div>

          <div className="rounded-2xl border p-4 bg-white space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium text-slate-700">Historical (price) — 1 year</div>
              <div className="text-xs text-slate-500">CSV export available</div>
            </div>
            {loadingMap['historical'] && <div className="text-sm text-slate-500">Loading…</div>}
            {!loadingMap['historical'] && historical && historical.datasets && Array.isArray(historical.datasets) && (
              <>
                {(() => {
                  const priceDs = historical.datasets.find(ds => /price/i.test(ds.metric || ds.label || '')) || historical.datasets[0];
                  const rows = (priceDs.values || []).map(r => [r[0], r[1]]);
                  return (
                    <>
                      <div className="mt-2">
                        <Sparkline values={priceDs.values || []} width={600} height={60} />
                      </div>
                      <div className="mt-3 text-xs text-slate-600 max-h-36 overflow-auto">
                        <table className="w-full text-xs">
                          <tbody>
                            {rows.slice(0, 10).map((r, i) => (<tr key={i}><td className="py-1">{r[0]}</td><td className="text-right py-1">{fmtNum(r[1])}</td></tr>))}
                          </tbody>
                        </table>
                      </div>
                      {rows.length > 0 && <div className="mt-3"><button onClick={() => csvDownload(`${stock?.companyName || selectedTicker}_1yr.csv`, [['date','price'], ...rows])} className="px-3 py-1 rounded-xl bg-slate-800 text-white text-sm">Download CSV</button></div>}
                    </>
                  );
                })()}
              </>
            )}
            {!loadingMap['historical'] && (!historical || !historical.datasets) && <div className="text-sm text-slate-500">No historical data</div>}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-2xl border p-4 bg-white">
              <div className="text-sm font-medium text-slate-700 mb-2">Recent Announcements</div>
              {loadingMap['announcements'] && <div className="text-sm text-slate-500">Loading…</div>}
              {!loadingMap['announcements'] && errorMap['announcements'] && <div className="text-sm text-rose-600">{errorMap['announcements']}</div>}
              {!loadingMap['announcements'] && news && (Array.isArray(news) ? news.slice(0, 6) : Object.values(news).slice(0,6)).map((n, i) => (
                <div key={i} className="py-1 border-b last:border-b-0 text-xs">
                  <a href={n.link ?? n.url ?? n.source_url ?? '#'} target="_blank" rel="noreferrer" className="hover:underline">{n.title ?? n.headline ?? n.name ?? 'Article'}</a>
                  <div className="text-xs text-slate-500">{n.source ?? n.date ?? ''}</div>
                </div>
              ))}
              {!loadingMap['announcements'] && (!news || (Array.isArray(news) && news.length === 0)) && <div className="text-sm text-slate-500">No announcements</div>}
            </div>

            <div className="rounded-2xl border p-4 bg-white">
              <div className="text-sm font-medium text-slate-700 mb-2">Upcoming IPOs</div>
              {loadingMap['ipo'] && <div className="text-sm text-slate-500">Loading…</div>}
              {!loadingMap['ipo'] && ipos && (Array.isArray(ipos) ? ipos.slice(0,6) : Object.values(ipos).slice(0,6)).map((i, idx) => (<div key={idx} className="py-1 border-b text-xs">{i.name ?? i.company ?? i.ticker ?? i.title}</div>))}
              {!loadingMap['ipo'] && (!ipos || (Array.isArray(ipos) && ipos.length === 0)) && <div className="text-sm text-slate-500">No upcoming IPOs</div>}
            </div>
          </div>
        </div>

        <aside className="space-y-4">
          <div className="rounded-2xl border p-4 bg-white w-72">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium text-slate-700">Trending</div>
              <div className="text-xs text-slate-500">Top movers</div>
            </div>
            <div className="mt-2 text-xs text-slate-500">Top Gainers</div>
            <div className="mt-1">{loadingMap['trending'] && <div className="text-xs text-slate-500">Loading…</div>}</div>
            <div className="mt-1 text-sm">{!loadingMap['trending'] && errorMap['trending'] ? <div className="text-xs text-rose-600">{errorMap['trending']}</div> : renderList(topGainers, 'company_name', 'percent_change')}</div>
            <div className="text-xs text-slate-500 mt-2">Top Losers</div>
            <div className="mt-1 text-sm">{!loadingMap['trending'] && renderList(topLosers, 'company_name', 'percent_change')}</div>
          </div>

          <div className="rounded-2xl border p-4 bg-white w-72">
            <div className="text-sm font-medium text-slate-700">NSE — Most Active</div>
            <div className="mt-2 text-xs text-slate-500">{loadingMap['nse'] ? 'Loading…' : (errorMap['nse'] ? <span className="text-rose-600">{errorMap['nse']}</span> : '')}</div>
            <div className="mt-2 text-sm">{!loadingMap['nse'] && renderList(nseActive || [], 'company', 'percent_change')}</div>
          </div>

          <div className="rounded-2xl border p-4 bg-white w-72">
            <div className="text-sm font-medium text-slate-700">BSE — Most Active</div>
            <div className="mt-2 text-xs text-slate-500">{loadingMap['bse'] ? 'Loading…' : (errorMap['bse'] ? <span className="text-rose-600">{errorMap['bse']}</span> : '')}</div>
            <div className="mt-2 text-sm">{!loadingMap['bse'] && renderList(bseActive || [], 'company', 'percent_change')}</div>
          </div>

          <div className="rounded-2xl border p-4 bg-white w-72">
            <div className="text-sm font-medium text-slate-700">Commodities</div>
            <div className="mt-2 text-xs text-slate-500">{loadingMap['commod'] ? 'Loading…' : (errorMap['commod'] ? <span className="text-rose-600">{errorMap['commod']}</span> : '')}</div>
            {!loadingMap['commod'] && commodities && Array.isArray(commodities) && commodities.slice(0,6).map((c, i) => (
              <div key={i} className="py-1 text-sm border-b last:border-b-0">
                <div className="truncate">{c.commoditySymbol ?? c.contractId ?? c.contractId}</div>
                <div className="text-xs text-slate-500">{fmtNum(c.lastTradedPrice ?? c.price ?? c.closingPrice)} ({fmtPct(c.percentageChange ?? c.priceChange ?? c.percentageChange)})</div>
              </div>
            ))}
            {!loadingMap['commod'] && (!commodities || (Array.isArray(commodities) && commodities.length === 0)) && <div className="text-xs text-slate-500 mt-2">No data</div>}
          </div>

          <div className="rounded-2xl border p-4 bg-white w-72">
            <div className="text-sm font-medium text-slate-700">Mutual Funds</div>
            <div className="mt-2 text-xs text-slate-500">{loadingMap['mf'] ? 'Loading…' : (errorMap['mf'] ? <span className="text-rose-600">{errorMap['mf']}</span> : '')}</div>
            {!loadingMap['mf'] && mutualFunds && typeof mutualFunds === 'object' && (
              <>
                {Object.entries(mutualFunds).slice(0,1).map(([k,v]) => {
                  // v may be object categories, or arrays; defend accordingly
                  const arr = Array.isArray(v) ? v : (v && typeof v === 'object' ? Object.values(v).flat().filter(Boolean) : []);
                  return (
                    <div key={k} className="mt-2 text-sm">
                      <div className="text-xs text-slate-600">{k}</div>
                      {(arr || []).slice(0,4).map((f,i) => (<div key={i} className="py-1 text-sm">{f.fund_name ?? f.schemeName ?? f.scheme_name ?? f.scheme}</div>))}
                    </div>
                  );
                })}
              </>
            )}
            {!loadingMap['mf'] && (!mutualFunds || (Object.keys(mutualFunds || {}).length === 0)) && <div className="text-xs text-slate-500 mt-2">No data</div>}
          </div>

          <div className="rounded-2xl border p-4 bg-white w-72">
            <div className="text-sm font-medium text-slate-700">Price Shockers</div>
            <div className="mt-2 text-xs text-slate-500">{loadingMap['shock'] ? 'Loading…' : (errorMap['shock'] ? <span className="text-rose-600">{errorMap['shock']}</span> : '')}</div>
            {!loadingMap['shock'] && priceShockers && (Array.isArray(priceShockers) ? priceShockers.slice(0,6) : Object.values(priceShockers).slice(0,6)).map((s,i) => (<div key={i} className="py-1 text-sm border-b">{s.company ?? s.ticker ?? s.name}</div>))}
            {!loadingMap['shock'] && (!priceShockers || (Array.isArray(priceShockers) && priceShockers.length === 0)) && <div className="text-xs text-slate-500 mt-2">No data</div>}
          </div>

          <div className="rounded-2xl border p-4 bg-white w-72">
            <div className="text-sm font-medium text-slate-700">Macro (World Bank)</div>
            <div className="mt-2 text-xs text-slate-500">{loadingMap['macro'] ? 'Loading…' : (errorMap['macro'] ? <span className="text-rose-600">{errorMap['macro']}</span> : '')}</div>
            {!loadingMap['macro'] && macro && Array.isArray(macro) && (
              <div className="text-xs text-slate-600 mt-2">
                <div>Indicator snapshot:</div>
                <pre className="text-[11px]">{JSON.stringify(macro, null, 2).slice(0, 400)}</pre>
              </div>
            )}
            {!loadingMap['macro'] && !macro && <div className="text-xs text-slate-500 mt-2">No data</div>}
          </div>
        </aside>
      </div>
    </div>
  );
}
