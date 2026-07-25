/**
 * Flagship company intelligence panels — extends existing page styling.
 * Does not expose internal engine names.
 */
import { Link } from 'react-router-dom';

function Card({ title, children }) {
  return (
    <article className="border border-[#dde1e6] bg-white p-5">
      <h2 className="text-sm font-bold text-[#18202b]">{title}</h2>
      <div className="mt-2 text-sm leading-relaxed text-[#4b5563]">{children}</div>
    </article>
  );
}

function asText(value) {
  if (value == null) return null;
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return String(value);
  if (typeof value === 'object') {
    return (
      value.label ||
      value.summary ||
      value.thesis ||
      value.regime ||
      value.risk_level ||
      value.status ||
      null
    );
  }
  return null;
}

function DocList({ items }) {
  const rows = (items || []).slice(0, 5);
  if (!rows.length) return <p className="text-xs text-[#929292]">No items yet.</p>;
  return (
    <ul className="space-y-2">
      {rows.map((item, idx) => (
        <li key={item.id || item.title || idx} className="border-b border-[#edf0f2] pb-2 last:border-0">
          <p className="text-sm font-bold text-[#18202b]">{item.title || item.id || String(item)}</p>
          {item.snippet && <p className="text-xs text-[#667085] mt-1 line-clamp-2">{item.snippet}</p>}
        </li>
      ))}
    </ul>
  );
}

export default function CompanyIntelligencePanels({ data }) {
  if (!data) return null;
  const overview = data.overview || {};
  const mi = data.market_intelligence || {};
  const research = data.research || {};
  const evidence = data.evidence || {};
  const portfolio = data.portfolio || {};

  const intelRows = [
    ['Technical Summary', asText(mi.technical_summary)],
    ['Fundamental Summary', asText(mi.fundamental_summary)],
    ['Macro Context', asText(mi.macro_context)],
    ['Risk Summary', asText(mi.risk_summary)],
    ['Volatility Summary', asText(mi.volatility_summary)],
    ['Trend Summary', asText(mi.trend_summary)],
    ['Event Summary', asText(mi.event_summary)],
    ['Sentiment Summary', asText(mi.sentiment_summary)],
  ].filter(([, v]) => v);

  return (
    <div className="mt-6 space-y-6">
      <section className="border border-[#dde1e6] bg-white p-5 sm:p-8">
        <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#274c77]">Overview</p>
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="border border-[#edf0f2] p-3">
            <p className="text-[10px] font-bold uppercase tracking-wide text-[#737982]">House View</p>
            <p className="mt-1 text-sm font-bold text-[#18202b]">{overview.house_view || overview.composite_label || 'Under review'}</p>
          </div>
          <div className="border border-[#edf0f2] p-3">
            <p className="text-[10px] font-bold uppercase tracking-wide text-[#737982]">Confidence</p>
            <p className="mt-1 text-sm font-bold text-[#18202b]">
              {overview.confidence != null
                ? `${Math.round(Number(overview.confidence) * (Number(overview.confidence) <= 1 ? 100 : 1))}%`
                : '—'}
            </p>
          </div>
          <div className="border border-[#edf0f2] p-3 sm:col-span-2">
            <p className="text-[10px] font-bold uppercase tracking-wide text-[#737982]">Last Updated</p>
            <p className="mt-1 text-sm font-bold text-[#18202b]">{overview.last_updated || '—'}</p>
          </div>
        </div>
        {overview.investment_thesis && (
          <div className="mt-5 border-l-4 border-[#274c77] bg-[#f8fafb] p-4">
            <p className="text-[10px] font-bold uppercase tracking-wide text-[#737982]">Investment Thesis</p>
            <p className="mt-2 text-sm leading-relaxed text-[#374151]">{overview.investment_thesis}</p>
          </div>
        )}
        <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
          <Card title="What's Changed">
            <DocList
              items={(overview.whats_changed || []).map((x) => ({ title: String(x) }))}
            />
          </Card>
          <Card title="Current Risks">
            <DocList
              items={(overview.current_risks || []).map((x) => ({ title: String(x) }))}
            />
          </Card>
          <Card title="Current Catalysts">
            <DocList
              items={(overview.current_catalysts || []).map((x) => ({ title: String(x) }))}
            />
          </Card>
        </div>
        <div className="mt-4">
          <Link
            to={`/ask?q=${encodeURIComponent(`What is AGI's view on ${data.ticker}?`)}`}
            className="text-xs font-bold text-[#274c77] hover:underline"
          >
            Ask AGI about {data.ticker} →
          </Link>
        </div>
      </section>

      {intelRows.length > 0 && (
        <section>
          <h2 className="text-sm font-bold text-[#18202b] mb-3">Market Intelligence</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {intelRows.map(([title, value]) => (
              <Card key={title} title={title}>
                {value}
              </Card>
            ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="text-sm font-bold text-[#18202b] mb-3">Research</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Card title="Latest AGI Articles">
            <DocList items={research.latest_agi_articles} />
          </Card>
          <Card title="Broker Research">
            <DocList items={research.broker_research} />
          </Card>
          <Card title="Earnings">
            <DocList items={research.earnings} />
          </Card>
          <Card title="Filings">
            <DocList items={research.filings} />
          </Card>
        </div>
        {(research.knowledge_timeline || []).length > 0 && (
          <div className="mt-4">
            <Card title="Knowledge Timeline">
              <DocList items={research.knowledge_timeline} />
            </Card>
          </div>
        )}
      </section>

      <section>
        <h2 className="text-sm font-bold text-[#18202b] mb-3">Evidence</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Card title="Supporting Research">
            <DocList items={evidence.supporting_research} />
          </Card>
          <Card title="Conflicting Research">
            <DocList items={evidence.conflicting_research} />
          </Card>
          <Card title="Evidence Confidence">
            {evidence.evidence_confidence != null
              ? `${Math.round(Number(evidence.evidence_confidence) * (Number(evidence.evidence_confidence) <= 1 ? 100 : 1))}%`
              : '—'}
          </Card>
        </div>
      </section>

      <section>
        <h2 className="text-sm font-bold text-[#18202b] mb-3">Portfolio</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Card title="Current Portfolio Exposure">
            {portfolio.current_exposure != null ? String(portfolio.current_exposure) : 'No active exposure'}
          </Card>
          <Card title="Prediction History">
            <DocList items={portfolio.prediction_history} />
          </Card>
          <Card title="House View Evolution">
            {Array.isArray(portfolio.house_view_evolution?.points) ? (
              <DocList
                items={portfolio.house_view_evolution.points.map((p) => ({
                  title: `${p.as_of}: ${p.label}`,
                  snippet: p.changed ? `Changed from ${p.prior_label || 'prior'}` : 'Stable',
                }))}
              />
            ) : (
              <DocList items={portfolio.house_view_evolution} />
            )}
          </Card>
        </div>
        <div className="mt-3">
          <Link to="/portfolio" className="text-xs font-bold text-[#274c77] hover:underline">
            Open portfolio desk →
          </Link>
        </div>
      </section>
    </div>
  );
}
