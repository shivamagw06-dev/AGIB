import { API_ORIGIN } from '@/config';

const BASE = API_ORIGIN || '';

let currentActor = 'admin';

/** The workspace names who is making every change; the server records it. */
export function setWarehouseActor(actor) {
  currentActor = String(actor || 'admin').slice(0, 200);
}

export function getWarehouseActor() {
  return currentActor;
}

async function warehouseFetch(path, { method = 'GET', body, timeoutMs = 60_000 } = {}) {
  if (!BASE) {
    throw new Error('API origin is not configured. Set VITE_API_URL to the backend.');
  }
  const url = `${BASE}/api/intelligence/warehouse${path}`;
  const headers = { 'X-AGI-Actor': currentActor };
  if (body) headers['Content-Type'] = 'application/json';

  let resp;
  try {
    resp = await fetch(url, {
      method,
      credentials: 'include',
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch (err) {
    const name = err?.name || '';
    if (name === 'TimeoutError' || name === 'AbortError') {
      throw new Error(
        `Warehouse request timed out after ${Math.round(timeoutMs / 1000)}s (${path}).`,
      );
    }
    throw err;
  }

  const text = await resp.text().catch(() => '');
  if (text.trim().startsWith('<')) {
    throw new Error(`Warehouse API returned HTML for ${path}. Check VITE_API_URL.`);
  }
  if (!resp.ok) {
    throw new Error(`Warehouse API error (${resp.status}) ${text.slice(0, 200)}`);
  }
  try {
    return text ? JSON.parse(text) : null;
  } catch {
    throw new Error(`Warehouse API invalid JSON for ${path}`);
  }
}

const qs = (params = {}) => {
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== null && v !== '',
  );
  if (!entries.length) return '';
  return `?${new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString()}`;
};

const tabPath = (tabId) => `/tab/${encodeURIComponent(tabId)}`;

/* Workbook + health */
export const getWarehouseHealth = () => warehouseFetch('/health');
export const getWorkbook = () => warehouseFetch('/workbook');
export const getWarehouseStats = () => warehouseFetch('/stats');
export const getWarehouseWhoami = () => warehouseFetch('/whoami');
export const getWarehouseCoverage = () => warehouseFetch('/coverage');

/* Sheets */
export const getSheet = (tabId, params = {}) => {
  const { filters, ...rest } = params;
  const query = { ...rest };
  if (filters && Object.keys(filters).length) query.filters = JSON.stringify(filters);
  return warehouseFetch(`${tabPath(tabId)}${qs(query)}`, { timeoutMs: 90_000 });
};
export const getTabSchema = (tabId) => warehouseFetch(`${tabPath(tabId)}/schema`);
export const getWarehouseRow = (tabId, rowId) =>
  warehouseFetch(`${tabPath(tabId)}/row/${encodeURIComponent(rowId)}`);

/* Editing */
export const editCells = (tabId, edits, { reason, recalculate = true } = {}) =>
  warehouseFetch(`${tabPath(tabId)}/edit`, {
    method: 'POST',
    body: { edits, reason, recalculate, actor: currentActor },
    timeoutMs: 120_000,
  });
export const createRow = (tabId, values) =>
  warehouseFetch(`${tabPath(tabId)}/row`, {
    method: 'POST',
    body: { values, actor: currentActor },
  });
export const clearOverride = (tabId, rowId, column) =>
  warehouseFetch(`${tabPath(tabId)}/clear-override`, {
    method: 'POST',
    body: { row_id: rowId, column, actor: currentActor },
  });
export const deleteRows = (tabId, rowIds, reason) =>
  warehouseFetch(`${tabPath(tabId)}/delete`, {
    method: 'POST',
    body: { row_ids: rowIds, reason, actor: currentActor },
  });
export const publishTab = (tabId) =>
  warehouseFetch(`${tabPath(tabId)}/publish`, { method: 'POST', body: { actor: currentActor } });

/* Import / export */
export const mapHeaders = (tabId, headers) =>
  warehouseFetch(`${tabPath(tabId)}/map-headers`, { method: 'POST', body: { headers } });
export const stageImport = (tabId, payload) =>
  warehouseFetch(`${tabPath(tabId)}/import`, {
    method: 'POST',
    body: { ...payload, actor: currentActor },
    timeoutMs: 300_000,
  });
export const commitImport = (importId) =>
  warehouseFetch(`/import/${encodeURIComponent(importId)}/commit`, {
    method: 'POST',
    body: { actor: currentActor },
    timeoutMs: 300_000,
  });
export const listImports = (params = {}) => warehouseFetch(`/imports${qs(params)}`);
export const exportTab = (tabId, params = {}) =>
  warehouseFetch(`${tabPath(tabId)}/export${qs(params)}`, { timeoutMs: 180_000 });

/* Versions + audit */
export const getRowHistory = (tabId, rowId, column) =>
  warehouseFetch(`${tabPath(tabId)}/row/${encodeURIComponent(rowId)}/history${qs({ column })}`);
export const compareVersions = (tabId, rowId, versionA, versionB) =>
  warehouseFetch(
    `${tabPath(tabId)}/row/${encodeURIComponent(rowId)}/compare${qs({
      version_a: versionA,
      version_b: versionB,
    })}`,
  );
export const restoreVersion = (tabId, rowId, version) =>
  warehouseFetch(`${tabPath(tabId)}/row/${encodeURIComponent(rowId)}/restore`, {
    method: 'POST',
    body: { version, actor: currentActor },
  });
export const getAuditLog = (params = {}) => warehouseFetch(`/audit${qs(params)}`);

/* Operations */
export const validateWarehouse = (params = {}) =>
  warehouseFetch(`/validate${qs(params)}`, { timeoutMs: 180_000 });
export const runRefresh = (payload = {}) =>
  warehouseFetch('/refresh', {
    method: 'POST',
    body: { ...payload, actor: currentActor },
    timeoutMs: 900_000,
  });
export const listRefreshRuns = (limit = 10) => warehouseFetch(`/refresh-runs${qs({ limit })}`);
export const recalculate = (payload = {}) =>
  warehouseFetch('/recalculate', {
    method: 'POST',
    body: { ...payload, actor: currentActor },
    timeoutMs: 600_000,
  });

/* Search */
export const searchWarehouse = (q, params = {}) => warehouseFetch(`/search${qs({ q, ...params })}`);
export const suggestCompanies = (prefix, limit = 10) =>
  warehouseFetch(`/suggest${qs({ prefix, limit })}`);
export const getCompanyView = (symbol, perTab = 25) =>
  warehouseFetch(`/company/${encodeURIComponent(symbol)}${qs({ per_tab: perTab })}`);
