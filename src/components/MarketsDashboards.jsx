// src/components/MarketsDashboards.jsx
import React, { useEffect, useMemo, useState } from 'react';
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
  const csv = rows.map(r => r.map(c => `"${String(c ?? '')}".replace(/"/g,'""')"`).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
}

/* ---------- basic safe fetch wrapper ---------- */
async function apiFetch(path, params = {}) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== '') qs.append(k, String(v)); });
  const qstr = qs.toString() ? `?${qs.toString()}` : '';
  const base = API_ORIGIN ? API_ORIGIN.replace(/\/$/, '') : window.location.origin;
  const url = `${base}/api/${path}${qstr}`;

  const res = await fetch(url, { credentials: 'same-origin' });
  const ct = (res.headers.get && res.headers.get('content-type')) || '';
  const text = await res.text().catch(() => '');
  if (!res.ok) {
    const snippet = text ? text.slice(0, 800) : res.statusText;
    const err = new Error(`HTTP ${res.status}: ${snippet}`);
    err.status = res.status; err.body = text;
    throw err;
  }
  if (ct.includes('json') || ct.includes('+json')) {
    try { return JSON.parse(text); } catch { return text; }
  }
  // fallback try parse
  try { return JSON.parse(text); } catch { return text; }
}

/* ---------- Stock search + details component ---------- */
function StockDetails({ stock }) {
  // stock is the object returned from /api/stock (shape per IndianAPI docs)
  if (!stock) return null;

  const tickerId = stock.tickerId || stock.ticker_id || stock.ticker || stock.ric || stock.tickerId;
  const name = stock.companyName || stock.company_name || stock.commonName || stock.name;
  const metrics = stock.keyMetrics || stock.key_metrics || stock.stockDetailsReusableData || {};
  const priceObj = stock.currentPrice || stock.current_price || stock.price || {};
  const price = typeof priceObj === 'object' ? (priceObj.NSE ?? priceObj.BSE ?? priceObj.latest ?? priceObj) : priceObj;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="text-lg font-semibold truncate">{name} <span className="text-sm text-slate-400">({tickerId})</span></div>
          <div className="text-sm text-slate-500 mt-1">{stock.industry ?? stock.mgIndustry ?? ''}</div>
        </div>
        <div className="text-right">
          <div className="text-xl font-semibold">{fmt(price)}</div>
          <div className={`text-sm ${Number(stock.percentChange ?? stock.percent_change ?? stock.percent ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>{fmtPct(stock.percentChange ?? stock.percent_change ?? stock.percent ?? 0)}</div>
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

function StockExtraPanels({ tickerId, stockName }) {
  const [forecasts, setForecasts] = useState(null);
  const [target, setTarget] = useState(null);
  const [historical, setHistorical] = useState(null);
  const [news, setNews] = useState(null);
  const [loading, setLoading] = useState({ f:false, t:false, h:false, n:false });
  const safeTicker = tickerId || stockName;

  useEffect(() => {
    let mounted = true;
    if (!safeTicker) return;

    // Forecasts — default example fetch for EPS Annual Current (you can expose UI to change params)
    setLoading(l => ({ ...l, f: true }));
    apiFetch('stock_forecasts', { stock_id: safeTicker, measure_code: 'EPS', period_type: 'Annual', data_type: 'Actuals', age: 'Current' })
      .then(j => { if (mounted) setForecasts(j); })
      .catch(e => { console.warn('fetch forecasts', e?.message || e); if (mounted) setForecasts({ upstream_issue:true }); })
      .finally(() => { if (mounted) setLoading(l => ({ ...l, f: false })); });

    // Analyst target price / recommendations
    setLoading(l => ({ ...l, t: true }));
    apiFetch('stock_target_price', { stock_id: safeTicker })
      .then(j => { if (mounted) setTarget(j); })
      .catch(e => { console.warn('fetch target', e?.message || e); if (mounted) setTarget({ upstream_issue:true }); })
      .finally(() => { if (mounted) setLoading(l => ({ ...l, t: false })); });

    // historical (price for 1yr default)
    setLoading(l => ({ ...l, h: true }));
    apiFetch('historical_data', { stock_name: safeTicker, period: '1yr', filter: 'price' })
      .then(j => { if (mounted) setHistorical(j); })
      .catch(e => { console.warn('fetch hist', e?.message || e); if (mounted) setHistorical(null); })
      .finally(() => { if (mounted) setLoading(l => ({ ...l, h: false })); });

    // news
    setLoading(l => ({ ...l, n: true }));
    apiFetch('news') // docs show /news general; backend also proxies specific recent_announcements
      .then(j => { if (mounted) setNews(j); })
      .catch(e => { console.warn('fetch news', e?.message || e); if (mounted) setNews([]); })
      .finally(() => { if (mounted) setLoading(l => ({ ...l, n: false })); });

    return () => { mounted = false; };
  }, [safeTicker]);

  // derive simple recommendation label
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
              {forecasts.slice(0, 4).map((fs, i) => (<div key={i}><strong>{fs.period ?? fs.horizon ?? fs.label ?? '—'}</strong>: {fs.value ?? fs.summary ?? JSON.stringify(fs)}</div>))}
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
            {/* find price dataset */}
            {(() => {
              const priceDs = historical.datasets.find(ds => /price/i.test(ds.metric || ds.label || '')) || historical.datasets[0];
              const rows = (priceDs.values || []).map(r => [r[0], r[1]]);
              return (
                <>
                  <div className="mt-2 text-xs text-slate-600 max-h-48 overflow-auto">
                    <table className="w-full text-xs">
                      <tbody>
                        {rows.slice(0, 10).map((r, i) => (<tr key={i}><td className="py-1">{r[0]}</td><td className="text-right py-1">{fmt(r[1])}</td></tr>))}
                      </tbody>
                    </table>
                    {rows.length === 0 && <div className="text-sm text-slate-500 mt-2">No history available</div>}
                  </div>
                  {rows.length > 0 && <div className="mt-3"><button onClick={() => {
                    // simple CSV: header + rows
                    const csv = [['date','price'], ...rows];
                    const blob = new Blob([csv.map(r => r.map(c => `"${String(c).replace(/"/g,'""')}"`).join(',')).join('\n')], { type: 'text/csv' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a'); a.href = url; a.download = `${stockName || safeTicker}_1yr.csv`; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
                  }} className="px-3 py-1 rounded-xl bg-slate-800 text-white text-sm">Download CSV</button></div>}
                </>
              );
            })()}
          </>
        )}
      </div>

      <div className="rounded-2xl border p-4 bg-white">
        <div className="text-sm font-medium text-slate-700 mb-2">Recent News</div>
        {loading.n && <div className="text-sm text-slate-500">Loading…</div>}
        {!loading.n && Array.isArray(news) && news.slice(0,6).map((n,i) => (
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

/* ---------- Main Markets view (keeps previous panels simplified) ---------- */

function TrendingPanel() {
  const [data, setData] = useState(null);
  useEffect(() => { apiFetch('trending').then(setData).catch(e => { console.warn(e); setData(null); }); }, []);
  const gainers = data?.top_gainers || data?.trending_stocks?.top_gainers || [];
  const losers = data?.top_losers || data?.trending_stocks?.top_losers || [];
  return (
    <div className="rounded-2xl border p-4 bg-white">
      <div className="text-sm font-medium text-slate-700 mb-2">Trending</div>
      <div className="text-xs text-slate-500 mb-1">Top Gainers</div>
      {gainers.slice(0,6).map((g,i) => (<div key={i} className="flex justify-between text-sm py-1 border-b"><div>{g.company_name ?? g.name ?? g.ticker}</div><div className={`text-xs ${Number(g.percent_change ?? g.percent ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>{fmtPct(g.percent_change ?? g.percent ?? 0)}</div></div>))}
      <div className="text-xs text-slate-500 mt-2 mb-1">Top Losers</div>
      {losers.slice(0,6).map((g,i) => (<div key={i} className="flex justify-between text-sm py-1 border-b"><div>{g.company_name ?? g.name ?? g.ticker}</div><div className={`text-xs ${Number(g.percent_change ?? g.percent ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>{fmtPct(g.percent_change ?? g.percent ?? 0)}</div></div>))}
    </div>
  );
}

function SideWidgets() {
  return (
    <aside className="space-y-4">
      <TrendingPanel />
      <div className="rounded-2xl border p-4 bg-white text-sm">Other widgets (Most Active, Commodities, Mutual Funds) — keep your existing components or wire them to /api endpoints as needed.</div>
    </aside>
  );
}

/* ---------- Composite main component ---------- */
export default function MarketsDashboard() {
  const [query, setQuery] = useState('');
  const [stock, setStock] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchErr, setSearchErr] = useState(null);

  async function handleSearch(q) {
    const qtrim = (q ?? query ?? '').trim();
    if (!qtrim) return;
    setLoading(true); setSearchErr(null); setStock(null);
    try {
      const data = await apiFetch('stock', { name: qtrim });
      // backend may return an object or array — unify
      const chosen = Array.isArray(data) ? data[0] : data;
      setStock(chosen);
    } catch (e) {
      console.warn('stock search', e);
      setSearchErr(e.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border p-4 bg-white">
        <div className="flex gap-2">
          <input value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') handleSearch(); }} placeholder="Search stock by name or symbol (e.g. Reliance, TCS)" className="flex-1 border rounded-xl px-3 py-2" />
          <button onClick={() => handleSearch()} className="px-4 py-2 rounded-xl bg-slate-800 text-white">Search</button>
        </div>
        {loading && <div className="text-sm text-slate-500 mt-2">Searching…</div>}
        {searchErr && <div className="text-sm text-rose-600 mt-2">{searchErr}</div>}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          {stock ? <StockDetails stock={stock} /> : <div className="rounded-2xl border p-4 bg-white text-sm text-slate-500">No stock selected — search above to view details.</div>}
          {stock && <StockExtraPanels tickerId={stock.tickerId || stock.ticker_id || stock.ticker || stock.ric || stock.tickerId} stockName={stock.companyName || stock.company_name || stock.commonName || stock.name} />}
        </div>

        <SideWidgets />
      </div>
    </div>
  );
}
