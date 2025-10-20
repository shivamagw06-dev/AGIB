// server/index.js
/**
 * IndianAPI proxy + research router
 *
 * - mounts ./research.js at /research
 * - provides /api/* proxy endpoints to IndianAPI
 * - robust headers / JSON parsing / error handling
 * - small caching for /api/trending
 *
 * Notes:
 * - ensure .env contains INDIANAPI_KEY (server-side) and FRONTEND_ORIGIN if you want restricted CORS
 * - research.js should export an Express Router (default export)
 *
 * This file uses top-level await to load `node-fetch` only if global fetch is not available.
 */

import express from "express";
import researchRouter from "./research.js";
import rateLimit from "express-rate-limit";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config();

// Prefer global fetch (Node 18+). Fallback to node-fetch if global not present.
let fetchImpl;
if (typeof globalThis.fetch === "function") {
  fetchImpl = globalThis.fetch.bind(globalThis);
} else {
  // dynamic import of node-fetch (only when needed)
  // top-level await is used here; ensure Node environment supports ESM + top-level await.
  const nf = await import("node-fetch");
  fetchImpl = nf.default;
}

const app = express();
app.use(express.json({ limit: "200kb" }));

const PORT = process.env.PORT ? Number(process.env.PORT) : 3000;
const BASE_URL = process.env.INDIANAPI_BASE || "https://stock.indianapi.in";

// API key (server-side only)
const API_KEY_RAW = process.env.INDIANAPI_KEY || process.env.VITE_INDIANAPI_KEY || "";
const API_KEY = typeof API_KEY_RAW === "string" ? API_KEY_RAW.trim() : "";

if (!API_KEY) console.warn("⚠️ Missing INDIANAPI_KEY — set INDIANAPI_KEY in your environment.");

// Perplexity config (server-side only)
const PERPLEXITY_KEY_RAW = process.env.PERPLEXITY_KEY || process.env.PERPLEXITY_API_KEY || process.env.VITE_PERPLEXITY_KEY || "";
const PERPLEXITY_KEY = typeof PERPLEXITY_KEY_RAW === "string" ? PERPLEXITY_KEY_RAW.trim() : "";
const PERPLEXITY_URL = process.env.PERPLEXITY_URL || "https://api.perplexity.ai/chat/completions";

if (!PERPLEXITY_KEY) console.warn("⚠️ Missing PERPLEXITY_KEY — set PERPLEXITY_KEY in your environment to enable Perplexity features.");

// CORS configuration: allow configured frontend OR fallback to permissive
const rawAllowed = (process.env.FRONTEND_ORIGIN || "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);

const allowed = rawAllowed.length
  ? rawAllowed
  : [
      "https://agarwalglobalinvestments.com",
      "https://www.agarwalglobalinvestments.com",
      "*", // fallback permissive; remove if you want to restrict
    ];

app.use(
  cors({
    origin: (origin, cb) => {
      // allow server-to-server & curl requests with no origin
      if (!origin) return cb(null, true);
      if (allowed.includes("*") || allowed.includes(origin)) return cb(null, true);
      return cb(new Error("CORS origin not allowed"));
    },
    methods: ["GET", "POST", "OPTIONS"],
    optionsSuccessStatus: 200,
  })
);

app.set("trust proxy", 1);

// Rate limiter for API routes
const apiLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 120, // increase for your needs
  standardHeaders: true,
  legacyHeaders: false,
});
app.use("/api", apiLimiter);

// Optionally rate limit research endpoint more strictly
const researchLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 30,
  standardHeaders: true,
  legacyHeaders: false,
});
app.use("/research", researchLimiter);

// Helper to build headers for IndianAPI
function makeHeaders() {
  const h = {
    Accept: "application/json",
    "Content-Type": "application/json",
    "User-Agent": "AGIB-Proxy/1.0",
  };
  if (API_KEY) h["x-api-key"] = API_KEY;
  return h;
}

/**
 * proxyFetch: centralised fetch + parse logic
 * - logs upstream response
 * - forwards JSON bodies preserving upstream status
 * - maps upstream errors into JSON with context
 *
 * Note: we avoid passing unsupported fetch options (like `timeout`) directly.
 */
async function proxyFetch(res, url, opts = {}) {
  try {
    console.log(`[proxy] -> ${url}`);
    const r = await fetchImpl(url, {
      method: opts.method || "GET",
      headers: opts.headers || makeHeaders(),
      body: opts.body,
    });

    const ct = r.headers.get("content-type") || "";
    const text = await r.text().catch(() => "");

    console.log(`[proxy] ${url} returned ${r.status} content-type:${ct} length:${String(text?.length || 0)}`);

    // no body
    if (!text) return res.status(r.status).end();

    // Auth errors: log and forward raw
    if ([401, 402, 403].includes(r.status)) {
      console.error(`[proxy][upstream ${r.status}] ${text.slice(0, 200)}`);
      res.set("Content-Type", ct || "text/plain");
      return res.status(r.status).send(text);
    }

    // JSON content-type -> try parse
    if (ct.includes("application/json") || ct.includes("+json")) {
      try {
        const json = JSON.parse(text);
        if (json && (json.error || json.upstream_error)) {
          console.error("[proxy][upstream error]", json.error || json.upstream_error);
          return res.status(502).json({ upstream_error: json.error || json.upstream_error, upstream_body: json });
        }
        return res.status(r.status).json(json);
      } catch (parseErr) {
        console.error("[proxy] failed to parse JSON from upstream", parseErr?.message || parseErr);
        res.set("Content-Type", ct || "application/json");
        return res.status(502).send(text);
      }
    }

    // Fallback: send raw text with upstream status
    res.set("Content-Type", ct || "text/plain");
    return res.status(r.status).send(text);
  } catch (err) {
    console.error("🔥 proxyFetch failed:", err?.message || err);
    return res.status(500).json({ error: "Proxy fetch failed", detail: err?.message || String(err) });
  }
}

// --- small in-memory trending cache (30s) ---
let trendingCache = null;
let trendingExpiry = 0;

// helper to register simple GET routes (for logging)
function reg(path, handler) {
  app.get(path, handler);
  console.log("[route registered]", path);
}

/* Health + debug endpoints */
reg("/", (req, res) => res.json({ service: "finance-news-backend", status: "running" }));
reg("/api/health", (req, res) => res.json({ ok: true }));

reg("/_debug_env", (req, res) =>
  res.json({
    API_KEY_exists: !!API_KEY,
    PERPLEXITY_key_present: !!PERPLEXITY_KEY,
    FRONTEND_ORIGIN: process.env.FRONTEND_ORIGIN || null,
    PORT: process.env.PORT || null,
  })
);

reg("/_debug_key", (req, res) => {
  if (!API_KEY) return res.json({ key_present: false });
  return res.json({ key_present: true, masked: `${API_KEY.slice(0, 6)}... (length ${API_KEY.length})` });
});

/* Mount research router (you provided research.js) */
app.use("/research", researchRouter);

/* --- Perplexity proxy endpoint --- */
/**
 * GET /api/perplexity/deals?region=global&limit=8
 * Note: requires PERPLEXITY_KEY env var on server.
 */
reg("/api/perplexity/deals", async (req, res) => {
  try {
    const region = req.query.region || "global";
    const limit = Math.min(50, Number(req.query.limit || 8));
    if (!PERPLEXITY_KEY) return res.status(500).json({ error: "Missing PERPLEXITY_KEY on server." });

    const prompt = `
Return a JSON array (max ${limit}) of recent M&A / PE deals for region: ${region}.
Each object must have these fields: acquirer, target, value, sector, region, date (ISO), source, type.
Respond ONLY with a valid JSON array.
    `.trim();

    const body = {
      model: "sonar",
      messages: [
        { role: "system", content: "You are a factual research assistant." },
        { role: "user", content: prompt },
      ],
      temperature: 0.1,
      max_tokens: 800,
    };

    const pRes = await fetchImpl(PERPLEXITY_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${PERPLEXITY_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const text = await pRes.text();
    if (!pRes.ok) {
      console.error("[perplexity] upstream error:", pRes.status, text.slice(0, 400));
      return res.status(502).json({ error: "Perplexity API error", detail: text });
    }

    // Try parse JSON strictly; if that fails, attempt to extract first JSON array substring
    let parsed = null;
    try {
      parsed = JSON.parse(text);
    } catch (e) {
      const match = text.match(/\[.*\]/s);
      if (match) {
        try {
          parsed = JSON.parse(match[0]);
        } catch (ee) {
          parsed = null;
        }
      }
    }

    // If parsing failed, return raw text so dev can debug
    if (!Array.isArray(parsed)) {
      return res.status(200).json({ parsed: null, raw: text });
    }

    // Normalize & cap
    const normalized = parsed.slice(0, limit).map((it) => ({
      acquirer: it.acquirer ?? it.buyer ?? null,
      target: it.target ?? it.company ?? null,
      value: it.value ?? null,
      sector: it.sector ?? null,
      region: it.region ?? region,
      date: it.date ?? new Date().toISOString(),
      source: it.source ?? null,
      type: it.type ?? "M&A",
    }));

    return res.json(normalized);
  } catch (err) {
    console.error("Perplexity proxy failed:", err);
    return res.status(500).json({ error: "Internal server error", detail: err?.message || String(err) });
  }
});

/* --- IndianAPI proxy endpoints --- */

/**
 * /api/quote
 * Attempts multiple upstream endpoints and returns a normalized object:
 * { currentPrice, percentChange, volume, prevClose, openPrice, dayRange, raw }
 */
reg("/api/quote", async (req, res) => {
  try {
    const symbol = req.query.symbol || req.query.name;
    if (!symbol) return res.status(400).json({ error: "Missing ?symbol or ?name" });

    const candidates = [
      `${BASE_URL}/stock?name=${encodeURIComponent(symbol)}`,
      `${BASE_URL}/stock?symbol=${encodeURIComponent(symbol)}`,
      `${BASE_URL}/quote?symbol=${encodeURIComponent(symbol)}`,
    ];

    let lastErr = null;
    for (const url of candidates) {
      try {
        const r = await fetchImpl(url, { method: "GET", headers: makeHeaders() });
        const ct = r.headers.get("content-type") || "";
        const text = await r.text().catch(() => "");
        if (!text) {
          lastErr = new Error(`empty upstream response ${r.status} from ${url}`);
          continue;
        }

        if (!r.ok) {
          lastErr = new Error(`${r.status} : ${text}`);
          // try next candidate for 4xx; for 5xx forward raw
          if (r.status >= 500) {
            res.set("Content-Type", ct || "text/plain");
            return res.status(r.status).send(text);
          }
          continue;
        }

        if (ct.includes("json") || ct.includes("+json")) {
          let json;
          try {
            json = JSON.parse(text);
          } catch (e) {
            // return raw text if JSON parse fails
            res.set("Content-Type", ct || "text/plain");
            return res.status(200).send(text);
          }

          // Normalize keys
          const cp = json.currentPrice ?? json.current_price ?? json.price ?? json.last_price ?? json.lastTradedPrice ?? null;
          const percent = json.percentChange ?? json.changePercent ?? json.percent_change ?? json.percent ?? json.change ?? null;
          const volume = json.volume ?? json.totalVolume ?? json.v ?? null;
          const prevClose = json.prevClose ?? json.previous_close ?? json.prev_close ?? null;
          const openPrice = json.openPrice ?? json.open ?? null;
          const dayRange = json.dayRange ?? (json.low && json.high ? { low: json.low, high: json.high } : null);

          return res.json({
            currentPrice: cp,
            percentChange: percent,
            volume,
            prevClose,
            openPrice,
            dayRange,
            raw: json,
          });
        }

        // non-json success
        res.set("Content-Type", ct || "text/plain");
        return res.status(200).send(text);
      } catch (err) {
        lastErr = err;
        continue;
      }
    }

    return res.status(502).json({ error: "Upstream quote fetch failed", detail: String(lastErr?.message || lastErr) });
  } catch (err) {
    console.error("/api/quote failed:", err);
    return res.status(500).json({ error: "Internal server error", detail: String(err?.message || err) });
  }
});

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

// /api/trending (cached 30s)
reg("/api/trending", async (req, res) => {
  const now = Date.now();
  if (trendingCache && now < trendingExpiry) {
    console.log("[trending] returning cache");
    return res.json(trendingCache);
  }
  try {
    const r = await fetchImpl(`${BASE_URL}/trending`, { headers: makeHeaders(), method: "GET" });
    const ct = r.headers.get("content-type") || "";
    const text = await r.text().catch(() => "");
    if (!text) return res.status(r.status).end();

    if (ct.includes("application/json") || ct.includes("+json")) {
      try {
        const json = JSON.parse(text);
        trendingCache = json;
        trendingExpiry = Date.now() + 30_000;
        return res.status(r.status).json(json);
      } catch (parseErr) {
        console.error("[trending] parse error:", parseErr?.message || parseErr);
        return res.status(502).json({ error: "Invalid trending JSON" });
      }
    } else {
      return res.status(r.status).send(text);
    }
  } catch (err) {
    console.error("trending fetch failed:", err?.message || err);
    if (trendingCache) return res.json({ data: trendingCache, upstream_issue: true });
    return res.status(502).json({ error: "Upstream trending error", detail: err?.message || String(err) });
  }
});

// /api/fetch_52_week_high_low_data
reg("/api/fetch_52_week_high_low_data", (req, res) => proxyFetch(res, `${BASE_URL}/fetch_52_week_high_low_data`));

// NSE / BSE most active
reg("/api/NSE_most_active", (req, res) => proxyFetch(res, `${BASE_URL}/NSE_most_active`));
reg("/api/BSE_most_active", (req, res) => proxyFetch(res, `${BASE_URL}/BSE_most_active`));

// mutual_funds (kept for compatibility)
reg("/api/mutual_funds", (req, res) => proxyFetch(res, `${BASE_URL}/mutual_funds`));

// price_shockers
reg("/api/price_shockers", (req, res) => proxyFetch(res, `${BASE_URL}/price_shockers`));

// commodities
reg("/api/commodities", (req, res) => proxyFetch(res, `${BASE_URL}/commodities`));

// stock_target_price
reg("/api/stock_target_price", (req, res) => {
  const id = req.query.stock_id;
  if (!id) return res.status(400).json({ error: "Missing ?stock_id" });
  return proxyFetch(res, `${BASE_URL}/stock_target_price?stock_id=${encodeURIComponent(id)}`);
});

// stock_forecasts
reg("/api/stock_forecasts", (req, res) => {
  const params = new URLSearchParams(req.query);
  if (!params.has("stock_id")) {
    return res.status(400).json({ error: "Missing required ?stock_id" });
  }
  return proxyFetch(res, `${BASE_URL}/stock_forecasts?${params.toString()}`);
});

// historical_data (improved proxy / forwards upstream error bodies)
reg("/api/historical_data", async (req, res) => {
  try {
    const symbol = req.query.symbol || req.query.stock_id || req.query.name;
    if (!symbol) return res.status(400).json({ error: "Missing required ?symbol or ?stock_id or ?name" });

    const qs = new URLSearchParams(req.query).toString();
    const upstream = `${BASE_URL}/historical_data?${qs}`;

    const r = await fetchImpl(upstream, { method: "GET", headers: makeHeaders() });
    const ct = r.headers.get("content-type") || "";
    const text = await r.text().catch(() => "");

    if (!r.ok) {
      res.set("Content-Type", ct || "text/plain");
      return res.status(r.status).send(text);
    }

    if (ct.includes("application/json") || ct.includes("+json")) {
      try {
        const json = JSON.parse(text);
        return res.status(200).json(json);
      } catch (e) {
        res.set("Content-Type", ct || "text/plain");
        return res.status(200).send(text);
      }
    }

    res.set("Content-Type", ct || "text/plain");
    return res.status(200).send(text);
  } catch (err) {
    console.error("/api/historical_data failed:", err);
    return res.status(500).json({ error: "Internal server error", detail: String(err?.message || err) });
  }
});

// historical_stats
reg("/api/historical_stats", (req, res) => proxyFetch(res, `${BASE_URL}/historical_stats?${new URLSearchParams(req.query).toString()}`));

// other standard endpoints
reg("/api/news", (req, res) => proxyFetch(res, `${BASE_URL}/news`));
reg("/api/ipo", (req, res) => proxyFetch(res, `${BASE_URL}/ipo`));
reg("/api/recent_announcements", (req, res) => proxyFetch(res, `${BASE_URL}/recent_announcements`));
reg("/api/corporate_actions", (req, res) => proxyFetch(res, `${BASE_URL}/corporate_actions`));
reg("/api/statement", (req, res) => proxyFetch(res, `${BASE_URL}/statement`));

/**
 * Wildcard fallback for anything else under /api/*
 * IMPORTANT: keep this AFTER all explicit /api/ registrations and AFTER /research
 */
reg("/api/:path(*)", (req, res) => {
  const path = req.params.path || "";
  const qs = new URLSearchParams(req.query).toString();
  const upstream = `${BASE_URL}/${path}${qs ? `?${qs}` : ""}`;
  console.log(`[wildcard proxy] /api/${path} -> ${upstream}`);
  return proxyFetch(res, upstream);
});

// debug route to list routes
reg("/__routes", (req, res) => {
  const routes = [];
  (app._router.stack || []).forEach((layer) => {
    if (layer.route && layer.route.path) {
      routes.push({ path: layer.route.path, methods: Object.keys(layer.route.methods).join(",") });
    }
  });
  res.json(routes);
});

// fallback 404 for other non-matched routes
app.use((req, res) => res.status(404).json({ error: "Not found", path: req.path }));

// graceful shutdown helpers
const server = app.listen(PORT, () => {
  console.log(`🚀 IndianAPI Proxy running on port ${PORT} — Base: ${BASE_URL}`);
});

process.on("SIGTERM", () => {
  console.info("SIGTERM received — closing HTTP server");
  server.close(() => {
    console.info("HTTP server closed");
    process.exit(0);
  });
});

// export app for tests if needed
export default app;
