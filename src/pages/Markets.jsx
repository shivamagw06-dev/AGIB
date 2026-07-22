import React, { useMemo, useState } from "react";
import { Helmet } from "react-helmet-async";
import { useSearchParams } from "react-router-dom";
import { Search, BarChart3 } from "lucide-react";
import TrendlyneWidget, { buildTrendlyneUrls } from "@/components/markets/TrendlyneWidget";
import {
  TradingViewFinancials,
  TradingViewHeatmap,
  TradingViewMarketOverview,
} from "@/components/markets/TradingViewWidgets";

const STOCK_CATALOG = [
  { symbol: "RELIANCE", name: "Reliance Industries" },
  { symbol: "TCS", name: "Tata Consultancy Services" },
  { symbol: "HDFCBANK", name: "HDFC Bank" },
  { symbol: "INFY", name: "Infosys" },
  { symbol: "ICICIBANK", name: "ICICI Bank" },
  { symbol: "ITC", name: "ITC Limited" },
  { symbol: "SBIN", name: "State Bank of India" },
  { symbol: "BHARTIARTL", name: "Bharti Airtel" },
  { symbol: "KOTAKBANK", name: "Kotak Mahindra Bank" },
  { symbol: "LT", name: "Larsen & Toubro" },
  { symbol: "AXISBANK", name: "Axis Bank" },
  { symbol: "MARUTI", name: "Maruti Suzuki" },
  { symbol: "TITAN", name: "Titan Company" },
  { symbol: "BAJFINANCE", name: "Bajaj Finance" },
  { symbol: "WIPRO", name: "Wipro" },
  { symbol: "HINDUNILVR", name: "Hindustan Unilever" },
  { symbol: "ASIANPAINT", name: "Asian Paints" },
  { symbol: "SUNPHARMA", name: "Sun Pharmaceutical" },
];

const DEFAULT_SYMBOL = "RELIANCE";

export default function Markets() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initial = (searchParams.get("symbol") || DEFAULT_SYMBOL).toUpperCase();
  const [symbol, setSymbol] = useState(initial);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);

  const trendlyne = useMemo(() => buildTrendlyneUrls(symbol), [symbol]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return STOCK_CATALOG.filter(
      (s) =>
        s.symbol.toLowerCase().includes(q) ||
        s.name.toLowerCase().includes(q)
    ).slice(0, 8);
  }, [query]);

  const selectSymbol = (next) => {
    const sym = next.toUpperCase();
    setSymbol(sym);
    setQuery("");
    setOpen(false);
    setSearchParams({ symbol: sym }, { replace: true });
  };

  const selectedStock = STOCK_CATALOG.find((s) => s.symbol === symbol);

  return (
    <>
      <Helmet>
        <title>Markets | Agarwal Global Investments</title>
        <meta
          name="description"
          content="Trendlyne and TradingView market widgets with SWOT, technicals, heatmap, and fundamentals."
        />
      </Helmet>

      <div className="bg-slate-50 min-h-screen">
        {/* Hero + stock picker */}
        <section className="bg-slate-950 text-white border-b border-white/10">
          <div className="max-w-7xl mx-auto px-6 py-14 lg:py-16">
            <div className="flex items-center gap-3 text-blue-400 text-sm font-semibold uppercase tracking-widest">
              <BarChart3 size={18} />
              Markets
            </div>
            <h1 className="mt-3 text-4xl md:text-5xl font-bold tracking-tight">
              Market Intelligence
            </h1>
            <p className="mt-4 text-slate-400 text-lg max-w-2xl">
              Search a stock to update SWOT, technical analysis, and fundamentals widgets below.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <span className="rounded-full bg-blue-600/20 border border-blue-500/30 px-4 py-1.5 text-sm font-semibold text-blue-300">
                Viewing: {symbol}
                {selectedStock ? ` · ${selectedStock.name}` : ""}
              </span>
            </div>

            <div className="relative mt-6 max-w-xl">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
              <input
                type="search"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setOpen(true);
                }}
                onFocus={() => setOpen(true)}
                onBlur={() => setTimeout(() => setOpen(false), 180)}
                placeholder="Search stock for widgets — Reliance, TCS, HDFC Bank…"
                className="w-full rounded-2xl border border-white/10 bg-white/5 pl-12 pr-4 py-4 text-white placeholder:text-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
              />
              {open && filtered.length > 0 && (
                <div className="absolute z-30 mt-2 w-full rounded-2xl border border-slate-200 bg-white shadow-2xl overflow-hidden">
                  {filtered.map((s) => (
                    <button
                      key={s.symbol}
                      type="button"
                      onMouseDown={() => selectSymbol(s.symbol)}
                      className="flex w-full items-center justify-between px-5 py-3.5 hover:bg-slate-50 text-left border-b border-slate-100 last:border-0"
                    >
                      <div>
                        <p className="font-semibold text-slate-900">{s.symbol}</p>
                        <p className="text-sm text-slate-500">{s.name}</p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              {STOCK_CATALOG.slice(0, 10).map((s) => (
                <button
                  key={s.symbol}
                  type="button"
                  onClick={() => selectSymbol(s.symbol)}
                  className={`rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors ${
                    symbol === s.symbol
                      ? "bg-blue-600 text-white"
                      : "bg-white/10 text-slate-300 hover:bg-white/20"
                  }`}
                >
                  {s.symbol}
                </button>
              ))}
            </div>
          </div>
        </section>

        <div className="max-w-7xl mx-auto px-6 py-10 lg:py-14 space-y-10 lg:space-y-14">
          {/* TradingView — market-wide */}
          <section className="space-y-10">
            <TradingViewMarketOverview />
            <TradingViewHeatmap />
          </section>

          {/* Stock-specific — 2 column layout */}
          <section>
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-slate-900">Stock Analysis · {symbol}</h2>
              <p className="text-slate-500 mt-1">Trendlyne & TradingView · updates when you search</p>
            </div>

            <div className="grid xl:grid-cols-2 gap-8">
              <TrendlyneWidget
                title="SWOT Analysis"
                subtitle={`Strengths, weaknesses, opportunities & threats · ${symbol}`}
                dataUrl={trendlyne.swot}
                minHeight={480}
              />
              <TradingViewFinancials symbol={symbol} />
            </div>

            <div className="grid xl:grid-cols-2 gap-8 mt-8">
              <TrendlyneWidget
                title="Technical Analysis"
                subtitle={`RSI, MACD, moving averages · ${symbol}`}
                dataUrl={trendlyne.technical}
                minHeight={480}
              />
              <TrendlyneWidget
                title="IPO Tracker"
                subtitle="Live IPOs, allotment status & listing returns"
                dataUrl={trendlyne.ipo}
                minHeight={480}
              />
            </div>
          </section>

          <p className="text-xs text-slate-400 text-center pb-6">
            Widgets by Trendlyne & TradingView. For informational purposes only — not investment advice.
          </p>
        </div>
      </div>
    </>
  );
}
