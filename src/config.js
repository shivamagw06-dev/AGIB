// Resolves API origin for market-data proxy (Render in prod, localhost in dev).

function readViteApiUrl() {
  // Vite only inlines import.meta.env.VITE_* — avoid optional chaining on import.meta.env.
  try {
    return import.meta.env.VITE_API_URL || null;
  } catch {
    return null;
  }
}

const viteUrl = readViteApiUrl();

const runtimeOverride =
  typeof window !== "undefined" && window.__API_ORIGIN
    ? String(window.__API_ORIGIN)
    : null;

const hostname =
  typeof window !== "undefined" && window.location?.hostname
    ? window.location.hostname
    : null;

const runningLocally = hostname === "localhost" || hostname === "127.0.0.1";

export const API_ORIGIN =
  runtimeOverride || viteUrl || (runningLocally ? "http://localhost:5000" : null);

export default API_ORIGIN;

if (runningLocally) {
  console.info("[config] API_ORIGIN =", API_ORIGIN);
}
