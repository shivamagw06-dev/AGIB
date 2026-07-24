import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import SurfaceChrome from '@/beta/components/SurfaceChrome';
import {
  StorySection,
  InsightCard,
  MetricStoryCard,
  OpportunityCard,
  RiskCard,
  TimelineCard,
  ForecastCard,
  EvidenceCard,
  EmptyState,
  CompanyCard,
} from '@/beta/components/Cards';
import { useBetaDepth } from '@/beta/BetaDepthContext';
import { buildStoryFromReport, stanceTone, whyFromText } from '@/beta/lib/reportStory';
import { getSimilarCompanies, listResearchRuns, getResearchRun, runAndWait } from '@/lib/intelligenceApi';
import useNifty500Research from '@/hooks/useNifty500Research';

const EQUITY_QUERY = 'Institutional equity research note — business, financials, risks, and catalysts.';

export default function CompanyStory() {
  const { symbol: paramSymbol } = useParams();
  const navigate = useNavigate();
  const symbol = (paramSymbol || 'RELIANCE').toUpperCase();
  const { isExplain, isProfessional } = useBetaDepth();
  const nifty = useNifty500Research();
  const [input, setInput] = useState(symbol);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [run, setRun] = useState(null);
  const [peers, setPeers] = useState([]);

  useEffect(() => {
    setInput(symbol);
  }, [symbol]);

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      setError(null);
      setRun(null);
      try {
        const runs = await listResearchRuns({ limit: '20' });
        const list = Array.isArray(runs) ? runs : runs?.runs || [];
        const existing = list.find(
          (r) =>
            (r.desk === 'equity' || r.desk === 'cio_morning' || r.desk === 'smoke') &&
            Array.isArray(r.symbols) &&
            r.symbols.map((s) => String(s).toUpperCase()).includes(symbol) &&
            ['completed', 'partial'].includes(r.status),
        );
        let full = existing ? await getResearchRun(existing.run_id) : null;
        if (!full?.report) {
          full = await runAndWait({
            desk: 'equity',
            symbols: [symbol],
            query: `${EQUITY_QUERY} Focus: ${symbol}`,
          });
        }
        if (active) setRun(full);
      } catch (err) {
        if (active) setError(err);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [symbol]);

  useEffect(() => {
    let active = true;
    getSimilarCompanies(symbol)
      .then((data) => {
        if (!active) return;
        const list = data?.similar || data?.peers || (Array.isArray(data) ? data : []);
        setPeers(list.map((p) => String(p).toUpperCase()));
      })
      .catch(() => {
        // Curated fallback peers for beta demo UX only (identity, not financials)
        const FALLBACK = {
          RELIANCE: ['ONGC', 'IOC', 'BPCL', 'HPCL'],
          TCS: ['INFY', 'WIPRO', 'HCLTECH', 'TECHM'],
          INFY: ['TCS', 'WIPRO', 'HCLTECH', 'TECHM'],
          TITAN: ['KALYANKJIL', 'SENCO', 'PCJEWELLER'],
          HDFCBANK: ['ICICIBANK', 'AXISBANK', 'KOTAKBANK'],
        };
        if (active) setPeers(FALLBACK[symbol] || []);
      });
    return () => {
      active = false;
    };
  }, [symbol]);

  const niftyRow = useMemo(() => {
    const rows = nifty?.stocks || nifty?.items || nifty?.results || [];
    return rows.find((r) => String(r.symbol || '').toUpperCase() === symbol);
  }, [nifty, symbol]);

  const story = buildStoryFromReport(run?.report, { symbols: [symbol] });
  const tone = stanceTone(story?.stance || niftyRow?.overallSentiment);

  const openSymbol = (e) => {
    e.preventDefault();
    const next = input.trim().toUpperCase();
    if (next) navigate(`/beta/companies/${encodeURIComponent(next)}`);
  };

  return (
    <SurfaceChrome askPlaceholder={`Ask about ${symbol}…`}>
      <div className="beta-story-stack">
        <form onSubmit={openSymbol} className="flex flex-wrap gap-2">
          <input
            className="beta-input max-w-xs"
            value={input}
            onChange={(e) => setInput(e.target.value.toUpperCase())}
            placeholder="Symbol"
          />
          <button type="submit" className="beta-btn">
            Open company
          </button>
        </form>

        <header>
          <p className="beta-kicker">Company Intelligence</p>
          <h1 className="beta-h1 mt-2">{symbol}</h1>
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className={`beta-chip beta-chip-${tone === 'pos' ? 'pos' : tone === 'neg' ? 'neg' : 'warn'}`}>
              {story?.stance || niftyRow?.overallSentiment || 'Awaiting stance'}
            </span>
            {(story?.confidence ?? niftyRow?.agiResearchScore) != null && (
              <span className="beta-chip">
                Confidence {story?.confidence ?? niftyRow?.agiResearchScore}
                {story?.confidence != null ? '%' : '/100'}
              </span>
            )}
            <span className="beta-chip">Read time {story?.readTime || 5} min</span>
          </div>
        </header>

        {loading && (
          <div className="beta-card flex items-center gap-2 text-sm text-[var(--beta-muted)]">
            <Loader2 className="h-4 w-4 animate-spin" /> Building company story…
          </div>
        )}
        {error && !story && (
          <EmptyState
            title="Could not load equity research"
            detail={error.message || 'Engine may be offline. Showing any published Nifty context available.'}
          />
        )}

        <StorySection kicker="01" title="One Minute Summary">
          <InsightCard
            body={
              story?.summary ||
              niftyRow?.researchSummary ||
              `${symbol} — open research when the Intelligence engine is available. No numbers are invented for this beta.`
            }
          />
          {!isExplain && (story?.takeaways || []).length > 0 && (
            <ul className="mt-4 space-y-2 text-sm text-[var(--beta-ink-soft)]">
              {story.takeaways.slice(0, 4).map((t) => (
                <li key={t}>• {t}</li>
              ))}
            </ul>
          )}
        </StorySection>

        {!isExplain && (
          <>
            <StorySection kicker="02" title="Business Story">
              {story?.business || niftyRow?.trendAnalysis ? (
                <InsightCard body={story?.business || niftyRow?.trendAnalysis} />
              ) : (
                <EmptyState title="Business narrative withheld" detail="Appears when Equity Desk / CIO note includes company_view." />
              )}
            </StorySection>

            <StorySection kicker="03" title="Financial Story">
              {story?.financial ? (
                <MetricStoryCard
                  label="Financials"
                  to="See narrative"
                  why={whyFromText(story.financial)}
                  meaning={story.financial}
                  watchNext="Can margins stay durable while growth compounds?"
                />
              ) : (
                <EmptyState
                  title="No financial metrics in this note"
                  detail="Beta never fabricates ₹ figures. Financial story renders when the report includes financial_view or cached metrics."
                />
              )}
            </StorySection>

            <StorySection kicker="04" title="Growth Story">
              <div className="grid gap-3 sm:grid-cols-2">
                {(story?.growth || []).length ? (
                  story.growth.map((g) => <OpportunityCard key={g} title={g} />)
                ) : (
                  <EmptyState title="No catalysts listed" detail="Growth drivers come from report catalysts." />
                )}
              </div>
            </StorySection>

            <StorySection kicker="05" title="Forecast Story">
              {story?.forecast ? (
                <div className="grid gap-3 sm:grid-cols-3">
                  {['bull', 'base', 'bear'].map((key) => {
                    const c = story.forecast[key];
                    if (!c) return null;
                    return <ForecastCard key={key} label={c.label || key} probability={c.probability} detail={c.detail} />;
                  })}
                </div>
              ) : (
                <EmptyState title="No scenario package" detail="Bull / base / bear appear when CIO attaches scenarios." />
              )}
            </StorySection>

            <StorySection kicker="06" title="Risk Story">
              <div className="grid gap-3 sm:grid-cols-2">
                {(story?.risks || niftyRow?.riskFactors || []).length ? (
                  (story?.risks || niftyRow?.riskFactors || []).slice(0, 6).map((r) => (
                    <RiskCard key={r} title="Stated risk" items={[r]} level="stated" />
                  ))
                ) : (
                  <EmptyState title="No risks listed" />
                )}
              </div>
            </StorySection>

            <StorySection kicker="07" title="Timeline">
              {(story?.timeline || []).length ? (
                <TimelineCard items={story.timeline} />
              ) : (
                <EmptyState title="No timeline events" detail="Action items and catalysts become the timeline." />
              )}
            </StorySection>

            <StorySection kicker="08" title="Peer Comparison">
              {peers.length ? (
                <>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {peers.slice(0, 4).map((p) => (
                      <CompanyCard
                        key={p}
                        symbol={p}
                        onOpen={() => navigate(`/beta/companies/${encodeURIComponent(p)}`)}
                      />
                    ))}
                  </div>
                  <button
                    type="button"
                    className="beta-btn mt-4"
                    onClick={() =>
                      navigate(`/beta/compare?symbols=${encodeURIComponent([symbol, ...peers].slice(0, 5).join(','))}`)
                    }
                  >
                    Compare {symbol} vs peers
                  </button>
                </>
              ) : (
                <EmptyState title="No peer set" detail="Similar companies appear from comparison maps when available." />
              )}
            </StorySection>

            {isProfessional && (story?.evidence || []).length > 0 && (
              <StorySection kicker="09" title="Sources">
                <div className="space-y-3">
                  {story.evidence.slice(0, 8).map((ev) => (
                    <EvidenceCard key={ev.claim} claim={ev.claim} source={`${ev.source_type} · ${ev.source_id}`} />
                  ))}
                </div>
              </StorySection>
            )}
          </>
        )}

        {isExplain && (
          <p className="beta-caption">
            Switch depth to <strong>Research Report</strong> for the full scroll story.
          </p>
        )}
      </div>
    </SurfaceChrome>
  );
}
