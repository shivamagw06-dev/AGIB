/**
 * server/index.js
 * IndianAPI proxy — explicit routes + wildcard fallback + route debug
 *
 * Notes:
 * - Reads INDIANAPI_KEY or VITE_INDIANAPI_KEY from env.
 * - Adds explicit endpoints + wildcard /api/:path(*) passthrough.
 * - Adds /indianapi/:path(*) passthrough to match frontend fallbacks.
 * - Minimal 30s cache for /api/trending.
 * - Validates stock_forecasts requires stock_id to avoid upstream 422s.
 */

import express from "express";
import rateLimit from "express-rate-limit";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config();

const app = express();
app.use(express.json());

// Config
const PORT = process.env.PORT || 3000;
const BASE_URL = "https://stock.indianapi.in";
const API_KEY = process.env.INDIANAPI_KEY || process.env.VITE_INDIANAPI_KEY || "";

if (!API_KEY) console.warn("⚠️ Missing INDIANAPI_KEY — set in env (Render/local).");

// CORS: allow configured frontend(s) or permissive for server/curl
const allowedOrigins = (process.env.FRONTEND_ORIGIN && process.env.FRONTEND_ORIGIN.split(",").map(s => s.trim())) || [
  "https://agarwalglobalinvestments.com",
  "https://www.agarwalglobalinvestments.com",
  "*"
];

app.use(cors({
  origin: (origin, cb) => {
    // allow non-browser requests with no origin (curl, server-to-server)
    if (!origin) return cb(null, true);
    if (allowedOrigins.includes("*") || allowedOrigins.includes(origin)) return cb(null, true);
    return cb(new Error("CORS blocked"));
  },
  methods: ["GET", "OPTIONS"]
}));

app.set("trust proxy", 1);
app.use("/api", rateLimit({ windowMs: 60 * 1000, max: 100 }));

// Build headers for upstream; include common forms but don't log them
function makeHeaders() {
  const h = {
    Accept: "application/json",
    "Content-Type": "application/json",
    "User-Agent": "AGIB-Proxy/1.0"
  };
  if (API_KEY) {
    // include both common header forms + Bearer authorization
    h["x-api-key"] = API_KEY;
    h["X-Api-Key"] = API_KEY;
    h["Authorization"] = `Bearer ${API_KEY}`;
  }
  return h;
}

// Generic proxy to upstream with careful parsing + upstream-error handling
async function proxyFetch(res, url) {
  try {
    console.log(`[proxy] -> ${url}`);
    const r = await fetch(url, { headers: makeHeaders() });
    const ct = r.headers.get("content-type") || "";
    let text = "";
    try { text = await r.text(); } catch { text = ""; }

    console.log(`[proxy] ${url} returned ${r.status} content-type:${ct}`);

    if (!text) {
      return res.status(r.status).end();
    }

    // Try parse JSON, handle upstream {"error": ...} shape
    try {
      const json = JSON.parse(text);
      if (json && (json.error || json.upstream_error)) {
        console.error("[upstream error]", json.error || json.upstream_error);
        // show upstream error as 502 for clarity, including the upstream body (not API key)
        return res.status(502).json({ upstream_error: json.error || json.upstream_error, upstream_body: json });
      }
      return res.status(r.status).json(json);
    } catch (e) {
      // Not JSON — forward as text/html or plain text
      res.set("Content-Type", ct || "text/plain");
      return res.status(r.status).send(text);
    }
  } catch (err) {
    console.error("🔥 proxyFetch failed:", err?.message || String(err));
    return res.status(500).json({ error: "Proxy fetch failed", detail: err?.message || String(err) });
  }
}

// small trending cache
let trendingCache = null;
let trendingExpiry = 0;

function reg(path, handler) {
  app.get(path, handler);
  console.log("[route registered]", path);
}

/* ===== health & debug ===== */
reg("/", (req, res) => res.json({ service: "finance-news-backend", status: "running" }));
reg("/api/health", (req, res) => res.json({ ok: true }));
reg("/_debug_env", (req, res) => res.json({
  API_KEY_exists: !!process.env.INDIANAPI_KEY || !!process.env.VITE_INDIANAPI_KEY,
  FRONTEND_ORIGIN: process.env.FRONTEND_ORIGIN || null,
  PORT: process.env.PORT || null
}));

/* ===== explicit API endpoints ===== */

// /api/stock?name=...
reg("/api/stock", (req, res) => {
  const q = req.query.name || req.query.symbol;
  if (!q) return res.status(400).json({ error: "Missing ?name or ?symbol" });
  return proxyFetch(res, `${BASE_URL}/stock?name=${encodeURIComponent(q)}`);
});

// /api/industry_search?query=...
reg("/api/industry_search", (req, res) => {
  const q = req.query.query;
  if (!q) return res.status(400).json({ error: "Missing ?query" });
  return proxyFetch(res, `${BASE_URL}/industry_search?query=${encodeURIComponent(q)}`);
});

// /api/mutual_fund_search?query=...
reg("/api/mutual_fund_search", (req, res) => {
  const q = req.query.query;
  if (!q) return res.status(400).json({ error: "Missing ?query" });
  return proxyFetch(res, `${BASE_URL}/mutual_fund_search?query=${encodeURIComponent(q)}`);
});

// /api/trending (cached for 30s)
reg("/api/trending", async (req, res) => {
  const now = Date.now();
  if (trendingCache && now < trendingExpiry) {
    console.log("[trending] returning cache");
    return res.json(trendingCache);
  }
  try {
    const r = await fetch(`${BASE_URL}/trending`, { headers: makeHeaders() });
    const json = await r.json();
    trendingCache = json;
    trendingExpiry = Date.now() + 30_000;
    return res.status(r.status).json(json);
  } catch (err) {
    console.error("trending fetch failed:", err?.message || String(err));
    if (trendingCache) return res.json({ data: trendingCache, upstream_issue: true });
    return res.status(502).json({ error: "Upstream trending error", detail: err?.message || String(err) });
  }
});

// /api/fetch_52_week_high_low_data
reg("/api/fetch_52_week_high_low_data", (req, res) => proxyFetch(res, `${BASE_URL}/fetch_52_week_high_low_data`));

// NSE / BSE most active
reg("/api/NSE_most_active", (req, res) => proxyFetch(res, `${BASE_URL}/NSE_most_active`));
reg("/api/BSE_most_active", (req, res) => proxyFetch(res, `${BASE_URL}/BSE_most_active`));

// mutual_funds
reg("/api/mutual_funds", (req, res) => proxyFetch(res, `${BASE_URL}/mutual_funds`));

// price_shockers
reg("/api/price_shockers", (req, res) => proxyFetch(res, `${BASE_URL}/price_shockers`));

// commodities
reg("/api/commodities", (req, res) => proxyFetch(res, `${BASE_URL}/commodities`));

// stock_target_price?stock_id=...
reg("/api/stock_target_price", (req, res) => {
  const id = req.query.stock_id;
  if (!id) return res.status(400).json({ error: "Missing ?stock_id" });
  return proxyFetch(res, `${BASE_URL}/stock_target_price?stock_id=${encodeURIComponent(id)}`);
});

// stock_forecasts - require stock_id to avoid upstream 422s
reg("/api/stock_forecasts", (req, res) => {
  const params = new URLSearchParams(req.query);
  if (!params.has("stock_id")) {
    return res.status(400).json({ error: "Missing required ?stock_id (avoid upstream 422)" });
  }
  return proxyFetch(res, `${BASE_URL}/stock_forecasts?${params.toString()}`);
});

// historical endpoints (pass through query)
reg("/api/historical_data", (req, res) => proxyFetch(res, `${BASE_URL}/historical_data?${new URLSearchParams(req.query).toString()}`));
reg("/api/historical_stats", (req, res) => proxyFetch(res, `${BASE_URL}/historical_stats?${new URLSearchParams(req.query).toString()}`));

// news / ipo / related
reg("/api/news", (req, res) => proxyFetch(res, `${BASE_URL}/news`));
reg("/api/ipo", (req, res) => proxyFetch(res, `${BASE_URL}/ipo`));
reg("/api/recent_announcements", (req, res) => proxyFetch(res, `${BASE_URL}/recent_announcements`));
reg("/api/corporate_actions", (req, res) => proxyFetch(res, `${BASE_URL}/corporate_actions`));
reg("/api/statement", (req, res) => proxyFetch(res, `${BASE_URL}/statement`));

/**
 * Wildcard fallback for /api/*
 * Forward to upstream if we don't have an explicit mapping above.
 */
reg("/api/:path(*)", (req, res) => {
  const path = req.params.path || "";
  const qs = new URLSearchParams(req.query).toString();
  const upstream = `${BASE_URL}/${path}${qs ? `?${qs}` : ""}`;
  console.log(`[wildcard proxy] /api/${path} -> ${upstream}`);
  return proxyFetch(res, upstream);
});

/**
 * Frontend fallback: /indianapi/* (some clients try this)
 * Mirrors the wildcard above so frontend fallbacks succeed.
 */
reg("/indianapi/:path(*)", (req, res) => {
  const path = req.params.path || "";
  const qs = new URLSearchParams(req.query).toString();
  const upstream = `${BASE_URL}/${path}${qs ? `?${qs}` : ""}`;
  console.log(`[indianapi passthrough] /indianapi/${path} -> ${upstream}`);
  return proxyFetch(res, upstream);
});

// __routes debug listing (lightweight)
reg("/__routes", (req, res) => {
  const routes = [];
  (app._router.stack || []).forEach(layer => {
    if (layer.route && layer.route.path) {
      routes.push({ path: layer.route.path, methods: Object.keys(layer.route.methods).join(",") });
    }
  });
  res.json(routes);
});

// fallback 404
app.use((req, res) => res.status(404).json({ error: "Not found", path: req.path }));

app.listen(PORT, () => {
  console.log(`🚀 IndianAPI Proxy running on port ${PORT} — Base: ${BASE_URL}`);
});
