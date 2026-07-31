/** Universal entity types for the Intelligence Platform. */

export const ENTITY_TYPES = {
  pe_firm: { label: 'Firm', plural: 'Firms', searchGroup: 'Firms' },
  general_partner: { label: 'General Partner', plural: 'General Partners', searchGroup: 'Firms' },
  limited_partner: { label: 'Limited Partner', plural: 'Limited Partners', searchGroup: 'Investors' },
  investor: { label: 'Investor', plural: 'Investors', searchGroup: 'Investors' },
  company: { label: 'Company', plural: 'Companies', searchGroup: 'Companies' },
  portfolio_company: { label: 'Portfolio Company', plural: 'Portfolio Companies', searchGroup: 'Portfolio Companies' },
  fund: { label: 'Fund', plural: 'Funds', searchGroup: 'Funds' },
  transaction: { label: 'Transaction', plural: 'Transactions', searchGroup: 'Transactions' },
  industry: { label: 'Industry', plural: 'Industries', searchGroup: 'Industries' },
  person: { label: 'Person', plural: 'People', searchGroup: 'People' },
  article: { label: 'Article', plural: 'Articles', searchGroup: 'Articles' },
  news: { label: 'News', plural: 'News', searchGroup: 'News' },
};

export const RELATION_TYPES = {
  OWNS: 'Owns',
  MANAGES: 'Manages',
  INVESTED_IN: 'Invested in',
  MENTIONS: 'Mentions',
  WORKS_AT: 'Works at',
  OPERATES_IN: 'Operates in',
  SPONSORED_BY: 'Sponsored by',
  EXITED: 'Exited',
  ACQUIRED: 'Acquired',
  FOUNDED: 'Founded',
};

/** Search result group order for universal search UI. */
export const SEARCH_GROUP_ORDER = [
  'Firms',
  'Funds',
  'Portfolio Companies',
  'Companies',
  'Transactions',
  'Articles',
  'People',
  'Industries',
  'News',
  'Investors',
];

export function entityTypeLabel(type) {
  return ENTITY_TYPES[type]?.label || type;
}

export function searchGroupForType(type) {
  return ENTITY_TYPES[type]?.searchGroup || 'Other';
}

export function slugify(name) {
  return String(name || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 120);
}
