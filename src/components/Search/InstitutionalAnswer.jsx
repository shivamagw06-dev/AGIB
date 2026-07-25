import { Link } from 'react-router-dom';

function Block({ title, children }) {
  return (
    <section className="border border-[#dddddd] p-5 bg-white">
      <h2 className="text-xs font-bold uppercase tracking-wide text-[#767676]">{title}</h2>
      <div className="mt-3 text-sm text-[#333333] leading-relaxed">{children}</div>
    </section>
  );
}

function List({ items, empty = 'None listed yet.' }) {
  const rows = (items || []).filter(Boolean);
  if (!rows.length) return <p className="text-xs text-[#929292]">{empty}</p>;
  return (
    <ul className="space-y-2">
      {rows.map((item, idx) => (
        <li key={item.id || item.title || item || idx} className="border-b border-[#eeeeee] pb-2 last:border-0">
          {typeof item === 'string' ? (
            <span>• {item}</span>
          ) : (
            <>
              <p className="font-bold text-[#111]">{item.title || item.id}</p>
              {item.snippet && <p className="text-xs text-[#767676] mt-1">{item.snippet}</p>}
            </>
          )}
        </li>
      ))}
    </ul>
  );
}

function fmtConfidence(value) {
  if (value == null) return '—';
  const n = Number(value);
  if (Number.isNaN(n)) return '—';
  return n <= 1 ? `${Math.round(n * 100)}%` : `${Math.round(n)}%`;
}

export default function InstitutionalAnswer({ pack, onFollowUp }) {
  if (!pack) return null;

  const houseLabel =
    pack.answer?.house_view_label ||
    pack.house_view?.current_view ||
    pack.house_view?.stance ||
    pack.house_view?.label ||
    'Under review';

  const recommendations = pack.recommendations || {};

  return (
    <div className="space-y-4">
      <header className="border border-[#dddddd] border-l-4 border-l-[#ff6600] bg-[#fafafa] p-5">
        <p className="text-[10px] font-bold uppercase tracking-wide text-[#ff6600]">Question</p>
        <h1 className="mt-2 text-2xl md:text-3xl font-bold text-[#111111] leading-tight">
          {pack.question}
        </h1>
        {pack.intent && (
          <p className="mt-2 text-xs text-[#767676]">Intent: {pack.intent.replace(/_/g, ' ')}</p>
        )}
      </header>

      <Block title="Short Executive Answer">
        <p>{pack.executive_summary || pack.answer?.summary}</p>
        <p className="mt-3 text-[11px] text-[#929292]">
          Institutional evidence pack — not a buy/sell instruction.
        </p>
      </Block>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Block title="AGI House View">
          <p className="text-lg font-bold text-[#111]">{houseLabel}</p>
        </Block>
        <Block title="Confidence">
          <p className="text-lg font-bold text-[#111]">{fmtConfidence(pack.confidence)}</p>
        </Block>
        <Block title="Last Updated">
          <p className="text-sm font-bold text-[#111]">{pack.last_updated || '—'}</p>
          {pack.knowledge_freshness?.score != null && (
            <p className="text-[11px] text-[#767676] mt-1">
              Knowledge freshness: {pack.knowledge_freshness.score}
            </p>
          )}
        </Block>
      </div>

      <Block title="Why">
        <List items={pack.why} empty="Reasoning will appear as evidence is retrieved." />
      </Block>

      {pack.investment_thesis && (
        <Block title="Investment Thesis">
          <p>{pack.investment_thesis}</p>
        </Block>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Block title="Bull Case">
          <List items={pack.bull_case} />
        </Block>
        <Block title="Bear Case">
          <List items={pack.bear_case} />
        </Block>
        <Block title="Key Risks">
          <List items={pack.key_risks} />
        </Block>
        <Block title="Key Catalysts">
          <List items={pack.key_catalysts} />
        </Block>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Block title="Supporting Evidence">
          <List items={pack.supporting_research} />
        </Block>
        <Block title="Latest AGI Research">
          <List items={pack.latest_articles} />
        </Block>
        <Block title="Latest News">
          <List items={pack.latest_news} />
        </Block>
        <Block title="Conflicting Opinions">
          <List items={pack.conflicting_opinions} empty="No material conflicts retrieved." />
        </Block>
      </div>

      <Block title="Knowledge Timeline">
        <List items={pack.knowledge_timeline} empty="Timeline populates as knowledge is ingested." />
      </Block>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Block title="Related Companies">
          <div className="flex flex-wrap gap-2">
            {(pack.related_companies || []).map((t) => (
              <Link
                key={t}
                to={`/research/stocks/${encodeURIComponent(t)}`}
                className="text-[11px] font-bold border border-[#ddd] px-2 py-1 hover:text-[#ff6600]"
              >
                {t}
              </Link>
            ))}
            {(pack.related_companies || []).length === 0 && (
              <p className="text-xs text-[#929292]">None detected.</p>
            )}
          </div>
        </Block>
        <Block title="Related Themes">
          <div className="flex flex-wrap gap-2">
            {(pack.related_themes || []).map((t) => (
              <Link
                key={t}
                to={`/themes/${encodeURIComponent(t)}`}
                className="text-[11px] font-bold border border-[#ddd] px-2 py-1 hover:text-[#ff6600]"
              >
                {t}
              </Link>
            ))}
          </div>
        </Block>
        <Block title="Related Sectors">
          <div className="flex flex-wrap gap-2">
            {(pack.related_sectors || []).map((t) => (
              <Link
                key={t}
                to={`/sectors/${encodeURIComponent(t)}`}
                className="text-[11px] font-bold border border-[#ddd] px-2 py-1 hover:text-[#ff6600]"
              >
                {t}
              </Link>
            ))}
          </div>
        </Block>
      </div>

      <Block title="Recommended Next">
        <div className="space-y-2">
          {(recommendations.related_questions || pack.follow_up_questions || []).slice(0, 4).map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => onFollowUp?.(q)}
              className="block w-full text-left text-sm border border-[#eee] px-3 py-2 hover:border-[#111] hover:text-[#ff6600]"
            >
              {q}
            </button>
          ))}
        </div>
      </Block>

      <Block title="Suggested Follow-up Questions">
        <div className="flex flex-wrap gap-2">
          {(pack.follow_up_questions || []).map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => onFollowUp?.(q)}
              className="text-[11px] border border-[#ddd] px-3 py-1.5 hover:border-[#111] hover:text-[#ff6600]"
            >
              {q}
            </button>
          ))}
        </div>
      </Block>
    </div>
  );
}
