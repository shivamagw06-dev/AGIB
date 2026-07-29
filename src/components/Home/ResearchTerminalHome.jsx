import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { Bell, ChevronRight } from 'lucide-react';
import AskAgiBar from '@/components/Home/AskAgiBar';
import ResearchFeedCard from '@/components/Home/ResearchFeedCard';
import NewsletterSection from '@/components/Home/NewsletterSection';
import IpoMonitorPreview from '@/components/Home/IpoMonitorPreview';
import usePublishedArticles from '@/hooks/usePublishedArticles';
import useUiHome from '@/hooks/useUiHome';
import { useAuth } from '@/contexts/AuthContext';
import { trackProductEvent } from '@/lib/productAnalytics';
import { getReadingHistory, getRecentSearches, getWatchlist } from '@/lib/searchHistory';
import {
  SESSIONS,
  formatIstTime,
  resolveMarketSession,
  sessionById,
} from '@/lib/marketSession';
import {
  CALENDAR_BLOCKS,
  DEFAULT_HIGHLIGHTS,
  FEATURED_LANES,
  GLOBAL_SNAPSHOT,
  RESEARCH_THEMES,
  TRENDING_CHIPS,
  articleMatchesSession,
} from '@/components/Home/homeTerminalData';

function SessionSwitcher({ active, onChange }) {
  return (
    <section className="border-y border-[#e6e8ec] bg-white" aria-label="Today's research sessions">
      <div className="mx-auto max-w-[1800px] px-4 sm:px-6 py-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ff6600]">Today&apos;s Research</p>
            <h2 className="mt-1 font-serif text-xl font-bold text-[#111111]">Session desk</h2>
          </div>
          <p className="text-[11px] text-[#767676]">IST · revisit any session published earlier today</p>
        </div>
        <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
          {SESSIONS.map((session) => {
            const on = session.id === active;
            return (
              <button
                key={session.id}
                type="button"
                onClick={() => onChange(session.id)}
                className={`min-w-[7.5rem] border px-3 py-2.5 text-left transition-colors ${
                  on
                    ? 'border-[#0b1f33] bg-[#0b1f33] text-white'
                    : 'border-[#e6e8ec] bg-[#fafbfc] text-[#252b36] hover:border-[#0b1f33]/40'
                }`}
              >
                <span className="flex items-center gap-2 text-xs font-bold">
                  <span
                    className={`inline-block h-2 w-2 rounded-full border ${
                      on ? 'border-white bg-white' : 'border-[#9298a3]'
                    }`}
                    aria-hidden
                  />
                  {session.label}
                </span>
                <span className={`mt-1 block text-[10px] ${on ? 'text-white/70' : 'text-[#767676]'}`}>
                  {session.window}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function AiHighlights({ items }) {
  return (
    <section className="border border-[#e6e8ec] bg-gradient-to-br from-[#0b1f33] via-[#12304a] to-[#1a3d55] p-5 text-white">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#ffb366]">AI Highlights</p>
          <h3 className="mt-1 font-serif text-lg font-bold">Today&apos;s 30-second briefing</h3>
        </div>
        <Bell className="h-4 w-4 text-white/50" aria-hidden />
      </div>
      <ul className="mt-4 space-y-2.5">
        {items.map((line) => (
          <li key={line} className="flex gap-2 text-sm leading-snug text-white/90">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[#ffb366]" aria-hidden />
            <span>{line}</span>
          </li>
        ))}
      </ul>
      <Link
        to="/ask?q=Today%20market%20highlights%20India"
        className="mt-5 inline-flex items-center gap-1 text-xs font-bold text-[#ffb366] hover:text-white"
      >
        View Full Analysis <ChevronRight className="h-3.5 w-3.5" />
      </Link>
    </section>
  );
}

function SideBlock({ title, children, action }) {
  return (
    <section className="border border-[#e6e8ec] bg-white p-4">
      <div className="mb-3 flex items-center justify-between gap-2 border-b border-[#f0f1f3] pb-2">
        <h3 className="text-[11px] font-bold uppercase tracking-[0.12em] text-[#111111]">{title}</h3>
        {action}
      </div>
      {children}
    </section>
  );
}

export default function ResearchTerminalHome() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const liveSession = resolveMarketSession();
  const [sessionId, setSessionId] = useState(liveSession);
  const { data: uiHome } = useUiHome();
  const { articles, loading } = usePublishedArticles({ limit: 24, section: null });
  const session = sessionById(sessionId);

  const [watchlist, setWatchlist] = useState([]);
  const [recentlyViewed, setRecentlyViewed] = useState([]);
  const [continueReading, setContinueReading] = useState([]);
  const [trendingSearches, setTrendingSearches] = useState(TRENDING_CHIPS);

  useEffect(() => {
    trackProductEvent('session_start', { surface: 'research_terminal_home', authenticated: Boolean(user) });
  }, [user]);

  useEffect(() => {
    setWatchlist(getWatchlist().slice(0, 8));
    setRecentlyViewed(getReadingHistory(6));
    setContinueReading(getReadingHistory(3));
    const recent = getRecentSearches(7).map((r) => r.query || r).filter(Boolean);
    if (recent.length) setTrendingSearches([...new Set([...recent, ...TRENDING_CHIPS])].slice(0, 8));
  }, [user]);

  const feedArticles = useMemo(() => {
    const matched = articles.filter((a) => articleMatchesSession(a, session));
    const pool = matched.length >= 3 ? matched : articles;
    return pool.slice(0, 8);
  }, [articles, session]);

  const mostRead = useMemo(() => articles.slice(0, 6), [articles]);
  const featured = useMemo(() => articles.slice(0, 4), [articles]);

  const highlights = useMemo(() => {
    const fromUi = uiHome?.highlights || uiHome?.ai_highlights || uiHome?.brief?.bullets;
    if (Array.isArray(fromUi) && fromUi.length) {
      return fromUi.map((x) => (typeof x === 'string' ? x : x.text || x.title)).filter(Boolean).slice(0, 5);
    }
    if (articles[0]?.title) {
      return [
        articles[0].title,
        articles[1]?.title,
        articles[2]?.title,
        ...DEFAULT_HIGHLIGHTS,
      ].filter(Boolean).slice(0, 5);
    }
    return DEFAULT_HIGHLIGHTS;
  }, [uiHome, articles]);

  return (
    <div className="home-terminal min-h-screen bg-[#f4f6f8] text-[#111111]">
      <Helmet>
        <title>AGI — Institutional Research Terminal</title>
        <meta
          name="description"
          content="AGIB research-first homepage: market outlook, AI search, session desks, institutional research notes, IPO and global intelligence."
        />
      </Helmet>

      {/* Hero — brand + AI search only */}
      <section className="relative overflow-hidden border-b border-[#dfe3e8]">
        <div
          className="pointer-events-none absolute inset-0 opacity-90"
          style={{
            background:
              'radial-gradient(1200px 480px at 18% -10%, rgba(255,102,0,0.14), transparent 55%), radial-gradient(900px 420px at 88% 0%, rgba(11,31,51,0.16), transparent 50%), linear-gradient(180deg, #eef2f6 0%, #f4f6f8 55%, #f4f6f8 100%)',
          }}
        />
        <div className="relative mx-auto max-w-[1100px] px-4 sm:px-6 pb-10 pt-12 md:pb-14 md:pt-16">
          <p className="home-hero-brand font-serif text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-[#0b1f33]">
            AGI
          </p>
          <h1 className="mt-4 max-w-2xl font-serif text-2xl sm:text-3xl font-bold leading-tight text-[#1a1a1a]">
            What would you like to analyse today?
          </h1>
          <p className="mt-3 max-w-xl text-sm text-[#555555]">
            Search companies, sectors, markets, macro, research notes and IPOs across the AGIB intelligence platform.
          </p>

          <div className="mt-8 home-hero-search">
            <AskAgiBar
              placeholder="Search Companies, Sectors, Markets, Macro, Research Notes, IPOs…"
              size="large"
              autoFocus={false}
            />
          </div>

          <div className="mt-6">
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#767676]">Trending</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {TRENDING_CHIPS.map((chip) => (
                <button
                  key={chip}
                  type="button"
                  onClick={() => navigate(`/ask?q=${encodeURIComponent(chip)}`)}
                  className="border border-[#d5dbe3] bg-white/70 px-3 py-1.5 text-xs font-semibold text-[#252b36] backdrop-blur transition hover:border-[#0b1f33] hover:bg-white"
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <SessionSwitcher active={sessionId} onChange={setSessionId} />

      <div className="mx-auto grid max-w-[1800px] grid-cols-1 gap-8 px-4 sm:px-6 py-8 lg:grid-cols-[minmax(0,1fr)_320px]">
        {/* Main column */}
        <div className="min-w-0 space-y-8">
          <AiHighlights items={highlights} />

          {user && continueReading.length > 0 && (
            <section className="border border-[#e6e8ec] bg-white p-5">
              <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#ff6600]">Continue Reading</p>
              <ul className="mt-3 space-y-2">
                {continueReading.map((item) => (
                  <li key={item.id || item.href}>
                    <Link to={item.href || '/research'} className="text-sm font-semibold text-[#111] hover:text-[#ff6600]">
                      {item.title}
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {user && watchlist.length > 0 && (
            <section className="border border-[#e6e8ec] bg-white p-5">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#ff6600]">Watchlist Feed</p>
                  <h3 className="mt-1 font-serif text-lg font-bold">Updates from Your Watchlist</h3>
                </div>
                <Link to="/workspace" className="text-xs font-bold text-[#0b1f33] hover:underline">
                  Workspace →
                </Link>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {watchlist.map((ticker) => (
                  <Link
                    key={ticker}
                    to={`/research/stocks/${encodeURIComponent(String(ticker).toLowerCase())}`}
                    className="border border-[#e6e8ec] bg-[#fafbfc] px-3 py-2 text-xs font-bold text-[#111] hover:border-[#0b1f33]"
                  >
                    {ticker}
                  </Link>
                ))}
              </div>
            </section>
          )}

          <section className="border border-[#e6e8ec] bg-white p-5 md:p-7">
            <div className="mb-5 flex flex-wrap items-end justify-between gap-3 border-b border-[#f0f1f3] pb-4">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#ff6600]">
                  {session.label} · {session.window}
                </p>
                <h2 className="mt-1 font-serif text-2xl font-bold text-[#111111]">Live Research Feed</h2>
                <p className="mt-1 text-xs text-[#767676]">
                  Institutional notes for this session desk · updated {formatIstTime()}
                </p>
              </div>
              <Link to="/sections/research-notes" className="text-xs font-bold text-[#0b1f33] hover:underline">
                All research notes →
              </Link>
            </div>

            <div className="mb-6 flex flex-wrap gap-2">
              {session.topics.map((topic) => (
                <button
                  key={topic}
                  type="button"
                  onClick={() => navigate(`/ask?q=${encodeURIComponent(topic)}`)}
                  className="border border-[#eceff3] bg-[#fafbfc] px-2.5 py-1 text-[11px] font-semibold text-[#444] hover:border-[#0b1f33]/30"
                >
                  {topic}
                </button>
              ))}
            </div>

            {loading ? (
              <div className="space-y-4">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="h-36 animate-pulse bg-[#f3f4f6]" />
                ))}
              </div>
            ) : feedArticles.length ? (
              feedArticles.map((article, index) => (
                <ResearchFeedCard key={article.id || article.slug || index} article={article} index={index} />
              ))
            ) : (
              <div className="border border-dashed border-[#d5d8de] bg-[#fafbfc] p-6 text-sm text-[#667085]">
                Research notes for this session will appear as the AGIB desk publishes. Ask AGI to brief the{' '}
                <button
                  type="button"
                  className="font-bold text-[#0b1f33] underline"
                  onClick={() => navigate(`/ask?q=${encodeURIComponent(session.label + ' market briefing')}`)}
                >
                  {session.label.toLowerCase()}
                </button>{' '}
                tape now.
              </div>
            )}
          </section>

          <section className="border border-[#e6e8ec] bg-white p-5 md:p-7">
            <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#ff6600]">Featured Research</p>
            <h2 className="mt-1 font-serif text-xl font-bold">Pinned premium lanes</h2>
            <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-3">
              {FEATURED_LANES.map((lane) => (
                <Link
                  key={lane.id}
                  to={lane.path}
                  className="border border-[#e6e8ec] bg-[#fafbfc] px-3 py-4 text-sm font-bold text-[#111] hover:border-[#0b1f33] hover:bg-white"
                >
                  {lane.label}
                </Link>
              ))}
            </div>
            {featured.length > 0 && (
              <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
                {featured.slice(0, 2).map((article, index) => (
                  <ResearchFeedCard key={`feat-${article.slug || index}`} article={article} index={index} />
                ))}
              </div>
            )}
          </section>

          <section className="border border-[#e6e8ec] bg-white p-5 md:p-7">
            <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#ff6600]">Research by Theme</p>
            <h2 className="mt-1 font-serif text-xl font-bold">Browse investment themes</h2>
            <div className="mt-5 flex flex-wrap gap-2">
              {RESEARCH_THEMES.map((theme) => (
                <Link
                  key={theme.id}
                  to={theme.path}
                  className="border border-[#dfe3e8] bg-[#f4f6f8] px-3 py-2 text-xs font-bold text-[#252b36] hover:border-[#0b1f33] hover:bg-white"
                >
                  {theme.label}
                </Link>
              ))}
            </div>
          </section>
        </div>

        {/* Right rail */}
        <aside className="space-y-4 lg:sticky lg:top-[118px] lg:self-start">
          <SideBlock title="Today's Calendar">
            <ul className="space-y-2">
              {CALENDAR_BLOCKS.map((block) => (
                <li key={block.id}>
                  <Link
                    to={
                      block.id === 'ipo'
                        ? '/ipo-intelligence'
                        : block.id === 'fed' || block.id === 'rbi' || block.id === 'economic'
                          ? '/macro-intelligence'
                          : '/events'
                    }
                    className="flex items-center justify-between gap-2 py-1.5 text-sm hover:text-[#ff6600]"
                  >
                    <span className="font-semibold text-[#111]">{block.label}</span>
                    <span className="text-[10px] text-[#9298a3]">{block.hint}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </SideBlock>

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

          {user && (
            <SideBlock
              title="Watchlist"
              action={
                <Link to="/workspace" className="text-[10px] font-bold text-[#767676] hover:text-[#ff6600]">
                  Edit
                </Link>
              }
            >
              {watchlist.length ? (
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
              ) : (
                <p className="text-xs text-[#767676]">Add names in Workspace to personalise this rail.</p>
              )}
            </SideBlock>
          )}

          <SideBlock title="Most Read Today">
            {mostRead.length ? (
              <ol className="space-y-3">
                {mostRead.map((article, i) => {
                  const rank = String(i + 1).padStart(2, "0");
                  return (
                    <li key={article.slug || i} className="flex gap-3">
                      <span className="font-serif text-lg font-bold text-[#ff6600]">{rank}</span>
                      <Link
                        to={"/article/" + article.slug}
                        className="text-sm font-semibold leading-snug hover:underline"
                      >
                        {article.title}
                      </Link>
                    </li>
                  );
                })}
              </ol>
            ) : (
              <p className="text-xs text-[#767676]">Readership ranks populate as notes circulate.</p>
            )}
          </SideBlock>

          <SideBlock title="Recently Viewed">
            {recentlyViewed.length ? (
              <ul className="space-y-2">
                {recentlyViewed.map((item) => (
                  <li key={item.id || item.href}>
                    <Link to={item.href || '/research'} className="text-sm text-[#444] hover:text-[#ff6600]">
                      {item.title}
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-[#767676]">Your recent research trail appears here.</p>
            )}
          </SideBlock>
        </aside>
      </div>

      <div className="border-t border-[#dfe3e8] bg-white">
        <div className="mx-auto max-w-[1800px] px-4 sm:px-6 py-2">
          <IpoMonitorPreview />
        </div>
      </div>

      <section className="border-t border-[#dfe3e8] bg-[#f4f6f8]">
        <div className="mx-auto max-w-[1800px] px-4 sm:px-6 py-10">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#ff6600]">Global Snapshot</p>
              <h2 className="mt-1 font-serif text-xl font-bold">World desk at a glance</h2>
            </div>
            <Link to="/global" className="text-xs font-bold text-[#0b1f33] hover:underline">
              Open Global Intelligence →
            </Link>
          </div>
          <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {GLOBAL_SNAPSHOT.map((row) => (
              <Link
                key={row.id}
                to={row.path}
                className="border border-[#dfe3e8] bg-white px-3 py-4 text-center text-sm font-bold text-[#111] hover:border-[#0b1f33]"
              >
                {row.label}
              </Link>
            ))}
          </div>
        </div>
      </section>

      <NewsletterSection />
    </div>
  );
}
