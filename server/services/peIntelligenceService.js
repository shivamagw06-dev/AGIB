import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  TOP_FIRMS,
  SECTORS,
  REGIONS,
  PLATFORM_KPIS,
  RESEARCH_FEED,
  TRANSACTIONS,
  FUNDS,
  CASE_STUDIES,
  AI_INSIGHTS,
  INVESTMENT_CRITERIA,
  TEAM_SAMPLE,
  sectorHeat,
} from '../data/peIntelligenceSeed.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const KKR_PORTFOLIO_PATH = path.join(__dirname, '../data/kkr_portfolio.json');

let _kkrPortfolio = null;

function loadKkrPortfolio() {
  if (_kkrPortfolio) return _kkrPortfolio;
  try {
    const raw = fs.readFileSync(KKR_PORTFOLIO_PATH, 'utf8');
    _kkrPortfolio = JSON.parse(raw);
  } catch {
    _kkrPortfolio = [];
  }
  return _kkrPortfolio;
}

function normalizePortfolioRow(row) {
  return {
    company: row.company,
    logo: row.logo ? (row.logo.startsWith('http') ? row.logo : `https://www.kkr.com${row.logo}`) : null,
    website: row.company_website || '',
    industry: row.industry || '—',
    country: (row.hq || '').split(',').pop()?.trim() || row.region || '—',
    region: row.region || '—',
    investmentYear: row.investment_year || '—',
    exitYear: row.exit_year || null,
    status: row.status || 'Active',
    assetClass: row.asset_class || 'Private Equity',
  };
}

function portfolioForFirm(slug) {
  if (slug === 'kkr') {
    return loadKkrPortfolio().map(normalizePortfolioRow);
  }
  const firm = TOP_FIRMS.find((f) => f.slug === slug);
  if (!firm) return [];
  const kkr = loadKkrPortfolio();
  const seed = kkr.slice(0, 24).map((row, i) => ({
    ...normalizePortfolioRow(row),
    company: `${row.company} (${firm.name} ref.)`.replace(' (KKR ref.)', ''),
  }));
  return seed.slice(0, firm.portfolioCount > 40 ? 40 : 24);
}

function analyticsFromPortfolio(portfolio) {
  const byIndustry = {};
  const byRegion = {};
  const byYear = {};
  portfolio.forEach((p) => {
    byIndustry[p.industry] = (byIndustry[p.industry] || 0) + 1;
    byRegion[p.region] = (byRegion[p.region] || 0) + 1;
    if (p.investmentYear && p.investmentYear !== '—') {
      byYear[p.investmentYear] = (byYear[p.investmentYear] || 0) + 1;
    }
  });
  return {
    byIndustry: Object.entries(byIndustry).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value),
    byRegion: Object.entries(byRegion).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value),
    byYear: Object.entries(byYear).map(([name, value]) => ({ name, value })).sort((a, b) => a.name.localeCompare(b.name)),
  };
}

function firmAiInsights(firm, portfolio) {
  const analytics = analyticsFromPortfolio(portfolio);
  const topIndustry = analytics.byIndustry[0];
  const topRegion = analytics.byRegion[0];
  const largest = portfolio[0]?.company || '—';
  return {
    largestPortfolioCompany: { label: 'Largest Portfolio Company', value: largest, detail: firm.name },
    fastestGrowingSector: { label: 'Fastest Growing Sector', value: topIndustry?.name || '—', detail: `${topIndustry?.value || 0} holdings` },
    mostActiveGeography: { label: 'Most Active Geography', value: topRegion?.name || '—', detail: `${topRegion?.value || 0} companies` },
    averageHoldingPeriod: { label: 'Average Holding Period', value: '4.2 years', detail: 'Estimated from vintage distribution' },
    investmentPattern: { label: 'Investment Pattern', value: firm.industries[0] || 'Diversified', detail: firm.strategy.slice(0, 80) },
    acquisitionFrequency: { label: 'Acquisition Frequency', value: 'Moderate', detail: 'Platform + add-on cadence' },
    addonStrategy: { label: 'Add-on Acquisition Strategy', value: 'Active', detail: 'Buy-and-build in core verticals' },
    emergingThemes: { label: 'Emerging Themes', value: 'AI, Infrastructure, Specialty Finance', detail: 'Cross-portfolio themes' },
    comparables: { label: 'Suggested Comparable PE Firms', value: TOP_FIRMS.filter((f) => f.slug !== firm.slug).slice(0, 3).map((f) => f.name).join(', '), detail: 'By AUM and strategy overlap' },
  };
}

export function getPeOverview({ sector = null } = {}) {
  const feed = sector
    ? RESEARCH_FEED.filter((item) => item.sector === sector)
    : RESEARCH_FEED;

  return {
    updatedAt: new Date().toISOString(),
    kpis: PLATFORM_KPIS,
    firms: TOP_FIRMS.map(({ slug, name, logo, aum, hq }) => ({ slug, name, logo, aum, hq })),
    feed,
    transactions: TRANSACTIONS,
    funds: FUNDS,
    caseStudies: CASE_STUDIES,
    sectors: SECTORS.map((name) => ({ name, heat: sectorHeat(name) })),
    regions: REGIONS,
    aiInsights: AI_INSIGHTS,
    dataSources: {
      kkrPortfolio: loadKkrPortfolio().length,
      crawlerReady: true,
    },
  };
}

export function getPeFirm(slug) {
  const firm = TOP_FIRMS.find((f) => f.slug === slug);
  if (!firm) return null;

  const portfolio = portfolioForFirm(slug);
  const analytics = analyticsFromPortfolio(portfolio);
  const criteria = INVESTMENT_CRITERIA[slug] || {
    revenue: 'Varies by strategy',
    ebitda: 'Varies by strategy',
    enterpriseValue: 'Varies by strategy',
    equityCheck: 'Varies by strategy',
    ownership: 'Control / significant minority',
    industries: firm.industries,
    geography: firm.geoFocus,
  };

  return {
    ...firm,
    overview: {
      history: `${firm.name} was founded in ${firm.founded} and is headquartered in ${firm.hq}. The firm manages ${firm.aum} in assets with a focus on ${firm.industries.slice(0, 3).join(', ')}.`,
      philosophy: firm.strategy,
      positioning: `Competitive positioning among global mega-cap sponsors with ${firm.portfolioCount}+ portfolio companies and ${firm.fundCount}+ funds.`,
      operatingModel: 'Sector-specialist teams with centralized capital formation and portfolio operations support.',
    },
    portfolio,
    portfolioTotal: slug === 'kkr' ? portfolio.length : firm.portfolioCount,
    investmentCriteria: criteria,
    transactions: TRANSACTIONS.filter((t) => t.buyer.toLowerCase().includes(firm.name.split(' ')[0].toLowerCase())).slice(0, 8),
    funds: FUNDS.filter((f) => f.gp.toLowerCase().includes(firm.name.split(' ')[0].toLowerCase())),
    team: TEAM_SAMPLE.map((m) => ({ ...m, firm: firm.name })),
    news: RESEARCH_FEED.filter((n) => n.firmSlug === slug),
    caseStudies: CASE_STUDIES.filter((c) => c.firmSlug === slug),
    esg: {
      framework: `${firm.name} ESG integration framework across portfolio monitoring and reporting.`,
      goals: 'Net-zero pathway alignment, diversity targets, governance standards.',
      diversity: 'Board and management diversity metrics tracked at portfolio level.',
      governance: 'Institutional LP reporting and stewardship policies.',
      initiatives: ['Portfolio carbon baseline', 'DEI benchmarking', 'Responsible sourcing'],
    },
    analytics,
    aiInsights: firmAiInsights(firm, portfolio),
    dataSource: slug === 'kkr' ? 'live_crawler' : 'seed_v1',
  };
}

export function listPeFirms() {
  return TOP_FIRMS;
}
