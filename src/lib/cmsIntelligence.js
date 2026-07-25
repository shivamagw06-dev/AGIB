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

export function extractTickersFromText(...parts) {
  const text = parts.filter(Boolean).join(' ').toUpperCase();
  const matches = text.match(/\b[A-Z]{2,12}\b/g) || [];
  const block = new Set([
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
    'IPO',
    'USD',
    'INR',
    'CEO',
    'GDP',
    'RBI',
    'AGI',
    'CMS',
  ]);
  return [...new Set(matches.filter((t) => !block.has(t) && t.length >= 3))].slice(0, 12);
}

/**
 * Push CMS research into the intelligence engine (KIP).
 * Website publish and private intelligence ingest both use this.
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
}) {
  const content = stripHtml(contentHtml);
  if (!title?.trim() || content.length < 40) {
    throw new Error('Add a title and enough article content before sending to intelligence.');
  }

  const tickers = extractTickersFromText(title, ...(tags || []), content.slice(0, 1200));
  const base = (API_ORIGIN || '').replace(/\/$/, '');
  const resp = await fetch(`${base}/api/intelligence/kip/ingest/agi`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
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
    }),
  });

  const text = await resp.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }
  if (!resp.ok) {
    throw new Error(data?.error || data?.detail || `Intelligence ingest failed (${resp.status})`);
  }
  return data;
}
