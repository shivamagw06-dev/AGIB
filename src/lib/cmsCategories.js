export const DEFAULT_CATEGORIES = [
  // AGI Morning Brief (7:00–8:00 AM IST)
  { name: 'Pre-Market Update', slug: 'pre-market-update', description: 'AGI Morning Brief — everything before the opening bell', sort_order: 1 },
  { name: 'Morning Market Update', slug: 'morning-market-update', description: 'Legacy alias for AGI Morning Brief', sort_order: 2 },
  // AGI Markets (flagship / midday / general)
  { name: '12 PM Market Update', slug: '12-pm-market-update', description: 'AGI Markets midday snapshot and key moves', sort_order: 3 },
  { name: 'Market News', slug: 'market-news', description: 'AGI Markets — breaking market news and headlines', sort_order: 4 },
  // AGI Evening Brief (4:30–6:00 PM IST)
  { name: 'Market Close Update', slug: 'market-close-update', description: 'AGI Evening Brief — what moved markets today and why', sort_order: 5 },
  { name: 'Day Close Update', slug: 'day-close-update', description: 'Legacy alias for AGI Evening Brief', sort_order: 6 },
  // AGI Macro
  { name: 'Macro Intelligence', slug: 'macro-intelligence', description: 'AGI Macro — policy, inflation, rates, FX, geopolitics', sort_order: 7 },
  { name: 'Economy', slug: 'economy', description: 'Macroeconomic trends, GDP, inflation and policy', sort_order: 8 },
  { name: 'Global Markets', slug: 'global-markets', description: 'US, Europe, Asia and cross-border markets', sort_order: 9 },
  { name: 'Commodities', slug: 'commodities', description: 'Oil, gold, metals and commodity markets', sort_order: 10 },
  { name: 'Research Reports', slug: 'research-reports', description: 'In-depth institutional research reports', sort_order: 11 },
  { name: 'Stock Analysis', slug: 'stock-analysis', description: 'Company and equity analysis', sort_order: 12 },
  { name: 'IPOs', slug: 'ipos', description: 'IPO pipeline, listings and new issues', sort_order: 13 },
];

const STORAGE_KEY = 'agib:cms:categories';

export function getLocalCategories() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    /* ignore */
  }
  return DEFAULT_CATEGORIES.map((c, i) => ({ ...c, id: `local-${i}`, is_active: true }));
}

export function saveLocalCategories(categories) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(categories));
}
