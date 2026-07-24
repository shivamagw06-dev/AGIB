export function StorySection({ kicker, title, children, className = '' }) {
  return (
    <section className={`scroll-mt-28 ${className}`}>
      {kicker && <p className="beta-kicker">{kicker}</p>}
      {title && <h2 className="beta-h2 mt-2">{title}</h2>}
      <div className={title || kicker ? 'mt-5' : ''}>{children}</div>
    </section>
  );
}

export function EmptyState({ title = 'Nothing to show yet', detail }) {
  return (
    <div className="beta-card-quiet">
      <p className="text-sm font-semibold text-[var(--beta-ink)]">{title}</p>
      {detail && <p className="beta-caption mt-2">{detail}</p>}
    </div>
  );
}

export function InsightCard({ title, body, meta, children }) {
  return (
    <article className="beta-card">
      {meta && <p className="beta-caption">{meta}</p>}
      {title && <h3 className="beta-h3 mt-1">{title}</h3>}
      {body && <p className="beta-body mt-3">{body}</p>}
      {children}
    </article>
  );
}

export function MetricStoryCard({
  label,
  from,
  to,
  change,
  why = [],
  meaning,
  watchNext,
}) {
  return (
    <article className="beta-card">
      <p className="beta-kicker">{label}</p>
      <div className="mt-4 flex flex-wrap items-end gap-3">
        {from != null && <p className="text-2xl font-semibold text-[var(--beta-muted)]">{from}</p>}
        {from != null && to != null && <span className="text-[var(--beta-caption)]">→</span>}
        {to != null && <p className="text-3xl font-semibold text-[var(--beta-ink)]">{to}</p>}
        {change && (
          <span className={`beta-chip ${String(change).startsWith('-') || String(change).includes('↓') ? 'beta-chip-neg' : 'beta-chip-pos'}`}>
            {change}
          </span>
        )}
      </div>
      {why.length > 0 && (
        <div className="mt-5">
          <p className="text-[12px] font-semibold text-[var(--beta-ink)]">Why?</p>
          <ul className="mt-2 space-y-1.5 beta-body">
            {why.map((line) => (
              <li key={line}>• {line}</li>
            ))}
          </ul>
        </div>
      )}
      {meaning && (
        <p className="mt-4 rounded-xl bg-[#f4f7fb] px-3 py-3 text-sm leading-relaxed text-[var(--beta-ink-soft)]">
          <span className="font-semibold text-[var(--beta-navy)]">Meaning · </span>
          {meaning}
        </p>
      )}
      {watchNext && (
        <p className="beta-caption mt-3">
          <span className="font-semibold text-[var(--beta-ink-soft)]">Watch next · </span>
          {watchNext}
        </p>
      )}
    </article>
  );
}

export function CompanyCard({ symbol, name, stance, confidence, why = [], onOpen }) {
  return (
    <article className="beta-card flex h-full flex-col">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-lg font-semibold text-[var(--beta-ink)]">{symbol}</p>
          {name && <p className="beta-caption mt-0.5">{name}</p>}
        </div>
        {stance && <span className="beta-chip">{stance}</span>}
      </div>
      {confidence != null && (
        <p className="beta-caption mt-3">Confidence {confidence}%</p>
      )}
      {why.length > 0 && (
        <ul className="mt-4 flex-1 space-y-1.5 text-sm text-[var(--beta-ink-soft)]">
          {why.slice(0, 3).map((line) => (
            <li key={line}>• {line}</li>
          ))}
        </ul>
      )}
      {onOpen && (
        <button type="button" className="beta-btn-ghost beta-btn mt-5 self-start" onClick={onOpen}>
          Open →
        </button>
      )}
    </article>
  );
}

export function EvidenceCard({ claim, source }) {
  return (
    <article className="beta-card-quiet">
      <p className="text-sm leading-relaxed text-[var(--beta-ink)]">{claim}</p>
      {source && <p className="beta-caption mt-2">{source}</p>}
    </article>
  );
}

export function RiskCard({ title, items = [], level = 'stated' }) {
  const tone =
    level === 'high' ? 'beta-chip-neg' : level === 'low' ? 'beta-chip-pos' : 'beta-chip-warn';
  return (
    <article className="beta-card">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-[var(--beta-ink)]">{title}</h3>
        <span className={`beta-chip ${tone}`}>{level}</span>
      </div>
      <ul className="mt-3 space-y-1.5 text-sm text-[var(--beta-ink-soft)]">
        {items.map((item) => (
          <li key={item}>• {item}</li>
        ))}
      </ul>
    </article>
  );
}

export function TimelineCard({ items = [] }) {
  if (!items.length) return null;
  return (
    <ol className="space-y-4 border-l border-[var(--beta-border-strong)] pl-5">
      {items.map((item, idx) => (
        <li key={`${item.label}-${idx}`} className="relative">
          <span className="absolute -left-[1.4rem] top-1.5 h-2.5 w-2.5 rounded-full bg-[var(--beta-navy)]" />
          <p className="text-sm font-semibold text-[var(--beta-ink)]">{item.label}</p>
          <p className="beta-body mt-1 text-[15px]">{item.detail}</p>
        </li>
      ))}
    </ol>
  );
}

export function ForecastCard({ label, probability, detail }) {
  return (
    <article className="beta-card">
      <div className="flex items-end justify-between gap-3">
        <p className="text-sm font-semibold text-[var(--beta-ink)]">{label}</p>
        {probability != null && (
          <p className="text-2xl font-semibold text-[var(--beta-navy)]">{probability}%</p>
        )}
      </div>
      {probability != null && (
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[#eef1f6]">
          <div
            className="h-full rounded-full bg-[var(--beta-navy)]"
            style={{ width: `${Math.min(100, Math.max(0, Number(probability) || 0))}%` }}
          />
        </div>
      )}
      {detail && <p className="beta-body mt-3 text-[15px]">{detail}</p>}
    </article>
  );
}

export function OpportunityCard({ title, detail }) {
  return (
    <article className="beta-card-quiet">
      <p className="text-sm font-semibold text-[var(--beta-ink)]">{title}</p>
      {detail && <p className="beta-caption mt-2">{detail}</p>}
    </article>
  );
}
