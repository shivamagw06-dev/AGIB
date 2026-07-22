export const DEFAULT_CATEGORIES = [
  { name: 'Morning Market Update', slug: 'morning-market-update', description: 'Pre-market and opening bell analysis', sort_order: 1 },
  { name: '12 PM Market Update', slug: '12-pm-market-update', description: 'Midday market snapshot and key moves', sort_order: 2 },
  { name: 'Day Close Update', slug: 'day-close-update', description: 'End-of-day market wrap and closing analysis', sort_order: 3 },
  { name: 'Market News', slug: 'market-news', description: 'Breaking market news and headlines', sort_order: 4 },
  { name: 'Research Reports', slug: 'research-reports', description: 'In-depth institutional research reports', sort_order: 5 },
  { name: 'Stock Analysis', slug: 'stock-analysis', description: 'Company and equity analysis', sort_order: 6 },
  { name: 'Economy', slug: 'economy', description: 'Macroeconomic trends, GDP, inflation and policy', sort_order: 7 },
  { name: 'Global Markets', slug: 'global-markets', description: 'US, Europe, Asia and cross-border markets', sort_order: 8 },
  { name: 'Commodities', slug: 'commodities', description: 'Oil, gold, metals and commodity markets', sort_order: 9 },
  { name: 'IPOs', slug: 'ipos', description: 'IPO pipeline, listings and new issues', sort_order: 10 },
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
