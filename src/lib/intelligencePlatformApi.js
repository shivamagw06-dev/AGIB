const API_BASE = import.meta.env.VITE_API_URL || window?.API_URL || '';

async function platformFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}/api/intelligence/platform${path}`, {
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Platform API ${res.status}`);
  return data;
}

export function searchEntities(q, { limit = 8 } = {}) {
  const params = new URLSearchParams({ q, limit: String(limit) });
  return platformFetch(`/search?${params}`);
}

export function fetchEntity(slug, { refresh = false } = {}) {
  const qs = refresh ? '?refresh=1' : '';
  return platformFetch(`/entities/${encodeURIComponent(slug)}${qs}`);
}

export function fetchEntityTimeline(slug) {
  return platformFetch(`/entities/${encodeURIComponent(slug)}/timeline`);
}

export function fetchPlatformStats() {
  return platformFetch('/stats');
}

export function fetchEntities({ type, q, limit = 50 } = {}) {
  const params = new URLSearchParams();
  if (type) params.set('type', type);
  if (q) params.set('q', q);
  if (limit) params.set('limit', String(limit));
  const qs = params.toString();
  return platformFetch(`/entities${qs ? `?${qs}` : ''}`);
}

export function entityPublicPath(entity) {
  if (!entity) return '/private-markets';
  if (entity.entity_type === 'pe_firm') return `/private-markets/firms/${entity.slug}`;
  return `/private-markets/entities/${entity.slug}`;
}
