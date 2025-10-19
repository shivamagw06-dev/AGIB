import React, { useEffect, useState, useMemo, useRef } from "react";
import PropTypes from "prop-types";
import { API_ORIGIN } from "../config";

// MarketsDashboard.jsx (fixed)
// - Uses API_ORIGIN from config and calls backend proxy under /api
// - Normalizes responses from IndianAPI (some endpoints wrap data)
// - Better error logging and graceful fallback when upstream returns non-JSON
// - Caches last-successful response in localStorage (2-hour default)

const TWO_HOURS = 2 * 60 * 60 * 1000; // ms
const CACHE_KEY = "markets_dashboard_cache_v1";

function fmtNumber(n) {
  if (n == null || n === "" || Number.isNaN(Number(n))) return "—";
  const num = Number(n);
  if (Math.abs(num) >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
  if (Math.abs(num) >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
  if (Math.abs(num) >= 1e3) return `${(num / 1e3).toFixed(2)}k`;
  return num.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function fmtPct(n) {
  if (n == null || n === "" || Number.isNaN(Number(n))) return "—";
  const v = Number(n);
  const sign = v > 0 ? "+" : "";
  return `${sign}${v.toFixed(2)}%`;
}

function buildApiBase() {
  // ensure we always call the proxy under /api
  const origin = (API_ORIGIN || "").replace(/\/+$/, "");
  return origin + "/api";
}

async function fetchJson(path, signal) {
  const base = buildApiBase();
  const url = `${base}${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, { signal, credentials: "omit" });
  if (!res.ok) {
    const txt = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${res.statusText} - ${txt}`);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  // non-json: return as text so caller can handle
  const text = await res.text().catch(() => "");
  return text;
}

export default function MarketsDashboard({ refreshInterval = TWO_HOURS }) {
  const [data, setData] = useState(() => {
    try {
      const raw = localStorage.getItem(CACHE_KEY);
      if (!raw) return { loadedAt: 0 };
      return JSON.parse(raw);
    } catch (e) {
      return { loadedAt: 0 };
    }
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const controllerRef = useRef(null);

  const needsRefresh = useMemo(() => {
    const now = Date.now();
    return !data || !data.loadedAt || now - data.loadedAt > TWO_HOURS;
  }, [data]);

  useEffect(() => {
    if (needsRefresh) refreshAll();
    const id = setInterval(() => refreshAll(), refreshInterval);
    return () => {
      clearInterval(id);
      if (controllerRef.current) controllerRef.current.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function refreshAll({ force = false } = {}) {
    if (loading) return;
    if (!force && !needsRefresh) return;

    setLoading(true);
    setError(null);
    controllerRef.current = new AbortController();
    const { signal } = controllerRef.current;

    try {
      const endpoints = [
        "/trending",
        "/fetch_52_week_high_low_data",
        "/NSE_most_active",
        "/BSE_most_active",
        "/commodities",
        "/price_shockers",
        "/mutual_funds",
      ];

      const results = await Promise.allSettled(endpoints.map(p => fetchJson(p, signal)));

      const normalize = (res) => {
        if (!res) return null;
        if (typeof res === 'string') return { rawText: res };
        return res;
      };

      const out = {
        loadedAt: Date.now(),
        trending: normalize(results[0].status === 'fulfilled' ? results[0].value : null),
        fetch52: normalize(results[1].status === 'fulfilled' ? results[1].value : null),
        nseActive: normalize(results[2].status === 'fulfilled' ? results[2].value : null),
        bseActive: normalize(results[3].status === 'fulfilled' ? results[3].value : null),
        commodities: normalize(results[4].status === 'fulfilled' ? results[4].value : null),
        priceShockers: normalize(results[5].status === 'fulfilled' ? results[5].value : null),
        mutualFunds: normalize(results[6].status === 'fulfilled' ? results[6].value : null),
      };

      // If all fetches failed, surface an error
      const anySuccess = results.some(r => r.status === 'fulfilled');
      if (!anySuccess) {
        const reasons = results.map(r => (r.status === 'rejected' ? r.reason?.message || String(r.reason) : null)).filter(Boolean);
        throw new Error(reasons.join(' | ') || 'All upstream requests failed');
      }

      // Normalize trending shape: some upstreams return { trending_stocks: { top_gainers: [...] } }
      if (out.trending && out.trending.trending_stocks) out.trending = out.trending.trending_stocks;

      setData(out);
      try { localStorage.setItem(CACHE_KEY, JSON.stringify(out)); } catch (e) { /* ignore */ }
    } catch (e) {
      console.error('MarketsDashboard refresh failed', e);
      setError(e.message || String(e));
    } finally {
      setLoading(false);
      controllerRef.current = null;
    }
  }

  // Helper to safely access a possibly wrapped top_gainers/top_losers
  function getGainersList(td) {
    if (!td) return [];
    return td.top_gainers || td.topGainers || td.topGainer || td.gainers || [];
  }
  function getLosersList(td) {
    if (!td) return [];
    return td.top_losers || td.topLosers || td.topLoser || td.losers || [];
  }

  return (
    <div className="p-4 max-w-screen-xl mx-auto">
      <header className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-semibold">Markets Dashboard</h1>
          <p className="text-sm text-slate-500">Realtime market snapshots — updated every 2 hours</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="text-sm text-slate-600 mr-3">
            {data.loadedAt ? (<span>Last update: {new Date(data.loadedAt).toLocaleString()}</span>) : (<span>Never updated</span>)}
          </div>
          <button
            className="px-3 py-2 rounded bg-slate-800 text-white text-sm hover:opacity-90"
            onClick={() => refreshAll({ force: true })}
            disabled={loading}
          >{loading ? 'Refreshing...' : 'Refresh'}</button>
        </div>
      </header>

      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded">Error: {error}</div>}

      <main className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Panel title="Top Gainers" subtitle="Real-time snapshot">
            <SimpleTable rows={getGainersList(data.trending)} emptyMessage="No gainers" />
          </Panel>

          <Panel title="Top Losers" subtitle="Real-time snapshot">
            <SimpleTable rows={getLosersList(data.trending)} emptyMessage="No losers" />
          </Panel>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-4">
            <Panel title="NSE - Most Active" subtitle="By volume">
              <ActiveTable rows={(Array.isArray(data.nseActive) ? data.nseActive : data.nseActive?.data || [])} />
            </Panel>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Panel title="52 Week (BSE)" subtitle="Highs & lows">
                <HighLowList high={data.fetch52?.BSE_52WeekHighLow?.high52Week || data.fetch52?.BSE_52WeekHighLow?.high || []}
                              low={data.fetch52?.BSE_52WeekHighLow?.low52Week || data.fetch52?.BSE_52WeekHighLow?.low || []} />
              </Panel>

              <Panel title="52 Week (NSE)" subtitle="Highs & lows">
                <HighLowList high={data.fetch52?.NSE_52WeekHighLow?.high52Week || []}
                              low={data.fetch52?.NSE_52WeekHighLow?.low52Week || []} />
              </Panel>
            </div>
          </div>

          <div className="space-y-4">
            <Panel title="BSE - Most Active" subtitle="By volume">
              <ActiveTable rows={(Array.isArray(data.bseActive) ? data.bseActive : data.bseActive?.data || [])} />
            </Panel>

            <Panel title="Commodities" subtitle="Futures snapshot">
              <CommodityTable rows={Array.isArray(data.commodities) ? data.commodities : data.commodities?.data || []} />
            </Panel>

            <Panel title="Mutual Funds" subtitle="Top categories">
              <MutualFundsView mf={data.mutualFunds?.data || data.mutualFunds || {}} />
            </Panel>

            <Panel title="Price Shockers" subtitle="Large intraday moves">
              <PriceShockers rows={Array.isArray(data.priceShockers) ? data.priceShockers : data.priceShockers?.data || []} />
            </Panel>
          </div>
        </div>

        <footer className="text-xs text-slate-500">Data provided via your IndianAPI proxy. UI refresh limit: 2 hours (configurable).</footer>
      </main>
    </div>
  );
}

MarketsDashboard.propTypes = { refreshInterval: PropTypes.number };

/* ---------- Presentational subcomponents (same as before) ---------- */
function Panel({ title, subtitle, children }) {
  return (
    <section className="bg-white shadow-sm rounded p-3 border">
      <div className="flex items-baseline justify-between mb-2">
        <div>
          <h3 className="text-lg font-medium">{title}</h3>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
        </div>
      </div>
      <div>{children}</div>
    </section>
  );
}

function SimpleTable({ rows = [], emptyMessage = "No data" }) {
  if (!rows || rows.length === 0) return <div className="text-sm text-slate-500">{emptyMessage}</div>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm table-auto">
        <thead>
          <tr className="text-left text-xs text-slate-400 border-b">
            <th className="py-2">Ticker</th>
            <th className="py-2">Price</th>
            <th className="py-2">% Change</th>
            <th className="py-2">Volume</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.ticker_id || r.ticker || i} className="border-b last:border-b-0 hover:bg-slate-50">
              <td className="py-2 font-medium">{r.company_name || r.company || r.ticker_id || r.ticker}</td>
              <td className="py-2">{fmtNumber(r.price || r.current_price || r.close || r.lastTradedPrice)}</td>
              <td className={`py-2 ${Number(r.percent_change || r.percentChange || r.percentageChange) > 0 ? "text-green-600" : "text-red-600"}`}>
                {fmtPct(Number(r.percent_change || r.percentChange || (r.percentageChange ? r.percentageChange * 100 : undefined) || r.net_change))}
              </td>
              <td className="py-2">{fmtNumber(r.volume)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ActiveTable({ rows = [] }) {
  if (!rows || rows.length === 0) return <div className="text-sm text-slate-500">No data</div>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm table-auto">
        <thead>
          <tr className="text-left text-xs text-slate-400 border-b">
            <th className="py-2">Ticker</th>
            <th className="py-2">Price</th>
            <th className="py-2">%</th>
            <th className="py-2">Volume</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.ticker || i} className="border-b last:border-b-0 hover:bg-slate-50">
              <td className="py-2 font-medium">{r.company || r.ticker}</td>
              <td className="py-2">{fmtNumber(r.price || r.currentPrice || r.lastTradedPrice)}</td>
              <td className={`py-2 ${Number(r.percent_change || r.percentChange) > 0 ? "text-green-600" : "text-red-600"}`}>
                {fmtPct(Number(r.percent_change || r.percentChange || (r.percentageChange ? r.percentageChange * 100 : undefined)))}
              </td>
              <td className="py-2">{fmtNumber(r.volume)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function HighLowList({ high = [], low = [] }) {
  if ((!high || high.length === 0) && (!low || low.length === 0)) return <div className="text-sm text-slate-500">No data</div>;
  return (
    <div className="grid grid-cols-1 gap-2">
      {high && high.length > 0 && (
        <div>
          <h4 className="text-sm font-medium">Highs</h4>
          <ul className="text-sm text-slate-700">
            {high.slice(0, 6).map((h, i) => (
              <li key={h.ticker || i} className="flex justify-between py-1 border-b last:border-b-0">
                <span>{h.company || h.ticker}</span>
                <span className="font-medium">{fmtNumber(h.price || h.lastTradedPrice)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {low && low.length > 0 && (
        <div>
          <h4 className="text-sm font-medium">Lows</h4>
          <ul className="text-sm text-slate-700">
            {low.slice(0, 6).map((h, i) => (
              <li key={h.ticker || i} className="flex justify-between py-1 border-b last:border-b-0">
                <span>{h.company || h.ticker}</span>
                <span className="font-medium">{fmtNumber(h.price || h.lastTradedPrice)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function CommodityTable({ rows = [] }) {
  if (!rows || rows.length === 0) return <div className="text-sm text-slate-500">No data</div>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm table-auto">
        <thead>
          <tr className="text-left text-xs text-slate-400 border-b">
            <th className="py-2">Symbol</th>
            <th className="py-2">LTP</th>
            <th className="py-2">Change</th>
            <th className="py-2">OI</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.contractId || i} className="border-b last:border-b-0 hover:bg-slate-50">
              <td className="py-2 font-medium">{r.commoditySymbol}</td>
              <td className="py-2">{fmtNumber(r.lastTradedPrice)}</td>
              <td className={`py-2 ${Number(r.priceChange) > 0 ? "text-green-600" : "text-red-600"}`}>
                {fmtNumber(r.priceChange)} ({r.percentageChange ? fmtPct(r.percentageChange * 100) : fmtPct(r.percentageChange)})
              </td>
              <td className="py-2">{fmtNumber(r.openInterest)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MutualFundsView({ mf = {} }) {
  if (!mf || Object.keys(mf).length === 0) return <div className="text-sm text-slate-500">No data</div>;
  return (
    <div className="space-y-3">
      {Object.entries(mf).slice(0, 3).map(([category, buckets]) => (
        <div key={category} className="border rounded p-2 bg-slate-50">
          <h4 className="text-sm font-medium">{category}</h4>
          {typeof buckets === "object" && (
            <ul className="text-sm mt-1">
              {Object.entries(buckets).flatMap(([, list]) => list || []).slice(0, 3).map((f, i) => (
                <li key={f.fund_name || i} className="flex justify-between py-1 border-b last:border-b-0">
                  <span>{f.fund_name}</span>
                  <span className="font-medium">{fmtNumber(f.latest_nav)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
}

function PriceShockers({ rows = [] }) {
  if (!rows || rows.length === 0) return <div className="text-sm text-slate-500">No data</div>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm table-auto">
        <thead>
          <tr className="text-left text-xs text-slate-400 border-b">
            <th className="py-2">Ticker</th>
            <th className="py-2">Price</th>
            <th className="py-2">%</th>
            <th className="py-2">Volume</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.ticker || i} className="border-b last:border-b-0 hover:bg-slate-50">
              <td className="py-2 font-medium">{r.company || r.ticker}</td>
              <td className="py-2">{fmtNumber(r.price)}</td>
              <td className={`py-2 ${Number(r.percent_change) > 0 ? "text-green-600" : "text-red-600"}`}>
                {fmtPct(Number(r.percent_change))}
              </td>
              <td className="py-2">{fmtNumber(r.volume)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
