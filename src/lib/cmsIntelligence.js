import { API_ORIGIN } from '@/config';

function stripHtml(html = '') {
  return String(html)
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/** Allowlisted equity tickers only — never scrape prose into fake tickers. */
const KNOWN_TICKERS = new Set([
  'ICICIBANK',
  'HDFCBANK',
  'RELIANCE',
  'TCS',
  'INFY',
  'SBIN',
  'AXISBANK',
  'KOTAKBANK',
  'BHARTIARTL',
  'LT',
  'ITC',
  'WIPRO',
  'MARUTI',
  'TATAMOTORS',
  'HINDUNILVR',
  'HCLTECH',
  'TECHM',
  'LTIM',
  'LTTS',
  'PERSISTENT',
  'COFORGE',
  'MPHASIS',
  'OFSS',
  'AAPL',
  'MSFT',
  'GOOGL',
  'AMZN',
  'NVDA',
]);

const TICKER_BLOCK = new Set([
  'THE',
  'AND',
  'FOR',
  'WITH',
  'FROM',
  'THIS',
  'THAT',
  'HAVE',
  'WILL',
  'INTO',
  'OVER',
  'UNDER',
  'INDIA',
  'INDIAN',
  'MARKET',
  'MARKETS',
  'STOCK',
  'STOCKS',
  'SECTOR',
  'UPDATE',
  'OUTLOOK',
  'REVIEW',
  'GROWTH',
  'WEAK',
  'DEAL',
  'DEALS',
  'SERVICE',
  'SERVICES',
  'GLOBAL',
  'RESEARCH',
  'NOTE',
  'WEEK',
  'CONTINUES',
  'EARNINGS',
  'PRESSURE',
  'DEMAND',
  'MACRO',
  'KEY',
  'TAKEAWAYS',
  'AMP',
  'HIS',
  'IMPLICATIONS',
  'IPO',
  'USD',
  'INR',
  'CEO',
  'GDP',
  'RBI',
  'AGI',
  'CMS',
  'QOQ',
  'YOY',
  'AI',
  'IT',
]);

export function extractTickersFromText(...parts) {
  const text = parts.filter(Boolean).join(' ').toUpperCase();
  const matches = text.match(/\b[A-Z]{2,12}\b/g) || [];
  return [
    ...new Set(
      matches.filter(
        (t) =>
          !TICKER_BLOCK.has(t) &&
          (KNOWN_TICKERS.has(t) || t.endsWith('BANK'))
      )
    ),
  ].slice(0, 12);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isTransientIngestError(err, status) {
  if ([502, 503, 504].includes(Number(status))) return true;
  const msg = String(err?.message || err || '');
  const name = String(err?.name || '');
  return (
    name === 'TypeError' ||
    name === 'AbortError' ||
    name === 'TimeoutError' ||
    /failed to fetch|fetch failed|networkerror|network request failed|load failed|timed out|timeout|aborted|502|503|504|unavailable|econnreset|enotfound/i.test(
      msg
    )
  );
}

/** Soft-wake Node + IE before a write so Render cold starts fail less often. */
async function warmIntelligence(base) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 25_000);
  try {
    await fetch(`${base}/api/health`, {
      method: 'GET',
      credentials: 'include',
      signal: ctrl.signal,
    }).catch(() => null);
    await fetch(`${base}/api/intelligence/health`, {
      method: 'GET',
      credentials: 'include',
      signal: ctrl.signal,
    }).catch(() => null);
  } finally {
    clearTimeout(timer);
  }
}

async function postIngest(base, payload, { timeoutMs = 90_000 } = {}) {
  const resp = await fetch(`${base}/api/intelligence/kip/ingest/agi`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(timeoutMs),
  });
  const text = await resp.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }
  return { resp, data };
}

/**
 * Push CMS research into the intelligence engine (KIP).
 * Retries on transient gateway/engine failures and browser "Failed to fetch"
 * (common during Render cold starts).
 */
export async function ingestArticleToIntelligence({
  title,
  contentHtml,
  slug,
  articleId,
  section,
  tags = [],
  status,
  destination = 'intelligence',
  onAttempt,
}) {
  const content = stripHtml(contentHtml);
  if (!title?.trim() || content.length < 40) {
    throw new Error('Add a title and enough article content before sending to intelligence.');
  }

  const tickers = extractTickersFromText(title, ...(tags || []), content.slice(0, 1200));
  const base = (API_ORIGIN || '').replace(/\/$/, '');
  if (!base) {
    throw new Error('API origin missing. Set VITE_API_URL for the Hostinger build.');
  }

  const payload = {
    title: title.trim(),
    content,
    slug,
    article_id: articleId || slug,
    section,
    tickers,
    themes: Array.isArray(tags) ? tags.slice(0, 8) : [],
    cms_status: status,
    destination,
    document_type: destination === 'website' ? 'agi_research' : 'agi_note',
    author: 'AGI Research Desk',
  };

  // Warm first — avoids the first write hitting a sleeping IE with a hard network fail.
  if (typeof onAttempt === 'function') onAttempt({ phase: 'warm', attempt: 0, maxAttempts: 5 });
  await warmIntelligence(base);

  const maxAttempts = 5;
  const backoffs = [0, 3000, 8000, 15000, 25000];
  let lastError = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    if (backoffs[attempt - 1]) await sleep(backoffs[attempt - 1]);
    if (typeof onAttempt === 'function') {
      onAttempt({ phase: 'ingest', attempt, maxAttempts });
    }
    try {
      const { resp, data } = await postIngest(base, payload);
      if (resp.ok) return data;

      const detail =
        data?.detail || data?.error || data?.hint || `Intelligence ingest failed (${resp.status})`;
      lastError = new Error(String(detail));
      if (!isTransientIngestError(lastError, resp.status) || attempt === maxAttempts) {
        throw lastError;
      }
      // Re-warm between retries when the engine is clearly cold.
      await warmIntelligence(base);
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
      if (!isTransientIngestError(lastError) || attempt === maxAttempts) throw lastError;
      await warmIntelligence(base);
    }
  }

  throw lastError || new Error('Intelligence ingest failed.');
}
