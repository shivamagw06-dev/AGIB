// src/components/MarketsDashboard.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  RadialBarChart,
  RadialBar,
} from "recharts";
import { FiSearch, FiRefreshCw, FiDownload } from "react-icons/fi";
import jsPDF from "jspdf";

/* ---------------------- CONFIG ---------------------- */
const API_ORIGIN =
  (typeof process !== "undefined" && process.env && process.env.REACT_APP_API_ORIGIN) ||
  (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_API_URL) ||
  "";

const SNAPSHOT_CACHE_KEY = "agimkt_snapshot_v2";
const RECENT_COMPANIES_KEY = "agimkt_recent_companies_v2";
const AUTO_REFRESH_MS = 2 * 60 * 60 * 1000; // 2h
const DEFAULT_LIVE_POLL_MS = 15 * 1000; // 15s default live poll interval

/* ---------------------- HELPERS ---------------------- */
function buildUrl(path, params = {}) {
  const base = API_ORIGIN ? API_ORIGIN.replace(/\/+$/, "") : "";
  const cleaned = path.startsWith("/") ? path : `/${path}`;
  const full = base ? `${base}${cleaned}` : cleaned;
  const url = new URL(full, typeof window !== "undefined" ? window.location.origin : "http://localhost");
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
  });
  return url.toString();
}

async function fetchWithRetry(url, options = {}, attempts = 3, baseDelay = 400) {
  let i = 0;
  while (i < attempts) {
    try {
      const res = await fetch(url, options);
      const text = await res.text().catch(() => "");
      const ct = (res.headers && res.headers.get && res.headers.get("content-type")) || "";
      if (!res.ok) {
        if (ct.includes("json")) {
          try {
            const j = JSON.parse(text);
            throw new Error(j.error || j.message || `${res.status} ${res.statusText}`);
          } catch {
            throw new Error(`${res.status} ${res.statusText}: ${text}`);
          }
        }
        throw new Error(`${res.status} ${res.statusText}: ${text}`);
      }
      if (ct.includes("json")) {
        try {
          return JSON.parse(text);
        } catch {
          return text;
        }
      }
      return text;
    } catch (err) {
      i++;
      if (i >= attempts) throw err;
      const delay = baseDelay * 2 ** (i - 1) + Math.round(Math.random() * 200);
      // eslint-disable-next-line no-await-in-loop
      await new Promise((r) => setTimeout(r, delay));
    }
  }
}

async function apiGet(path, params = {}) {
  const url = buildUrl(path, params);
  return fetchWithRetry(url, { headers: { Accept: "application/json" } }, 4, 300);
}

const fmtNumber = (v) => {
  if (v === null || v === undefined || v === "") return "—";
  const n = Number(v);
  if (Number.isNaN(n)) return String(v);
  return new Intl.NumberFormat().format(n);
};
const fmtPct = (v) => {
  if (v === null || v === undefined || v === "") return "—";
  const n = Number(v);
  if (Number.isNaN(n)) return String(v);
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;
};
const clamp = (s, n = 180) => (s ? (String(s).length > n ? `${String(s).slice(0, n)}…` : s) : "—");

/* ---------------------- SMALL UI ---------------------- */
const Card = ({ children, className = "" }) => (
  <div className={`bg-white rounded-2xl shadow border p-4 ${className}`}>{children}</div>
);

const Stat = ({ label, value }) => (
  <div>
    <div className="text-xs text-gray-500">{label}</div>
    <div className="text-lg font-semibold text-slate-800">{value}</div>
  </div>
);

const Loading = ({ text = "Loading..." }) => (
  <div className="flex items-center gap-2 text-sm text-gray-500">
    <div className="w-4 h-4 border-2 border-current rounded-full animate-spin border-r-transparent" />
    <span>{text}</span>
  </div>
);

/* ---------------------- MAIN ---------------------- */
export default function MarketsDashboard() {
  const [snapshotLoading, setSnapshotLoading] = useState(false);
  const [trending, setTrending] = useState(null);
  const [nseActive, setNseActive] = useState([]);
  const [bseActive, setBseActive] = useState([]);
  const [week52, setWeek52] = useState(null);
  const [mutualFunds, setMutualFunds] = useState(null);
  const [priceShockers, setPriceShockers] = useState([]);
  const [commodities, setCommodities] = useState([]);

  const [query, setQuery] = useState("TCS");
  const [company, setCompany] = useState(null);
  const [historical, setHistorical] = useState(null);
  const [priceTarget, setPriceTarget] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [historicalStats, setHistoricalStats] = useState(null);

  const [deepDive, setDeepDive] = useState(null);

  const [industryQuery, setIndustryQuery] = useState("");
  const [industryResults, setIndustryResults] = useState([]);
  const [mfQuery, setMfQuery] = useState("");
  const [mfResults, setMfResults] = useState([]);

  const [loadingCompany, setLoadingCompany] = useState(false);
  const [error, setError] = useState(null);
  const [serverErrorCount, setServerErrorCount] = useState(0);
  const [showRecSnapshots, setShowRecSnapshots] = useState(false);

  const refreshTimer = useRef(null);
  const livePollTimer = useRef(null);
  const livePollTicker = useRef(null);
  const livePollIntervalMs = useRef(DEFAULT_LIVE_POLL_MS);

  /* ------------------ cache helpers ------------------ */
  function saveSnapshotCache(snapshot) {
    try {
      localStorage.setItem(SNAPSHOT_CACHE_KEY, JSON.stringify({ ts: Date.now(), data: snapshot }));
    } catch {}
  }
  function loadSnapshotCache() {
    try {
      const raw = localStorage.getItem(SNAPSHOT_CACHE_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (Date.now() - (parsed.ts || 0) > 10 * 60 * 1000) return parsed.data;
      return parsed.data;
    } catch {
      return null;
    }
  }
  function saveRecentCompany(name, payload) {
    try {
      const raw = JSON.parse(localStorage.getItem(RECENT_COMPANIES_KEY) || "[]");
      const filtered = raw.filter((r) => r.name !== name);
      filtered.unshift({ name, ts: Date.now(), payload });
      localStorage.setItem(RECENT_COMPANIES_KEY, JSON.stringify(filtered.slice(0, 8)));
    } catch {}
  }
  function loadRecentCompanies() {
    try {
      return JSON.parse(localStorage.getItem(RECENT_COMPANIES_KEY) || "[]");
    } catch {
      return [];
    }
  }

  /* ------------------ research helper (Perplexity-backed) ------------------ */
  async function fetchResearchSummary(ticker, mode = "short") {
    // Try several likely endpoints so this works whether server mounts router at /research or /api/research
    const candidates = [
      "/research/summary",
      "/api/research/summary",
      buildUrl("/research/summary"),
    ].filter(Boolean);

    const tryPost = async (url) => {
      return fetchWithRetry(url, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ ticker, mode }),
      }, 2, 300);
    };

    let lastErr = null;
    for (const url of candidates) {
      try {
        const r = await tryPost(url);
        if (r) return r;
      } catch (err) {
        lastErr = err;
        // try next candidate
      }
    }
    console.warn("research fetch failed (all candidates):", lastErr);
    return null;
  }

  /* ------------------ live quote poll helpers ------------------ */
  function stopLivePoll() {
    if (livePollTimer.current) {
      clearInterval(livePollTimer.current);
      livePollTimer.current = null;
    }
    livePollTicker.current = null;
  }

  async function pollLiveQuote(ticker) {
    if (!ticker) return;
    try {
      // Backend endpoint expected: GET /api/quote?symbol=XYZ
      const q = await apiGet("/api/quote", { symbol: ticker });
      if (!q) return;
      // normalize minimal fields
      const cp = q.currentPrice || q.current_price || q.price || q.last_price || q.lastTradedPrice || q.last_traded_price || null;
      const percent = q.percentChange ?? q.changePercent ?? q.percent_change ?? q.percent ?? null;
      const volume = q.volume ?? q.totalVolume ?? q.v ?? null;
      const prevClose = q.prevClose ?? q.previous_close ?? q.prev_close ?? null;
      const openPrice = q.openPrice ?? q.open ?? null;
      const dayRange = q.dayRange ?? (q.low && q.high ? { low: q.low, high: q.high } : null);

      setCompany((prev) => {
        if (!prev) return prev;
        const updated = { ...prev };
        updated.currentPrice = cp || updated.currentPrice;
        updated.percentChange = percent ?? updated.percentChange;
        updated.stockDetailsReusableData = {
          ...(updated.stockDetailsReusableData || {}),
          volume: volume ?? (updated.stockDetailsReusableData || {}).volume,
          prevClose: prevClose ?? (updated.stockDetailsReusableData || {}).prevClose,
          openPrice: openPrice ?? (updated.stockDetailsReusableData || {}).openPrice,
        };
        if (dayRange) {
          updated.dayRange = dayRange;
        }
        return updated;
      });
      setServerErrorCount(0);
    } catch (e) {
      console.warn("live quote poll failed", e);
      setServerErrorCount((c) => c + 1);
      // if serverErrorCount grows too high, stop polling to avoid hammering
      // we'll rely on existing serverErrorCount state elsewhere
    }
  }

  function startLivePoll(ticker, intervalMs = DEFAULT_LIVE_POLL_MS) {
    if (!ticker) return;
    // if same ticker already polling, no-op
    if (livePollTicker.current && String(livePollTicker.current).toLowerCase() === String(ticker).toLowerCase()) return;
    stopLivePoll();
    livePollTicker.current = ticker;
    livePollIntervalMs.current = intervalMs;
    // do an immediate poll, then interval
    pollLiveQuote(ticker).catch(() => {});
    livePollTimer.current = setInterval(() => {
      pollLiveQuote(ticker).catch(() => {});
    }, intervalMs);
  }

  /* ------------------ load snapshot ------------------ */
  async function loadSnapshot(useCache = true) {
    setSnapshotLoading(true);
    setError(null);
    try {
      const cached = useCache ? loadSnapshotCache() : null;
      if (cached) {
        setTrending(cached.trending || null);
        setNseActive(cached.nseActive || []);
        setBseActive(cached.bseActive || []);
        setWeek52(cached.week52 || null);
        setMutualFunds(cached.mutualFunds || null);
        setPriceShockers(cached.priceShockers || []);
        setCommodities(cached.commodities || []);
      }

      const [
        trRes,
        nseRes,
        bseRes,
        week52Res,
        mfRes,
        shockersRes,
        commRes,
      ] = await Promise.allSettled([
        apiGet("/api/trending"),
        apiGet("/api/NSE_most_active"),
        apiGet("/api/BSE_most_active"),
        apiGet("/api/fetch_52_week_high_low_data"),
        apiGet("/api/mutual_funds"),
        apiGet("/api/price_shockers"),
        apiGet("/api/commodities"),
      ]);

      // Prefer Perplexity research for a curated snapshot of commodities (server research.js may provide this)
      let researchCom = null;
      try {
        researchCom = await fetchResearchSummary("market_snapshot", "short");
      } catch (e) {
        researchCom = null;
      }

      const snapshot = {
        trending: trRes.status === "fulfilled" ? (trRes.value.trending_stocks || trRes.value) : null,
        nseActive: nseRes.status === "fulfilled" ? (Array.isArray(nseRes.value) ? nseRes.value : nseRes.value || []) : [],
        bseActive: bseRes.status === "fulfilled" ? (Array.isArray(bseRes.value) ? bseRes.value : bseRes.value || []) : [],
        week52: week52Res.status === "fulfilled" ? week52Res.value : null,
        mutualFunds: mfRes.status === "fulfilled" ? mfRes.value : null,
        priceShockers: shockersRes.status === "fulfilled" ? shockersRes.value || [] : [],
        commodities:
          (researchCom && researchCom.source_data && Array.isArray(researchCom.source_data.commodities) && researchCom.source_data.commodities.length)
            ? researchCom.source_data.commodities
            : (commRes.status === "fulfilled" ? commRes.value || [] : []),
      };

      setTrending(snapshot.trending);
      setNseActive(snapshot.nseActive);
      setBseActive(snapshot.bseActive);
      setWeek52(snapshot.week52);
      setMutualFunds(snapshot.mutualFunds);
      setPriceShockers(snapshot.priceShockers);
      setCommodities(snapshot.commodities);

      saveSnapshotCache(snapshot);
      setServerErrorCount(0);
    } catch (e) {
      console.error("snapshot error", e);
      setError(String(e));
      setServerErrorCount((c) => c + 1);
    } finally {
      setSnapshotLoading(false);
    }
  }

  /* ------------------ load company (prefer research) ------------------ */
  async function loadCompany(name) {
    if (!name) return;
    setLoadingCompany(true);
    setError(null);
    setCompany(null);
    setHistorical(null);
    setPriceTarget(null);
    setForecast(null);
    setHistoricalStats(null);
    setDeepDive(null);

    // stop any existing live poll while loading a new company
    stopLivePoll();

    try {
      // 1) Ask Perplexity research for a summary + source_data (server should call Perplexity)
      const research = await fetchResearchSummary(name, "short");

      if (research && research.source_data && research.source_data.stockData) {
        // research returned structured stockData — prefer it
        const sd = research.source_data.stockData || {};

        // Normalization: map many possible keys to our canonical structure
        const normalized = {
          companyName: sd.companyName || sd.commonName || sd.name || sd.company_name || sd.company || name,
          tickerId: sd.tickerId || sd.ticker || sd.ticker_id || sd.symbol || name,
          industry: sd.industry || sd.sector || sd.industrySector || null,
          currentPrice:
            sd.currentPrice ||
            sd.current_price ||
            (sd.last_price ? (typeof sd.last_price === "object" ? sd.last_price : { NSE: sd.last_price, BSE: sd.last_price }) : null) ||
            null,
          percentChange: sd.percentChange ?? sd.changePercent ?? sd.percent_change ?? sd.change ?? null,
          stockDetailsReusableData: sd.stockDetailsReusableData || sd.stock_details_reusable_data || {
            marketCap: sd.marketCap || sd.market_cap || sd.marketCapitalization || sd.marketCapital || null,
            peRatio: sd.peRatio || sd.pe || sd.p_e_ratio || sd.pe_ratio || sd.pe_ratio,
            eps: sd.eps || sd.EPS || sd.e_p_s,
            dividendYield: sd.dividendYield || sd.dividend_yield || sd.div_yield,
            volume: sd.volume ?? sd.last_traded_volume ?? sd.avgVolume ?? null,
            prevClose: sd.prevClose ?? sd.previous_close ?? sd.prev_close ?? null,
          },
          companyProfile: sd.companyProfile || sd.company_profile || sd.profile || sd.description || {},
          yearHigh: sd.yearHigh ?? sd.high52 ?? sd._52WeekHigh ?? null,
          yearLow: sd.yearLow ?? sd.low52 ?? sd._52WeekLow ?? null,
          dayRange: sd.dayRange || sd.day_range || null,
        };

        // Ensure currentPrice shape is consistent (NSE/BSE keys if possible)
        if (typeof normalized.currentPrice === "number") {
          normalized.currentPrice = { NSE: normalized.currentPrice, BSE: normalized.currentPrice };
        }

        setCompany(normalized);
        setDeepDive(research); // entire research payload (one_liner, citations, etc.)

        if (research.source_data.priceTarget) setPriceTarget(research.source_data.priceTarget);

        // historical: prefer research.source_data.historical if present
        if (research.source_data.historical && Array.isArray(research.source_data.historical) && research.source_data.historical.length) {
          setHistorical(research.source_data.historical);
        } else {
          try {
            const hist = await apiGet("/api/historical_data", { symbol: name, period: "1yr", filter: "price" });
            setHistorical(hist?.datasets || hist || null);
          } catch (e) {
            setHistorical(null);
          }
        }

        // If research returned commodities for the market snapshot, prefer it
        if (research.source_data.commodities && Array.isArray(research.source_data.commodities) && research.source_data.commodities.length) {
          setCommodities(research.source_data.commodities);
        }

        saveRecentCompany(name, normalized);

        // Start live polling for quotes (use tickerId if available)
        const ticker = normalized.tickerId || name;
        startLivePoll(ticker, DEFAULT_LIVE_POLL_MS);
      } else {
        // fallback: use existing APIs
        const stock = await apiGet("/api/stock", { name });
        setCompany(stock || null);
        saveRecentCompany(name, stock || null);

        const ticker = stock?.tickerId || stock?.ticker || stock?.ticker_id || name;

        try {
          const hist = await apiGet("/api/historical_data", { symbol: name, period: "1yr", filter: "price" });
          setHistorical(hist?.datasets || hist || null);
        } catch {
          setHistorical(null);
        }

        try {
          const pt = await apiGet("/api/stock_target_price", { stock_id: ticker });
          setPriceTarget(pt || null);
        } catch {
          setPriceTarget(null);
        }

        try {
          const fc = await apiGet("/api/stock_forecasts", { stock_id: ticker, measure_code: "EPS", period_type: "Annual", data_type: "Estimates", age: "Current" });
          setForecast(fc || null);
        } catch {
          setForecast(null);
        }

        try {
          const hs = await apiGet("/api/historical_stats", { stock_name: name, stats: "quarter_results" });
          setHistoricalStats(hs || null);
        } catch {
          setHistoricalStats(null);
        }

        // start live poll using ticker
        startLivePoll(ticker, DEFAULT_LIVE_POLL_MS);
      }

      setServerErrorCount(0);
    } catch (e) {
      console.error("company fetch error", e);
      setError(String(e));
      setServerErrorCount((c) => c + 1);
      const recents = loadRecentCompanies();
      const r = recents.find((x) => x.name.toLowerCase() === name.toLowerCase());
      if (r) setCompany(r.payload || null);
    } finally {
      setLoadingCompany(false);
    }
  }

  /* ------------------ search helpers ------------------ */
  async function doIndustrySearch(q) {
    if (!q) return setIndustryResults([]);
    try {
      const res = await apiGet("/api/industry_search", { query: q });
      setIndustryResults(Array.isArray(res) ? res : res.data || []);
    } catch (e) {
      console.error("industry search fail", e);
      setIndustryResults([]);
    }
  }
  async function doMfSearch(q) {
    if (!q) return setMfResults([]);
    try {
      const res = await apiGet("/api/mutual_fund_search", { query: q });
      setMfResults(Array.isArray(res) ? res : res.data || []);
    } catch (e) {
      console.error("mf search fail", e);
      setMfResults([]);
    }
  }

  useEffect(() => {
    loadSnapshot(true);
    refreshTimer.current = setInterval(() => loadSnapshot(false), AUTO_REFRESH_MS);
    const recents = loadRecentCompanies();
    const r = recents.find((x) => x.name.toLowerCase() === query.toLowerCase());
    if (r) setCompany(r.payload);

    // cleanup on unmount
    return () => {
      clearInterval(refreshTimer.current);
      stopLivePoll();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ------------------ derived values ------------------ */
  const topGainers = useMemo(() => {
    const t = trending?.top_gainers || trending?.topGainers || [];
    if (t && t.length) return t.slice(0, 6);
    const arr = (nseActive || []).map((a) => ({ company_name: a.company, ticker_id: a.ticker, price: a.price, percent_change: a.percent_change }));
    return arr.sort((a, b) => (Number(b.percent_change || 0) - Number(a.percent_change || 0))).slice(0, 6);
  }, [trending, nseActive]);

  const topLosers = useMemo(() => {
    const t = trending?.top_losers || trending?.topLosers || [];
    if (t && t.length) return t.slice(0, 6);
    const arr = (nseActive || []).map((a) => ({ company_name: a.company, ticker_id: a.ticker, price: a.price, percent_change: a.percent_change }));
    return arr.sort((a, b) => (Number(a.percent_change || 0) - Number(b.percent_change || 0))).slice(0, 6);
  }, [trending, nseActive]);

  const priceSetForChart = useMemo(() => {
    if (!historical) return [];
    const datasets = Array.isArray(historical) ? historical : (historical.datasets || []);
    const priceSet = datasets.find((d) => /price/i.test(d.metric || d.label || "")) || datasets[0];
    const values = priceSet?.values || [];
    return values.map((v) => ({ date: v[0], value: Number(v[1]) }));
  }, [historical]);

  const normalizedCommodities = useMemo(() => {
    return (commodities || []).map((c) => {
      return {
        id: c.contractId || c.contract_id || c.id || (c.commoditySymbol || c.commodity_symbol ? `${c.commoditySymbol || c.commodity_symbol}` : c.contractId),
        name: c.commoditySymbol || c.commodity_symbol || c.commodity || c.commodityName || c.contractId || "Unknown",
        lastTradedPrice: c.lastTradedPrice ?? c.last_traded_price ?? c.lastPrice ?? c.last_price ?? null,
      };
    });
  }, [commodities]);

  const sectorTiles = useMemo(() => {
    const map = {};
    (industryResults || []).forEach((it) => {
      const sector = it.mgSector || it.mgIndustry || "Other";
      map[sector] = map[sector] || { count: 0, sumPct: 0, sourceCount: 0 };
      const rating = (it.activeStockTrends?.overallRating || "").toLowerCase();
      let approx = 0;
      if (rating.includes("bull")) approx = 1.5;
      if (rating.includes("bear")) approx = -1.5;
      if (rating.includes("neutral")) approx = 0;
      map[sector].count += 1;
      map[sector].sumPct += approx;
      map[sector].sourceCount += 1;
    });
    (nseActive || []).forEach((st) => {
      const sector = st.sector || st.mgSector || st.industry || "Other";
      map[sector] = map[sector] || { count: 0, sumPct: 0, sourceCount: 0 };
      const pct = Number(st.percent_change || st.percentChange || 0);
      map[sector].count += 1;
      map[sector].sumPct += pct;
      map[sector].sourceCount += 1;
    });

    return Object.entries(map).map(([sector, v]) => {
      const avgPct = v.sourceCount ? v.sumPct / v.sourceCount : 0;
      return { sector, count: v.count, avgPct };
    }).sort((a, b) => b.count - a.count);
  }, [industryResults, nseActive]);

  /* ------------------ export helpers ------------------ */
  function exportTableToCSV(rows, filename = "report.csv") {
    if (!rows || !rows.length) return;
    const header = Object.keys(rows[0]);
    const csv = [
      header.join(","),
      ...rows.map((r) => header.map((h) => {
        let cell = r[h] === null || r[h] === undefined ? "" : String(r[h]);
        if (cell.includes(",") || cell.includes('"') || cell.includes("\n")) cell = `"${cell.replace(/"/g, '""')}"`;
        return cell;
      }).join(",")),
    ].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  function exportReportPdf() {
    const doc = new jsPDF({ unit: "pt", format: "a4" });
    const margin = 40;
    let y = 40;
    doc.setFontSize(16);
    doc.text("Markets Dashboard Report", margin, y);
    y += 22;
    doc.setFontSize(10);
    doc.text(`Generated: ${new Date().toLocaleString()}`, margin, y);
    y += 18;

    if (company) {
      doc.setFontSize(12);
      doc.text(`Company: ${company.companyName || company.tickerId || query}`, margin, y);
      y += 16;
      doc.setFontSize(10);
      const cpText = company.currentPrice
        ? `${company.currentPrice.NSE ?? company.currentPrice?.nse ?? "—"} / ${company.currentPrice.BSE ?? company.currentPrice?.bse ?? "—"}`
        : "—";
      doc.text(`Price (NSE / BSE): ${cpText}`, margin, y);
      y += 12;
      doc.text(`Percent change: ${fmtPct(company.percentChange)}`, margin, y);
      y += 12;
      const sd = company.stockDetailsReusableData || {};
      doc.text(`P/E: ${fmtNumber(sd.peRatio ?? sd.pe ?? sd.PE) }  ·  EPS: ${fmtNumber(sd.eps ?? sd.EPS) }  ·  Dividend Yield: ${fmtNumber(sd.dividendYield ?? sd.dividend_yield)}`, margin, y);
      y += 18;
    }

    doc.setFontSize(11);
    doc.text("Top Gainers (sample)", margin, y);
    y += 14;
    const g = topGainers.slice(0, 6);
    g.forEach((row) => {
      if (y > 740) { doc.addPage(); y = 40; }
      doc.text(`${row.company_name || row.company || row.ticker || "-"}  —  ${fmtNumber(row.price)}  (${fmtPct(row.percent_change ?? row.percentChange)})`, margin, y);
      y += 12;
    });

    doc.save(`markets-report-${(company?.tickerId || query).toLowerCase()}.pdf`);
  }

  /* ------------------ PRICE TARGET helpers ------------------ */
  function getPriceTargetSummary(pt) {
    if (!pt || !pt.priceTarget) return null;
    const mean = pt.priceTarget.Mean ?? pt.priceTarget.UnverifiedMean ?? pt.priceTarget.PreliminaryMean ?? null;
    const median = pt.priceTarget.Median ?? null;
    const count = pt.priceTarget.NumberOfEstimates ?? pt.priceTarget.NumberOfRecommendations ?? null;
    let recentSnapshot = null;
    const snaps = pt.priceTargetSnapshots?.PriceTargetSnapshot || pt.priceTargetSnapshots || [];
    if (Array.isArray(snaps) && snaps.length) {
      const found = snaps.find((s) => s.Mean || s.UnverifiedMean) || snaps[0];
      recentSnapshot = {
        age: found.Age || found.age || "Snapshot",
        mean: found.Mean ?? found.UnverifiedMean ?? null,
      };
    }
    return { mean, median, count, recentSnapshot };
  }

  const priceTargetSummary = useMemo(() => getPriceTargetSummary(priceTarget), [priceTarget]);

  /* ------------------ Render ------------------ */
  return (
    <div className="p-6 max-w-screen-6xl mx-auto">
      <div className="flex items-start justify-between gap-6 mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-800">Markets Dashboard</h1>
          <div className="mt-1 text-sm text-slate-500">
            Using backend: <span className="font-mono text-xs">{API_ORIGIN ? `${API_ORIGIN}/api/*` : "/api/* (same origin)"}</span>
          </div>
          {serverErrorCount > 0 && (
            <div className="mt-2 text-xs text-red-600">Server errors detected: {serverErrorCount}</div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button onClick={() => loadSnapshot(false)} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg flex items-center gap-2">
            <FiRefreshCw /> Refresh
          </button>
          <button onClick={() => exportReportPdf()} className="px-4 py-2 bg-slate-50 border rounded-lg flex items-center gap-2">
            <FiDownload /> Export PDF
          </button>
        </div>
      </div>

      {/* search + summary */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6">
        <div className="lg:col-span-8">
          <Card>
            <div className="flex flex-col md:flex-row md:items-center gap-4">
              <div className="flex-1">
                <label className="text-xs text-slate-500 mb-2 block">Company Search</label>
                <div className="flex gap-2">
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && loadCompany(query)}
                    placeholder="Search company name or ticker (TCS, Reliance)"
                    className="flex-1 px-3 py-2 rounded-lg border focus:ring-2 focus:ring-indigo-200 outline-none"
                  />
                  <button onClick={() => loadCompany(query)} className="px-4 py-2 bg-indigo-600 text-white rounded-lg flex items-center gap-2">
                    <FiSearch /> Search
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3 w-full md:w-96">
                <Stat label="Top Gainers" value={topGainers.length || 0} />
                <Stat label="Top Losers" value={topLosers.length || 0} />
                <Stat label="NSE Active" value={nseActive.length || 0} />
              </div>
            </div>

            <div className="mt-4 border-t pt-4">
              {loadingCompany ? (
                <Loading text="Loading company..." />
              ) : company ? (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                  <div className="lg:col-span-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="text-lg font-semibold">{company.companyName || company.tickerId || query}</div>
                        <div className="text-xs text-slate-500">{company.industry || "—"}</div>
                      </div>

                      <div className="text-right">
                        <div className="text-xs text-slate-500">Price (NSE / BSE)</div>
                        <div className="text-xl font-semibold">{company.currentPrice ? `${company.currentPrice.NSE ?? company.currentPrice?.nse ?? "—"} / ${company.currentPrice.BSE ?? company.currentPrice?.bse ?? "—"}` : "—"}</div>
                        <div className={`text-sm ${Number(company.percentChange) >= 0 ? "text-green-600" : "text-red-600"}`}>{fmtPct(company.percentChange)}</div>
                        <div className="text-xs text-slate-400 mt-1">Prev close: {fmtNumber(company.stockDetailsReusableData?.prevClose ?? company.stockDetailsReusableData?.previous_close ?? company.stockDetailsReusableData?.prev_close ?? "—")}</div>
                      </div>
                    </div>

                    <div className="mt-3 p-3 rounded bg-slate-50 text-sm text-slate-600 max-h-28 overflow-auto">
                      <div className="font-medium mb-1">Company profile</div>
                      <div>{company.companyProfile?.companyDescription || company.companyProfile?.description || clamp(JSON.stringify(company.companyProfile || {}, null, 2), 800) || "Not available"}</div>
                    </div>

                    <div className="mt-3 grid grid-cols-3 gap-3">
                      <Stat label="52wk High" value={fmtNumber(company.yearHigh)} />
                      <Stat label="52wk Low" value={fmtNumber(company.yearLow)} />
                      <Stat label="Market Cap" value={fmtNumber(company.stockDetailsReusableData?.marketCap || company.marketCap || "—")} />
                    </div>

                    <div className="mt-3 grid grid-cols-4 gap-3 text-sm">
                      <div className="p-2 bg-slate-50 rounded">
                        <div className="text-xs text-slate-500">P/E</div>
                        <div className="font-semibold">{fmtNumber(company.stockDetailsReusableData?.peRatio ?? company.stockDetailsReusableData?.pe ?? "—")}</div>
                      </div>
                      <div className="p-2 bg-slate-50 rounded">
                        <div className="text-xs text-slate-500">EPS</div>
                        <div className="font-semibold">{fmtNumber(company.stockDetailsReusableData?.eps ?? "—")}</div>
                      </div>
                      <div className="p-2 bg-slate-50 rounded">
                        <div className="text-xs text-slate-500">Div Yield</div>
                        <div className="font-semibold">{fmtNumber(company.stockDetailsReusableData?.dividendYield ?? company.stockDetailsReusableData?.dividend_yield ?? "—")}</div>
                      </div>
                      <div className="p-2 bg-slate-50 rounded">
                        <div className="text-xs text-slate-500">Volume</div>
                        <div className="font-semibold">{fmtNumber(company.stockDetailsReusableData?.volume ?? "—")}</div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Card className="p-3">
                      <div className="text-xs text-slate-500">Analyst Recommendation</div>
                      <div className="text-lg font-semibold mt-2">
                        {priceTargetSummary?.mean != null ? `${recommendationLabel(priceTargetSummary.mean)} (${Number(priceTargetSummary.mean).toFixed(2)})` : "No data"}
                      </div>
                      <div className="text-xs mt-2 text-slate-400">Estimates: {priceTargetSummary?.count ?? "—"}</div>
                      <div style={{ height: 120 }}>
                        {priceTargetSummary?.mean != null ? (
                          <ResponsiveContainer width="100%" height={120}>
                            <RadialBarChart innerRadius="70%" outerRadius="100%" data={[{ name: "rec", uv: Math.max(0, Math.min(100, (5 - Number(priceTargetSummary.mean)) * 20)) }]} startAngle={180} endAngle={-0}>
                              <RadialBar minAngle={15} cornerRadius={10} dataKey="uv" fill="#4f46e5" />
                            </RadialBarChart>
                          </ResponsiveContainer>
                        ) : (
                          <div className="text-xs text-slate-400">No gauge data</div>
                        )}
                      </div>
                    </Card>

                    <Card className="p-3">
                      <div className="flex items-center justify-between">
                        <div className="text-xs text-slate-500">Forecast / Price Target</div>
                        <div className="text-xs text-indigo-600 cursor-pointer" onClick={() => setShowRecSnapshots((s) => !s)}>{showRecSnapshots ? "Hide" : "Show"}</div>
                      </div>

                      <div className="mt-3">
                        {priceTargetSummary ? (
                          <>
                            <div className="text-sm text-slate-500">Mean target</div>
                            <div className="text-2xl font-semibold">{fmtNumber(priceTargetSummary.mean)}</div>
                            <div className="text-xs text-slate-400 mt-1">Median: {fmtNumber(priceTargetSummary.median)} · Estimates: {priceTargetSummary.count ?? "—"}</div>

                            {priceTargetSummary.recentSnapshot ? (
                              <div className="mt-3 text-sm">
                                <div className="text-xs text-slate-500">Recent snapshot</div>
                                <div className="font-medium">{fmtNumber(priceTargetSummary.recentSnapshot.mean)}</div>
                                <div className="text-xs text-slate-400">{priceTargetSummary.recentSnapshot.age}</div>
                              </div>
                            ) : null}
                          </>
                        ) : (
                          <div className="text-sm text-slate-400">No price target data</div>
                        )}
                      </div>
                    </Card>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-slate-500">Enter company to fetch details.</div>
              )}
            </div>
          </Card>
        </div>

        {/* right column */}
        <div className="lg:col-span-4 space-y-4">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold">Market Movers — NSE Active</div>
                <div className="text-xs text-slate-400">Live snapshot</div>
              </div>
              <div className="text-xs text-slate-400">{snapshotLoading ? "Refreshing…" : "Snapshot"}</div>
            </div>

            <div className="mt-3 space-y-2">
              {nseActive && nseActive.length ? (
                nseActive.slice(0, 6).map((r) => (
                  <div key={r.ticker || r.company} className="flex items-center justify-between text-sm">
                    <div className="flex-1">
                      <div className="font-medium">{r.company}</div>
                      <div className="text-xs text-slate-400">{r.ticker}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">{fmtNumber(r.price)}</div>
                      <div className={`text-xs ${Number(r.percent_change || r.percentChange) >= 0 ? "text-green-600" : "text-red-600"}`}>{fmtPct(r.percent_change ?? r.percentChange)}</div>
                    </div>
                  </div>
                ))
              ) : topGainers && topGainers.length ? (
                topGainers.map((g) => (
                  <div key={g.ticker_id || g.ticker} className="flex items-center justify-between text-sm">
                    <div className="flex-1">
                      <div className="font-medium">{g.company_name || g.company || g.ticker}</div>
                      <div className="text-xs text-slate-400">{g.ticker_id || g.ticker}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">{fmtNumber(g.price)}</div>
                      <div className={`text-xs ${Number(g.percent_change || g.percentChange) >= 0 ? "text-green-600" : "text-red-600"}`}>{fmtPct(g.percent_change ?? g.percentChange)}</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-sm text-slate-400">No data</div>
              )}
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold">52-week Highs / Lows (sample)</div>
                <div className="text-xs text-slate-400">From API</div>
              </div>
              <div className="text-xs text-slate-400">Snapshot</div>
            </div>

            <div className="mt-3 text-sm">
              {week52 ? (
                <>
                  <div className="mb-2 text-xs text-slate-500">NSE - Highs</div>
                  {(week52.NSE_52WeekHighLow?.high52Week || []).slice(0, 4).map((h) => (
                    <div key={h.ticker} className="flex justify-between"><div>{h.company}</div><div className="font-medium">{fmtNumber(h.price)}</div></div>
                  ))}
                </>
              ) : <div className="text-slate-400">No 52-week data</div>}
            </div>
          </Card>
        </div>
      </div>

      {/* chart and snapshot */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2">
          <Card className="flex flex-col h-96">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-sm font-semibold">Historical Price — 1 Year</div>
                <div className="text-xs text-slate-400">Endpoint: /api/historical_data (preferred via research when available)</div>
              </div>

              <div className="flex items-center gap-2">
                <button onClick={() => {
                  const rows = priceSetForChart.map((p) => ({ date: p.date, price: p.value }));
                  exportTableToCSV(rows, `${(company?.tickerId || query).toLowerCase()}-historical.csv`);
                }} className="text-xs px-3 py-1 bg-slate-50 border rounded">Export CSV</button>
                <button onClick={() => exportReportPdf()} className="text-xs px-3 py-1 bg-slate-50 border rounded"><FiDownload/> PDF</button>
              </div>
            </div>

            <div className="flex-1">
              {priceSetForChart.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={priceSetForChart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e6e6e6" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis tickFormatter={(v) => fmtNumber(v)} />
                    <Tooltip formatter={(v) => fmtNumber(v)} />
                    <Line type="monotone" dataKey="value" stroke="#4f46e5" dot={false} strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-400">No historical price — search a symbol to load historical data (Perplexity preferred).</div>
              )}
            </div>
          </Card>
        </div>

        <div>
          <Card>
            <div className="text-sm font-semibold mb-3">Snapshot — Top Movers</div>
            <div className="text-xs text-slate-400 mb-2">Real-time</div>

            <div className="mt-2">
              <div className="text-xs text-slate-500">Top Gainers</div>
              {topGainers.length ? topGainers.slice(0, 5).map((g) => (
                <div key={g.ticker_id || g.ticker} className="flex justify-between items-center text-sm">
                  <div>{g.company_name || g.company || g.ticker}</div>
                  <div className="text-right"><div className="font-medium">{fmtNumber(g.price)}</div><div className="text-xs text-green-600">{fmtPct(g.percent_change ?? g.percentChange)}</div></div>
                </div>
              )) : <div className="text-sm text-slate-400">No data</div>}

              <div className="mt-4 text-xs text-slate-500">Top Losers</div>
              {topLosers.length ? topLosers.slice(0, 5).map((g) => (
                <div key={g.ticker_id || g.ticker} className="flex justify-between items-center text-sm">
                  <div>{g.company_name || g.company || g.ticker}</div>
                  <div className="text-right"><div className="font-medium">{fmtNumber(g.price)}</div><div className="text-xs text-red-600">{fmtPct(g.percent_change ?? g.percentChange)}</div></div>
                </div>
              )) : <div className="text-sm text-slate-400">No data</div>}
            </div>
          </Card>
        </div>
      </div>

      {/* bottom: Analysts, mutual funds, commodities */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2">
          <Card>
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-semibold">Analyst Targets & Forecasts</div>
              <div className="text-xs text-slate-400">stock_target_price / stock_forecasts</div>
            </div>

            {priceTarget ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-3 bg-slate-50 rounded"><div className="text-xs text-slate-500">Mean Target</div><div className="font-semibold">{fmtNumber(priceTarget.priceTarget?.Mean ?? priceTarget.priceTarget?.UnverifiedMean)}</div></div>
                  <div className="p-3 bg-slate-50 rounded"><div className="text-xs text-slate-500">Median</div><div className="font-semibold">{fmtNumber(priceTarget.priceTarget?.Median)}</div></div>
                  <div className="p-3 bg-slate-50 rounded"><div className="text-xs text-slate-500">Number Estimates</div><div className="font-semibold">{fmtNumber(priceTarget.priceTarget?.NumberOfEstimates)}</div></div>
                </div>

                <div className="mt-4">
                  <div className="text-xs text-slate-500">Recommendation snapshot</div>
                  {priceTarget.priceTargetSnapshots?.PriceTargetSnapshot?.length ? (
                    <table className="w-full text-xs mt-2">
                      <thead className="text-left text-gray-500"><tr><th>Age</th><th>Mean</th><th># Estimates</th></tr></thead>
                      <tbody>
                        {priceTarget.priceTargetSnapshots.PriceTargetSnapshot.map((s, idx) => (
                          <tr key={idx} className="border-t"><td>{s.Age || s.age}</td><td>{fmtNumber(s.Mean ?? s.UnverifiedMean)}</td><td>{s.NumberOfEstimates ?? "-"}</td></tr>
                        ))}
                      </tbody>
                    </table>
                  ) : <div className="text-sm text-slate-400 mt-2">No snapshots</div>}
                </div>
              </>
            ) : <div className="text-sm text-slate-400">No analyst targets for this symbol.</div>}
          </Card>
        </div>

        <div>
          <Card>
            <div className="text-sm font-semibold mb-3">Mutual Funds & Commodities</div>

            <div>
              <div className="text-xs text-slate-500 mb-2">Mutual Funds (Large Cap sample)</div>
              {mutualFunds?.Equity?.["Large Cap"] ? mutualFunds.Equity["Large Cap"].slice(0, 6).map((f, i) => (
                <div key={i} className="flex justify-between text-sm mb-2"><div>{f.schemeName || f.fund_name}</div><div className="font-medium">{fmtNumber(f.latest_nav)}</div></div>
              )) : <div className="text-sm text-slate-400">No mutual funds snapshot</div>}
            </div>

            <div className="mt-4">
              <div className="text-xs text-slate-500 mb-2">Price Shockers</div>
              {priceShockers.length ? priceShockers.slice(0, 6).map((s) => (<div key={s.ticker} className="flex justify-between text-sm mb-2"><div>{s.company || s.ticker}</div><div className="font-medium">{fmtNumber(s.price)}</div></div>)) : <div className="text-sm text-slate-400">No shockers</div>}
            </div>

            <div className="mt-4">
              <div className="text-xs text-slate-500 mb-2">Commodities</div>
              {normalizedCommodities.length ? normalizedCommodities.slice(0, 6).map((c) => (<div key={c.id} className="flex justify-between text-sm mb-2"><div>{c.name}</div><div className="font-medium">{fmtNumber(c.lastTradedPrice)}</div></div>)) : <div className="text-sm text-slate-400">No commodities</div>}
            </div>
          </Card>
        </div>
      </div>

      {/* industry search / mutual fund search */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <Card>
          <div className="flex items-center justify-between mb-3"><div className="text-sm font-semibold">Industry Search</div><div className="text-xs text-slate-400">industry_search</div></div>
          <div className="flex gap-2">
            <input value={industryQuery} onChange={(e) => setIndustryQuery(e.target.value)} onKeyDown={(e) => e.key === "Enter" && doIndustrySearch(industryQuery)} className="flex-1 px-3 py-2 rounded-lg border" placeholder="Search industry (e.g. Technology)" />
            <button onClick={() => doIndustrySearch(industryQuery)} className="px-4 py-2 bg-indigo-600 text-white rounded-lg">Search</button>
          </div>

          <div className="mt-3">
            {industryResults.length ? industryResults.slice(0, 8).map((it) => (
              <div key={it.id} className="flex justify-between items-start p-2 border-b last:border-b-0">
                <div><div className="font-medium">{it.commonName}</div><div className="text-xs text-slate-500">{it.mgIndustry} • {it.mgSector}</div></div>
                <div className="text-right text-xs"><div>{it.exchangeCodeNsi || it.exchangeCodeNse || "-"}</div><div className="text-xs text-slate-400">{it.activeStockTrends?.overallRating}</div></div>
              </div>
            )) : <div className="text-sm text-slate-400">No industry results</div>}
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between mb-3"><div className="text-sm font-semibold">Mutual Fund Search</div><div className="text-xs text-slate-400">mutual_fund_search</div></div>
          <div className="flex gap-2">
            <input value={mfQuery} onChange={(e) => setMfQuery(e.target.value)} onKeyDown={(e) => e.key === "Enter" && doMfSearch(mfQuery)} className="flex-1 px-3 py-2 rounded-lg border" placeholder="Search mutual funds by name or ISIN" />
            <button onClick={() => doMfSearch(mfQuery)} className="px-4 py-2 bg-indigo-600 text-white rounded-lg">Search</button>
          </div>

          <div className="mt-3">
            {mfResults.length ? mfResults.slice(0, 8).map((m) => (
              <div key={m.id} className="flex justify-between items-start p-2 border-b last:border-b-0">
                <div><div className="font-medium">{m.schemeName || m.scheme_name}</div><div className="text-xs text-slate-500">{m.isin}</div></div>
                <div className="text-sm text-slate-600">{m.schemeType || m.scheme_type}</div>
              </div>
            )) : <div className="text-sm text-slate-400">No mutual fund results</div>}
          </div>
        </Card>
      </div>

      {/* sector heatmap — simplified, clear values */}
      <div className="mt-6">
        <Card>
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-semibold">Sector Heatmap</div>
            <div className="text-xs text-slate-400">Avg % move + counts (industry + movers)</div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {sectorTiles.length ? sectorTiles.slice(0, 12).map((s) => {
              const score = Math.max(-20, Math.min(20, Number(s.avgPct) || 0));
              const pct = Math.round(score * 100) / 100;
              const hue = Math.round((score + 20) * (120 / 40));
              const bg = `hsl(${hue}, 70%, 92%)`;
              const text = `hsl(${hue}, 70%, 20%)`;
              return (
                <div key={s.sector} className="p-3 rounded" style={{ background: bg, color: text }}>
                  <div className="text-sm font-semibold">{s.sector}</div>
                  <div className="text-xs mt-1">Count: {s.count}</div>
                  <div className="text-xs">Avg move: {fmtNumber(s.avgPct)}%</div>
                </div>
              );
            }) : <div className="text-sm text-slate-400">No sector data</div>}
          </div>
        </Card>
      </div>

      {error && (
        <div className="fixed right-6 bottom-6 bg-red-600 text-white p-3 rounded-lg shadow z-50">
          <div className="text-sm font-semibold">Error</div>
          <div className="text-xs mt-1 max-w-xs">{String(error)}</div>
          <div className="text-xs mt-2 opacity-80">Server errors: {serverErrorCount}</div>
        </div>
      )}
    </div>
  );
}

/* ------------------ helpers ------------------ */
function recommendationLabel(mean) {
  if (mean == null) return "—";
  const m = Number(mean);
  if (Number.isNaN(m)) return String(mean);
  const r = Math.round(m);
  switch (r) {
    case 1: return "Buy";
    case 2: return "Outperform";
    case 3: return "Hold";
    case 4: return "Underperform";
    case 5: return "Sell";
    default:
      if (m < 2) return "Buy";
      if (m < 3) return "Outperform";
      if (m < 4) return "Hold";
      return "Sell";
  }
}
