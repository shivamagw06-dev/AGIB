import { useEffect, useMemo, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import {
  getCompanyWorkspace,
  getCompanyWorkspaceEvidence,
  getCompanyWorkspaceTimeline,
} from '@/lib/intelligenceApi';
import {
  COMPANY_TABS,
  boardOf,
  coverageLabel,
  eventLabel,
  firstBlockText,
  formatConfidence,
  formatPct,
  productizeText,
  researchStatusTone,
  sectionByKey,
} from './helpers';

function MetricGrid({ payload }) {
  if (!payload || typeof payload !== 'object') return null;
  const keys = [
    ['revenue', 'Revenue'],
    ['ebit', 'EBIT'],
    ['margins', 'Margins'],
    ['gross_margin', 'Gross margin'],
    ['ebit_margin', 'EBIT margin'],
    ['roe', 'ROE'],
    ['roce', 'ROCE'],
    ['cash_flow', 'Cash flow'],
    ['fcf', 'FCF'],
    ['debt', 'Debt'],
  ];
  const rows = keys
    .map(([k, label]) => {
      const v = payload[k] ?? payload[label] ?? payload[label.toLowerCase()];
      if (v == null || (typeof v === 'object' && !Array.isArray(v))) return null;
      return { label, value: typeof v === 'number' ? String(v) : String(v) };
    })
    .filter(Boolean)
    .slice(0, 8);
  if (!rows.length) return null;
  return (
    <div className="agi-stat-row" style={{ marginTop: '1rem' }}>
      {rows.map((r) => (
        <div key={r.label} className="agi-stat">
          <div className="agi-stat-label">{r.label}</div>
          <div className="agi-stat-value" style={{ fontSize: '1.15rem' }}>
            {r.value}
          </div>
        </div>
      ))}
    </div>
  );
}

function DriversList({ payload }) {
  const drivers =
    payload?.drivers ||
    payload?.quality_drivers ||
    payload?.key_drivers ||
    payload?.factors ||
    [];
  const list = Array.isArray(drivers) ? drivers : [];
  if (!list.length) return null;
  return (
    <ul className="agi-list" style={{ marginTop: '1rem' }}>
      {list.slice(0, 8).map((d, i) => {
        const title = typeof d === 'string' ? d : d?.name || d?.driver || d?.label || `Driver ${i + 1}`;
        const meta = typeof d === 'object' ? d?.detail || d?.trend || d?.note || '' : '';
        return (
          <li key={`${title}-${i}`}>
            <div>
              <div className="agi-list-title">{productizeText(title)}</div>
              {meta ? <div className="agi-list-meta">{productizeText(String(meta))}</div> : null}
            </div>
          </li>
        );
      })}
    </ul>
  );
}

export default function CompanyWorkspacePage() {
  const { ticker: rawTicker } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const ticker = String(rawTicker || '').trim().toUpperCase();
  const tab = searchParams.get('tab') || 'overview';

  const [workspace, setWorkspace] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [evidence, setEvidence] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!ticker) return;
    let active = true;
    setLoading(true);
    setError(null);
    Promise.all([
      getCompanyWorkspace(ticker),
      getCompanyWorkspaceTimeline(ticker).catch(() => null),
      getCompanyWorkspaceEvidence(ticker).catch(() => null),
    ])
      .then(([ws, tl, ev]) => {
        if (!active) return;
        setWorkspace(ws);
        const events =
          tl?.events ||
          tl?.board?.events ||
          sectionByKey(ws, 'historical_timeline')?.board?.events ||
          [];
        setTimeline(Array.isArray(events) ? events : []);
        const refs =
          ev?.references ||
          ev?.board?.references ||
          sectionByKey(ws, 'evidence_references')?.board?.references ||
          [];
        setEvidence(Array.isArray(refs) ? refs : []);
        setLoading(false);
      })
      .catch((err) => {
        if (!active) return;
        setError(err?.message || 'Unable to load company workspace');
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [ticker]);

  const overview = useMemo(() => boardOf(sectionByKey(workspace, 'overview')), [workspace]);
  const profile = useMemo(() => boardOf(sectionByKey(workspace, 'company_profile')), [workspace]);
  const activeSection = useMemo(() => sectionByKey(workspace, tab), [workspace, tab]);
  const activeBoard = boardOf(activeSection);

  const companyName = overview.company || profile.company || ticker;
  const exchange = overview.exchange || profile.exchange || 'NSE';
  const sector = overview.sector || profile.sector || '—';
  const industry = overview.industry || profile.industry || '';
  const coverage = overview.coverage || {};
  const confidence = overview.confidence;
  const researchStatus = overview.current_research_status || '—';
  const lastUpdated = overview.last_updated || workspace?.metadata?.generated_at || '—';
  const watchCount = boardOf(sectionByKey(workspace, 'watchlist_status')).count || 0;
  const portCount = boardOf(sectionByKey(workspace, 'portfolio_references')).count || 0;

  const qualityPayload = boardOf(sectionByKey(workspace, 'business_quality')).payload || {};
  const qualityScore =
    qualityPayload.score ??
    qualityPayload.quality_score ??
    qualityPayload.business_quality_score ??
    confidence;

  const setTab = (id) => {
    const next = new URLSearchParams(searchParams);
    next.set('tab', id);
    setSearchParams(next, { replace: true });
  };

  if (!ticker) {
    return <div className="agi-empty">Choose a company to open its workspace.</div>;
  }

  return (
    <div>
      <div className="agi-company-header">
        <div className="agi-company-title-row">
          <h1>{companyName}</h1>
          <span className="agi-chip">{ticker}</span>
          <span className="agi-chip muted">{exchange}</span>
          {industry ? <span className="agi-chip muted">{industry}</span> : null}
          {sector && sector !== '—' ? <span className="agi-chip muted">{sector}</span> : null}
        </div>
        <div className="agi-meta-row">
          <span>{coverageLabel(coverage)}</span>
          <span>Confidence {formatConfidence(confidence)}</span>
          <span>Updated {String(lastUpdated).slice(0, 19) || '—'}</span>
          <span className={`agi-chip ${researchStatusTone(researchStatus)}`}>
            {productizeText(researchStatus)}
          </span>
          {watchCount > 0 ? <span className="agi-chip ok">Watchlisted</span> : <span className="agi-chip muted">Not watchlisted</span>}
          {portCount > 0 ? <span className="agi-chip ok">In portfolio</span> : <span className="agi-chip muted">Not in portfolio</span>}
        </div>
        <div className="agi-stat-row">
          <div className="agi-stat">
            <div className="agi-stat-label">Coverage</div>
            <div className="agi-stat-value">{formatPct(coverage.ratio, 0)}</div>
          </div>
          <div className="agi-stat">
            <div className="agi-stat-label">Confidence</div>
            <div className="agi-stat-value">{formatConfidence(confidence)}</div>
          </div>
          <div className="agi-stat">
            <div className="agi-stat-label">Research</div>
            <div className="agi-stat-value" style={{ fontSize: '1.05rem' }}>
              {productizeText(String(researchStatus).slice(0, 28))}
            </div>
          </div>
          <div className="agi-stat">
            <div className="agi-stat-label">Ask</div>
            <div className="agi-stat-value" style={{ fontSize: '1.05rem' }}>
              <Link to={`/agi/ask?ticker=${encodeURIComponent(ticker)}&q=${encodeURIComponent('Explain margins.')}`}>
                Open Ask AGI
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="agi-tabs" role="tablist" aria-label="Company sections">
        {COMPANY_TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={tab === t.id ? 'active' : undefined}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading && <div className="agi-empty">Loading company workspace…</div>}
      {error && <div className="agi-error">{error}</div>}

      {!loading && !error && tab === 'overview' && (
        <div>
          <p className="agi-lede" style={{ marginBottom: '1rem' }}>
            {productizeText(firstBlockText(sectionByKey(workspace, 'overview'))) ||
              `${companyName} research workspace — quality, financials, evidence, and timeline.`}
          </p>
          <div className="agi-grid-2">
            <section className="agi-panel">
              <div className="agi-section-head">
                <h2>Business quality</h2>
                <button type="button" className="agi-btn" onClick={() => setTab('business_quality')}>
                  Open
                </button>
              </div>
              <div className="agi-score-block">
                <div className="agi-score-ring">
                  <strong>{formatConfidence(qualityScore)}</strong>
                  <span>Score</span>
                </div>
                <div>
                  <div className="agi-list-title">Institutional quality view</div>
                  <div className="agi-list-meta" style={{ marginTop: '0.35rem' }}>
                    Trend, drivers, and historical context live in the Business Quality section — not a spreadsheet.
                  </div>
                </div>
              </div>
            </section>
            <section className="agi-panel">
              <div className="agi-section-head">
                <h2>Outstanding questions</h2>
              </div>
              <ul className="agi-list">
                {(boardOf(sectionByKey(workspace, 'outstanding_questions')).questions || []).length ? (
                  (boardOf(sectionByKey(workspace, 'outstanding_questions')).questions || []).map((q) => (
                    <li key={q}>
                      <div className="agi-list-title">{productizeText(q)}</div>
                    </li>
                  ))
                ) : (
                  <li>
                    <div className="agi-list-meta">No open coverage gaps recorded.</div>
                  </li>
                )}
              </ul>
            </section>
          </div>
        </div>
      )}

      {!loading && !error && tab === 'business_quality' && (
        <div>
          <div className="agi-score-block">
            <div className="agi-score-ring">
              <strong>{formatConfidence(qualityScore)}</strong>
              <span>Quality</span>
            </div>
            <div>
              <h2 style={{ margin: 0, fontFamily: 'var(--agi-display)', fontSize: '1.5rem' }}>
                Business Quality
              </h2>
              <p className="agi-list-meta" style={{ marginTop: '0.45rem' }}>
                {productizeText(firstBlockText(activeSection)) ||
                  'Large visual score with drivers and trend context.'}
              </p>
            </div>
          </div>
          <DriversList payload={qualityPayload} />
          {!Object.keys(qualityPayload).length && (
            <div className="agi-empty">Quality intelligence will appear when research layers are available.</div>
          )}
        </div>
      )}

      {!loading && !error && tab === 'financial_trends' && (
        <div>
          <h2 style={{ margin: '0 0 0.5rem', fontFamily: 'var(--agi-display)', fontSize: '1.5rem' }}>
            Financials
          </h2>
          <p className="agi-list-meta">
            Revenue, EBIT, margins, ROE, ROCE, cash flow, debt — institutional charts, not spreadsheets.
          </p>
          <MetricGrid payload={activeBoard.payload || activeBoard} />
          <p style={{ marginTop: '1rem' }}>{productizeText(firstBlockText(activeSection))}</p>
          {!activeBoard.available && !activeBoard.payload && (
            <div className="agi-empty">Financial intelligence pending for this company.</div>
          )}
        </div>
      )}

      {!loading && !error && tab === 'historical_timeline' && (
        <div>
          <h2 style={{ margin: '0 0 0.75rem', fontFamily: 'var(--agi-display)', fontSize: '1.5rem' }}>
            Timeline
          </h2>
          {timeline.length ? (
            <div className="agi-timeline">
              {[...timeline]
                .slice()
                .reverse()
                .slice(0, 24)
                .map((ev, i) => (
                  <div key={`${ev.at || i}-${ev.event_type || i}`} className="agi-timeline-item">
                    <div className="agi-timeline-when">{String(ev.at || '—').slice(0, 19)}</div>
                    <div className="agi-timeline-title">{eventLabel(ev)}</div>
                    <div className="agi-timeline-body">{productizeText(ev.summary || '')}</div>
                  </div>
                ))}
            </div>
          ) : (
            <div className="agi-empty">Timeline will fill as filings, calls, and research updates arrive.</div>
          )}
        </div>
      )}

      {!loading && !error && tab === 'evidence_references' && (
        <div>
          <h2 style={{ margin: '0 0 0.5rem', fontFamily: 'var(--agi-display)', fontSize: '1.5rem' }}>
            Evidence
          </h2>
          <p className="agi-list-meta" style={{ marginBottom: '0.75rem' }}>
            Every statement drills to original evidence — click through to the source trail.
          </p>
          <ul className="agi-list">
            {(evidence.length ? evidence : activeBoard.references || []).map((ref, i) => {
              const id = ref.evidence_id || ref.id || `ref-${i}`;
              const conf = ref.confidence;
              return (
                <li key={id}>
                  <div>
                    <div className="agi-list-title">{id}</div>
                    <div className="agi-list-meta">
                      {ref.source ? productizeText(String(ref.source)) : 'Evidence reference'}
                      {conf != null ? ` · confidence ${formatConfidence(conf)}` : ''}
                    </div>
                  </div>
                  <span className="agi-chip">Filing</span>
                </li>
              );
            })}
          </ul>
          {!evidence.length && !(activeBoard.references || []).length && (
            <div className="agi-empty">No evidence references on file yet.</div>
          )}
        </div>
      )}

      {!loading &&
        !error &&
        !['overview', 'business_quality', 'financial_trends', 'historical_timeline', 'evidence_references'].includes(
          tab
        ) && (
          <div>
            <h2 style={{ margin: '0 0 0.5rem', fontFamily: 'var(--agi-display)', fontSize: '1.5rem' }}>
              {COMPANY_TABS.find((t) => t.id === tab)?.label || 'Section'}
            </h2>
            <p style={{ marginBottom: '1rem' }}>
              {productizeText(firstBlockText(activeSection)) || 'Section assembled from institutional research.'}
            </p>
            {tab === 'research_notes' && (
              <ul className="agi-list">
                {(activeBoard.research_history || []).length ? (
                  (activeBoard.research_history || []).slice(0, 12).map((note, i) => (
                    <li key={note.id || i}>
                      <div>
                        <div className="agi-list-title">
                          {note.package_type || note.title || 'Research note'}
                        </div>
                        <div className="agi-list-meta">
                          {String(note.recorded_at || note.status || '').slice(0, 32)}
                        </div>
                      </div>
                    </li>
                  ))
                ) : (
                  <li>
                    <div className="agi-list-meta">No research notes on file.</div>
                  </li>
                )}
              </ul>
            )}
            {tab === 'watchlist_status' && (
              <ul className="agi-list">
                {(activeBoard.watchlists || []).length ? (
                  (activeBoard.watchlists || []).map((w, i) => (
                    <li key={w.id || i}>
                      <div className="agi-list-title">{w.name || w.list || 'Watchlist'}</div>
                      <div className="agi-list-meta">{w.status || 'Monitoring'}</div>
                    </li>
                  ))
                ) : (
                  <li>
                    <div className="agi-list-meta">Not on a research queue yet.</div>
                  </li>
                )}
              </ul>
            )}
            {tab === 'portfolio_references' && (
              <ul className="agi-list">
                {(activeBoard.memberships || []).length ? (
                  (activeBoard.memberships || []).map((m, i) => (
                    <li key={m.id || i}>
                      <div className="agi-list-title">{m.portfolio || m.name || 'Portfolio'}</div>
                      <div className="agi-list-meta">{m.weight != null ? `Weight ${m.weight}` : 'Holding'}</div>
                    </li>
                  ))
                ) : (
                  <li>
                    <div className="agi-list-meta">Not referenced in a portfolio.</div>
                  </li>
                )}
              </ul>
            )}
            {['business_strategy', 'management_execution'].includes(tab) && !activeBoard.available && (
              <div className="agi-empty">Intelligence for this section is not cached yet.</div>
            )}
          </div>
        )}
    </div>
  );
}
