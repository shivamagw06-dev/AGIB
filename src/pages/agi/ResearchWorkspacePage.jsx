import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  getResearchWorkspaceCompany,
  getResearchWorkspacePortfolio,
  searchResearchWorkspace,
} from '@/lib/intelligenceApi';

const NAV = [
  'Overview',
  'Timeline',
  'Evidence',
  'Decisions',
  'Risk',
  'Policy',
  'Committee',
  'Forecast',
  'Knowledge Graph',
  'Notes',
  'Ask AGI',
];

const CONTEXTS = [
  { id: 'company', label: 'Company' },
  { id: 'portfolio', label: 'Portfolio' },
];

export default function ResearchWorkspacePage() {
  const [params, setParams] = useSearchParams();
  const context = (params.get('context') || 'company').toLowerCase();
  const ticker = (params.get('ticker') || 'AXISBANK').toUpperCase();
  const portfolioId = params.get('portfolio') || 'agi-core-equity';
  const tab = (params.get('tab') || 'Overview').replace(/_/g, ' ');
  const [workspace, setWorkspace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState([]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    const load =
      context === 'portfolio'
        ? getResearchWorkspacePortfolio(portfolioId, { focus: 'overview' })
        : getResearchWorkspaceCompany(ticker, { focus: 'overview' });
    load
      .then((res) => {
        if (!active) return;
        if (!res || res.ok === false) {
          setError(res?.error || 'Workspace unavailable');
          setWorkspace(null);
        } else {
          setWorkspace(res.workspace || res);
        }
        setLoading(false);
      })
      .catch((err) => {
        if (!active) return;
        setError(err?.message || 'Unable to load research workspace');
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [context, ticker, portfolioId]);

  const setContext = (id) => {
    const next = new URLSearchParams(params);
    next.set('context', id);
    setParams(next, { replace: true });
  };

  const setTab = (label) => {
    const next = new URLSearchParams(params);
    next.set('tab', label);
    setParams(next, { replace: true });
  };

  const onSearch = async (e) => {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    const res = await searchResearchWorkspace(q, {
      contextType: context === 'portfolio' ? 'portfolio' : 'company',
      contextId: context === 'portfolio' ? portfolioId : ticker,
    }).catch(() => null);
    setHits(res?.hits || []);
  };

  const activeNav = useMemo(() => {
    const match = NAV.find((n) => n.toLowerCase() === tab.toLowerCase());
    return match || 'Overview';
  }, [tab]);

  const askHref =
    workspace?.ask_deep_link ||
    (context === 'portfolio'
      ? `/agi/ask?context=portfolio&portfolio=${encodeURIComponent(portfolioId)}`
      : `/agi/ask?ticker=${encodeURIComponent(ticker)}`);

  return (
    <div>
      <h1 className="agi-greeting">Research Workspace</h1>
      <p className="agi-lede">
        The complete investment story — timeline, evidence, decisions, risk, policy, and committee —
        linked for reconstruction. Ask AGI points here; this is where analysts spend the day.
      </p>

      <div className="agi-tabs" role="tablist" aria-label="Workspace context">
        {CONTEXTS.map((c) => (
          <button
            key={c.id}
            type="button"
            className={context === c.id ? 'active' : undefined}
            onClick={() => setContext(c.id)}
          >
            {c.label}
          </button>
        ))}
      </div>

      <div className="agi-meta-row" style={{ marginBottom: '0.75rem' }}>
        <span className="agi-chip">{context === 'portfolio' ? portfolioId : ticker}</span>
        <span className="agi-chip muted">RW-01</span>
        {workspace?.workspace_id ? (
          <span className="agi-chip muted">{workspace.workspace_id}</span>
        ) : null}
        <Link className="agi-chip ok" to={askHref}>
          Ask AGI
        </Link>
        {context === 'company' ? (
          <Link className="agi-chip" to={`/agi/companies/${ticker}?rw=1`}>
            Company page
          </Link>
        ) : (
          <Link className="agi-chip" to="/agi/portfolio?rw=1">
            Portfolio page
          </Link>
        )}
      </div>

      <div className="agi-tabs" role="tablist" aria-label="Workspace navigation">
        {NAV.map((n) => (
          <button
            key={n}
            type="button"
            className={activeNav === n ? 'active' : undefined}
            onClick={() => (n === 'Ask AGI' ? null : setTab(n))}
          >
            {n === 'Ask AGI' ? (
              <Link to={askHref} style={{ color: 'inherit', textDecoration: 'none' }}>
                Ask AGI
              </Link>
            ) : (
              n
            )}
          </button>
        ))}
      </div>

      <form className="agi-ask-input-wrap" style={{ margin: '1rem 0' }} onSubmit={onSearch}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search within workspace — capital allocation, CEO, buyback, risk…"
          aria-label="Search workspace"
        />
        <button type="submit" className="agi-btn agi-btn-primary">
          Search
        </button>
      </form>

      {hits.length ? (
        <section className="agi-section" style={{ marginBottom: '1rem' }}>
          <div className="agi-section-head">
            <h2>Search results</h2>
          </div>
          <ul className="agi-list">
            {hits.map((h, i) => (
              <li key={`${h.kind}-${h.title}-${i}`}>
                <div className="agi-list-title">
                  [{h.kind}] {h.title}
                </div>
                <div className="agi-list-meta">
                  {h.object_type}
                  {h.href ? (
                    <>
                      {' · '}
                      <Link to={h.href}>Open</Link>
                    </>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {loading && <div className="agi-empty">Loading research workspace…</div>}
      {error && <div className="agi-error">{error}</div>}

      {!loading && !error && workspace ? (
        <div className="agi-grid-2">
          <section className="agi-section">
            <div className="agi-section-head">
              <h2>{activeNav}</h2>
              <span className="agi-list-meta">{workspace.title}</span>
            </div>

            {(activeNav === 'Overview' || activeNav === 'Timeline') && (
              <ul className="agi-list">
                {(workspace.timeline || []).map((e) => (
                  <li key={e.event_id || e.title}>
                    <div className="agi-list-title">
                      [{e.kind}] {e.title}
                    </div>
                    <div className="agi-list-meta">
                      {e.object_type} · {e.summary}
                    </div>
                  </li>
                ))}
                {!(workspace.timeline || []).length ? (
                  <li>
                    <div className="agi-list-meta">Timeline will fill as objects link.</div>
                  </li>
                ) : null}
              </ul>
            )}

            {activeNav === 'Evidence' && (
              <ul className="agi-list">
                {(workspace.evidence || []).map((e) => (
                  <li key={e.evidence_id || e.title}>
                    <div className="agi-list-title">{e.title}</div>
                    <div className="agi-list-meta">
                      {e.source_type} · {(e.linked_object_ids || []).join(', ') || 'unlinked'}
                    </div>
                  </li>
                ))}
              </ul>
            )}

            {(activeNav === 'Decisions' ||
              activeNav === 'Risk' ||
              activeNav === 'Policy' ||
              activeNav === 'Committee' ||
              activeNav === 'Forecast' ||
              activeNav === 'Knowledge Graph') && (
              <ul className="agi-list">
                {(workspace.linked_objects || [])
                  .filter((o) => {
                    const t = (o.object_type || '').toLowerCase();
                    if (activeNav === 'Decisions') return t.includes('decision');
                    if (activeNav === 'Risk') return t.includes('risk');
                    if (activeNav === 'Policy') return t.includes('policy');
                    if (activeNav === 'Committee') return t.includes('committee');
                    if (activeNav === 'Forecast') return t.includes('forecast') || t.includes('scenario');
                    return true;
                  })
                  .map((o) => (
                    <li key={`${o.object_type}-${o.object_id}`}>
                      <div className="agi-list-title">{o.label}</div>
                      <div className="agi-list-meta">
                        {o.object_type} · {o.relation}
                        {o.href ? (
                          <>
                            {' · '}
                            <Link to={o.href}>Open</Link>
                          </>
                        ) : null}
                      </div>
                      {o.summary ? <div className="agi-list-meta">{o.summary}</div> : null}
                    </li>
                  ))}
              </ul>
            )}

            {activeNav === 'Notes' && (
              <ul className="agi-list">
                {(workspace.notes || []).map((n) => (
                  <li key={n.note_id}>
                    <div className="agi-list-title">{n.title}</div>
                    <div className="agi-list-meta">
                      Analyst note · {(n.tags || []).join(', ') || 'untagged'} · never mutates system
                      intelligence
                    </div>
                    <p className="agi-list-meta" style={{ marginTop: '0.35rem' }}>
                      {n.body}
                    </p>
                  </li>
                ))}
                {!(workspace.notes || []).length ? (
                  <li>
                    <div className="agi-list-meta">No analyst notes yet.</div>
                  </li>
                ) : null}
              </ul>
            )}
          </section>

          <section className="agi-section">
            <div className="agi-section-head">
              <h2>Linked objects</h2>
            </div>
            <ul className="agi-list">
              {(workspace.linked_objects || []).map((o) => (
                <li key={`${o.object_type}-${o.object_id}`}>
                  <div className="agi-list-title">{o.label}</div>
                  <div className="agi-list-meta">
                    {o.object_type}
                    {o.href ? (
                      <>
                        {' · '}
                        <Link to={o.href}>Navigate</Link>
                      </>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
            <div className="agi-panel" style={{ marginTop: '1rem' }}>
              <div className="agi-section-head">
                <h2>Diagnostics</h2>
              </div>
              <p className="agi-list-meta" style={{ margin: 0 }}>
                Missing links: {(workspace.diagnostics?.missing_links || []).length} · Timeline gaps:{' '}
                {workspace.diagnostics?.timeline_gaps ?? '—'} · Orphaned notes:{' '}
                {workspace.diagnostics?.orphaned_notes ?? '—'} · Presentation only
              </p>
            </div>
          </section>
        </div>
      ) : null}
    </div>
  );
}
