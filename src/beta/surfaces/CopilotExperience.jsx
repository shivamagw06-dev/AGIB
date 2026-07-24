import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Loader2, Sparkles } from 'lucide-react';
import SurfaceChrome from '@/beta/components/SurfaceChrome';
import { StorySection, EvidenceCard, EmptyState, CompanyCard } from '@/beta/components/Cards';
import { useBetaDepth } from '@/beta/BetaDepthContext';
import { buildStoryFromReport } from '@/beta/lib/reportStory';
import { copilotChat, runAndWait } from '@/lib/intelligenceApi';

export default function CopilotExperience() {
  const [params] = useSearchParams();
  const initial = params.get('q') || '';
  const [query, setQuery] = useState(initial);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const { isExplain, isProfessional } = useBetaDepth();

  useEffect(() => {
    if (initial) setQuery(initial);
  }, [initial]);

  const ask = async (e) => {
    e?.preventDefault?.();
    const q = query.trim();
    if (!q || running) return;
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      try {
        const data = await copilotChat({
          message: q,
          query: q,
          mode: 'quick_answer',
        });
        setResult({ kind: 'copilot', data });
      } catch {
        const run = await runAndWait({
          desk: 'cio_morning',
          query: q,
        });
        setResult({ kind: 'run', data: run });
      }
    } catch (err) {
      setError(err);
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    if (initial) ask();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const story =
    result?.kind === 'run'
      ? buildStoryFromReport(result.data?.report, { symbols: result.data?.symbols || [] })
      : null;
  const copilot = result?.kind === 'copilot' ? result.data?.copilot || result.data : null;
  const executive =
    copilot?.executive_answer ||
    copilot?.answer ||
    story?.summary ||
    result?.data?.report?.executive_summary ||
    null;

  return (
    <SurfaceChrome>
      <div className="beta-story-stack">
        <header className="text-center">
          <p className="beta-kicker">AGI Copilot</p>
          <h1 className="beta-h1 mt-3">Ask AGI</h1>
          <p className="mx-auto mt-3 max-w-xl text-[var(--beta-ink-soft)]">
            One question. Evidence-backed answer. No invented analysis.
          </p>
        </header>

        <form onSubmit={ask} className="mx-auto w-full max-w-2xl">
          <textarea
            className="beta-textarea min-h-[9rem] text-lg"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="How will lower oil prices affect Indian paint companies?"
          />
          <button type="submit" className="beta-btn mt-4 w-full sm:w-auto" disabled={running || !query.trim()}>
            {running ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Thinking…
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" /> Ask AGI
              </>
            )}
          </button>
        </form>

        {error && (
          <EmptyState
            title="Could not reach intelligence"
            detail={error.message || 'Start the intelligence engine or try again.'}
          />
        )}

        {executive && (
          <StorySection kicker="Layer 1" title="Executive Summary">
            <div className="beta-card">
              <p className="beta-body text-lg leading-8">{executive}</p>
            </div>
          </StorySection>
        )}

        {!isExplain && story?.forecast && (
          <StorySection title="Charts / Scenarios">
            <div className="grid gap-3 sm:grid-cols-3">
              {['bull', 'base', 'bear'].map((key) => {
                const c = story.forecast[key];
                if (!c) return null;
                return (
                  <div key={key} className="beta-card">
                    <p className="beta-caption capitalize">{c.label || key}</p>
                    <p className="mt-2 text-2xl font-semibold text-[var(--beta-navy)]">{c.probability}%</p>
                    <p className="beta-caption mt-2">{c.detail}</p>
                  </div>
                );
              })}
            </div>
          </StorySection>
        )}

        {!isExplain && (story?.evidence?.length > 0 || (copilot?.evidence || []).length > 0) && (
          <StorySection title="Evidence">
            <div className="space-y-3">
              {(story?.evidence || copilot?.evidence || []).slice(0, isProfessional ? 8 : 4).map((ev, i) => (
                <EvidenceCard
                  key={ev.claim || i}
                  claim={ev.claim || ev.statement || String(ev)}
                  source={ev.source_id || ev.source_type}
                />
              ))}
            </div>
          </StorySection>
        )}

        {isProfessional && (copilot?.child_runs || []).length > 0 && (
          <StorySection title="Research">
            <div className="space-y-2">
              {copilot.child_runs.map((row) => (
                <div key={row.run_id || row.desk} className="beta-card-quiet">
                  <p className="text-sm font-semibold">{row.desk}</p>
                  <p className="beta-caption mt-1">{row.title}</p>
                </div>
              ))}
            </div>
          </StorySection>
        )}

        {(copilot?.related_companies || story?.symbols || []).length > 0 && (
          <StorySection title="Related Companies">
            <div className="grid gap-3 sm:grid-cols-2">
              {(copilot?.related_companies || story?.symbols || []).slice(0, 4).map((sym) => (
                <CompanyCard
                  key={sym}
                  symbol={sym}
                  onOpen={() => {
                    window.location.assign(`/beta/companies/${encodeURIComponent(sym)}`);
                  }}
                />
              ))}
            </div>
          </StorySection>
        )}

        {!running && !executive && !error && (
          <EmptyState
            title="Ask anything institutional"
            detail="Try oil → paints, private banks comparison, or a single name like RELIANCE."
          />
        )}

        <p className="beta-caption text-center">
          Prefer the production workspace? <Link to="/intelligence" className="underline">Open Intelligence</Link>
        </p>
      </div>
    </SurfaceChrome>
  );
}
