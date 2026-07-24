function apiBase() {
  if (typeof window !== 'undefined' && window.API_URL) return String(window.API_URL).replace(/\/$/, '');
  return (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
}

async function request(path) {
  const response = await fetch(`${apiBase()}/api/ipo${path}`);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || 'Unable to load IPO information.');
  }
  return response.json();
}

export function getIpoSummary() {
  return request('/summary');
}

export function getIpoDetail(symbol) {
  return request(`/${encodeURIComponent(symbol)}`);
}
