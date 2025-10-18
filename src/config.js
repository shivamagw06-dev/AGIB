// src/config.js
// Resolves API origin in a predictable order:
// 1) runtime override via window.__API_ORIGIN (optional, set on the hosted page)
// 2) Vite env VITE_API_URL (set at build time)
// 3) local dev fallback (localhost)
// 4) null otherwise

const viteUrl = typeof import.meta !== 'undefined' && import.meta.env ? import.meta.env.VITE_API_URL : null;

const runtimeOverride = (typeof window !== 'undefined' && window.__API_ORIGIN) ? window.__API_ORIGIN : null;

const hostname = (typeof window !== 'undefined' && window.location && window.location.hostname) ? window.location.hostname : null;
const runningLocally = hostname === 'localhost' || hostname === '127.0.0.1';

export const API_ORIGIN = runtimeOverride || viteUrl || (runningLocally ? 'http://localhost:3000' : null);
export default API_ORIGIN;
