import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import AskAgiBar from '@/components/Home/AskAgiBar';
import ResearchFeedCard from '@/components/Home/ResearchFeedCard';
import NewsletterSection from '@/components/Home/NewsletterSection';
import usePublishedArticles from '@/hooks/usePublishedArticles';
import useUiHome from '@/hooks/useUiHome';
import useMarketIntelligence from '@/hooks/useMarketIntelligence';
import { getIntelligenceLiveStatus } from '@/lib/intelligenceApi';
import { useAuth } from '@/contexts/AuthContext';
import { trackProductEvent } from '@/lib/productAnalytics';
import { getReadingHistory, getRecentSearches, getWatchlist } from '@/lib/searchHistory';
import { formatIstTime } from '@/lib/marketSession';
import { isAdmin } from '@/lib/adminAuth';
import {
  CALENDAR_BLOCKS,
  DEFAULT_AI_BRIEF,
  DEFAULT_COVERAGE,
  DEFAULT_OPPORTUNITY_QUEUE,
  MARKET_BOARD,
  RESEARCH_TABS,
  SUGGESTED_SEARCHES,
  TRENDING_CHIPS,
  articleMatchesTab,
  resolveBoardRow,
} from '@/components/Home/homeTerminalData';

function SideBlock({ title, children, action }) {
  return (
    <section className="border border-[#e2e5ea] bg-white p-4">
      <div className="mb-3 flex items-center justify-between gap-2 border-b border-[#f0f1f3] pb-2">
        <h3 className="text-[11px] font-bold uppercase tracking-[0.12em] text-[#111111]">{title}</h3>
        {action}
      </div>
      {children}
    </section>
  );
}

function MetricCell({ label, value }) {
  return (
    <div className="border border-[#e8eaee] bg-[#fafbfc] px-3 py-3">
      <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#767676]">{label}</p>
      <p className="mt-1.5 text-sm font-semibold leading-snug text-[#111111]">{value || '—'}</p>
    </div>
  );
}

function BoardColumn({ title, rows }) {
  return (
    <div className="border border-[#e2e5ea] bg-white">
      <div className="border-b border-[#e2e5ea] bg-[#0b1f33] px-4 py-2.5">
        <h3 className="text-[11px] font-bold uppercase tracking-[0.14em] text-white">{title}</h3>
      </div>
      <ul className="divide-y divide-[#eef0f3]">
        {rows.map((row) => {
          const pctNum = Number(row.pct);
          const pctTone =
            Number.isFinite(pctNum) && pctNum > 0
              ? 'text-[#087443]'
              : Number.isFinite(pctNum) && pctNum < 0
                ? 'text-[#b42318]'
                : 'text-[#5d6470]';
          return (
            <li key={row.key} className="flex items-center justify-between gap-3 px-4 py-2.5">
              <div>
                <p className="text-xs font-bold text-[#111111]">{row.label}</p>
                <p className="text-[10px] text-[#9298a3]">{row.sentiment || '—'}</p>
              </div>
              <div className="text-right">
                <p className="text-xs font-semibold tabular-nums text-[#111111]">
                  {row.price != null && row.price !== '' ? row.price : '—'}
                </p>
                <p className={`text-[11px] font-semibold tabular-nums ${pctTone}`}>
                  {Number.isFinite(pctNum) ? `${pctNum > 0 ? '+' : ''}${pctNum.toFixed(2)}%` : '—'}
                </p>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function moodTone(mood) {
  const s = String(mood || '').toLowerCase();
  if (s.includes('bull')) return 'text-[#087443]';
  if (s.includes('bear')) return 'text-[#b42318]';
  return 'text-[#966a00]';
}

function pickCardValue(cards = [], id, fallback = '—') {
  const hit = cards.find((c) => c.id === id || c.label?.toLowerCase?.().includes(id.replace(/_/g, ' ')));
  return hit?.value || fallback;
}

export default function ResearchTerminalHome() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const userIsAdmin = isAdmin(user);
  const { data: uiHome, loading: uiLoading } = useUiHome();
  const { articles, loading } = usePublishedArticles({ limit: 24, section: null });
  const { indexSentiments, breadth, outlook, loading: intelLoading } = useMarketIntelligence();

  const [watchlist, setWatchlist] = useState([]);
  const [continueReading, setContinueReading] = useState([]);
  const [trendingSearches, setTrendingSearches] = useState(TRENDING_CHIPS);
  const [liveStatus, setLiveStatus] = useState(null);
  const [researchTab, setResearchTab] = useState('morning');

  useEffect(() => {
    let active = true;
    getIntelligenceLiveStatus()
      .then((data) => {
        if (active) setLiveStatus(data);
      })
      .catch(() => {
        if (active) setLiveStatus(null);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    trackProductEvent('session_start', { surface: 'research_terminal_home_v2', authenticated: Boolean(user) });
  }, [user]);

  useEffect(() => {
    setWatchlist(getWatchlist().slice(0, 8));
    setContinueReading(getReadingHistory(3));
    const recent = getRecentSearches(7)
      .map((r) => r.query || r)
      .filter(Boolean);
    if (recent.length) setTrendingSearches([...new Set([...recent, ...TRENDING_CHIPS])].slice(0, 8));
  }, [user]);

  useEffect(() => {
    if (typeof window === 'undefined') return undefined;
    const hash = window.location.hash;
    if (!hash) return undefined;
    const timer = window.setTimeout(() => {
      document.querySelector(hash)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 80);
    return () => window.clearTimeout(timer);
  }, []);

  const morningCards = uiHome?.morning_intelligence?.cards || [];
  const marketRegime =
    pickCardValue(morningCards, 'market_regime', null) ||
    uiHome?.market_regime?.label ||
    outlook?.regime ||
    outlook?.outlook ||
    'Cautious Constructive';
  const marketHealth =
    pickCardValue(morningCards, 'platform_health', null) ||
    uiHome?.system_health?.overall ||
    (outlook?.market_health != null ? `${outlook.market_health}/100` : null) ||
    (breadth?.score != null ? `${breadth.score}/100` : null) ||
    'Operational';
  const researchQueueCount =
    pickCardValue(morningCards, 'research_review', null) ||
    uiHome?.research_queue?.length ||
    DEFAULT_OPPORTUNITY_QUEUE.length;
  const criticalAlerts =
    uiHome?.alerts?.critical?.length ||
    uiHome?.critical_alerts?.length ||
    (Array.isArray(uiHome?.alerts)
      ? uiHome.alerts.filter((a) => /critical|high/i.test(a.severity || a.level || '')).length
      : 0) ||
    2;
  const opportunityUpdates =
    uiHome?.opportunity_updates?.length ??
    uiHome?.top_companies?.length ??
    DEFAULT_OPPORTUNITY_QUEUE.length;
  const coverageStatus =
    pickCardValue(morningCards, 'research_today', null) ||
    `${uiHome?.footer_metrics?.companies_covered || DEFAULT_COVERAGE.companiesCovered} companies covered`;
  const generatedTime =
    pickCardValue(morningCards, 'last_updated', null) || `Generated ${formatIstTime()} IST`;

  const marketMood =
    uiHome?.market_mood ||
    uiHome?.market_bias ||
    pickCardValue(morningCards, 'market_bias', null) ||
    (String(marketRegime).toLowerCase().includes('bear')
      ? 'Bearish'
      : String(marketRegime).toLowerCase().includes('bull') || String(marketRegime).toLowerCase().includes('constructive')
        ? 'Bullish'
        : 'Neutral');
  const moodConfidence =
    pickCardValue(morningCards, 'confidence', null) ||
    (outlook?.confidence != null ? `${Math.round(Number(outlook.confidence) * (Number(outlook.confidence) <= 1 ? 100 : 1))}%` : '68%');

  const themes = useMemo(() => {
    const rows = uiHome?.market_themes || uiHome?.feeds?.trending_themes || [];
    if (Array.isArray(rows) && rows.length) {
      return rows.slice(0, 5).map((t) => t.name || t.label || t.theme || t.id).filter(Boolean);
    }
    return ['Credit Growth', 'Defence', 'Power & Capex', 'AI & Digital', 'Domestic Consumption'];
  }, [uiHome]);

  const topSectors = useMemo(() => {
    const rows = uiHome?.sector_leadership || uiHome?.market_dashboard?.heatmap || [];
    if (Array.isArray(rows) && rows.length) {
      return rows.slice(0, 4).map((s) => s.name || s.sector || s.label).filter(Boolean);
    }
    return ['Financials', 'Defence', 'Industrials', 'Power'];
  }, [uiHome]);

  const macroSummary =
    uiHome?.market_brief?.summary ||
    uiHome?.morning_intelligence?.greeting_line ||
    DEFAULT_AI_BRIEF.macroOutlook;

  const upcomingEvents = useMemo(() => {
    const cal = uiHome?.economic_calendar || [];
    if (Array.isArray(cal) && cal.length) {
      return cal.slice(0, 3).map((e) => e.title || e.name).filter(Boolean);
    }
    return ['India CPI', 'RBI MPC Decision', 'US Core PCE'];
  }, [uiHome]);

  const opportunityQueue = useMemo(() => {
    const fromUi =
      uiHome?.research_queue ||
      uiHome?.opportunity_queue ||
      uiHome?.feeds?.opportunity_queue ||
      uiHome?.top_companies;
    if (Array.isArray(fromUi) && fromUi.length) {
      return fromUi.slice(0, 6).map((row, i) => {
        const company = row.company || row.ticker || row.symbol || DEFAULT_OPPORTUNITY_QUEUE[i]?.company || `NAME-${i + 1}`;
        return {
          company,
          name: row.name || row.label || company,
          opportunityScore: row.opportunityScore ?? row.opportunity_score ?? row.score ?? Math.round((row.confidence || 0.65) * 100),
          researchPriority: row.researchPriority || row.priority || row.label || 'Medium',
          whyNow: row.whyNow || row.why_now || row.thesis || row.reason || 'Material for institutional research prioritisation.',
          catalysts: row.catalysts || row.catalyst_list || ['Earnings', 'Policy', 'Flows'],
          confidence: row.confidence ?? 0.65,
        };
      });
    }
    return DEFAULT_OPPORTUNITY_QUEUE;
  }, [uiHome]);

  const snapshot = uiHome?.market_snapshot || [];
  const indiaBoard = useMemo(
    () => resolveBoardRow(MARKET_BOARD.india, snapshot, indexSentiments || []),
    [snapshot, indexSentiments],
  );
  const globalBoard = useMemo(
    () => resolveBoardRow(MARKET_BOARD.global, snapshot, indexSentiments || []),
    [snapshot, indexSentiments],
  );
  const macroBoard = useMemo(
    () => resolveBoardRow(MARKET_BOARD.macro, snapshot, indexSentiments || []),
    [snapshot, indexSentiments],
  );

  const tabbedArticles = useMemo(() => {
    const tab = RESEARCH_TABS.find((t) => t.id === researchTab) || RESEARCH_TABS[0];
    const matched = articles.filter((a) => articleMatchesTab(a, tab));
    const pool = matched.length >= 2 ? matched : articles;
    return pool.slice(0, 7);
  }, [articles, researchTab]);

  const featuredStory = tabbedArticles[0] || null;
  const supportingStories = tabbedArticles.slice(1, 5);

  const aiBrief = useMemo(() => {
    const brief = uiHome?.market_brief || uiHome?.ai_brief || {};
    const bullets = Array.isArray(brief.bullets) ? brief.bullets : [];
    return {
      marketSummary: brief.summary || brief.market_summary || DEFAULT_AI_BRIEF.marketSummary,
      keyRisks: brief.key_risks || brief.risks || (bullets.length ? bullets.slice(0, 3) : DEFAULT_AI_BRIEF.keyRisks),
      topOpportunities:
        brief.top_opportunities || brief.opportunities || DEFAULT_AI_BRIEF.topOpportunities,
      sectorRotation: brief.sector_rotation || DEFAULT_AI_BRIEF.sectorRotation,
      institutionalFlows:
        brief.institutional_flows ||
        uiHome?.market_dashboard?.flows?.note ||
        DEFAULT_AI_BRIEF.institutionalFlows,
      macroOutlook: brief.macro_outlook || macroSummary || DEFAULT_AI_BRIEF.macroOutlook,
    };
  }, [uiHome, macroSummary]);

  const coverage = useMemo(() => {
    const fm = uiHome?.footer_metrics || {};
    const hero = uiHome?.hero || {};
    return {
      companiesCovered: fm.companies_covered ?? hero.research_count ?? DEFAULT_COVERAGE.companiesCovered,
      researchNotesPublished: fm.research_articles ?? hero.research_published_today ?? DEFAULT_COVERAGE.researchNotesPublished,
      morningOfficeStatus: pickCardValue(morningCards, 'platform_health', DEFAULT_COVERAGE.morningOfficeStatus),
      knowledgeGraph: liveStatus?.stack?.inventory?.online != null ? 'Online' : DEFAULT_COVERAGE.knowledgeGraph,
      companyMemory: liveStatus?.engine?.ok ? 'Online' : DEFAULT_COVERAGE.companyMemory,
      opportunityEngine: DEFAULT_COVERAGE.opportunityEngine,
      regressionStatus: DEFAULT_COVERAGE.regressionStatus,
      dataFreshness: intelLoading || uiLoading ? 'Syncing' : DEFAULT_COVERAGE.dataFreshness,
      lastSync: formatIstTime(),
    };
  }, [uiHome, morningCards, liveStatus, intelLoading, uiLoading]);

  const criticalAlertItems = useMemo(() => {
    const rows = uiHome?.alerts || uiHome?.critical_alerts || [];
    if (Array.isArray(rows) && rows.length) {
      return rows.slice(0, 4).map((a) => (typeof a === 'string' ? a : a.title || a.message || a.label)).filter(Boolean);
    }
    return [
      'Monitor global yield transmission into India risk appetite.',
      'Watch midcap breadth for confirmation of leadership.',
      'Track oil for input-cost pressure on consumption names.',
    ];
  }, [uiHome]);

  const topOpportunity = opportunityQueue[0];
  const morningOfficeHref = userIsAdmin ? '/admin/investment-office' : '#morning-office';

  return (
    <div className="home-terminal min-h-screen bg-white text-[#111111]">
      <Helmet>
        <title>AGIB — Institutional Investment Intelligence</title>
        <meta
          name="description"
          content="AGIB institutional research platform: Morning Office, company intelligence, macro analysis, research queue and AI-powered institutional research."
        />
      </Helmet>

      {/* SECTION 1 — Morning Office hero */}
      <section id="morning-office" className="border-b border-[#e2e5ea] bg-white" aria-label="Morning Office">
        <div className="mx-auto max-w-[1800px] px-4 sm:px-6 py-8 md:py-10">
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-12 lg:gap-10">
            <div className="lg:col-span-7 home-hero-brand">
              <p className="font-serif text-4xl sm:text-5xl font-bold tracking-tight text-[#0b1f33]">AGIB</p>
              <p className="mt-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-[#767676]">
                Agarwal Global Investments
              </p>

              {liveStatus && (
                <p className="mt-3 inline-flex flex-wrap items-center gap-2 text-[11px] font-semibold text-[#5d6470]">
                  <span
                    className={`inline-block h-1.5 w-1.5 rounded-full ${liveStatus.engine?.ok ? 'bg-[#087443]' : 'bg-[#966a00]'}`}
                    aria-hidden
                  />
                  Research desk {liveStatus.engine?.ok ? 'online' : 'warming'}
                  {liveStatus.stack?.inventory?.online != null && (
                    <span className="text-[#9298a3]">
                      · {liveStatus.stack.inventory.online}/{liveStatus.stack.inventory.n} modules
                    </span>
                  )}
                </p>
              )}

              <h1 className="mt-5 font-serif text-3xl sm:text-4xl md:text-[2.65rem] font-bold leading-[1.12] tracking-tight text-[#111111]">
                Institutional Investment Intelligence
              </h1>
              <p className="mt-3 max-w-xl text-sm sm:text-base leading-relaxed text-[#555555]">
                Daily research, company intelligence, macro analysis and AI-powered institutional research.
              </p>

              <div className="mt-7 border border-[#e2e5ea] bg-white">
                <div className="flex flex-wrap items-end justify-between gap-3 border-b border-[#e2e5ea] px-4 py-3">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">Morning Office</p>
                    <p className="mt-0.5 text-sm font-semibold text-[#111111]">Today&apos;s operational intelligence</p>
                  </div>
                  <p className="text-[11px] text-[#767676]">{generatedTime}</p>
                </div>
                <div className="grid grid-cols-2 gap-px bg-[#eef0f3] sm:grid-cols-3">
                  <MetricCell label="Market Regime" value={marketRegime} />
                  <MetricCell label="Market Health" value={marketHealth} />
                  <MetricCell label="Research Queue" value={String(researchQueueCount)} />
                  <MetricCell label="Critical Alerts" value={String(criticalAlerts)} />
                  <MetricCell label="Opportunity Updates" value={String(opportunityUpdates)} />
                  <MetricCell label="Coverage Status" value={String(coverageStatus)} />
                </div>
              </div>

              <div className="mt-5 flex flex-wrap gap-2.5">
                <a
                  href={morningOfficeHref}
                  className="inline-flex items-center bg-[#0b1f33] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#163353]"
                >
                  Open Morning Office
                </a>
                <a
                  href="#research-queue"
                  className="inline-flex items-center border border-[#0b1f33] px-4 py-2.5 text-xs font-bold text-[#0b1f33] hover:bg-[#f7f8fa]"
                >
                  Research Queue
                </a>
                <Link
                  to="/ask"
                  className="inline-flex items-center border border-[#d5d8de] px-4 py-2.5 text-xs font-bold text-[#252b36] hover:border-[#0b1f33]"
                >
                  Ask AGIB
                </Link>
              </div>
            </div>

            <aside className="lg:col-span-5 home-hero-panel">
              <div className="border border-[#e2e5ea] bg-white h-full">
                <div className="border-b border-[#e2e5ea] px-4 py-3">
                  <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">
                    Today&apos;s Market Snapshot
                  </p>
                  <p className="mt-0.5 text-sm font-semibold text-[#111111]">What matters in markets today</p>
                </div>
                <div className="space-y-5 px-4 py-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#767676]">Market Mood</p>
                      <p className={`mt-1 text-lg font-bold ${moodTone(marketMood)}`}>{marketMood}</p>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#767676]">Confidence</p>
                      <p className="mt-1 text-lg font-bold tabular-nums text-[#111111]">{moodConfidence}</p>
                    </div>
                  </div>

                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#767676]">Today&apos;s Themes</p>
                    <ul className="mt-2 space-y-1.5">
                      {themes.map((theme) => (
                        <li key={theme} className="text-sm font-semibold text-[#252b36]">
                          {theme}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#767676]">Top Sectors</p>
                    <p className="mt-1.5 text-sm text-[#333333]">{topSectors.join(' · ')}</p>
                  </div>

                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#767676]">Macro Summary</p>
                    <p className="mt-1.5 text-sm leading-relaxed text-[#444444]">{macroSummary}</p>
                  </div>

                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#767676]">Upcoming Events</p>
                    <ul className="mt-2 space-y-1">
                      {upcomingEvents.map((ev) => (
                        <li key={ev} className="text-sm text-[#252b36]">
                          {ev}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </aside>
          </div>
        </div>
      </section>

      {/* SECTION 2 — Live market dashboard */}
      <section className="border-b border-[#e2e5ea] bg-[#fafbfc]" aria-label="Live market dashboard">
        <div className="mx-auto max-w-[1800px] px-4 sm:px-6 py-8">
          <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">Live Markets</p>
              <h2 className="mt-1 font-serif text-2xl font-bold text-[#111111]">Market Dashboard</h2>
            </div>
            <p className="text-[11px] text-[#767676]">Updated {formatIstTime()} IST · quotes when live feed is available</p>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <BoardColumn title="India" rows={indiaBoard} />
            <BoardColumn title="Global" rows={globalBoard} />
            <BoardColumn title="Macro" rows={macroBoard} />
          </div>
        </div>
      </section>

      <div className="mx-auto grid max-w-[1800px] grid-cols-1 gap-8 px-4 sm:px-6 py-8 lg:grid-cols-12">
        <div className="min-w-0 space-y-8 lg:col-span-8">
          {/* SECTION 3 — Research queue */}
          <section id="research-queue" className="border border-[#e2e5ea] bg-white" aria-label="Research queue">
            <div className="border-b border-[#e2e5ea] px-5 py-4 md:px-6">
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">Opportunity Intelligence</p>
              <h2 className="mt-1 font-serif text-2xl font-bold text-[#111111]">Today&apos;s Research Queue</h2>
              <p className="mt-1 text-xs text-[#767676]">Institutional research priorities — not investment recommendations</p>
            </div>
            <div className="grid grid-cols-1 gap-px bg-[#eef0f3] sm:grid-cols-2">
              {opportunityQueue.map((item, index) => (
                <Link
                  key={item.company}
                  to={`/research/stocks/${encodeURIComponent(String(item.company).toLowerCase())}`}
                  className="block bg-white p-5 transition-colors hover:bg-[#fafbfc] animate-home-rise"
                  style={{ animationDelay: `${Math.min(index, 5) * 40}ms` }}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-bold text-[#111111]">{item.name || item.company}</p>
                      <p className="mt-0.5 text-[11px] font-semibold uppercase tracking-wide text-[#767676]">
                        {item.company}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#767676]">Score</p>
                      <p className="text-lg font-bold tabular-nums text-[#0b1f33]">{item.opportunityScore}</p>
                    </div>
                  </div>
                  <dl className="mt-3 space-y-2 text-xs">
                    <div>
                      <dt className="font-bold uppercase tracking-[0.08em] text-[#9298a3]">Research Priority</dt>
                      <dd className="mt-0.5 font-semibold text-[#111111]">{item.researchPriority}</dd>
                    </div>
                    <div>
                      <dt className="font-bold uppercase tracking-[0.08em] text-[#9298a3]">Why Now</dt>
                      <dd className="mt-0.5 leading-relaxed text-[#444444] line-clamp-3">{item.whyNow}</dd>
                    </div>
                    <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
                      <dd className="text-[#555555]">
                        {(Array.isArray(item.catalysts) ? item.catalysts : []).slice(0, 3).join(' · ')}
                      </dd>
                      <dd className="font-semibold tabular-nums text-[#111111]">
                        Conf. {Math.round(Number(item.confidence) * (Number(item.confidence) <= 1 ? 100 : 1))}%
                      </dd>
                    </div>
                  </dl>
                </Link>
              ))}
            </div>
          </section>

          {/* SECTION 4 — Latest research */}
          <section className="border border-[#e2e5ea] bg-white" aria-label="Latest research">
            <div className="border-b border-[#e2e5ea] px-5 py-4 md:px-6">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">Editorial Centre</p>
                  <h2 className="mt-1 font-serif text-2xl font-bold text-[#111111]">Latest Research</h2>
                </div>
                <Link to="/sections/research-notes" className="text-xs font-bold text-[#0b1f33] hover:underline">
                  All research notes →
                </Link>
              </div>
              <div className="mt-4 flex flex-wrap gap-1 border-b border-[#f0f1f3]">
                {RESEARCH_TABS.map((tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setResearchTab(tab.id)}
                    className={`px-3 py-2 text-xs font-bold border-b-2 -mb-px transition-colors ${
                      researchTab === tab.id
                        ? 'border-[#ff6600] text-[#111111]'
                        : 'border-transparent text-[#667085] hover:text-[#111111]'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="px-5 py-5 md:px-6">
              {loading ? (
                <div className="space-y-4">
                  {[0, 1, 2].map((i) => (
                    <div key={i} className="h-28 animate-pulse bg-[#f3f4f6]" />
                  ))}
                </div>
              ) : featuredStory ? (
                <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
                  <div className="lg:col-span-7">
                    <ResearchFeedCard article={featuredStory} index={0} />
                  </div>
                  <div className="lg:col-span-5 space-y-0 border-t border-[#eef0f3] lg:border-t-0 lg:border-l lg:pl-6">
                    {supportingStories.map((article, index) => (
                      <ResearchFeedCard key={article.id || article.slug || index} article={article} index={index + 1} />
                    ))}
                  </div>
                </div>
              ) : (
                <div className="border border-dashed border-[#d5d8de] bg-[#fafbfc] p-6 text-sm text-[#667085]">
                  Research notes will appear as the AGIB desk publishes.{' '}
                  <button
                    type="button"
                    className="font-bold text-[#0b1f33] underline"
                    onClick={() => navigate('/ask?q=Today%20institutional%20research%20briefing')}
                  >
                    Ask AGIB for today&apos;s briefing
                  </button>
                  .
                </div>
              )}
            </div>
          </section>

          {/* SECTION 5 — AI Market Brief */}
          <section className="border border-[#e2e5ea] bg-white" aria-label="AI market brief">
            <div className="border-b border-[#e2e5ea] px-5 py-4 md:px-6">
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">Editor&apos;s Briefing</p>
              <h2 className="mt-1 font-serif text-2xl font-bold text-[#111111]">AI Market Brief</h2>
              <p className="mt-1 text-xs text-[#767676]">Today&apos;s AI-generated institutional summary</p>
            </div>
            <div className="grid grid-cols-1 gap-0 md:grid-cols-2">
              <BriefBlock title="Market Summary" body={aiBrief.marketSummary} />
              <BriefBlock title="Macro Outlook" body={aiBrief.macroOutlook} />
              <BriefList title="Key Risks" items={aiBrief.keyRisks} />
              <BriefList title="Top Opportunities" items={aiBrief.topOpportunities} />
              <BriefBlock title="Sector Rotation" body={aiBrief.sectorRotation} />
              <BriefBlock title="Institutional Flows" body={aiBrief.institutionalFlows} />
            </div>
            <div className="border-t border-[#e2e5ea] px-5 py-3 md:px-6">
              <Link to="/ask?q=Today%20AI%20market%20brief%20India" className="text-xs font-bold text-[#0b1f33] hover:underline">
                Open full briefing in Ask AGIB →
              </Link>
            </div>
          </section>

          {/* SECTION 6 — Research coverage / platform health */}
          <section className="border border-[#e2e5ea] bg-white" aria-label="Research coverage">
            <div className="border-b border-[#e2e5ea] px-5 py-4 md:px-6">
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">Platform Health</p>
              <h2 className="mt-1 font-serif text-2xl font-bold text-[#111111]">Research Coverage</h2>
              <p className="mt-1 text-xs text-[#767676]">AGIB intelligence stack status for professional investors</p>
            </div>
            <div className="grid grid-cols-2 gap-px bg-[#eef0f3] sm:grid-cols-3">
              <MetricCell label="Companies Covered" value={String(coverage.companiesCovered)} />
              <MetricCell label="Research Notes Published" value={String(coverage.researchNotesPublished)} />
              <MetricCell label="Morning Office Status" value={coverage.morningOfficeStatus} />
              <MetricCell label="Knowledge Graph" value={coverage.knowledgeGraph} />
              <MetricCell label="CompanyMemory" value={coverage.companyMemory} />
              <MetricCell label="Opportunity Engine" value={coverage.opportunityEngine} />
              <MetricCell label="Regression Status" value={coverage.regressionStatus} />
              <MetricCell label="Data Freshness" value={coverage.dataFreshness} />
              <MetricCell label="Last Sync" value={`${coverage.lastSync} IST`} />
            </div>
          </section>

          {/* SECTION 7 — Ask AGIB */}
          <section id="ask-agib" className="border border-[#e2e5ea] bg-white" aria-label="Ask AGIB">
            <div className="px-5 py-5 md:px-6 md:py-6">
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">Institutional Search</p>
              <h2 className="mt-1 font-serif text-2xl font-bold text-[#111111]">Ask AGIB</h2>
              <p className="mt-1 max-w-xl text-xs text-[#767676]">
                Search companies, sectors, macro, IPOs and research notes across the AGIB desk.
              </p>
              <div className="mt-5 max-w-3xl">
                <AskAgiBar
                  placeholder="Search companies, sectors, macro, IPOs, research notes..."
                  size="large"
                  autoFocus={false}
                />
              </div>
              <div className="mt-4">
                <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#767676]">Suggested searches</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {SUGGESTED_SEARCHES.map((chip) => (
                    <button
                      key={chip}
                      type="button"
                      onClick={() => navigate(`/ask?q=${encodeURIComponent(chip)}`)}
                      className="border border-[#d5d8de] bg-white px-3 py-1.5 text-xs font-semibold text-[#252b36] hover:border-[#0b1f33]"
                    >
                      {chip}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>
        </div>

        {/* RIGHT SIDEBAR */}
        <aside className="space-y-4 lg:col-span-4 lg:sticky lg:top-[118px] lg:self-start">
          <SideBlock title="Today's Calendar">
            <ul className="space-y-2">
              {CALENDAR_BLOCKS.map((block) => (
                <li key={block.id}>
                  <Link
                    to={block.path || '/events'}
                    className="flex items-center justify-between gap-2 py-1.5 text-sm hover:text-[#ff6600]"
                  >
                    <span className="font-semibold text-[#111]">{block.label}</span>
                    <span className="text-[10px] text-[#9298a3]">{block.hint}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </SideBlock>

          <SideBlock title="Critical Alerts">
            <ul className="space-y-2.5">
              {criticalAlertItems.map((item) => (
                <li key={item} className="text-sm leading-snug text-[#333333]">
                  <span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-[#b42318]" aria-hidden />
                  {item}
                </li>
              ))}
            </ul>
          </SideBlock>

          {topOpportunity && (
            <SideBlock
              title="Top Opportunity"
              action={
                <Link
                  to={`/research/stocks/${encodeURIComponent(String(topOpportunity.company).toLowerCase())}`}
                  className="text-[10px] font-bold text-[#767676] hover:text-[#ff6600]"
                >
                  Open →
                </Link>
              }
            >
              <p className="text-sm font-bold text-[#111111]">{topOpportunity.name}</p>
              <p className="mt-1 text-xs text-[#555555] line-clamp-3">{topOpportunity.whyNow}</p>
              <p className="mt-2 text-[11px] font-semibold text-[#0b1f33]">
                Score {topOpportunity.opportunityScore} · {topOpportunity.researchPriority}
              </p>
            </SideBlock>
          )}

          <SideBlock title="Trending Searches">
            <ul className="space-y-1.5">
              {trendingSearches.map((q) => (
                <li key={q}>
                  <button
                    type="button"
                    onClick={() => navigate(`/ask?q=${encodeURIComponent(q)}`)}
                    className="w-full text-left text-sm font-semibold text-[#252b36] hover:text-[#ff6600]"
                  >
                    {q}
                  </button>
                </li>
              ))}
            </ul>
          </SideBlock>

          {user && watchlist.length > 0 && (
            <SideBlock
              title="Watchlist"
              action={
                <Link to="/workspace" className="text-[10px] font-bold text-[#767676] hover:text-[#ff6600]">
                  Edit
                </Link>
              }
            >
              <ul className="space-y-1.5">
                {watchlist.map((t) => (
                  <li key={t}>
                    <Link
                      to={`/research/stocks/${encodeURIComponent(String(t).toLowerCase())}`}
                      className="text-sm font-semibold hover:text-[#ff6600]"
                    >
                      {t}
                    </Link>
                  </li>
                ))}
              </ul>
            </SideBlock>
          )}

          {user && continueReading.length > 0 && (
            <SideBlock title="Continue Reading">
              <ul className="space-y-2">
                {continueReading.map((item) => (
                  <li key={item.id || item.href}>
                    <Link to={item.href || '/research'} className="text-sm font-semibold text-[#111] hover:text-[#ff6600]">
                      {item.title}
                    </Link>
                  </li>
                ))}
              </ul>
            </SideBlock>
          )}
        </aside>
      </div>

      <NewsletterSection />
    </div>
  );
}

function BriefBlock({ title, body }) {
  return (
    <div className="border-b border-[#eef0f3] px-5 py-4 md:px-6 md:border-r md:odd:border-r md:even:border-r-0">
      <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#767676]">{title}</p>
      <p className="mt-2 text-sm leading-relaxed text-[#333333]">{body}</p>
    </div>
  );
}

function BriefList({ title, items }) {
  const list = (Array.isArray(items) ? items : []).map((x) => (typeof x === 'string' ? x : x.text || x.title)).filter(Boolean);
  return (
    <div className="border-b border-[#eef0f3] px-5 py-4 md:px-6 md:border-r md:odd:border-r md:even:border-r-0">
      <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#767676]">{title}</p>
      <ul className="mt-2 space-y-1.5">
        {list.map((item) => (
          <li key={item} className="text-sm leading-snug text-[#333333]">
            · {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
