import React, { useEffect, useState, useMemo, useRef } from "react";
import PropTypes from "prop-types";
import { API_ORIGIN } from "../config";

// MarketsDashboard.jsx
// Production-ready single-file React component (default export)
// - TailwindCSS for styling
// - Polls backend proxy endpoints and respects a 2-hour freshness limit
// - Caches last-successful response in localStorage to avoid hitting rate limits
// - Manual refresh button and lightweight error handling
// - Uses simple cards / tables to mimic a professional market page layout

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

async function fetchJson(path, signal) {
  const res = await fetch(`${API_ORIGIN}${path}`, { signal });
  if (!res.ok) {
    const txt = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${res.statusText} - ${txt}`);
  }
  return res.json();
}

export default function MarketsDashboard({ refreshInterval = TWO_HOURS }) {
  const [data, setData] = useState(() => {
    try {
      const raw = localStorage.getItem(CACHE_KEY);
      if (!raw) return { loadedAt: 0 };
      const parsed = JSON.parse(raw);
      return parsed;
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
    // auto-refresh on mount if stale
    if (needsRefresh) {
      refreshAll();
    }

    // setup periodic refresh to run at refreshInterval
    const id = setInterval(() => {
      refreshAll();
    }, refreshInterval);

    return () => {
      clearInterval(id);
      if (controllerRef.current) controllerRef.current.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function refreshAll({ force = false } = {}) {
    if (loading) return;
    if (!force && !needsRefresh) return; // respect freshness

    setLoading(true);
    setError(null);
    controllerRef.current = new AbortController();
    const { signal } = controllerRef.current;

    try {
      // Parallel fetch common panels
      const [trending, fetch52, nseActive, bseActive, commodities, priceShockers, mutualFunds] =
        await Promise.all([
          fetchJson("/trending", signal).catch((e) => ({ _error: e.message })),
          fetchJson("/fetch_52_week_high_low_data", signal).catch((e) => ({ _error: e.message })),
          fetchJson("/NSE_most_active", signal).catch((e) => ({ _error: e.message })),
          fetchJson("/BSE_most_active", signal).catch((e) => ({ _error: e.message })),
          fetchJson("/commodities", signal).catch((e) => ({ _error: e.message })),
          fetchJson("/price_shockers", signal).catch((e) => ({ _error: e.message })),
          fetchJson("/mutual_funds", signal).catch((e) => ({ _error: e.message })),
        ]);

      const newState = {
        loadedAt: Date.now(),
        trending: trending && !trending._error ? trending : null,
        fetch52: fetch52 && !fetch52._error ? fetch52 : null,
        nseActive: nseActive && !nseActive._error ? nseActive : null,
        bseActive: bseActive && !bseActive._error ? bseActive : null,
        commodities: commodities && !commodities._error ? commodities : null,
        priceShockers: priceShockers && !priceShockers._error ? priceShockers : null,
        mutualFunds: mutualFunds && !mutualFunds._error ? mutualFunds : null,
      };

      setData(newState);
      try {
        localStorage.setItem(CACHE_KEY, JSON.stringify(newState));
      } catch (e) {
        // ignore
      }
    } catch (e) {
      console.error("MarketsDashboard refresh failed", e);
      setError(e.message || String(e));
    } finally {
      setLoading(false);
      controllerRef.current = null;
    }
  }

  function renderTopGainersLosers() {
    const trending = data.trending || {};
    const topGainers = trending.top_gainers || [];
    const topLosers = trending.top_losers || [];

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Panel title="Top Gainers" subtitle="Real-time snapshot">
          <SimpleTable rows={topGainers.slice(0, 6)} emptyMessage="No gainers" />
        </Panel>

        <Panel title="Top Losers" subtitle="Real-time snapshot">
          <SimpleTable rows={topLosers.slice(0, 6)} emptyMessage="No losers" />
        </Panel>
      </div>
    );
  }

  function renderMostActive() {
    const nse = data.nseActive || [];
    const bse = data.bseActive || [];
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Panel title="NSE - Most Active" subtitle="By volume">
          <ActiveTable rows={nse.slice(0, 8)} />
        </Panel>
        <Panel title="BSE - Most Active" subtitle="By volume">
          <ActiveTable rows={bse.slice(0, 8)} />
        </Panel>
      </div>
    );
  }

  function render52Week() {
    const f52 = data.fetch52 || {};
    const bse = f52.BSE_52WeekHighLow || {};
    const nse = f52.NSE_52WeekHighLow || {};
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Panel title="52 Week (BSE)" subtitle="Highs & lows">
          <HighLowList high={bse.high52Week} low={bse.low52Week} />
        </Panel>
        <Panel title="52 Week (NSE)" subtitle="Highs & lows">
          <HighLowList high={nse.high52Week} low={nse.low52Week} />
        </Panel>
      </div>
    );
  }

  function renderCommodities() {
    const c = data.commodities || [];
    return (
      <Panel title="Commodities" subtitle="Futures snapshot">
        <CommodityTable rows={c.slice(0, 8)} />
      </Panel>
    );
  }

  function renderMutualFunds() {
    const m = data.mutualFunds || {};
    return (
      <Panel title="Mutual Funds" subtitle="Top categories">
        <MutualFundsView mf={m} />
      </Panel>
    );
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
            {data.loadedAt ? (
              <span>Last update: {new Date(data.loadedAt).toLocaleString()}</span>
            ) : (
              <span>Never updated</span>
            )}
          </div>
          <button
            className="px-3 py-2 rounded bg-slate-800 text-white text-sm hover:opacity-90"
            onClick={() => refreshAll({ force: true })}
            disabled={loading}
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </header>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded">Error: {error}</div>
      )}

      <main className="space-y-4">
        {renderTopGainersLosers()}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            {renderMostActive()}
            <div className="mt-4">{render52Week()}</div>
          </div>

          <div>
            {renderCommodities()}
            <div className="mt-4">{renderMutualFunds()}</div>
            <div className="mt-4">
              <Panel title="Price Shockers" subtitle="Large intraday moves">
                <PriceShockers rows={(data.priceShockers || []).slice(0, 8)} />
              </Panel>
            </div>
          </div>
        </div>

        <footer className="text-xs text-slate-500">Data provided via your IndianAPI proxy. UI refresh limit: 2 hours (configurable).</footer>
      </main>
    </div>
  );
}

MarketsDashboard.propTypes = {
  refreshInterval: PropTypes.number,
};

/* ---------- Presentational subcomponents ---------- */
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
              <td className="py-2">{fmtNumber(r.price || r.current_price || r.close || r.price)}</td>
              <td className={`py-2 ${Number(r.percent_change) > 0 ? "text-green-600" : "text-red-600"}`}>
                {fmtPct(Number(r.percent_change) || Number(r.percentChange) || Number(r.net_change))}
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
                <span className="font-medium">{fmtNumber(h.price)}</span>
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
                <span className="font-medium">{fmtNumber(h.price)}</span>
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
                {fmtNumber(r.priceChange)} ({fmtPct(r.percentageChange * 100)})
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
  // mf often has nested categories; show top-level categories and their first funds
  if (!mf || Object.keys(mf).length === 0) return <div className="text-sm text-slate-500">No data</div>;

  return (
    <div className="space-y-3">
      {Object.entries(mf).slice(0, 3).map(([category, buckets]) => (
        <div key={category} className="border rounded p-2 bg-slate-50">
          <h4 className="text-sm font-medium">{category}</h4>
          {typeof buckets === "object" && (
            <ul className="text-sm mt-1">
              {Object.entries(buckets)
                .flatMap(([, list]) => list || [])
                .slice(0, 3)
                .map((f, i) => (
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
