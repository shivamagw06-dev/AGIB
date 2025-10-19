import React, { useEffect, useState, useRef } from "react";
import PropTypes from "prop-types";
import { API_ORIGIN } from "../config";

const CACHE_KEY = "markets_news_cache_v1";
const CACHE_TTL = 30 * 60 * 1000; // 30 minutes cache for news

function buildApiBase() {
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
  return res.json();
}

export default function LatestNews({ max = 6 }) {
  const [items, setItems] = useState(() => {
    try {
      const raw = localStorage.getItem(CACHE_KEY);
      if (!raw) return { loadedAt: 0, items: [] };
      return JSON.parse(raw);
    } catch {
      return { loadedAt: 0, items: [] };
    }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const ctrlRef = useRef(null);

  useEffect(() => {
    const now = Date.now();
    if (!items.loadedAt || now - items.loadedAt > CACHE_TTL) {
      loadNews();
    }
    return () => { if (ctrlRef.current) ctrlRef.current.abort(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadNews({ force = false } = {}) {
    if (loading) return;
    const now = Date.now();
    if (!force && items.loadedAt && now - items.loadedAt <= CACHE_TTL) return;

    setLoading(true);
    setError(null);
    ctrlRef.current = new AbortController();
    const { signal } = ctrlRef.current;

    try {
      const body = await fetchJson("/news", signal);
      // API returns an array of articles
      const normalized = Array.isArray(body) ? body : (body.data || body.articles || []);
      const out = { loadedAt: Date.now(), items: normalized.slice(0, 50) }; // keep up to 50 cached
      setItems(out);
      try { localStorage.setItem(CACHE_KEY, JSON.stringify(out)); } catch {}
    } catch (e) {
      console.error("LatestNews load failed", e);
      setError(e.message || String(e));
    } finally {
      setLoading(false);
      ctrlRef.current = null;
    }
  }

  function renderItem(it, i) {
    const title = it.title || it.headline || "Untitled";
    const summary = it.summary || it.description || "";
    const url = it.url || it.link || "#";
    const img = it.image_url || it.image || "";
    const date = it.pub_date || it.published_at || it.pubDate || null;
    const source = it.source || it.publisher || "";

    return (
      <article key={i} className="flex gap-3 py-2 border-b last:border-b-0">
        <div className="w-20 h-14 flex-shrink-0 rounded overflow-hidden bg-slate-100">
          {img ? (
            <img src={img} alt={title} className="object-cover w-full h-full" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-xs text-slate-400">No image</div>
          )}
        </div>

        <div className="flex-1">
          <a href={url} target="_blank" rel="noopener noreferrer" className="text-sm font-medium text-slate-800 hover:underline">
            {title}
          </a>
          <div className="text-xs text-slate-500 mt-1 line-clamp-2">{summary}</div>
          <div className="text-xs text-slate-400 mt-1">{source} {date ? ` • ${new Date(date).toLocaleString()}` : null}</div>
        </div>
      </article>
    );
  }

  const list = (items.items || []).slice(0, max);

  return (
    <section className="bg-white shadow-sm rounded p-3 border">
      <div className="flex items-baseline justify-between mb-2">
        <div>
          <h3 className="text-lg font-medium">Latest News</h3>
          <p className="text-xs text-slate-500">From your IndianAPI feed</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => loadNews({ force: true })} className="text-xs px-2 py-1 rounded border bg-slate-50">Refresh</button>
        </div>
      </div>

      {error && <div className="text-xs text-red-600 mb-2">Error loading news: {String(error)}</div>}

      {loading && <div className="text-sm text-slate-500">Loading...</div>}

      {!loading && list.length === 0 && <div className="text-sm text-slate-500">No news available</div>}

      <div>{list.map(renderItem)}</div>

      <div className="text-xs text-slate-400 mt-2">Source: IndianAPI news • Updated every 30 minutes (cached)</div>
    </section>
  );
}

LatestNews.propTypes = { max: PropTypes.number };
