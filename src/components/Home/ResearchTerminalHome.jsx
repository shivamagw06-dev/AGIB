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
import { getWatchlist } from '@/lib/searchHistory';
import { SESSIONS, formatIstTime, resolveMarketSession } from '@/lib/marketSession';
import { isAdmin } from '@/lib/adminAuth';
import {
  CALENDAR_BLOCKS,
  COMPANY_INTEL_EXAMPLES,
  COMPANY_INTEL_PANELS,
  DEFAULT_AI_BRIEF,
  DEFAULT_COVERAGE,
  DEFAULT_OPPORTUNITY_QUEUE,
  HERO_TRUST_LINE,
  MARKET_BOARD,
  POPULAR_ASK_QUESTIONS,
  POPULAR_RESEARCH_SEARCHES,
  RESEARCH_TABS,
  articleMatchesSession,
  articleMatchesTab,
  resolveBoardRow,
} from '@/components/Home/homeTerminalData';

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

function BriefBlock({ title, body }) {
  return (
    <div className="border-b border-[#eef0f3] px-5 py-4 md:px-6 md:border-r md:[&:nth-child(even)]:border-r-0">
      <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#767676]">{title}</p>
      <p className="mt-2 text-sm leading-relaxed text-[#333333]">{body}</p>
    </div>
  );
}

function BriefList({ title, items }) {
  const list = (Array.isArray(items) ? items : [])
    .map((x) => (typeof x === 'string' ? x : x.text || x.title))
    .filter(Boolean);
  return (
    <div className="border-b border-[#eef0f3] px-5 py-4 md:px-6 md:border-r md:[&:nth-child(even)]:border-r-0">
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

function pickCardValue(cards = [], id, fallback = '—') {
  const hit = cards.find((c) => c.id === id || c.label?.toLowerCase?.().includes(id.replace(/_/g, ' ')));
  return hit?.value || fallback;
}

function FeaturedStory({ article }) {
  if (!article) return null;
  const href = article.href || (article.slug ? `/article/${article.slug}` : '/research');
  const cover =
    article.cover_url ||
    article.coverUrl ||
    article.image ||
    'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1400&q=80';
  const excerpt = article.excerpt || article.summary || article.executiveSummary || '';
  const why =
    article.whyItMatters ||
    article.why_it_matters ||
    (excerpt ? `Institutional relevance: ${excerpt.slice(0, 160)}${excerpt.length > 160 ? '…' : ''}` : 'Material for portfolio and sector monitoring.');
  const companies = article.affectedCompanies || article.companies || article.tickers || [];
  const sectors = article.affectedSectors || (article.sector ? [article.sector] : article.category ? [article.category] : []);

  return (
    <article className="home-hero-panel">
      <Link to={href} className="block overflow-hidden border border-[#e2e5ea] bg-[#f4f5f7]">
        <img
          src={cover}
          alt=""
          className="aspect-[16/9] w-full object-cover"
          loading="eager"
        />
      </Link>
      <p className="mt-4 text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">
        {article.section || article.category || 'Featured Research'}
      </p>
      <h3 className="mt-2 font-serif text-2xl md:text-[1.85rem] font-bold leading-tight text-[#111111]">
        <Link to={href} className="hover:underline decoration-[#ff6600] underline-offset-4">
          {article.title}
        </Link>
      </h3>
      <dl className="mt-4 space-y-3 text-sm">
        <div>
          <dt className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#767676]">Executive Summary</dt>
          <dd className="mt-1 text-[#333] leading-relaxed line-clamp-4">{excerpt || 'Summary pending from AGI research desk.'}</dd>
        </div>
        <div>
          <dt className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#767676]">Why It Matters</dt>
          <dd className="mt-1 text-[#444] leading-relaxed line-clamp-3">{why}</dd>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <dt className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#767676]">Affected Companies</dt>
            <dd className="mt-1 text-[#252b36]">
              {(Array.isArray(companies) ? companies : []).slice(0, 4).map((c) => (typeof c === 'string' ? c : c.name || c.ticker)).filter(Boolean).join(', ') || '—'}
            </dd>
          </div>
          <div>
            <dt className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#767676]">Affected Sectors</dt>
            <dd className="mt-1 text-[#252b36]">
              {(Array.isArray(sectors) ? sectors : []).slice(0, 4).map((s) => (typeof s === 'string' ? s : s.name)).filter(Boolean).join(', ') || '—'}
            </dd>
          </div>
        </div>
      </dl>
      <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
        <p className="text-[11px] text-[#767676]">
          {article.readTime || article.read_time || '5 min read'}
          {' · '}
          Published {article.publishedLabel || article.date || 'Today'}
        </p>
        <Link
          to={href}
          className="inline-flex items-center bg-[#0b1f33] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#163353]"
        >
          Read Research →
        </Link>
      </div>
    </article>
  );
}

export default function ResearchTerminalHome() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const userIsAdmin = isAdmin(user);
  const { data: uiHome, loading: uiLoading } = useUiHome();
  const { articles, loading } = usePublishedArticles({ limit: 28, section: null });
  const { indexSentiments, outlook, loading: intelLoading } = useMarketIntelligence();
  const liveSession = resolveMarketSession();

  const [heroTab, setHeroTab] = useState('ask');
  const [researchTab, setResearchTab] = useState('morning');
  const [companyQuery, setCompanyQuery] = useState('');
  const [watchlist, setWatchlist] = useState([]);
  const [liveStatus, setLiveStatus] = useState(null);

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
    trackProductEvent('session_start', { surface: 'research_terminal_home_v3', authenticated: Boolean(user) });
  }, [user]);

  useEffect(() => {
    setWatchlist(getWatchlist().slice(0, 6));
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
    'Operational';
  const researchQueueCount =
    pickCardValue(morningCards, 'research_review', null) ||
    uiHome?.research_queue?.length ||
    DEFAULT_OPPORTUNITY_QUEUE.length;
  const criticalAlerts =
    uiHome?.alerts?.critical?.length ||
    uiHome?.critical_alerts?.length ||
    2;
  const opportunityUpdates =
    uiHome?.opportunity_updates?.length ||
    uiHome?.top_companies?.length ||
    DEFAULT_OPPORTUNITY_QUEUE.length;
  const coverageStatus =
    pickCardValue(morningCards, 'research_today', null) ||
    `${uiHome?.footer_metrics?.companies_covered || DEFAULT_COVERAGE.companiesCovered} companies covered`;
  const generatedTime = pickCardValue(morningCards, 'last_updated', null) || `Generated ${formatIstTime()} IST`;

  const sessionCounts = useMemo(() => {
    return SESSIONS.map((session) => {
      const count = articles.filter((a) => articleMatchesSession(a, session)).length;
      return {
        ...session,
        count: count || (session.id === liveSession ? Math.max(3, Math.min(articles.length, 5)) : Math.max(0, Math.min(articles.length, session.id === 'morning' ? 5 : session.id === 'post' ? 3 : 2))),
        active: session.id === liveSession,
      };
    });
  }, [articles, liveSession]);

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
          opportunityScore:
            row.opportunityScore ?? row.opportunity_score ?? row.score ?? Math.round((row.confidence || 0.65) * 100),
          researchPriority: row.researchPriority || row.priority || row.label || 'Medium',
          whyNow: row.whyNow || row.why_now || row.thesis || row.reason || 'Material for institutional research prioritisation.',
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
    return pool.slice(0, 8);
  }, [articles, researchTab]);

  const featuredStory = tabbedArticles[0] || null;
  const latestNotes = tabbedArticles.slice(1, 7);

  const aiBrief = useMemo(() => {
    const brief = uiHome?.market_brief || uiHome?.ai_brief || {};
    const bullets = Array.isArray(brief.bullets) ? brief.bullets : [];
    return {
      marketSummary: brief.summary || brief.market_summary || DEFAULT_AI_BRIEF.marketSummary,
      keyRisks: brief.key_risks || brief.risks || (bullets.length ? bullets.slice(0, 3) : DEFAULT_AI_BRIEF.keyRisks),
      topOpportunities: brief.top_opportunities || brief.opportunities || DEFAULT_AI_BRIEF.topOpportunities,
      sectorRotation: brief.sector_rotation || DEFAULT_AI_BRIEF.sectorRotation,
      institutionalFlows:
        brief.institutional_flows ||
        uiHome?.market_dashboard?.flows?.note ||
        DEFAULT_AI_BRIEF.institutionalFlows,
      macroOutlook: brief.macro_outlook || uiHome?.morning_intelligence?.greeting_line || DEFAULT_AI_BRIEF.macroOutlook,
    };
  }, [uiHome]);

  const coverage = useMemo(() => {
    const fm = uiHome?.footer_metrics || {};
    const hero = uiHome?.hero || {};
    return {
      companiesCovered: fm.companies_covered ?? hero.research_count ?? 2500,
      researchNotesToday: hero.research_published_today ?? pickCardValue(morningCards, 'research_today', '10+'),
      knowledgeGraph: liveStatus?.stack?.inventory?.online != null ? 'Online' : DEFAULT_COVERAGE.knowledgeGraph,
      companyMemory: liveStatus?.engine?.ok ? 'Online' : DEFAULT_COVERAGE.companyMemory,
      opportunityIntelligence: DEFAULT_COVERAGE.opportunityEngine,
      morningOffice: pickCardValue(morningCards, 'platform_health', DEFAULT_COVERAGE.morningOfficeStatus),
      coverageStatus: coverageStatus,
      dataFreshness: intelLoading || uiLoading ? 'Syncing' : DEFAULT_COVERAGE.dataFreshness,
      lastSync: formatIstTime(),
    };
  }, [uiHome, morningCards, liveStatus, intelLoading, uiLoading, coverageStatus]);

  const morningOfficeHref = userIsAdmin ? '/admin/investment-office' : '#morning-office';
  const popularAsk = uiHome?.example_questions?.slice?.(0, 5) || POPULAR_ASK_QUESTIONS;

  const openCompany = (raw) => {
    const value = String(raw || companyQuery).trim();
    if (!value) return;
    const symbol = value.toLowerCase().replace(/\s+/g, '');
    navigate(`/research/stocks/${encodeURIComponent(symbol)}`);
  };

  return (
    <div className="home-terminal min-h-screen bg-white text-[#111111]">
      <Helmet>
        <title>AGI — Institutional Investment Intelligence</title>
        <meta
          name="description"
          content="AGI institutional research platform: Ask AGI, read today's research, company intelligence, macro analysis and evidence-backed investment intelligence."
        />
      </Helmet>

      {/* SECTION 1 — Institutional Intelligence Workspace */}
      <section id="intelligence-workspace" className="border-b border-[#e2e5ea] bg-white" aria-label="Institutional intelligence workspace">
        <div className="mx-auto max-w-[1800px] px-4 sm:px-6 py-8 md:py-11">
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-12 lg:gap-10">
            <div className="lg:col-span-8 home-hero-brand">
              <p className="font-serif text-4xl sm:text-5xl font-bold tracking-tight text-[#0b1f33]">AGI</p>
              <p className="mt-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-[#767676]">
                Agarwal Global Investments · Independent Equity Research
              </p>

              <h1 className="mt-5 font-serif text-3xl sm:text-4xl md:text-[2.75rem] font-bold leading-[1.1] tracking-tight text-[#111111]">
                Institutional Investment Intelligence
              </h1>
              <p className="mt-3 max-w-2xl text-sm sm:text-base leading-relaxed text-[#555555]">
                Ask investment questions. Read institutional research. Make evidence-backed investment decisions.
              </p>

              <div className="mt-7 border border-[#e2e5ea] bg-white">
                <div className="flex border-b border-[#e2e5ea]" role="tablist" aria-label="Workspace mode">
                  <button
                    type="button"
                    role="tab"
                    aria-selected={heroTab === 'ask'}
                    onClick={() => setHeroTab('ask')}
                    className={`flex-1 px-4 py-3 text-sm font-bold transition-colors ${
                      heroTab === 'ask'
                        ? 'bg-white text-[#111111] border-b-2 border-[#ff6600]'
                        : 'bg-[#fafbfc] text-[#667085] hover:text-[#111]'
                    }`}
                  >
                    Ask AGI
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={heroTab === 'research'}
                    onClick={() => setHeroTab('research')}
                    className={`flex-1 px-4 py-3 text-sm font-bold transition-colors ${
                      heroTab === 'research'
                        ? 'bg-white text-[#111111] border-b-2 border-[#ff6600]'
                        : 'bg-[#fafbfc] text-[#667085] hover:text-[#111]'
                    }`}
                  >
                    Search Research Notes
                  </button>
                </div>

                <div className="p-4 sm:p-5" role="tabpanel">
                  {heroTab === 'ask' ? (
                    <>
                      <AskAgiBar
                        placeholder="Ask anything about companies, sectors, macro, IPOs, valuation, risks or markets..."
                        size="large"
                        autoFocus={false}
                        buttonLabel="Ask AGI"
                        ariaLabel="Ask AGI"
                      />
                      <div className="mt-4">
                        <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#767676]">Popular questions</p>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {popularAsk.map((q) => (
                            <button
                              key={q}
                              type="button"
                              onClick={() => navigate(`/ask?q=${encodeURIComponent(q)}`)}
                              className="border border-[#d5d8de] bg-white px-3 py-1.5 text-xs font-semibold text-[#252b36] hover:border-[#0b1f33]"
                            >
                              {q}
                            </button>
                          ))}
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      <AskAgiBar
                        placeholder="Search Morning Desk, Global Desk, Macro, IPO and Research Notes..."
                        size="large"
                        autoFocus={false}
                        buttonLabel="Search"
                        ariaLabel="Search research notes"
                        onAsk={(q) => navigate(`/research?q=${encodeURIComponent(q)}`)}
                      />
                      <div className="mt-4">
                        <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#767676]">Popular searches</p>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {POPULAR_RESEARCH_SEARCHES.map((q) => (
                            <button
                              key={q}
                              type="button"
                              onClick={() => navigate(`/research?q=${encodeURIComponent(q)}`)}
                              className="border border-[#d5d8de] bg-white px-3 py-1.5 text-xs font-semibold text-[#252b36] hover:border-[#0b1f33]"
                            >
                              {q}
                            </button>
                          ))}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>

              <p className="mt-4 text-[12px] leading-relaxed text-[#5d6470]">{HERO_TRUST_LINE}</p>
            </div>

            {/* Right — Today's Research Cycle */}
            <aside className="lg:col-span-4 home-hero-panel space-y-4">
              <div className="border border-[#e2e5ea] bg-white">
                <div className="border-b border-[#e2e5ea] px-4 py-3">
                  <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">Today&apos;s Research Cycle</p>
                  <h2 className="mt-0.5 text-sm font-bold text-[#111111]">Session Desk</h2>
                </div>
                <ul className="divide-y divide-[#eef0f3]">
                  {sessionCounts.map((session) => (
                    <li key={session.id}>
                      <button
                        type="button"
                        onClick={() => {
                          setResearchTab(session.id === 'pre' || session.id === 'afternoon' ? 'morning' : session.id === 'post' ? 'post' : session.id === 'global' ? 'global' : 'morning');
                          document.getElementById('todays-research')?.scrollIntoView({ behavior: 'smooth' });
                        }}
                        className={`flex w-full items-center justify-between gap-3 px-4 py-3 text-left hover:bg-[#fafbfc] ${
                          session.active ? 'bg-[#f7f8fa]' : ''
                        }`}
                      >
                        <div>
                          <p className="text-sm font-bold text-[#111111]">
                            {session.label}
                            {session.active && (
                              <span className="ml-2 text-[10px] font-bold uppercase tracking-wide text-[#ff6600]">Live</span>
                            )}
                          </p>
                          <p className="text-[11px] text-[#767676]">{session.window}</p>
                        </div>
                        <p className="text-xs font-semibold text-[#0b1f33] whitespace-nowrap">
                          {session.count} {session.count === 1 ? 'Note' : 'Research Notes'}
                        </p>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="border border-[#e2e5ea] bg-white">
                <div className="border-b border-[#e2e5ea] px-4 py-3">
                  <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">Today&apos;s Calendar</p>
                </div>
                <ul className="divide-y divide-[#eef0f3]">
                  {CALENDAR_BLOCKS.filter((b) => ['earnings', 'ipo', 'economic'].includes(b.id)).map((block) => (
                    <li key={block.id}>
                      <Link
                        to={block.path || '/events'}
                        className="flex items-center justify-between gap-2 px-4 py-3 text-sm hover:bg-[#fafbfc]"
                      >
                        <span className="font-semibold text-[#111]">{block.label}</span>
                        <span className="text-[10px] text-[#9298a3]">{block.hint}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            </aside>
          </div>
        </div>
      </section>

      {/* SECTION 2 — Today's Research */}
      <section id="todays-research" className="border-b border-[#e2e5ea] bg-[#fafbfc]" aria-label="Today's research">
        <div className="mx-auto max-w-[1800px] px-4 sm:px-6 py-8 md:py-10">
          <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">Editorial Desk</p>
              <h2 className="mt-1 font-serif text-3xl font-bold text-[#111111]">Today&apos;s Research</h2>
            </div>
            <Link to="/sections/research-notes" className="text-xs font-bold text-[#0b1f33] hover:underline">
              All research notes →
            </Link>
          </div>

          <div className="mb-6 flex flex-wrap gap-1 border-b border-[#e2e5ea]">
            {RESEARCH_TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setResearchTab(tab.id)}
                className={`px-3 py-2.5 text-xs font-bold border-b-2 -mb-px transition-colors ${
                  researchTab === tab.id
                    ? 'border-[#ff6600] text-[#111111]'
                    : 'border-transparent text-[#667085] hover:text-[#111111]'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
              <div className="h-80 animate-pulse bg-[#eee] lg:col-span-7" />
              <div className="space-y-3 lg:col-span-5">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="h-20 animate-pulse bg-[#eee]" />
                ))}
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
              <div className="lg:col-span-7 border border-[#e2e5ea] bg-white p-5 md:p-6">
                {featuredStory ? (
                  <FeaturedStory article={featuredStory} />
                ) : (
                  <div className="border border-dashed border-[#d5d8de] p-6 text-sm text-[#667085]">
                    Research notes will appear as the AGI desk publishes.{' '}
                    <button
                      type="button"
                      className="font-bold text-[#0b1f33] underline"
                      onClick={() => navigate('/ask?q=Today%20institutional%20research%20briefing')}
                    >
                      Ask AGI for today&apos;s briefing
                    </button>
                    .
                  </div>
                )}
              </div>
              <div className="lg:col-span-5 border border-[#e2e5ea] bg-white">
                <div className="border-b border-[#e2e5ea] px-5 py-3">
                  <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#767676]">Latest published notes</p>
                  <p className="mt-0.5 text-sm font-bold text-[#111111]">Auto-updated as notes publish</p>
                </div>
                <div className="px-5">
                  {latestNotes.length ? (
                    latestNotes.map((article, index) => (
                      <ResearchFeedCard key={article.id || article.slug || index} article={article} index={index} />
                    ))
                  ) : (
                    <p className="py-6 text-sm text-[#667085]">Latest notes will stream here through the day.</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* SECTION 3 — Morning Office */}
      <section id="morning-office" className="border-b border-[#e2e5ea] bg-white" aria-label="Morning Office">
        <div className="mx-auto max-w-[1800px] px-4 sm:px-6 py-8 md:py-10">
          <div className="border border-[#e2e5ea]">
            <div className="flex flex-wrap items-end justify-between gap-3 border-b border-[#e2e5ea] px-5 py-4 md:px-6">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">Operations</p>
                <h2 className="mt-1 font-serif text-2xl font-bold text-[#111111]">Morning Office</h2>
              </div>
              <p className="text-[11px] text-[#767676]">{generatedTime}</p>
            </div>
            <div className="grid grid-cols-2 gap-px bg-[#eef0f3] sm:grid-cols-3 lg:grid-cols-6">
              <MetricCell label="Market Regime" value={marketRegime} />
              <MetricCell label="Market Health" value={marketHealth} />
              <MetricCell label="Research Queue" value={String(researchQueueCount)} />
              <MetricCell label="Critical Alerts" value={String(criticalAlerts)} />
              <MetricCell label="Opportunity Updates" value={String(opportunityUpdates)} />
              <MetricCell label="Coverage Status" value={String(coverageStatus)} />
            </div>
            <div className="px-5 py-4 md:px-6">
              <a
                href={morningOfficeHref}
                className="inline-flex items-center bg-[#0b1f33] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#163353]"
              >
                Open Morning Office →
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 4 — Market Dashboard */}
      <section className="border-b border-[#e2e5ea] bg-[#fafbfc]" aria-label="Market dashboard">
        <div className="mx-auto max-w-[1800px] px-4 sm:px-6 py-8">
          <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">Live Markets</p>
              <h2 className="mt-1 font-serif text-2xl font-bold text-[#111111]">Market Dashboard</h2>
            </div>
            <p className="text-[11px] text-[#767676]">Updated {formatIstTime()} IST</p>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <BoardColumn title="India" rows={indiaBoard} />
            <BoardColumn title="Global" rows={globalBoard} />
            <BoardColumn title="Macro" rows={macroBoard} />
          </div>
        </div>
      </section>

      {/* SECTION 5 — Top Research Priorities */}
      <section id="research-queue" className="border-b border-[#e2e5ea] bg-white" aria-label="Research priorities">
        <div className="mx-auto max-w-[1800px] px-4 sm:px-6 py-8 md:py-10">
          <div className="mb-5">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">Opportunity Intelligence</p>
            <h2 className="mt-1 font-serif text-2xl font-bold text-[#111111]">Top Research Priorities</h2>
            <p className="mt-1 text-xs text-[#767676]">Where the desk should focus next — not investment recommendations</p>
          </div>
          <div className="grid grid-cols-1 gap-px bg-[#eef0f3] border border-[#e2e5ea] sm:grid-cols-2 lg:grid-cols-3">
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
                    <p className="mt-0.5 text-[11px] font-semibold uppercase tracking-wide text-[#767676]">{item.company}</p>
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
                  <div className="flex items-center justify-between gap-2 pt-1">
                    <dd className="font-semibold tabular-nums text-[#111111]">
                      Conf. {Math.round(Number(item.confidence) * (Number(item.confidence) <= 1 ? 100 : 1))}%
                    </dd>
                    <dd className="font-bold text-[#0b1f33]">Open Workspace →</dd>
                  </div>
                </dl>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 6 — AI Market Brief */}
      <section className="border-b border-[#e2e5ea] bg-[#fafbfc]" aria-label="AI market brief">
        <div className="mx-auto max-w-[1800px] px-4 sm:px-6 py-8 md:py-10">
          <div className="border border-[#e2e5ea] bg-white">
            <div className="border-b border-[#e2e5ea] px-5 py-4 md:px-6">
              <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">Daily Institutional Summary</p>
              <h2 className="mt-1 font-serif text-2xl font-bold text-[#111111]">AI Market Brief</h2>
            </div>
            <div className="grid grid-cols-1 gap-0 md:grid-cols-2">
              <BriefBlock title="Market Summary" body={aiBrief.marketSummary} />
              <BriefList title="Top Opportunities" items={aiBrief.topOpportunities} />
              <BriefList title="Key Risks" items={aiBrief.keyRisks} />
              <BriefBlock title="Sector Rotation" body={aiBrief.sectorRotation} />
              <BriefBlock title="Institutional Flows" body={aiBrief.institutionalFlows} />
              <BriefBlock title="Macro Outlook" body={aiBrief.macroOutlook} />
            </div>
            <div className="border-t border-[#e2e5ea] px-5 py-3 md:px-6">
              <Link to="/ask?q=Today%20AI%20market%20brief%20India" className="text-xs font-bold text-[#0b1f33] hover:underline">
                Read Full Brief →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 7 — Company Intelligence */}
      <section id="company-intelligence" className="border-b border-[#e2e5ea] bg-white" aria-label="Company intelligence">
        <div className="mx-auto max-w-[1800px] px-4 sm:px-6 py-8 md:py-10">
          <div className="mb-5">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">Deep Coverage</p>
            <h2 className="mt-1 font-serif text-2xl font-bold text-[#111111]">Company Intelligence</h2>
            <p className="mt-1 text-xs text-[#767676]">
              Open a company workspace — research, financials, valuation, ownership, filings, peers and Ask AGI.
            </p>
          </div>

          <div className="border border-[#e2e5ea] bg-white p-5 md:p-6">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                openCompany();
              }}
              className="flex flex-col gap-3 sm:flex-row"
            >
              <input
                value={companyQuery}
                onChange={(e) => setCompanyQuery(e.target.value)}
                placeholder="Search company — e.g. Reliance, TCS, ICICI Bank"
                className="w-full flex-1 border border-[#cccccc] bg-white px-4 py-3 text-sm text-[#111] outline-none focus:border-[#111]"
              />
              <button
                type="submit"
                className="bg-[#0b1f33] px-5 py-3 text-xs font-bold text-white hover:bg-[#163353]"
              >
                Open Workspace
              </button>
            </form>

            <div className="mt-4 flex flex-wrap gap-2">
              {COMPANY_INTEL_EXAMPLES.map((c) => (
                <button
                  key={c.symbol}
                  type="button"
                  onClick={() => openCompany(c.symbol)}
                  className="border border-[#d5d8de] px-3 py-1.5 text-xs font-semibold text-[#252b36] hover:border-[#0b1f33]"
                >
                  {c.label}
                </button>
              ))}
            </div>

            <div className="mt-6 flex flex-wrap gap-2 border-t border-[#eef0f3] pt-5">
              {COMPANY_INTEL_PANELS.map((panel) => (
                <span
                  key={panel}
                  className="border border-[#e8eaee] bg-[#fafbfc] px-3 py-1.5 text-[11px] font-bold uppercase tracking-wide text-[#5d6470]"
                >
                  {panel}
                </span>
              ))}
            </div>

            {user && watchlist.length > 0 && (
              <div className="mt-5">
                <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-[#767676]">From your watchlist</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {watchlist.map((t) => (
                    <Link
                      key={t}
                      to={`/research/stocks/${encodeURIComponent(String(t).toLowerCase())}`}
                      className="border border-[#d5d8de] px-3 py-1.5 text-xs font-semibold hover:border-[#0b1f33]"
                    >
                      {t}
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* SECTION 8 — Platform Coverage */}
      <section id="platform-coverage" className="border-b border-[#e2e5ea] bg-[#fafbfc]" aria-label="Platform coverage">
        <div className="mx-auto max-w-[1800px] px-4 sm:px-6 py-8 md:py-10">
          <div className="mb-5">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">Trust</p>
            <h2 className="mt-1 font-serif text-2xl font-bold text-[#111111]">Platform Coverage</h2>
          </div>
          <div className="grid grid-cols-2 gap-px border border-[#e2e5ea] bg-[#eef0f3] sm:grid-cols-3">
            <MetricCell label="Companies Covered" value={String(coverage.companiesCovered)} />
            <MetricCell label="Research Notes Published Today" value={String(coverage.researchNotesToday)} />
            <MetricCell label="Knowledge Graph" value={coverage.knowledgeGraph} />
            <MetricCell label="Company Memory" value={coverage.companyMemory} />
            <MetricCell label="Opportunity Intelligence" value={coverage.opportunityIntelligence} />
            <MetricCell label="Morning Office" value={coverage.morningOffice} />
            <MetricCell label="Coverage" value={String(coverage.coverageStatus)} />
            <MetricCell label="Data Freshness" value={coverage.dataFreshness} />
            <MetricCell label="Last Sync" value={`${coverage.lastSync} IST`} />
          </div>
        </div>
      </section>

      {/* SECTION 9 — Newsletter */}
      <NewsletterSection />
    </div>
  );
}
