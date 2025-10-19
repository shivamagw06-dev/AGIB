// src/config.js
// Resolves API origin in a predictable order:
// 1) runtime override via window.__API_ORIGIN (optional, set on the hosted page)
// 2) Vite build-time env VITE_API_URL (import.meta.env.VITE_API_URL)
// 3) local dev fallback (localhost)
// 4) null otherwise

// safe read of Vite env — use try/catch to avoid parser/runtime issues
let viteUrl = null;
try {
  // import.meta is valid in ESM builds (Vite). If not available or removed by tooling, this will throw.
  viteUrl = import.meta?.env?.VITE_API_URL ?? null;
} catch (e) {
  viteUrl = null;
}

// runtime override (set window.__API_ORIGIN on the page if you want to override the env)
const runtimeOverride = (typeof window !== 'undefined' && window.__API_ORIGIN) ? String(window.__API_ORIGIN) : null;

// hostname detection (safe for SSR)
const hostname = (typeof window !== 'undefined' && window.location && window.location.hostname)
  ? window.location.hostname
  : null;
const runningLocally = hostname === 'localhost' || hostname === '127.0.0.1';

// NOTE: pick a local port that matches your backend dev server.
// Your earlier logs showed calls to localhost:5000, so default to 5000.
// Change to 3000 if your backend runs on :3000.
export const API_ORIGIN = runtimeOverride || viteUrl || (runningLocally ? 'http://localhost:5000' : null);
export default API_ORIGIN;

// Optional debug during development
if (typeof window !== 'undefined' && (hostname === 'localhost' || hostname === '127.0.0.1')) {
  // eslint-disable-next-line no-console
  console.info('[config] API_ORIGIN resolved to', API_ORIGIN);
}
