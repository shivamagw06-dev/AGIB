// src/components/MarketsDashboards.jsx
import React, { useEffect, useMemo, useState, useRef } from 'react';
import { API_ORIGIN } from '../config'; // keep your existing config or window.location origin

/* ---------- small utils ---------- */
function fmt(n, d = 2) {
  if (n == null || n === '' || !isFinite(Number(n))) return '—';
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: d }).format(Number(n));
}
function fmtPct(n) {
  if (n == null || n === '' || !isFinite(Number(n))) return '—';
  const v = Number(n);
  return `${v >= 0 ? '+' : ''}${v}%`;
}
function csvDownload(filename, rows) {
  // rows: array of arrays (rows/cols)
  const csv = rows
    .map(r =>
      r
        .map(c => {
          const cell = c == null ? '' : String(c);
          return `"${cell.replace(/"/g, '""')}"`;
        })
        .join(',')
    )
    .join('\n');
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

/* ---------- basic safe fetch wrapper ---------- */
async function apiFetch(path, params = {}) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') qs.append(k, String(v));
  });
  const qstr = qs.toString() ? `?${qs.toString()}` : '';
  const base = API_ORIGIN ? API_ORIGIN.replace(/\/$/, '') : window.location.origin;
  // Backend proxy assumed at /api/<path>
  const url = `${base}/api/${path}${qstr}`;

  const res = await fetch(url, { credentials: 'same-origin' });
  const ct = (res.headers.get && res.headers.get('content-type')) || '';
  const text = await res.text().catch(() => '');
  if (!res.ok) {
    const snippet = text ? text.slice(0, 800) : res.statusText;
    const err = new Error(`HTTP ${res.status}: ${snippet}`);
    err.status = res.status;
    err.body = text;
    throw err;
  }
  if (ct.includes('json') || ct.includes('+json')) {
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

/* ---------- G20 countries list (name + ISO2/ISO3 where useful) ---------- */
const G20 = [
  { name: 'Argentina', iso2: 'AR', iso3: 'ARG' },
  { name: 'Australia', iso2: 'AU', iso3: 'AUS' },
  { name: 'Brazil', iso2: 'BR', iso3: 'BRA' },
  { name: 'Canada', iso2: 'CA', iso3: 'CAN' },
  { name: 'China', iso2: 'CN', iso3: 'CHN' },
  { name: 'France', iso2: 'FR', iso3: 'FRA' },
  { name: 'Germany', iso2: 'DE', iso3: 'DEU' },
  { name: 'India', iso2: 'IN', iso3: 'IND' },
  { name: 'Indonesia', iso2: 'ID', iso3: 'IDN' },
  { name: 'Italy', iso2: 'IT', iso3: 'ITA' },
  { name: 'Japan', iso2: 'JP', iso3: 'JPN' },
  { name: 'Mexico', iso2: 'MX', iso3: 'MEX' },
  { name: 'Russia', iso2: 'RU', iso3: 'RUS' },
  { name: 'Saudi Arabia', iso2: 'SA', iso3: 'SAU' },
  { name: 'South Africa', iso2: 'ZA', iso3: 'ZAF' },
  { name: 'South Korea', iso2: 'KR', iso3: 'KOR' },
  { name: 'Turkey', iso2: 'TR', iso3: 'TUR' },
  { name: 'United Kingdom', iso2: 'GB', iso3: 'GBR' },
  { name: 'United States', iso2: 'US', iso3: 'USA' },
  { name: 'European Union', iso2: 'EU', iso3: 'EU' } // EU often included in G20 context
];

/* ---------- Stock search + details component ---------- */
function StockDetails({ stock }) {
  if (!stock) return null;

  const tickerId = stock.tickerId || stock.ticker_id || stock.ticker || stock.ric || stock.symbol;
  const name = stock.companyName || stock.company_name || stock.commonName || stock.name || tickerId;
  const metrics = stock.keyMetrics || stock.key_metrics || stock.stockDetailsReusableData || {};
  const priceObj = stock.currentPrice || stock.current_price || stock.price || stock.latestPrice || {};
  const price = typeof priceObj === 'object' ? (priceObj.NSE ?? priceObj.BSE ?? priceObj.latest ?? priceObj.value ?? priceObj) : priceObj;
  const pct = Number(stock.percentChange ?? stock.percent_change ?? stock.percent ?? stock.changePercent ?? 0);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="text-lg font-semibold truncate">
            {name} <span className="text-sm text-slate-400">({tickerId})</span>
          </div>
          <div className="text-sm text-slate-500 mt-1">{stock.industry ?? stock.mgIndustry ?? stock.sector ?? ''}</div>
        </div>
        <div className="text-right">
          <div className="text-xl font-semibold">{fmt(price)}</div>
          <div className={`text-sm ${pct >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>{fmtPct(pct)}</div>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-4 text-xs text-slate-600">
        <div>PE: {fmt(metrics.pe_ratio ?? metrics.pe ?? metrics.PE)}</div>
        <div>PB: {fmt(metrics.pb_ratio ?? metrics.pb ?? metrics.PB)}</div>
        <div>Div Yld: {fmt(metrics.dividend_yield ?? metrics.dividendYield ?? metrics.div_yield)}</div>
        <div>52wk High: {fmt(stock.yearHigh ?? stock.year_high)}</div>
        <div>52wk Low: {fmt(stock.yearLow ?? stock.year_low)}</div>
        <div>Mkt Cap: {fmt(metrics.market_cap ?? metrics.mktcap ?? metrics.marketCap, 0)}</div>
      </div>
    </div>
  );
}

/* ---------- Extra panels for a selected stock (forecasts, targets, history, news) ---------- */
function StockExtraPanels({ tickerId, stockName }) {
  const [forecasts, setForecasts] = useState(null);
  const [target, setTarget] = useState(null);
  const [historical, setHistorical] = useState(null);
  const [news, setNews] = useState(null);
  const [loading, setLoading] = useState({ f: false, t: false, h: false, n: false });
  const safeTicker = tickerId || stockName;

  useEffect(() => {
    let mounted = true;
    if (!safeTicker) return;

    // Forecasts
    setLoading(l => ({ ...l, f: true }));
    apiFetch('stock_forecasts', { stock_id: safeTicker, measure_code: 'EPS', period_type: 'Annual', data_type: 'Actuals', age: 'Current' })
      .then(j => { if (mounted) setForecasts(j); })
      .catch(e => { console.warn('fetch forecasts', e?.message || e); if (mounted) setForecasts({ upstream_issue: true }); })
      .finally(() => { if (mounted) setLoading(l => ({ ...l, f: false })); });

    // Target / recommendation
    setLoading(l => ({ ...l, t: true }));
    apiFetch('stock_target_price', { stock_id: safeTicker })
      .then(j => { if (mounted) setTarget(j); })
      .catch(e => { console.warn('fetch target', e?.message || e); if (mounted) setTarget({ upstream_issue: true }); })
      .finally(() => { if (mounted) setLoading(l => ({ ...l, t: false })); });

    // historical price
    setLoading(l => ({ ...l, h: true }));
    apiFetch('historical_data', { stock_name: safeTicker, period: '1yr', filter: 'price' })
      .then(j => { if (mounted) setHistorical(j); })
      .catch(e => { console.warn('fetch hist', e?.message || e); if (mounted) setHistorical(null); })
      .finally(() => { if (mounted) setLoading(l => ({ ...l, h: false })); });

    // news (global)
    setLoading(l => ({ ...l, n: true }));
    apiFetch('news', { q: safeTicker })
      .then(j => { if (mounted) setNews(j); })
      .catch(e => { console.warn('fetch news', e?.message || e); if (mounted) setNews([]); })
      .finally(() => { if (mounted) setLoading(l => ({ ...l, n: false })); });

    return () => { mounted = false; };
  }, [safeTicker]);

  const recLabel = useMemo(() => {
    if (!target || !target.recommendation) return null;
    const mean = target.recommendation.PreliminaryMean ?? target.recommendation.UnverifiedMean ?? target.recommendation.Mean ?? target.recommendation;
    if (mean == null) return null;
    const m = Number(mean);
    if (m <= 1.5) return 'Buy';
    if (m <= 2.5) return 'Outperform';
    if (m <= 3.5) return 'Hold';
    if (m <= 4.5) return 'Underperform';
    return 'Sell';
  }, [target]);

  // helper to extract price dataset and allow CSV export
  const historicalRows = useMemo(() => {
    if (!historical || !historical.datasets || !Array.isArray(historical.datasets)) return [];
    const priceDs = historical.datasets.find(ds => /price/i.test(String(ds.metric || ds.label || ''))) || historical.datasets[0];
    const rows = (priceDs.values || []).map(r => [r[0], r[1]]);
    return rows;
  }, [historical]);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-2xl border p-4 bg-white">
          <div className="text-sm font-medium text-slate-700 mb-2">Analyst Recommendation</div>
          {loading.t && <div className="text-sm text-slate-500">Loading…</div>}
          {!loading.t && target && (
            <>
              <div className="text-lg font-semibold">{recLabel ?? 'N/A'}</div>
              <div className="text-xs text-slate-500 mt-1">Estimates: {target.priceTarget?.NumberOfEstimates ?? target.priceTarget?.NumberOfAnalysts ?? '—'}</div>
              <div className="mt-3 text-xs text-slate-600">{target.priceTarget ? `Mean: ${fmt(target.priceTarget.Mean)} High: ${fmt(target.priceTarget.High)} Low: ${fmt(target.priceTarget.Low)}` : 'No analyst target available.'}</div>
            </>
          )}
          {!loading.t && target?.upstream_issue && <div className="text-xs text-amber-700 mt-2">Target price service temporarily unavailable.</div>}
        </div>

        <div className="rounded-2xl border p-4 bg-white">
          <div className="text-sm font-medium text-slate-700 mb-2">Forecasts (sample)</div>
          {loading.f && <div className="text-sm text-slate-500">Loading…</div>}
          {!loading.f && forecasts && Array.isArray(forecasts) && forecasts.length === 0 && <div className="text-sm text-slate-500">No forecasts</div>}
          {!loading.f && forecasts && !Array.isArray(forecasts) && forecasts.upstream_issue && <div className="text-sm text-amber-700">Forecast service temporarily unavailable.</div>}
          {!loading.f && forecasts && Array.isArray(forecasts) && (
            <div className="space-y-2 text-xs text-slate-600">
              {forecasts.slice(0, 6).map((fs, i) => (<div key={i}><strong>{fs.period ?? fs.horizon ?? fs.label ?? '—'}</strong>: {fs.value ?? fs.summary ?? JSON.stringify(fs)}</div>))}
            </div>
          )}
        </div>
      </div>

      <div className="rounded-2xl border p-4 bg-white">
        <div className="flex items-center justify-between">
          <div className="text-sm font-medium text-slate-700">Historical (price) — 1 year</div>
          <div className="text-xs text-slate-500">CSV export available</div>
        </div>
        {loading.h && <div className="text-sm text-slate-500 mt-2">Loading…</div>}
        {!loading.h && historical && historical.datasets && Array.isArray(historical.datasets) && (
          <>
            <div className="mt-2 text-xs text-slate-600 max-h-48 overflow-auto">
              <table className="w-full text-xs">
                <tbody>
                  {historicalRows.slice(0, 10).map((r, i) => (<tr key={i}><td className="py-1">{r[0]}</td><td className="text-right py-1">{fmt(r[1])}</td></tr>))}
                </tbody>
              </table>
              {historicalRows.length === 0 && <div className="text-sm text-slate-500 mt-2">No history available</div>}
            </div>
            {historicalRows.length > 0 && <div className="mt-3"><button onClick={() => csvDownload(`${(stockName || safeTicker).replace(/\s+/g,'_')}_1yr.csv`, [['date','price'], ...historicalRows])} className="px-3 py-1 rounded-xl bg-slate-800 text-white text-sm">Download CSV</button></div>}
          </>
        )}
        {!loading.h && (!historical || !historical.datasets) && <div className="text-sm text-slate-500 mt-2">No historical data</div>}
      </div>

      <div className="rounded-2xl border p-4 bg-white">
        <div className="text-sm font-medium text-slate-700 mb-2">Recent News</div>
        {loading.n && <div className="text-sm text-slate-500">Loading…</div>}
        {!loading.n && Array.isArray(news) && news.slice(0, 6).map((n, i) => (
          <div key={i} className="py-1 border-b last:border-b-0 text-xs">
            <a href={n.link ?? n.url ?? n.source_url ?? '#'} target="_blank" rel="noreferrer" className="hover:underline">{n.title ?? n.headline ?? n.name ?? 'Article'}</a>
            <div className="text-xs text-slate-500">{n.source ?? n.date ?? ''}</div>
          </div>
        ))}
        {!loading.n && (!news || news.length === 0) && <div className="text-sm text-slate-500">No recent news</div>}
      </div>
    </div>
  );
}

/* ---------- Trending & Side widgets ---------- */
function TrendingPanel() {
  const [data, setData] = useState(null);
  useEffect(() => {
    let mounted = true;
    apiFetch('trending').then(d => { if (mounted) setData(d); }).catch(e => { console.warn('trending', e); setData(null); });
    return () => { mounted = false; };
  }, []);
  const gainers = data?.top_gainers || data?.trending_stocks?.top_gainers || [];
  const losers = data?.top_losers || data?.trending_stocks?.top_losers || [];
  return (
    <div className="rounded-2xl border p-4 bg-white">
      <div className="text-sm font-medium text-slate-700 mb-2">Trending</div>
      <div className="text-xs text-slate-500 mb-1">Top Gainers</div>
      {gainers.slice(0, 6).map((g, i) => (<div key={i} className="flex justify-between text-sm py-1 border-b"><div>{g.company_name ?? g.name ?? g.ticker}</div><div className={`text-xs ${Number(g.percent_change ?? g.percent ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>{fmtPct(g.percent_change ?? g.percent ?? 0)}</div></div>))}
      <div className="text-xs text-slate-500 mt-2 mb-1">Top Losers</div>
      {losers.slice(0, 6).map((g, i) => (<div key={i} className="flex justify-between text-sm py-1 border-b"><div>{g.company_name ?? g.name ?? g.ticker}</div><div className={`text-xs ${Number(g.percent_change ?? g.percent ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>{fmtPct(g.percent_change ?? g.percent ?? 0)}</div></div>))}
      <div className="mt-3 flex gap-2">
        <button className="text-xs px-2 py-1 rounded-xl border" onClick={() => {
          // export top gainers CSV (simple)
          const rows = [['name','ticker','percent_change'], ...gainers.slice(0, 50).map(g => [g.company_name ?? g.name ?? '', g.ticker ?? '', g.percent_change ?? g.percent ?? ''])];
          csvDownload('top_gainers.csv', rows);
        }}>Export Gainers</button>
        <button className="text-xs px-2 py-1 rounded-xl border" onClick={() => {
          const rows = [['name','ticker','percent_change'], ...losers.slice(0, 50).map(g => [g.company_name ?? g.name ?? '', g.ticker ?? '', g.percent_change ?? g.percent ?? ''])];
          csvDownload('top_losers.csv', rows);
        }}>Export Losers</button>
      </div>
    </div>
  );
}

function SideWidgets() {
  return (
    <aside className="space-y-4">
      <TrendingPanel />
      <div className="rounded-2xl border p-4 bg-white text-sm">
        <div className="font-medium text-slate-700 text-sm mb-2">Quick Widgets</div>
        <div className="text-xs text-slate-500">Most Active, Commodities, Mutual Funds — wire to /api endpoints as needed.</div>
      </div>
    </aside>
  );
}

/* ---------- Economics / G20 Panel ---------- */
function G20EconomicsPanel() {
  const [g20Data, setG20Data] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  const controllers = useRef({});

  // Example indicators we want from World Bank (or backend proxy). These keys are illustrative:
  // GDP (current US$): NY.GDP.MKTP.CD
  // Inflation (CPI annual %): FP.CPI.TOTL.ZG
  // Unemployment rate (%): SL.UEM.TOTL.ZS
  // Population: SP.POP.TOTL
  const indicators = [
    { code: 'NY.GDP.MKTP.CD', label: 'GDP (current US$)' },
    { code: 'FP.CPI.TOTL.ZG', label: 'Inflation (CPI %)' },
    { code: 'SL.UEM.TOTL.ZS', label: 'Unemployment (%)' },
    { code: 'SP.POP.TOTL', label: 'Population' }
  ];

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setErr(null);
    // fetch in parallel for all G20 countries via backend endpoint 'worldbank' (proxy)
    // backend expected to accept: /api/worldbank?country=ISO2&indicators=code1,code2&date=2022:2024 etc.
    Promise.all(G20.map(async (c) => {
      try {
        // optional: pass 'latest' param so backend returns the most recent available value
        const q = { country: c.iso2, indicators: indicators.map(i => i.code).join(','), date: '2020:2024', per_page: 1, latest: true };
        const data = await apiFetch('worldbank', q);
        return { country: c, data };
      } catch (e) {
        console.warn('worldbank fetch', c.name, e?.message || e);
        return { country: c, error: true, message: e?.message || String(e) };
      }
    })).then(results => {
      if (!mounted) return;
      setG20Data(results);
    }).catch(e => {
      console.warn('g20 fetch all', e);
      if (mounted) setErr(e?.message || String(e));
    }).finally(() => { if (mounted) setLoading(false); });

    return () => { mounted = false; Object.values(controllers.current).forEach(ctrl => ctrl?.abort?.()); };
  }, []);

  function exportG20Csv() {
    if (!g20Data || !Array.isArray(g20Data)) return;
    // build rows header: country + indicator labels
    const header = ['country', ...indicators.map(i => i.label)];
    const rows = [header];
    g20Data.forEach(item => {
      if (item.error) {
        rows.push([item.country.name, 'error', item.message || '']);
        return;
      }
      // attempt to read latest values from returned data structure (backend may return an object keyed by indicator)
      const values = indicators.map(ind => {
        // try common shapes
        const v = (item.data && (item.data[ind.code] ?? item.data[ind.code]?.value)) ?? null;
        if (v == null) {
          // attempt: item.data may be an array of indicator results
          if (Array.isArray(item.data)) {
            const found = item.data.find(d => d.indicator?.id === ind.code || d.indicator === ind.code);
            if (found) return found.value ?? found.latest_value ?? found.data?.value ?? '—';
          }
          return '—';
        }
        return v;
      });
      rows.push([item.country.name, ...values]);
    });
    csvDownload('g20_macro.csv', rows);
  }

  return (
    <div className="rounded-2xl border p-4 bg-white">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-lg font-semibold">G20 — Economics snapshot</div>
          <div className="text-xs text-slate-500">Latest indicators (via World Bank proxy). Click export to download CSV.</div>
        </div>
        <div className="flex items-center gap-2">
          <button className="px-3 py-1 rounded-xl border text-xs" onClick={exportG20Csv}>Export CSV</button>
        </div>
      </div>

      {loading && <div className="text-sm text-slate-500 mt-3">Loading G20 data…</div>}
      {!loading && err && <div className="text-sm text-rose-600 mt-3">Error loading G20 data: {err}</div>}

      {!loading && g20Data && Array.isArray(g20Data) && (
        <div className="mt-3 overflow-auto text-xs">
          <table className="w-full">
            <thead>
              <tr className="text-left">
                <th className="pr-4 pb-2">Country</th>
                {indicators.map(ind => <th key={ind.code} className="pr-4 pb-2">{ind.label}</th>)}
              </tr>
            </thead>
            <tbody>
              {g20Data.map((item, idx) => {
                if (item.error) {
                  return (<tr key={idx}><td className="py-1">{item.country.name}</td><td colSpan={indicators.length} className="py-1 text-xs text-rose-600">Error: {item.message}</td></tr>);
                }
                // try several shapes for data
                const rowVals = indicators.map(ind => {
                  const d = item.data;
                  // common shapes: { 'NY.GDP.MKTP.CD': { value: ... } } OR array [{ indicator: {id: code}, value: ... }]
                  const byKey = d?.[ind.code];
                  if (byKey != null) {
                    // if object with value
                    if (typeof byKey === 'object' && ('value' in byKey)) return fmt(byKey.value);
                    return fmt(byKey);
                  }
                  if (Array.isArray(d)) {
                    const found = d.find(x => (x.indicator && (x.indicator.id === ind.code || x.indicator === ind.code)) || x.code === ind.code);
                    if (found) return fmt(found.value ?? found.latest_value ?? found.data?.value);
                  }
                  // fallback try top-level fields
                  return '—';
                });
                return (
                  <tr key={idx} className="border-t">
                    <td className="py-1 pr-4">{item.country.name}</td>
                    {rowVals.map((v, i) => <td key={i} className="py-1 pr-4">{v}</td>)}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

/* ---------- Main Markets view ---------- */
export default function MarketsDashboard() {
  const [query, setQuery] = useState('');
  const [stock, setStock] = useState(null);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [searchErr, setSearchErr] = useState(null);

  async function handleSearch(q) {
    const qtrim = (q ?? query ?? '').trim();
    if (!qtrim) return;
    setLoadingSearch(true); setSearchErr(null); setStock(null);
    try {
      const data = await apiFetch('stock', { name: qtrim });
      const chosen = Array.isArray(data) ? data[0] : data;
      setStock(chosen);
    } catch (e) {
      console.warn('stock search', e);
      setSearchErr(e.message || 'Search failed');
    } finally {
      setLoadingSearch(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border p-4 bg-white">
        <div className="flex gap-2">
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') handleSearch(); }}
            placeholder="Search stock by name or symbol (e.g. Reliance, TCS)"
            className="flex-1 border rounded-xl px-3 py-2"
          />
          <button onClick={() => handleSearch()} className="px-4 py-2 rounded-xl bg-slate-800 text-white">Search</button>
        </div>
        {loadingSearch && <div className="text-sm text-slate-500 mt-2">Searching…</div>}
        {searchErr && <div className="text-sm text-rose-600 mt-2">{searchErr}</div>}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          {/* G20 economics summary (top) */}
          <G20EconomicsPanel />

          {/* Stock details */}
          <div className="rounded-2xl border p-4 bg-white">
            {!stock && <div className="text-sm text-slate-500">No stock selected — search above to view details.</div>}
            {stock && <StockDetails stock={stock} />}
          </div>

          {/* Extra panels for selected stock */}
          {stock && <StockExtraPanels
            tickerId={stock.tickerId || stock.ticker_id || stock.ticker || stock.ric || stock.symbol}
            stockName={stock.companyName || stock.company_name || stock.commonName || stock.name}
          />}
        </div>

        <div>
          <SideWidgets />
        </div>
      </div>
    </div>
  );
}
