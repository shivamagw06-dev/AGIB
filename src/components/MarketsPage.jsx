// src/components/MarketsDashboards.jsx
import React, { useEffect, useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

/* ============================================================
   Utils (kept from your original)
============================================================ */
const fmt = (n, d = 2) =>
  n == null || !isFinite(n)
    ? "—"
    : new Intl.NumberFormat(undefined, { maximumFractionDigits: d }).format(n);

const pct = (n, d = 2) =>
  n == null || !isFinite(n)
    ? "—"
    : `${n >= 0 ? "▲" : "▼"} ${fmt(Math.abs(n), d)}%`;

const byDateAsc = (a, b) => a.date.localeCompare(b.date);

/* ============================================================
   WORLD BANK CODE (unchanged)
============================================================ */
async function wbFetchSeries(countryCode, indicator, signal) {
  const url = `https://api.worldbank.org/v2/country/${countryCode}/indicator/${indicator}?format=json&per_page=100`;
  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error("WorldBank fetch failed");
  const j = await res.json();

  const rows = Array.isArray(j) ? j[1] || [] : [];
  const series = rows
    .filter((r) => r.value != null)
    .map((r) => ({ date: `${r.date}`, value: Number(r.value) }))
    .sort(byDateAsc);

  const last = series.at(-1)?.value ?? null;
  const prev = series.at(-2)?.value ?? null;
  const changePct =
    last != null && prev != null ? ((last - prev) / Math.abs(prev)) * 100 : null;

  let cagr5 = null;
  if (series.length >= 6) {
    const end = series.at(-1).value;
    const start = series.at(-6).value;
    if (isFinite(end) && isFinite(start) && start !== 0) {
      cagr5 = (Math.pow(end / start, 1 / 5) - 1) * 100;
    }
  }
  const min = series.reduce(
    (m, x) => (m == null || x.value < m ? x.value : m),
    null
  );
  const max = series.reduce(
    (m, x) => (m == null || x.value > m ? x.value : m),
    null
  );

  return {
    series,
    last,
    changePct,
    cagr5,
    min,
    max,
    latestYear: series.at(-1)?.date ?? null,
  };
}

/* ============================================================
   UI: TabBar (kept + added tab labels)
============================================================ */
function TabBar({ tab, setTab }) {
  const tabs = [
    { id: "economics", label: "Economics (Open)" },
    { id: "fixedincome", label: "Fixed Income" },
    { id: "indices", label: "Indices" },
    { id: "commodities", label: "Commodities" },
  ];
  return (
    <div className="flex flex-wrap gap-3">
      {tabs.map((t) => (
        <button
          key={t.id}
          onClick={() => setTab(t.id)}
          className={`px-4 py-2 rounded-md border text-sm font-medium transition 
            ${
              tab === t.id
                ? "bg-amber-400 text-white border-amber-400 shadow-sm"
                : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
            }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

/* ============================================================
   Small UI helpers / panels used below
============================================================ */
function MiniRow({ item, onClick }) {
  const pctVal = Number(item.percent_change ?? item.percent ?? 0);
  const positive = pctVal >= 0;
  return (
    <div
      onClick={onClick}
      className="flex items-center justify-between py-2 border-b last:border-b-0 cursor-pointer hover:bg-slate-50"
    >
      <div className="min-w-0">
        <div className="text-sm font-medium truncate">{item.company_name || item.name || item.symbol}</div>
        <div className="text-xs text-gray-500 truncate">{item.ric || item.ticker || item.exchange_type || ""}</div>
      </div>
      <div className="text-right ml-4">
        <div className="text-sm font-semibold">₹{item.price ?? item.last ?? item.close ?? "—"}</div>
        <div className={`text-xs ${positive ? "text-emerald-600" : "text-rose-600"}`}>
          {pctVal === 0 ? "—" : `${pctVal >= 0 ? "+" : ""}${pctVal}`}%
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

/* ============================================================
   IndianAPI fetch helper (calls your local proxy /api/*)
   Light in-memory cache for the lifetime of component
============================================================ */
const cache = {};
async function fetchApi(path) {
  if (cache[path]) return cache[path];
  const res = await fetch(`/api/${path}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `${res.status}`);
  }
  const j = await res.json();
  cache[path] = j;
  return j;
}

/* ============================================================
   Panels that call IndianAPI endpoints
============================================================ */

function TrendingPanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setErr(null);
    fetchApi("trending")
      .then((j) => {
        if (!cancelled) setData(j?.trending_stocks ?? j);
      })
      .catch((e) => setErr(e.message || String(e)))
      .finally(() => !cancelled && setLoading(false));
    return () => (cancelled = true);
  }, []);

  return (
    <PanelShell title="Trending Stocks">
      {loading && <div className="text-sm text-slate-500">Loading…</div>}
      {err && <div className="text-sm text-rose-600">Error: {err}</div>}
      {!loading && !err && data && (
        <div className="space-y-3">
          <div>
            <div className="text-xs text-slate-500 mb-2">Top Gainers</div>
            <div className="space-y-1">
              {(data.top_gainers || []).slice(0, 6).map((s) => (
                <MiniRow key={s.ticker_id} item={s} onClick={() => window.open(`/stock/${encodeURIComponent(s.ric || s.ticker_id)}`, "_self")} />
              ))}
            </div>
          </div>
          <div className="mt-3">
            <div className="text-xs text-slate-500 mb-2">Top Losers</div>
            <div className="space-y-1">
              {(data.top_losers || []).slice(0, 6).map((s) => (
                <MiniRow key={s.ticker_id} item={s} onClick={() => window.open(`/stock/${encodeURIComponent(s.ric || s.ticker_id)}`, "_self")} />
              ))}
            </div>
          </div>
        </div>
      )}
    </PanelShell>
  );
}

function MostActivePanel({ which = "BSE" }) {
  const [data, setData] = useState([]);
  useEffect(() => {
    let cancelled = false;
    fetchApi(which === "BSE" ? "BSE_most_active" : "NSE_most_active")
      .then((j) => {
        if (!cancelled) setData(j?.data ?? j ?? []);
      })
      .catch(() => {})
      .finally(() => {});
    return () => (cancelled = true);
  }, [which]);

  return (
    <PanelShell title={`${which} — Most Active`}>
      <div className="space-y-1">
        {data.slice(0, 8).map((s) => (
          <MiniRow key={s.ticker_id || s.ticker} item={s} onClick={() => window.open(`/stock/${encodeURIComponent(s.ric || s.ticker_id)}`, "_self")} />
        ))}
      </div>
    </PanelShell>
  );
}

function CommoditiesPanel() {
  const [data, setData] = useState(null);
  useEffect(() => {
    let cancelled = false;
    fetchApi("commodities")
      .then((j) => { if (!cancelled) setData(j); })
      .catch(() => {})
      .finally(() => {});
    return () => (cancelled = true);
  }, []);
  const items = data?.data ?? data?.commodities ?? [];
  return (
    <PanelShell title="Commodities">
      <div className="space-y-1">
        {items.slice(0, 8).map((c) => (
          <div key={c.ticker || c.name} className="flex justify-between py-2 border-b last:border-b-0">
            <div>
              <div className="text-sm font-medium">{c.name || c.instrument || c.ticker}</div>
              <div className="text-xs text-gray-500">{c.exchange || c.market || ""}</div>
            </div>
            <div className="text-right ml-4">
              <div className="text-sm font-semibold">{c.price ?? c.last ?? "—"}</div>
              <div className={`text-xs ${Number(c.percent_change ?? 0) >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
                {c.percent_change ?? c.change ?? "—"}
              </div>
            </div>
          </div>
        ))}
      </div>
    </PanelShell>
  );
}

function MutualFundsPanel() {
  const [data, setData] = useState(null);
  useEffect(() => {
    let cancelled = false;
    fetchApi("mutual_funds")
      .then((j) => { if (!cancelled) setData(j); })
      .catch(() => {})
      .finally(() => {});
    return () => (cancelled = true);
  }, []);
  const items = data?.data ?? data?.mutual_funds ?? [];
  return (
    <PanelShell title="Mutual Funds">
      <div className="space-y-1">
        {items.slice(0, 8).map((m) => (
          <div key={m.scheme_code || m.name} className="flex justify-between py-2 border-b last:border-b-0">
            <div>
              <div className="text-sm font-medium truncate">{m.scheme_name ?? m.name}</div>
              <div className="text-xs text-gray-500 truncate">{m.scheme_type ?? m.category ?? ""}</div>
            </div>
            <div className="text-right ml-4">
              <div className="text-sm font-semibold">{m.nav ?? m.price ?? "—"}</div>
              <div className="text-xs text-gray-500">{m.date ?? ""}</div>
            </div>
          </div>
        ))}
      </div>
    </PanelShell>
  );
}

function StockForecastsPanel() {
  const [data, setData] = useState(null);
  useEffect(() => {
    let cancelled = false;
    fetchApi("stock_forecasts")
      .then((j) => { if (!cancelled) setData(j); })
      .catch(() => {})
      .finally(() => {});
    return () => (cancelled = true);
  }, []);
  const items = data?.forecasts ?? data?.data ?? [];
  return (
    <PanelShell title="Stock Forecasts">
      <div className="space-y-2">
        {items.slice(0, 8).map((f, i) => (
          <div key={f.ticker_id || i} className="py-2 border-b last:border-b-0">
            <div className="flex justify-between">
              <div className="text-sm font-medium">{f.company_name ?? f.ticker ?? f.symbol}</div>
              <div className="text-xs text-gray-500">{f.horizon ?? f.period ?? ""}</div>
            </div>
            <div className="text-xs text-slate-600">{f.summary ?? f.note ?? ""}</div>
          </div>
        ))}
      </div>
    </PanelShell>
  );
}

function NewsPanel() {
  const [data, setData] = useState(null);
  useEffect(() => {
    let cancelled = false;
    fetchApi("news")
      .then((j) => { if (!cancelled) setData(j); })
      .catch(() => {})
      .finally(() => {});
    return () => (cancelled = true);
  }, []);
  const items = data?.data ?? data?.news ?? [];
  return (
    <PanelShell title="Market News">
      <div className="space-y-2">
        {items.slice(0, 6).map((n, i) => (
          <div key={n.id ?? i} className="py-2 border-b last:border-b-0">
            <a className="text-sm font-medium" href={n.link ?? "#"} target="_blank" rel="noreferrer">
              {n.title ?? n.headline ?? n.name}
            </a>
            <div className="text-xs text-gray-500">{n.source ?? n.date ?? ""}</div>
          </div>
        ))}
      </div>
    </PanelShell>
  );
}

function IPOPanel() {
  const [data, setData] = useState(null);
  useEffect(() => {
    let cancelled = false;
    fetchApi("ipo")
      .then((j) => { if (!cancelled) setData(j); })
      .catch(() => {})
      .finally(() => {});
    return () => (cancelled = true);
  }, []);
  const items = data?.data ?? data?.ipos ?? [];
  return (
    <PanelShell title="Upcoming IPOs">
      <div className="space-y-2">
        {items.slice(0, 6).map((ip, i) => (
          <div key={ip.ticker_id ?? i} className="py-2 border-b last:border-b-0">
            <div className="text-sm font-medium">{ip.company_name ?? ip.name}</div>
            <div className="text-xs text-gray-500">{ip.listing_date ?? ip.date ?? ""}</div>
          </div>
        ))}
      </div>
    </PanelShell>
  );
}

/* ============================================================
   Main Component (rewritten)
============================================================ */
export default function MarketsDashboards() {
  // original worldbank state
  const [tab, setTab] = useState("economics");
  const [country, setCountry] = useState("IN");
  const [activeCode, setActiveCode] = useState("NY.GDP.MKTP.KD.ZG");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  const [macro, setMacro] = useState({});

  // WB indicators (kept small)
  const WB_SET = useMemo(
    () => [
      { code: "NY.GDP.MKTP.KD.ZG", label: "GDP growth (real, YoY %)" },
      { code: "NY.GDP.PCAP.KD", label: "GDP per capita (real)" },
      { code: "FP.CPI.TOTL.ZG", label: "Inflation CPI (YoY %)" },
      { code: "SL.UEM.TOTL.ZS", label: "Unemployment rate (%)" },
      { code: "NE.EXP.GNFS.ZS", label: "Exports (% of GDP)" },
    ],
    []
  );

  useEffect(() => {
    const ctrl = new AbortController();
    const load = async () => {
      setLoading(true);
      setErr(null);
      try {
        const entries = await Promise.all(
          WB_SET.map(async (ind) => {
            const data = await wbFetchSeries(country, ind.code, ctrl.signal);
            return [ind.code, data];
          })
        );
        setMacro(Object.fromEntries(entries));
      } catch (e) {
        setErr("Failed to load World Bank data.");
      } finally {
        setLoading(false);
      }
    };
    load();
    return () => ctrl.abort();
  }, [country, WB_SET]);

  const activeMeta = WB_SET.find((x) => x.code === activeCode);
  const activeData = macro[activeCode] || { series: [] };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <TabBar tab={tab} setTab={setTab} />
      </div>

      {/* ================= ECONOMICS ================= */}
      {tab === "economics" && (
        <div className="space-y-8">
          <div className="flex flex-wrap items-center gap-3">
            <select
              className="border rounded-md px-2 py-1 text-sm"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
            >
              {[
                { code: "AR", name: "Argentina" },
                { code: "AU", name: "Australia" },
                { code: "BR", name: "Brazil" },
                { code: "CA", name: "Canada" },
                { code: "CN", name: "China" },
                { code: "FR", name: "France" },
                { code: "DE", name: "Germany" },
                { code: "IN", name: "India" },
                { code: "JP", name: "Japan" },
                { code: "US", name: "United States" },
              ].map((c) => (
                <option key={c.code} value={c.code}>
                  {c.name}
                </option>
              ))}
            </select>

            <select
              className="border rounded-md px-2 py-1 text-sm"
              value={activeCode}
              onChange={(e) => setActiveCode(e.target.value)}
            >
              {WB_SET.map((x) => (
                <option key={x.code} value={x.code}>
                  {x.label}
                </option>
              ))}
            </select>

            {loading && (
              <span className="text-sm text-slate-500">Loading open data…</span>
            )}
            {err && <span className="text-sm text-amber-600">{err}</span>}
          </div>

          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="rounded-2xl border border-slate-200 p-4 bg-white shadow-sm">
              <div className="text-sm text-slate-500">Latest</div>
              <div className="text-2xl font-semibold text-slate-900">
                {fmt(activeData.last)}
              </div>
              <div className="text-xs text-slate-500">
                Year: {activeData.latestYear || "—"}
              </div>
            </div>
            <div className="rounded-2xl border border-slate-200 p-4 bg-white shadow-sm">
              <div className="text-sm text-slate-500">YoY Change</div>
              <div
                className={`text-2xl font-semibold ${
                  (activeData.changePct ?? 0) >= 0
                    ? "text-emerald-700"
                    : "text-rose-700"
                }`}
              >
                {pct(activeData.changePct)}
              </div>
            </div>
            <div className="rounded-2xl border border-slate-200 p-4 bg-white shadow-sm">
              <div className="text-sm text-slate-500">5Y CAGR</div>
              <div className="text-2xl font-semibold text-slate-900">
                {fmt(activeData.cagr5, 2)}%
              </div>
            </div>
            <div className="rounded-2xl border border-slate-200 p-4 bg-white shadow-sm">
              <div className="text-sm text-slate-500">Range (min–max)</div>
              <div className="text-2xl font-semibold text-slate-900">
                {fmt(activeData.min)} – {fmt(activeData.max)}
              </div>
            </div>
          </div>

          {/* Chart */}
          <div className="rounded-2xl border border-slate-200 p-4 bg-white shadow-sm">
            <div className="mb-2 text-sm text-slate-600">
              {activeMeta?.label || "Indicator"}
            </div>
            <div style={{ width: "100%", height: 320 }}>
              <ResponsiveContainer>
                <LineChart data={activeData.series}>
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} minTickGap={24} />
                  <YAxis tick={{ fontSize: 12 }} domain={["auto", "auto"]} />
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* ================= OTHER TABS (load IndianAPI panels) ================= */}
      {tab !== "economics" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column: main content (charts or TradingView) */}
          <div className="lg:col-span-2 space-y-6">
            {/* Indices chart / TradingView */}
            <div className="rounded-2xl border border-slate-200 p-4 bg-white shadow-sm">
              <div className="mb-2 text-sm text-slate-600">Market Chart</div>
              {/* TradingView embed (keeps your existing widget) */}
              <div dangerouslySetInnerHTML={{
                __html: `
                <div class="tradingview-widget-container" style="height:480px;width:100%">
                  <div class="tradingview-widget-container__widget"></div>
                  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
                  {
                    "allow_symbol_change": true,
                    "details": false,
                    "interval": "D",
                    "locale": "en",
                    "save_image": true,
                    "symbol": "BSE:SENSEX",
                    "theme": "light",
                    "autosize": true
                  }
                  </script>
                </div>
                `
              }} />
            </div>

            {/* News & Forecasts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <NewsPanel />
              <StockForecastsPanel />
            </div>

            {/* IPOs */}
            <IPOPanel />
          </div>

          {/* Right column: small panels */}
          <aside className="space-y-4">
            <TrendingPanel />
            <MostActivePanel which="BSE" />
            <MostActivePanel which="NSE" />
            <CommoditiesPanel />
            <MutualFundsPanel />
          </aside>
        </div>
      )}
    </div>
  );
}
