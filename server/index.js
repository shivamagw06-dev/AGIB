/**
 * server/index.js
 * IndianAPI proxy — robust headers, trimmed key, masked-key debug
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

// trim to avoid stray newline/quotes problems
const API_KEY_RAW = process.env.INDIANAPI_KEY || process.env.VITE_INDIANAPI_KEY || "";
const API_KEY = typeof API_KEY_RAW === "string" ? API_KEY_RAW.trim() : "";

if (!API_KEY) console.warn("⚠️ Missing INDIANAPI_KEY — set in env (Render/local).");

// CORS: allow configured frontend OR fallback to *
const allowed = (process.env.FRONTEND_ORIGIN && process.env.FRONTEND_ORIGIN.split(",").map(s => s.trim())) || [
  "https://agarwalglobalinvestments.com",
  "https://www.agarwalglobalinvestments.com",
  "*"
];
app.use(cors({ origin: (origin, cb) => {
  if (!origin) return cb(null, true);
  if (allowed.includes("*") || allowed.includes(origin)) return cb(null, true);
  return cb(null, false);
}, methods: ["GET","OPTIONS"] }));

app.set("trust proxy", 1);
app.use("/api", rateLimit({ windowMs: 60 * 1000, max: 100 }));

function makeHeaders() {
  const h = {
    Accept: "application/json",
    "Content-Type": "application/json",
    "User-Agent": "AGIB-Proxy/1.0"
  };
  // IndianAPI accepts header 'x-api-key' — use lowercase and a single header.
  if (API_KEY) h["x-api-key"] = API_KEY;
  return h;
}

async function proxyFetch(res, url) {
  try {
    console.log(`[proxy] -> ${url}`);
    const r = await fetch(url, { headers: makeHeaders() });
    const ct = r.headers.get("content-type") || "";
    // read raw text for robust logging and parsing
    const text = await r.text().catch(() => "");
    console.log(`[proxy] ${url} returned ${r.status} content-type:${ct} length:${String(text?.length || 0)}`);
    if (!text) return res.status(r.status).end();

    // upstream may return plain text (e.g. "Invalid API key") — log and forward intelligently
    if (r.status === 401 || r.status === 402 || r.status === 403) {
      console.error(`[proxy][upstream ${r.status}] ${text.slice(0, 200)}`);
    }

    try {
      const json = JSON.parse(text);
      if (json && (json.error || json.upstream_error)) {
        console.error("[upstream error]", json.error || json.upstream_error);
        return res.status(502).json({ upstream_error: json.error || json.upstream_error, upstream_body: json });
      }
      return res.status(r.status).json(json);
    } catch (e) {
      // non-json payload (HTML/text) - forward content type and body
      res.set("Content-Type", ct || "text/plain");
      // if upstream said "Invalid API key" return 401 to caller (helpful)
      if (r.status === 401) {
        return res.status(401).send(text);
      }
      return res.status(r.status).send(text);
    }
  } catch (err) {
    console.error("🔥 proxyFetch failed:", err?.message || err);
    return res.status(500).json({ error: "Proxy fetch failed", detail: err?.message || String(err) });
  }
}

// trending cache (30s)
let trendingCache = null;
let trendingExpiry = 0;

function reg(path, handler) {
  app.get(path, handler);
  console.log("[route registered]", path);
}

/* Health + debug */
reg("/", (req, res) => res.json({ service: "finance-news-backend", status: "running" }));
reg("/api/health", (req, res) => res.json({ ok: true }));
reg("/_debug_env", (req, res) => res.json({
  API_KEY_exists: !!API_KEY,
  FRONTEND_ORIGIN: process.env.FRONTEND_ORIGIN || null,
  PORT: process.env.PORT || null
}));

// Temporary masked key debug — shows only first 6 chars if present. REMOVE after verification.
reg("/_debug_key", (req, res) => {
  if (!API_KEY) return res.json({ key_present: false });
  return res.json({ key_present: true, masked: `${API_KEY.slice(0,6)}... (length ${API_KEY.length})` });
});

/* Explicit endpoints (same as earlier) */
reg("/api/stock", (req, res) => {
  const q = req.query.name || req.query.symbol;
  if (!q) return res.status(400).json({ error: "Missing ?name or ?symbol" });
  return proxyFetch(res, `${BASE_URL}/stock?name=${encodeURIComponent(q)}`);
});

reg("/api/industry_search", (req, res) => {
  const q = req.query.query; if (!q) return res.status(400).json({ error: "Missing ?query" });
  return proxyFetch(res, `${BASE_URL}/industry_search?query=${encodeURIComponent(q)}`);
});

reg("/api/mutual_fund_search", (req, res) => {
  const q = req.query.query; if (!q) return res.status(400).json({ error: "Missing ?query" });
  return proxyFetch(res, `${BASE_URL}/mutual_fund_search?query=${encodeURIComponent(q)}`);
});

reg("/api/trending", async (req, res) => {
  const now = Date.now();
  if (trendingCache && now < trendingExpiry) return res.json(trendingCache);
  try {
    const r = await fetch(`${BASE_URL}/trending`, { headers: makeHeaders() });
    const text = await r.text().catch(() => "");
    try {
      const json = JSON.parse(text);
      trendingCache = json;
      trendingExpiry = Date.now() + 30_000;
      return res.status(r.status).json(json);
    } catch {
      // non-json
      if (text) return res.status(r.status).send(text);
      return res.status(502).json({ error: "Invalid trending response" });
    }
  } catch (err) {
    console.error("trending fetch failed:", err?.message || err);
    if (trendingCache) return res.json({ data: trendingCache, upstream_issue: true });
    return res.status(502).json({ error: "Upstream trending error", detail: err?.message || String(err) });
  }
});

reg("/api/fetch_52_week_high_low_data", (req, res) => proxyFetch(res, `${BASE_URL}/fetch_52_week_high_low_data`));
reg("/api/NSE_most_active", (req, res) => proxyFetch(res, `${BASE_URL}/NSE_most_active`));
reg("/api/BSE_most_active", (req, res) => proxyFetch(res, `${BASE_URL}/BSE_most_active`));
reg("/api/mutual_funds", (req, res) => proxyFetch(res, `${BASE_URL}/mutual_funds`));
reg("/api/price_shockers", (req, res) => proxyFetch(res, `${BASE_URL}/price_shockers`));
reg("/api/commodities", (req, res) => proxyFetch(res, `${BASE_URL}/commodities`));

reg("/api/stock_target_price", (req, res) => {
  const id = req.query.stock_id;
  if (!id) return res.status(400).json({ error: "Missing ?stock_id" });
  return proxyFetch(res, `${BASE_URL}/stock_target_price?stock_id=${encodeURIComponent(id)}`);
});

reg("/api/stock_forecasts", (req, res) => {
  const params = new URLSearchParams(req.query);
  // upstream returns 422 if stock_id missing — be explicit
  if (!params.has("stock_id")) return res.status(400).json({ error: "Missing required ?stock_id" });
  return proxyFetch(res, `${BASE_URL}/stock_forecasts?${params.toString()}`);
});

reg("/api/historical_data", (req, res) => proxyFetch(res, `${BASE_URL}/historical_data?${new URLSearchParams(req.query).toString()}`));
reg("/api/historical_stats", (req, res) => proxyFetch(res, `${BASE_URL}/historical_stats?${new URLSearchParams(req.query).toString()}`));

reg("/api/news", (req, res) => proxyFetch(res, `${BASE_URL}/news`));
reg("/api/ipo", (req, res) => proxyFetch(res, `${BASE_URL}/ipo`));
reg("/api/recent_announcements", (req, res) => proxyFetch(res, `${BASE_URL}/recent_announcements`));
reg("/api/corporate_actions", (req, res) => proxyFetch(res, `${BASE_URL}/corporate_actions`));
reg("/api/statement", (req, res) => proxyFetch(res, `${BASE_URL}/statement`));

// Wildcard fallback for any other /api/<path>
reg("/api/:path(*)", (req, res) => {
  const path = req.params.path;
  const qs = new URLSearchParams(req.query).toString();
  const upstream = `${BASE_URL}/${path}${qs ? `?${qs}` : ""}`;
  console.log(`[wildcard proxy] /api/${path} -> ${upstream}`);
  return proxyFetch(res, upstream);
});

// __routes dump
reg("/__routes", (req, res) => {
  const routes = [];
  (app._router.stack || []).forEach(layer => {
    if (layer.route && layer.route.path) {
      routes.push({ path: layer.route.path, methods: Object.keys(layer.route.methods).join(",") });
    }
  });
  res.json(routes);
});

// fallback
app.use((req, res) => res.status(404).json({ error: "Not found", path: req.path }));

app.listen(PORT, () => {
  console.log(`🚀 IndianAPI Proxy running on port ${PORT} — Base: ${BASE_URL}`);
});
