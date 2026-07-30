import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

const FILTERS = ['Latest', 'Macro', 'Company', 'Sector', 'Portfolio', 'Thematic', 'Saved', 'Published'];

const NOTES = [
  {
    id: 'kotak-rbi',
    title: 'Kotak Mahindra Bank — RBI supervisory episode',
    meta: 'Company · Published',
    ticker: 'KOTAKBANK',
    sections: {
      'Executive Summary':
        'Supervisory constraints altered near-term growth optics; franchise quality remains the core research question.',
      Financial:
        'Deposit franchise and unsecured mix dominate the financial narrative; monitor NIM and growth trade-offs.',
      Business:
        'Business quality hinges on liability franchise durability and credit culture under tighter supervision.',
      Evidence:
        'RBI communications, management commentary, and subsequent disclosures form the primary evidence chain.',
      Risks: 'Re-acceleration risk if controls ease without process proof; peer share shifts in liabilities.',
      Unknowns: 'Duration of constraints, remediation evidence quality, and competitive deposit response.',
      Monitoring: 'Quarterly liability mix, unsecured growth, management language on remediation milestones.',
      Confidence: 'Moderate — evidence is strong on what happened; forward path remains incompletely observed.',
      Appendix: 'Filing references, timeline of supervisory events, and peer comparison notes.',
    },
  },
  {
    id: 'it-margins',
    title: 'IT services margins — what changed this quarter',
    meta: 'Sector · Draft',
    ticker: 'TCS',
    sections: {
      'Executive Summary': 'Margin bridges remain the institutional focus across large-cap IT.',
      Financial: 'Deal mix, utilisation, and wage cycles drive the bridge.',
      Business: 'Client budgets and vertical mix still set the tone.',
      Evidence: 'Earnings transcripts and order-book commentary.',
      Risks: 'Pricing pressure and delayed decision cycles.',
      Unknowns: 'Sustainability of cost actions vs demand recovery.',
      Monitoring: 'Next-quarter commentary on large deals and attrition.',
      Confidence: 'Moderate.',
      Appendix: 'Peer margin table.',
    },
  },
];

export default function ResearchWorkspacePage() {
  const [filter, setFilter] = useState('Latest');
  const [activeId, setActiveId] = useState(NOTES[0].id);
  const note = useMemo(() => NOTES.find((n) => n.id === activeId) || NOTES[0], [activeId]);

  return (
    <div>
      <h1 className="agi-greeting">Research</h1>
      <p className="agi-lede">
        Institutional notes — Executive Summary through Appendix — with evidence, risks, unknowns, monitoring, and
        confidence.
      </p>

      <div className="agi-tabs" role="tablist" aria-label="Research filters">
        {FILTERS.map((f) => (
          <button
            key={f}
            type="button"
            className={filter === f ? 'active' : undefined}
            onClick={() => setFilter(f)}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="agi-grid-2">
        <section className="agi-section">
          <div className="agi-section-head">
            <h2>{filter} notes</h2>
          </div>
          <ul className="agi-list">
            {NOTES.map((n) => (
              <li key={n.id}>
                <button type="button" onClick={() => setActiveId(n.id)} style={{ all: 'unset', cursor: 'pointer' }}>
                  <div className="agi-list-title">{n.title}</div>
                  <div className="agi-list-meta">{n.meta}</div>
                </button>
                <Link className="agi-chip" to={`/agi/companies/${n.ticker}`}>
                  Company
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section className="agi-section">
          <div className="agi-section-head">
            <h2>Research Note</h2>
            <Link to={`/agi/ask?ticker=${note.ticker}&q=${encodeURIComponent(`Summarise research on ${note.ticker}`)}`}>
              Ask AGI
            </Link>
          </div>
          <h3 style={{ fontFamily: 'var(--agi-display)', fontSize: '1.35rem', margin: '0 0 1rem' }}>{note.title}</h3>
          {Object.entries(note.sections).map(([label, body]) => (
            <div key={label} className="agi-panel" style={{ marginBottom: '0.85rem' }}>
              <div className="agi-section-head">
                <h2>{label === 'Financial' ? 'Financial Analysis' : label === 'Business' ? 'Business Analysis' : label}</h2>
              </div>
              <p className="agi-list-meta" style={{ margin: 0 }}>
                {body}
              </p>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}
