import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, Loader2 } from 'lucide-react';
import SurfaceChrome from '@/beta/components/SurfaceChrome';
import { StorySection, InsightCard, OpportunityCard, RiskCard, CompanyCard, EmptyState } from '@/beta/components/Cards';
import { useBetaDepth } from '@/beta/BetaDepthContext';
import { formatCountdown, getMarketSession, greetingForHour } from '@/beta/lib/marketClock';
import { buildStoryFromReport } from '@/beta/lib/reportStory';
import useMorningBrief from '@/hooks/useMorningBrief';
import useMarketDashboard from '@/hooks/useMarketDashboard';
import usePublishedArticles from '@/hooks/usePublishedArticles';
import useNifty500Research from '@/hooks/useNifty500Research';
import { getIntelligenceHealth, listResearchRuns, getResearchRun } from '@/lib/intelligenceApi';

export default function HomeTerminal() {
  const navigate = useNavigate();
  const { isExplain, isProfessional } = useBetaDepth();
  const { brief, loading: briefLoading } = useMorningBrief();
  const dash = useMarketDashboard();
  const { articles } = usePublishedArticles({ limit: 4 });
  const nifty = useNifty500Research();
  const [ask, setAsk] = useState('');
  const [now, setNow] = useState(() => new Date());
  const [cioRun, setCioRun] = useState(null);
  const [engineOk, setEngineOk] = useState(null);

  useEffect(() => {
    const t = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(t);
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const health = await getIntelligenceHealth();
        if (!active) return;
        setEngineOk(Boolean(health?.engine?.ok || health?.ok || health?.engineStatus === 200));
      } catch {
        if (active) setEngineOk(false);
      }
      try {
        const runs = await listResearchRuns({ limit: '8' });
        const list = Array.isArray(runs) ? runs : runs?.runs || [];
        const morning =
          list.find((r) => r.desk === 'cio_morning' && ['completed', 'partial'].includes(r.status)) ||
          list.find((r) => ['completed', 'partial'].includes(r.status));
        if (!morning?.run_id || !active) return;
        const full = await getResearchRun(morning.run_id);
        if (active) setCioRun(full);
      } catch {
        /* honest empty — engine may be offline */
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const session = useMemo(() => getMarketSession(now), [now]);
  const countdown = formatCountdown(session.target, now);
  const greeting = greetingForHour(now);
  const story = buildStoryFromReport(cioRun?.report, { symbols: cioRun?.symbols || [] });

  const opportunities = story?.growth?.length
    ? story.growth
    : (dash.gainers || []).slice(0, 3).map((s) => `${s.symbol || s.name}: ${s.trend || 'in focus'}`);
  const risks = story?.risks?.length
    ? story.risks
    : (dash.losers || []).slice(0, 3).map((s) => `${s.symbol || s.name}: ${s.trend || 'watch'}`);

  const screenerPicks = (nifty?.topBullish || nifty?.leaders || nifty?.stocks || dash.stocksInFocus || []).slice(0, 4);

  const onAsk = (e) => {
    e.preventDefault();
    const q = ask.trim();
    navigate(q ? `/beta/copilot?q=${encodeURIComponent(q)}` : '/beta/copilot');
  };

  return (
    <SurfaceChrome askPlaceholder="Ask what matters for today’s session…">
      <div className="beta-story-stack">
        <header>
          <p className="beta-kicker">Home Terminal</p>
          <h1 className="beta-h1 mt-2">
            {greeting}, Shiv
          </h1>
          <p className="mt-3 text-lg text-[var(--beta-ink-soft)]">
            {session.label}{' '}
            <span className="font-[family-name:var(--beta-serif)] text-2xl font-semibold tabular-nums text-[var(--beta-navy)]">
              {countdown}
            </span>
          </p>
          <p className="beta-caption mt-2">
            {engineOk === false
              ? 'Intelligence engine offline — showing market context only.'
              : engineOk
                ? 'Live intelligence connected.'
                : 'Checking intelligence engine…'}
          </p>
        </header>

        <StorySection kicker="What do I need to know?" title="CIO Morning Brief">
          {story ? (
            <InsightCard
              title={story.title}
              body={isExplain ? story.summary?.slice(0, 220) + (story.summary?.length > 220 ? '…' : '') : story.summary}
              meta={story.stance}
            >
              {!isExplain && story.takeaways?.length > 0 && (
                <ul className="mt-4 space-y-2 text-sm text-[var(--beta-ink-soft)]">
                  {story.takeaways.slice(0, isProfessional ? 6 : 3).map((t) => (
                    <li key={t}>• {t}</li>
                  ))}
                </ul>
              )}
              <div className="mt-5 flex flex-wrap gap-2">
                <Link to="/beta/research" className="beta-btn">
                  Read full brief
                  <ArrowRight className="h-4 w-4" />
                </Link>
                {cioRun?.run_id && isProfessional && (
                  <span className="beta-chip">run {cioRun.run_id.slice(0, 10)}</span>
                )}
              </div>
            </InsightCard>
          ) : briefLoading ? (
            <div className="beta-card flex items-center gap-2 text-sm text-[var(--beta-muted)]">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading morning context…
            </div>
          ) : (
            <InsightCard
              title={brief?.title || "Today's Market Brief"}
              body={brief?.excerpt}
              meta={brief?.heroLabel || 'Editorial'}
            >
              {brief?.slug && (
                <Link to={`/article/${brief.slug}`} className="beta-btn mt-5 inline-flex">
                  Open article
                </Link>
              )}
              <p className="beta-caption mt-3">
                CIO desk brief unavailable — showing published morning context instead.
              </p>
            </InsightCard>
          )}
        </StorySection>

        {!isExplain && (
          <StorySection title="Global Markets">
            <div className="grid gap-3 sm:grid-cols-2">
              {(dash.indexSentiments || dash.sectors || []).slice(0, 4).length === 0 && !dash.pulse ? (
                <EmptyState
                  title="Market snapshot loading"
                  detail="Index and sector context appears when market intelligence is available."
                />
              ) : (
                <>
                  <div className="beta-card">
                    <p className="beta-kicker">Pulse</p>
                    <p className="beta-h3 mt-2">{dash.pulse || dash.summary || 'Awaiting session data'}</p>
                    <p className="beta-caption mt-2">{dash.outlook || 'Outlook updates with the live brief.'}</p>
                  </div>
                  {(dash.sectors || []).slice(0, 3).map((s) => (
                    <div key={s.name || s.sector} className="beta-card-quiet">
                      <p className="text-sm font-semibold">{s.name || s.sector}</p>
                      <p className="beta-caption mt-1">{s.bias || s.trend || s.sentiment || '—'}</p>
                    </div>
                  ))}
                </>
              )}
            </div>
          </StorySection>
        )}

        <div className="grid gap-6 lg:grid-cols-2">
          <StorySection title="Biggest Opportunities Today">
            <div className="space-y-3">
              {opportunities.length ? (
                opportunities.slice(0, isExplain ? 2 : 4).map((item) => (
                  <OpportunityCard key={item} title={typeof item === 'string' ? item : item.title} />
                ))
              ) : (
                <EmptyState title="No opportunity list yet" detail="Catalysts appear when a CIO brief or market focus set is available." />
              )}
            </div>
          </StorySection>
          <StorySection title="Biggest Risks Today">
            <div className="space-y-3">
              {risks.length ? (
                risks.slice(0, isExplain ? 2 : 4).map((item) => (
                  <RiskCard key={item} title="Watch" items={[typeof item === 'string' ? item : item.title]} level="stated" />
                ))
              ) : (
                <EmptyState title="No risk list yet" detail="Risks surface from CIO notes or market focus." />
              )}
            </div>
          </StorySection>
        </div>

        <StorySection title="Macro Dashboard">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              ['India', dash.pulse ? 'In focus' : '—'],
              ['Breadth', dash.breadth?.advancers != null ? `${dash.breadth.advancers} adv` : '—'],
              ['Leaders', (dash.gainers || []).length ? `${(dash.gainers || []).length} names` : '—'],
              ['Pressure', (dash.losers || []).length ? `${(dash.losers || []).length} names` : '—'],
            ].map(([label, value]) => (
              <div key={label} className="beta-card text-center">
                <p className="beta-caption">{label}</p>
                <p className="mt-2 font-[family-name:var(--beta-serif)] text-xl font-semibold text-[var(--beta-navy)]">
                  {value}
                </p>
              </div>
            ))}
          </div>
          <Link to="/beta/macro" className="beta-btn-ghost beta-btn mt-4 inline-flex">
            Open macro →
          </Link>
        </StorySection>

        <StorySection title="AI Screener Picks">
          {screenerPicks.length ? (
            <div className="grid gap-3 sm:grid-cols-2">
              {screenerPicks.slice(0, isExplain ? 2 : 4).map((row) => {
                const symbol = row.symbol || row.ticker || row.name;
                return (
                  <CompanyCard
                    key={symbol}
                    symbol={symbol}
                    stance={row.overallSentiment || row.trend || row.sentiment}
                    confidence={row.agiResearchScore || row.aiConfidencePercent}
                    why={[row.researchSummary || row.reason || row.note].filter(Boolean)}
                    onOpen={() => navigate(`/beta/companies/${encodeURIComponent(symbol)}`)}
                  />
                );
              })}
            </div>
          ) : (
            <EmptyState
              title="No screener picks yet"
              detail="When Nifty 500 research or market focus is available, interesting names appear here."
            />
          )}
          <Link to="/beta/screener" className="beta-btn mt-4 inline-flex">
            Open screener
          </Link>
        </StorySection>

        {!isExplain && (
          <StorySection title="Research Feed">
            <div className="space-y-3">
              {(articles || []).slice(0, isProfessional ? 4 : 3).map((a) => (
                <Link key={a.id || a.slug} to={a.slug ? `/article/${a.slug}` : '/research'} className="beta-card block hover:border-[var(--beta-navy)]">
                  <p className="beta-caption">{a.section || 'Research'}</p>
                  <p className="mt-1 text-base font-semibold text-[var(--beta-ink)]">{a.title}</p>
                  {a.excerpt && <p className="beta-caption mt-2 line-clamp-2">{a.excerpt}</p>}
                </Link>
              ))}
              {!(articles || []).length && (
                <EmptyState title="Research feed empty" detail="Published articles will appear here." />
              )}
            </div>
          </StorySection>
        )}

        <StorySection title="Ask AGI…">
          <form onSubmit={onAsk} className="beta-card bg-[#f4f7fb]">
            <p className="beta-caption">Start with one question. Copilot routes to the right desk.</p>
            <textarea
              className="beta-textarea mt-3"
              value={ask}
              onChange={(e) => setAsk(e.target.value)}
              placeholder="How will lower oil prices affect Indian paint companies?"
            />
            <button type="submit" className="beta-btn mt-3">
              Ask AGI
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>
        </StorySection>
      </div>
    </SurfaceChrome>
  );
}
