// server/index.js
/**
 * Unified Express Proxy for IndianAPI (Full Coverage)
 * Shivam's version — covers all known endpoints (July 2024 doc)
 * Backend: Render (Node/Express)
 * Frontend: Hostinger (CORS allowed)
 */

import express from "express";
import rateLimit from "express-rate-limit";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config();
const app = express();
app.use(express.json());

// --- CONFIG ---
const PORT = process.env.PORT || 3000;
const BASE_URL = "https://stock.indianapi.in";
const API_KEY = process.env.INDIANAPI_KEY || process.env.VITE_INDIANAPI_KEY || "";

if (!API_KEY)
  console.warn("⚠️ Missing INDIANAPI_KEY — requests will fail until key is added to Render.");

// --- MIDDLEWARE ---
app.use(
  cors({
    origin: process.env.FRONTEND_ORIGIN || [
      "https://agarwalglobalinvestments.com",
      "https://www.agarwalglobalinvestments.com",
    ],
    methods: ["GET", "OPTIONS"],
  })
);

app.set("trust proxy", 1);
app.use("/api", rateLimit({ windowMs: 60 * 1000, max: 100 }));

// --- HELPERS ---
function makeHeaders() {
  return {
    Accept: "application/json",
    "Content-Type": "application/json",
    "X-Api-Key": API_KEY,
    "User-Agent": "AGIB-Proxy/1.0",
  };
}

async function proxyFetch(res, url) {
  try {
    const response = await fetch(url, { headers: makeHeaders() });
    const text = await response.text();
    console.log(`[Proxy] ${url} -> ${response.status}`);

    // empty body
    if (!text) return res.status(response.status).end();

    try {
      const json = JSON.parse(text);
      if (json.error) {
        console.error("[Upstream error]", json.error);
        return res.status(502).json({ upstream_error: json.error, body: json });
      }
      return res.status(response.status).json(json);
    } catch {
      res.set("Content-Type", response.headers.get("content-type") || "text/plain");
      return res.status(response.status).send(text);
    }
  } catch (err) {
    console.error("🔥 Fetch failed:", err);
    return res.status(500).json({ error: "Proxy fetch failed", message: err.message });
  }
}

// Cache for /trending (30 seconds)
let trendingCache = null;
let trendingExpiry = 0;

// --- HEALTH ---
app.get("/", (req, res) => res.json({ service: "finance-news-backend", status: "running" }));
app.get("/api/health", (req, res) => res.json({ ok: true }));

// --- CORE PROXY ROUTES ---

// 1. Stock by name
app.get("/api/stock", (req, res) => {
  const name = req.query.name || req.query.symbol;
  if (!name) return res.status(400).json({ error: "Missing ?name" });
  return proxyFetch(res, `${BASE_URL}/stock?name=${encodeURIComponent(name)}`);
});

// 2. Industry search
app.get("/api/industry_search", (req, res) => {
  const q = req.query.query;
  if (!q) return res.status(400).json({ error: "Missing ?query" });
  return proxyFetch(res, `${BASE_URL}/industry_search?query=${encodeURIComponent(q)}`);
});

// 3. Mutual fund search
app.get("/api/mutual_fund_search", (req, res) => {
  const q = req.query.query;
  if (!q) return res.status(400).json({ error: "Missing ?query" });
  return proxyFetch(res, `${BASE_URL}/mutual_fund_search?query=${encodeURIComponent(q)}`);
});

// 4. Trending (cached)
app.get("/api/trending", async (req, res) => {
  const now = Date.now();
  if (trendingCache && now < trendingExpiry) {
    console.log("[Cache hit] trending");
    return res.json(trendingCache);
  }

  try {
    const response = await fetch(`${BASE_URL}/trending`, { headers: makeHeaders() });
    const data = await response.json();
    trendingCache = data;
    trendingExpiry = Date.now() + 30 * 1000;
    res.json(data);
  } catch (err) {
    console.error("Trending fetch failed:", err);
    if (trendingCache) return res.json(trendingCache);
    res.status(502).json({ error: "Upstream error", detail: err.message });
  }
});

// 5. 52-week highs/lows
app.get("/api/fetch_52_week_high_low_data", (req, res) =>
  proxyFetch(res, `${BASE_URL}/fetch_52_week_high_low_data`)
);

// 6–7. NSE/BSE most active
app.get("/api/NSE_most_active", (req, res) =>
  proxyFetch(res, `${BASE_URL}/NSE_most_active`)
);
app.get("/api/BSE_most_active", (req, res) =>
  proxyFetch(res, `${BASE_URL}/BSE_most_active`)
);

// 8. Mutual funds
app.get("/api/mutual_funds", (req, res) =>
  proxyFetch(res, `${BASE_URL}/mutual_funds`)
);

// 9. Price shockers
app.get("/api/price_shockers", (req, res) =>
  proxyFetch(res, `${BASE_URL}/price_shockers`)
);

// 10. Commodities
app.get("/api/commodities", (req, res) =>
  proxyFetch(res, `${BASE_URL}/commodities`)
);

// 11. Analyst recommendations
app.get("/api/stock_target_price", (req, res) => {
  const id = req.query.stock_id;
  if (!id) return res.status(400).json({ error: "Missing ?stock_id" });
  return proxyFetch(res, `${BASE_URL}/stock_target_price?stock_id=${encodeURIComponent(id)}`);
});

// 12. Stock forecasts
app.get("/api/stock_forecasts", (req, res) => {
  const params = new URLSearchParams(req.query);
  return proxyFetch(res, `${BASE_URL}/stock_forecasts?${params}`);
});

// 13. Historical data
app.get("/api/historical_data", (req, res) => {
  const params = new URLSearchParams(req.query);
  return proxyFetch(res, `${BASE_URL}/historical_data?${params}`);
});

// 14. Historical stats
app.get("/api/historical_stats", (req, res) => {
  const params = new URLSearchParams(req.query);
  return proxyFetch(res, `${BASE_URL}/historical_stats?${params}`);
});

// Extra: /news, /ipo, /recent_announcements, /corporate_actions, /statement
["news", "ipo", "recent_announcements", "corporate_actions", "statement"].forEach((ep) => {
  app.get(`/api/${ep}`, (req, res) => proxyFetch(res, `${BASE_URL}/${ep}`));
});

// --- FALLBACK 404 ---
app.use((req, res) => res.status(404).json({ error: "Not found", path: req.path }));

// --- START SERVER ---
app.listen(PORT, () => {
  console.log(`🚀 IndianAPI Proxy running on port ${PORT}`);
  console.log(`Base URL: ${BASE_URL}`);
});
