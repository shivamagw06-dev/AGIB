async function request(path, { method = 'GET', body } = {}) {
  const resp = await fetch(path, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    credentials: 'include',
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok && data?.ok === false) {
    throw new Error(data.error || data.message || `HTTP ${resp.status}`);
  }
  return data;
}

export function getUifiCoverage() {
  return request('/api/upstox/coverage');
}

export function getUifiFailures() {
  return request('/api/upstox/failures');
}

export function getUifiBootstrapStatus() {
  return request('/api/upstox/bootstrap/status');
}

export function getUifiSchedulerStatus() {
  return request('/api/upstox/scheduler');
}

export function startUifiBootstrap(body = {}) {
  return request('/api/upstox/bootstrap/start', { method: 'POST', body });
}

export function stopUifiBootstrap() {
  return request('/api/upstox/bootstrap/stop', { method: 'POST', body: {} });
}

export function bootstrapDataset(dataset, body = {}) {
  const path = {
    profile: '/api/upstox/profile/bootstrap',
    statements: '/api/upstox/statements/bootstrap',
    shareholding: '/api/upstox/shareholding/bootstrap',
    competitors: '/api/upstox/competitors/bootstrap',
    'corporate-actions': '/api/upstox/corporate-actions/bootstrap',
  }[dataset];
  if (!path) throw new Error(`unknown_dataset:${dataset}`);
  return request(path, { method: 'POST', body });
}
