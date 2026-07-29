/** Curated homepage catalogs — soft fallbacks when live CMS/API is thin. */

export const TRENDING_CHIPS = [
  'Reliance',
  'HDFC Bank',
  'RBI Policy',
  'Defence',
  'NIFTY Outlook',
  'Gold',
  'IPO Calendar',
  'Fed',
];

export const RESEARCH_THEMES = [
  { id: 'ai-tech', label: 'AI & Technology', path: '/themes/ai_productivity' },
  { id: 'defence', label: 'Defence', path: '/sectors/defence' },
  { id: 'banking', label: 'Banking', path: '/sectors/banks' },
  { id: 'energy', label: 'Energy Transition', path: '/themes/energy_transition' },
  { id: 'infra', label: 'Infrastructure', path: '/themes/capex_cycle' },
  { id: 'consumption', label: 'Consumption', path: '/sectors/fmcg' },
  { id: 'pharma', label: 'Pharma', path: '/sectors/pharma' },
  { id: 'manufacturing', label: 'Manufacturing', path: '/themes/manufacturing' },
  { id: 'china-plus-one', label: 'China+1', path: '/themes/china_plus_one' },
  { id: 'psu', label: 'PSU', path: '/themes/psu' },
  { id: 'smallcaps', label: 'Small Caps', path: '/ask?q=Small%20cap%20outlook%20India' },
];

export const FEATURED_LANES = [
  { id: 'editors', label: "Editor's Pick", path: '/research' },
  { id: 'institutional', label: 'Institutional Research', path: '/sections/research-notes' },
  { id: 'weekly', label: 'Weekly Outlook', path: '/market-intelligence' },
  { id: 'monthly', label: 'Monthly Outlook', path: '/macro-intelligence' },
  { id: 'thematic', label: 'Thematic Research', path: '/themes' },
  { id: 'strategy', label: 'Strategy Notes', path: '/ask?q=India%20equity%20strategy' },
];

export const DEFAULT_OUTLOOK = [
  { key: 'nifty50', label: 'NIFTY 50', sentiment: 'Bullish', score: 72, path: '/market-intelligence' },
  { key: 'next50', label: 'NIFTY NEXT 50', sentiment: 'Bullish', score: 68, path: '/market-intelligence' },
  { key: 'banknifty', label: 'BANK NIFTY', sentiment: 'Neutral', score: 55, path: '/market-intelligence' },
  { key: 'midcap', label: 'MIDCAP', sentiment: 'Bearish', score: 38, path: '/market-intelligence' },
  { key: 'smallcap', label: 'SMALLCAP', sentiment: 'Bullish', score: 64, path: '/market-intelligence' },
  { key: 'sensex', label: 'SENSEX', sentiment: 'Bullish', score: 70, path: '/market-intelligence' },
];

export const DEFAULT_HIGHLIGHTS = [
  'RBI commentary improves banking outlook.',
  'Defence sector continues to outperform.',
  'FIIs bought ₹2,800 crore.',
  'Oil down 3%.',
  'AI upgrades Larsen & Toubro.',
];

export const CALENDAR_BLOCKS = [
  { id: 'earnings', label: 'Earnings', hint: 'Results desk' },
  { id: 'ipo', label: 'IPO', hint: 'Offer calendar' },
  { id: 'economic', label: 'Economic Events', hint: 'Macro releases' },
  { id: 'rbi', label: 'RBI Events', hint: 'Policy & speeches' },
  { id: 'fed', label: 'Fed', hint: 'Global policy' },
  { id: 'results', label: 'Results Today', hint: 'Live board' },
];

export const GLOBAL_SNAPSHOT = [
  { id: 'us', label: 'US', path: '/global' },
  { id: 'europe', label: 'Europe', path: '/global' },
  { id: 'asia', label: 'Asia', path: '/global' },
  { id: 'fx', label: 'Currencies', path: '/global' },
  { id: 'commodities', label: 'Commodities', path: '/global' },
  { id: 'bonds', label: 'Bond Yields', path: '/global' },
];

export function scoreFromSentiment(sentiment = '', strength = '') {
  const s = String(sentiment).toLowerCase();
  const n = Number(String(strength).replace(/[^\d.]/g, ''));
  if (Number.isFinite(n) && n > 0) return Math.min(99, Math.round(n));
  if (s.includes('bull')) return 68;
  if (s.includes('bear')) return 38;
  if (s.includes('neutral')) return 52;
  return 50;
}

export function normalizeSentiment(sentiment = '') {
  const s = String(sentiment).toLowerCase();
  if (s.includes('bull')) return 'Bullish';
  if (s.includes('bear')) return 'Bearish';
  if (s.includes('neutral')) return 'Neutral';
  if (s.includes('calculat') || s.includes('pending') || s.includes('sync')) return 'Syncing';
  return sentiment || 'Neutral';
}

export function matchOutlookIndices(indexSentiments = []) {
  const aliases = [
    { key: 'nifty50', match: /nifty\s*50(?!\s*next)/i, label: 'NIFTY 50' },
    { key: 'next50', match: /next\s*50/i, label: 'NIFTY NEXT 50' },
    { key: 'banknifty', match: /bank/i, label: 'BANK NIFTY' },
    { key: 'midcap', match: /midcap|mid\s*cap/i, label: 'MIDCAP' },
    { key: 'smallcap', match: /smallcap|small\s*cap/i, label: 'SMALLCAP' },
    { key: 'sensex', match: /sensex/i, label: 'SENSEX' },
  ];
  return aliases.map((alias) => {
    const hit = indexSentiments.find((row) => alias.match.test(row.label || row.key || ''));
    const fallback = DEFAULT_OUTLOOK.find((d) => d.key === alias.key);
    if (!hit) return { ...fallback };
    const sentiment = normalizeSentiment(hit.sentiment);
    return {
      key: alias.key,
      label: alias.label,
      sentiment,
      score: scoreFromSentiment(hit.sentiment, hit.strength),
      path: '/market-intelligence',
    };
  });
}

export function articleMatchesSession(article, session) {
  if (!article || !session) return false;
  const blob = [
    article.title,
    article.excerpt,
    article.section,
    article.category,
    ...(Array.isArray(article.tags) ? article.tags : []),
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();
  return session.topics.some((topic) => {
    const words = topic.toLowerCase().split(/\s+/).filter((w) => w.length > 3);
    return words.some((w) => blob.includes(w));
  });
}

export function enrichResearchCard(article) {
  if (!article) return null;
  const excerpt = article.excerpt || article.summary || '';
  return {
    ...article,
    executiveSummary: article.executiveSummary || excerpt,
    whyItMatters:
      article.whyItMatters ||
      article.why_it_matters ||
      (excerpt ? `Institutional relevance: ${excerpt.slice(0, 140)}${excerpt.length > 140 ? '…' : ''}` : 'Material for portfolio and sector monitoring.'),
    affectedCompanies: article.affectedCompanies || article.companies || article.tickers || [],
    affectedSectors: article.affectedSectors || (article.sector ? [article.sector] : article.category ? [article.category] : []),
    marketImpact: article.marketImpact || article.market_impact || 'Monitor positioning and relative performance.',
    readTime: article.readTime || article.read_time || '3 min read',
    premium: Boolean(article.premium || article.isPremium || /premium|institutional/i.test(article.section || '')),
    publishedLabel: article.publishedLabel || article.date || article.published_at,
  };
}
