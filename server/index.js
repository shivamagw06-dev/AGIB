/**
 * server/index.js
 * Unified proxy for IndianAPI — full coverage + debug /__routes
 */
import express from "express";
import rateLimit from "express-rate-limit";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config();
const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const BASE_URL = "https://stock.indianapi.in";
const API_KEY = process.env.INDIANAPI_KEY || process.env.VITE_INDIANAPI_KEY || "";

if (!API_KEY) console.warn("⚠️ Missing INDIANAPI_KEY — add to Render env variables.");

// CORS - allow your frontend
const allowed = (process.env.FRONTEND_ORIGIN && process.env.FRONTEND_ORIGIN.split(",")) || [
  "https://agarwalglobalinvestments.com",
  "https://www.agarwalglobalinvestments.com",
];
app.use(cors({ origin: allowed, methods: ["GET", "OPTIONS"] }));

app.set("trust proxy", 1);
app.use("/api", rateLimit({ windowMs: 60 * 1000, max: 100 }));

function makeHeaders() {
  const h = {
    Accept: "application/json",
    "Content-Type": "application/json",
    "User-Agent": "AGIB-Proxy/1.0"
  };
  if (API_KEY) h["X-Api-Key"] = API_KEY;
  return h;
}

async function proxyFetch(res, url) {
  try {
    const r = await fetch(url, { headers: makeHeaders() });
    const text = await r.text();
    console.log(`[proxy] ${url} -> ${r.status}`);
    if (!text) return res.status(r.status).end();
    try {
      const json = JSON.parse(text);
      if (json && json.error) {
        console.error("[upstream error]", json.error);
        return res.status(502).json({ upstream_error: json.error, upstream_body: json });
      }
      return res.status(r.status).json(json);
    } catch {
      res.set("Content-Type", r.headers.get("content-type") || "text/plain");
      return res.status(r.status).send(text);
    }
  } catch (err) {
    console.error("🔥 proxyFetch failed:", err);
    return res.status(500).json({ error: "Proxy fetch failed", detail: err.message });
  }
}

// Trending cache (30s)
let trendingCache = null;
let trendingExpiry = 0;

// Health + debug
app.get("/", (req, res) => res.json({ service: "finance-news-backend", status: "running" }));
app.get("/api/health", (req, res) => res.json({ ok: true }));
app.get("/_debug_env", (req, res) => res.json({
  API_KEY_exists: !!process.env.INDIANAPI_KEY || !!process.env.VITE_INDIANAPI_KEY,
  FRONTEND_ORIGIN: process.env.FRONTEND_ORIGIN || null,
  PORT: process.env.PORT || null
}));

// Routes (documented endpoints)

// 1) /api/stock?name=...
app.get("/api/stock", (req, res) => {
  const name = req.query.name || req.query.symbol;
  if (!name) return res.status(400).json({ error: "Missing ?name" });
  return proxyFetch(res, `${BASE_URL}/stock?name=${encodeURIComponent(name)}`);
});

// 2) industry_search
app.get("/api/industry_search", (req, res) => {
  const q = req.query.query; if (!q) return res.status(400).json({ error: "Missing ?query" });
  return proxyFetch(res, `${BASE_URL}/industry_search?query=${encodeURIComponent(q)}`);
});

// 3) mutual_fund_search
app.get("/api/mutual_fund_search", (req, res) => {
  const q = req.query.query; if (!q) return res.status(400).json({ error: "Missing ?query" });
  return proxyFetch(res, `${BASE_URL}/mutual_fund_search?query=${encodeURIComponent(q)}`);
});

// 4) trending (cached + retry behavior)
app.get("/api/trending", async (req, res) => {
  const now = Date.now();
  if (trendingCache && now < trendingExpiry) return res.json(trendingCache);
  try {
    const r = await fetch(`${BASE_URL}/trending`, { headers: makeHeaders() });
    const data = await r.json();
    trendingCache = data; trendingExpiry = Date.now() + 30 * 1000;
    return res.json(data);
  } catch (err) {
    console.error("trending fetch failed:", err);
    if (trendingCache) return res.json(trendingCache);
    return res.status(502).json({ error: "Upstream trending error", detail: err.message });
  }
});

// 5) fetch_52_week_high_low_data
app.get("/api/fetch_52_week_high_low_data", (req, res) =>
  proxyFetch(res, `${BASE_URL}/fetch_52_week_high_low_data`)
);

// 6/7) NSE/BSE most active
app.get("/api/NSE_most_active", (req, res) => proxyFetch(res, `${BASE_URL}/NSE_most_active`));
app.get("/api/BSE_most_active", (req, res) => proxyFetch(res, `${BASE_URL}/BSE_most_active`));

// 8) mutual_funds
app.get("/api/mutual_funds", (req, res) => proxyFetch(res, `${BASE_URL}/mutual_funds`));

// 9) price_shockers
app.get("/api/price_shockers", (req, res) => proxyFetch(res, `${BASE_URL}/price_shockers`));

// 10) commodities
app.get("/api/commodities", (req, res) => proxyFetch(res, `${BASE_URL}/commodities`));

// 11) stock_target_price?stock_id=...
app.get("/api/stock_target_price", (req, res) => {
  const id = req.query.stock_id;
  if (!id) return res.status(400).json({ error: "Missing ?stock_id" });
  return proxyFetch(res, `${BASE_URL}/stock_target_price?stock_id=${encodeURIComponent(id)}`);
});

// 12) stock_forecasts (accepts any query params)
app.get("/api/stock_forecasts", (req, res) => {
  const params = new URLSearchParams(req.query);
  if (!params.has("measure_code") && !params.has("stock_id")) {
    // upstream may require certain params; we proactively validate common required ones
    // but we don't block — we'll forward anyway and surface upstream error
    console.log("[stock_forecasts] forwarded with params:", params.toString());
  }
  return proxyFetch(res, `${BASE_URL}/stock_forecasts?${params.toString()}`);
});

// 13) historical_data (accepts any query params)
app.get("/api/historical_data", (req, res) => {
  const params = new URLSearchParams(req.query);
  return proxyFetch(res, `${BASE_URL}/historical_data?${params.toString()}`);
});

// 14) historical_stats (accepts any query params)
app.get("/api/historical_stats", (req, res) => {
  const params = new URLSearchParams(req.query);
  return proxyFetch(res, `${BASE_URL}/historical_stats?${params.toString()}`);
});

// Extra simple endpoints (news, ipo, recent_announcements, corporate_actions, statement)
["news","ipo","recent_announcements","corporate_actions","statement"].forEach(ep => {
  app.get(`/api/${ep}`, (req, res) => proxyFetch(res, `${BASE_URL}/${ep}`));
});

// Debug: list registered routes
app.get("/__routes", (req, res) => {
  const routes = [];
  (app._router.stack || []).forEach(m => {
    if (m.route && m.route.path) {
      routes.push({ path: m.route.path, methods: Object.keys(m.route.methods).join(",") });
    } else if (m.name === "router" && m.handle && m.handle.stack) {
      m.handle.stack.forEach(r => { if (r.route) routes.push({ path: r.route.path, methods: Object.keys(r.route.methods).join(",") }); });
    }
  });
  res.json(routes);
});

// fallback
app.use((req, res) => res.status(404).json({ error: "Not found", path: req.path }));

app.listen(PORT, () => {
  console.log(`🚀 IndianAPI Proxy running on port ${PORT} — Base: ${BASE_URL}`);
});