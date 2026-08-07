import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import AskAgiBar from '@/components/Home/AskAgiBar';
import DeskResearchFeed from '@/components/Research/DeskResearchFeed';
import { getMieSnapshot } from '@/lib/intelligenceApi';

const NAV = [
  ['overview', 'Overview'], ['rates', 'Rates'], ['fx', 'FX'], ['commodities', 'Commodities'],
  ['macro', 'Macro'], ['risk', 'Liquidity & Risk'], ['india', 'India Impact'], ['research', 'Research'],
];

function label(value, fallback = 'Data unavailable') {
  if (value === null || value === undefined || value === '') return fallback;
  if (typeof value === 'object') return value.label || value.name || value.regime || fallback;
  return String(value);
}

function number(value, suffix = '') {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? `${parsed.toLocaleString('en-IN', { maximumFractionDigits: 2 })}${suffix}` : 'Data unavailable';
}

function statusTone(value) {
  const raw = String(value || '').toLowerCase();
  if (/(risk.off|tight|high|elevated|pressure|negative|down)/.test(raw)) return 'text-rose-300 border-rose-800 bg-rose-950/30';
  if (/(risk.on|improving|loose|positive|up|pass)/.test(raw)) return 'text-emerald-300 border-emerald-800 bg-emerald-950/30';
  return 'text-amber-200 border-amber-800 bg-amber-950/20';
}

function Section({ id, eyebrow, title, children, action }) {
  return (
    <section id={id} className="border border-slate-800 bg-[#0d131c] p-4 md:p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-sky-300">{eyebrow}</p>
          <h2 className="mt-1 text-base font-semibold text-slate-100 md:text-lg">{title}</h2>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

function Empty({ children = 'Awaiting connected source' }) {
  return <p className="py-3 text-sm text-slate-500">{children}</p>;
}

function Findings({ section, limit = 5 }) {
  const findings = section?.findings || [];
  if (!findings.length) return <Empty />;
  return (
    <ul className="space-y-2 text-sm leading-relaxed text-slate-300">
      {findings.slice(0, limit).map((item, index) => <li key={`${index}-${item}`}>• {item}</li>)}
    </ul>
  );
}

function ObservedGrid({ cards }) {
  const rows = [
    ['India GDP growth', cards.growth?.gdp, '%'], ['CPI', cards.inflation?.cpi, '%'],
    ['RBI policy rate', cards.interest_rates?.repo, '%'], ['India 10Y', cards.interest_rates?.india_10y, '%'],
    ['USD/INR', cards.currency?.usdinr, ''], ['Brent', cards.commodities?.brent, ''],
  ];
  return <div className="grid grid-cols-2 gap-px overflow-hidden border border-slate-800 bg-slate-800 md:grid-cols-3 lg:grid-cols-6">
    {rows.map(([name, value, suffix]) => <div key={name} className="min-h-[76px] bg-[#101720] p-3">
      <p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">{name}</p>
      <p className="mt-2 text-sm font-semibold text-slate-100">{number(value, suffix)}</p>
      <p className="mt-1 text-[10px] text-slate-500">Observed · warehouse snapshot</p>
    </div>)}
  </div>;
}

export default function GlobalMarketsPage() {
  const [snapshot, setSnapshot] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getMieSnapshot('Global')
      .then((payload) => { if (!cancelled) setSnapshot(payload); })
      .catch(() => { if (!cancelled) setSnapshot({ ok: false, status: 'SNAPSHOT_UNAVAILABLE' }); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const pack = snapshot?.pack || null;
  const modules = pack?.modules || {};
  const cards = modules.dashboard?.cards || {};
  const regime = useMemo(() => [
    ['Risk appetite', modules.risks?.state || pack?.regime],
    ['Growth', modules.cycle?.cycle || pack?.cycle],
    ['Inflation', modules.inflation?.state || cards.inflation?.direction],
    ['Monetary policy', modules.rates?.state || cards.interest_rates?.direction],
    ['Liquidity', modules.liquidity?.state || cards.liquidity?.direction],
    ['USD / INR', modules.currency?.state || cards.currency?.direction],
  ], [pack, modules, cards]);
  const servedIndiaFallback = snapshot?.fallback;

  return (
    <main className="min-h-screen bg-[#070b10] pb-14 text-slate-100">
      <div className="border-b border-slate-800 bg-[#0a1017]">
        <div className="mx-auto flex max-w-[1600px] items-center gap-3 overflow-x-auto px-4 py-2 text-[11px] md:px-6">
          <span className="shrink-0 font-bold tracking-[0.18em] text-sky-300">AGI GLOBAL MARKETS</span>
          <span className="shrink-0 text-slate-500">Global Macro · Rates · FX · Commodities · Liquidity · Risk</span>
          <span className={`ml-auto shrink-0 border px-2 py-1 text-[10px] font-bold ${snapshot?.ok ? 'border-emerald-900 text-emerald-300' : 'border-amber-900 text-amber-200'}`}>
            {loading ? 'LOADING SNAPSHOT' : snapshot?.ok ? `CACHED${servedIndiaFallback ? ' · INDIA READ-THROUGH' : ''}` : label(snapshot?.status, 'AWAITING SNAPSHOT')}
          </span>
        </div>
      </div>

      <div className="mx-auto max-w-[1600px] px-4 md:px-6">
        <header className="border-b border-slate-800 py-7 md:py-8">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-sky-300">Global macro & cross-asset intelligence terminal</p>
          <div className="mt-2 flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-white md:text-3xl">Global Markets</h1>
              <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-400">Data → context → signal → interpretation → India impact. Major indices and macro only; no company recommendations.</p>
            </div>
            <p className="text-xs text-slate-500">Snapshot published: {snapshot?.published_at || pack?.generated_at || 'Awaiting background refresh'}</p>
          </div>
        </header>

        <nav className="sticky top-0 z-10 -mx-4 overflow-x-auto border-b border-slate-800 bg-[#070b10]/95 px-4 py-3 backdrop-blur md:-mx-6 md:px-6">
          <div className="flex min-w-max gap-2">{NAV.map(([id, title]) => <a key={id} href={`#${id}`} className="border border-slate-800 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-300 hover:border-sky-600 hover:text-sky-200">{title}</a>)}</div>
        </nav>

        {!snapshot?.ok && !loading ? <div className="mt-5 border border-amber-900 bg-amber-950/20 p-4 text-sm text-amber-100"><b>Snapshot unavailable.</b> The page did not start a calculation. It will show the next background-published macro snapshot automatically.</div> : null}

        <div className="space-y-5 py-5">
          <Section id="overview" eyebrow="Observed data" title="Market state">
            <ObservedGrid cards={cards} />
            <p className="mt-3 text-xs text-slate-500">Observed values are sourced from the existing AGI warehouse snapshot. Global instruments display only after their authorised source is connected and stored.</p>
          </Section>

          <div className="grid gap-5 xl:grid-cols-[1.65fr_1fr]">
            <Section eyebrow="AGI interpretation" title="AGI Global Market View">
              <p className="max-w-4xl text-sm leading-7 text-slate-300">{pack?.executive_summary || modules.executive?.summary || 'Awaiting a published macro interpretation from the background runtime.'}</p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div className="border-l-2 border-sky-400 bg-slate-950/40 p-3"><p className="text-[10px] font-bold uppercase tracking-wide text-sky-300">What is driving markets</p><Findings section={modules.attribution || modules.executive} limit={3} /></div>
                <div className="border-l-2 border-amber-400 bg-slate-950/40 p-3"><p className="text-[10px] font-bold uppercase tracking-wide text-amber-200">What AGI is watching</p><Findings section={modules.risks} limit={3} /></div>
              </div>
            </Section>
            <Section eyebrow="AGI derived" title="Global regime engine">
              <div className="space-y-2">{regime.map(([name, value]) => <div key={name} className="flex items-center justify-between gap-3 border-b border-slate-800 pb-2 text-sm"><span className="text-slate-400">{name}</span><span className={`border px-2 py-0.5 text-xs font-semibold ${statusTone(label(value, 'Neutral'))}`}>{label(value, 'Awaiting source')}</span></div>)}</div>
              <p className="mt-3 text-[11px] leading-relaxed text-slate-500">Deterministic classifications are published by the macro runtime; AGI narrative explains rather than invents the state.</p>
            </Section>
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <Section id="rates" eyebrow="Observed + derived" title="Rates & central banks"><Findings section={modules.rates} /><p className="mt-3 text-[11px] text-slate-500">Market-implied policy pricing is intentionally hidden until an authorised futures/OIS source is stored.</p></Section>
            <Section id="fx" eyebrow="Observed + derived" title="FX & USD/INR"><Findings section={modules.currency} /><p className="mt-3 text-[11px] text-slate-500">USD/INR is shown as an India read-through, not a currency trading signal.</p></Section>
            <Section id="commodities" eyebrow="Observed + India read-through" title="Commodities"><Findings section={modules.commodities} /><p className="mt-3 text-[11px] text-slate-500">Oil, gold and industrial commodities are interpreted only where the snapshot carries evidence.</p></Section>
            <Section id="macro" eyebrow="Observed + derived" title="Global macro momentum"><div className="grid grid-cols-1 gap-3 sm:grid-cols-3"><MiniState name="Growth" section={modules.economy} /><MiniState name="Inflation" section={modules.inflation} /><MiniState name="Cycle" section={modules.cycle} /></div></Section>
          </div>

          <div className="grid gap-5 xl:grid-cols-2">
            <Section id="risk" eyebrow="AGI derived" title="Liquidity, financial conditions & risk"><Findings section={modules.liquidity} /><div className="mt-4 border-t border-slate-800 pt-4"><Findings section={modules.risks} limit={3} /></div></Section>
            <Section eyebrow="AGI derived" title="Cross-asset signals"><Findings section={modules.relationships} /><p className="mt-3 text-[11px] text-slate-500">A relationship is shown only when calculations have been published from a sufficient, comparable history.</p></Section>
          </div>

          <Section id="india" eyebrow="AGI flagship · probabilistic transmission" title="Global → India">
            <p className="mb-4 text-sm text-slate-400">Global factors are translated into potential effects on inflation, INR, flows and sector conditions. These are conditional relationships, not recommendations.</p>
            {modules.sector_impact?.impacts?.length ? <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">{modules.sector_impact.impacts.map((row) => <div key={row.sector} className="border border-slate-800 bg-slate-950/30 p-3"><div className="flex items-center justify-between gap-3"><b className="text-sm text-slate-200">{row.sector}</b><span className={`border px-2 py-0.5 text-[10px] font-bold ${statusTone(row.impact)}`}>{label(row.impact)}</span></div><p className="mt-2 text-xs leading-relaxed text-slate-500">{(row.evidence || []).slice(0, 2).join(' · ') || 'Transmission evidence awaiting publication.'}</p></div>)}</div> : <Empty>India transmission snapshot is awaiting publication.</Empty>}
          </Section>

          <div className="grid gap-5 xl:grid-cols-[1.3fr_1fr]">
            <Section id="research" eyebrow="AGI editorial research" title="Global research"><DeskResearchFeed deskId="global-markets" title="Latest global research" /></Section>
            <Section id="calendar" eyebrow="Upcoming macro events" title="Economic calendar"><Empty>Event calendar will appear when an authorised calendar source is connected to the global warehouse.</Empty><p className="text-xs text-slate-500">No calendar dates or consensus values are inferred by AGI.</p></Section>
          </div>

          <Section eyebrow="Ask AGI" title="Ask AGI about global markets" action={<Link to="/ask-agi" className="text-xs font-semibold text-sky-300 hover:text-sky-200">Open full research desk →</Link>}>
            <AskAgiBar placeholder="Why are yields moving, what does Brent mean for India, and what should I watch next?" size="large" buttonLabel="Ask AGI" ariaLabel="Ask AGI about global markets" />
          </Section>
        </div>
      </div>
    </main>
  );
}

function MiniState({ name, section }) {
  return <div className="border border-slate-800 bg-slate-950/30 p-3"><p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">{name}</p><p className="mt-2 text-sm font-semibold text-slate-200">{label(section?.state || section?.summary || section?.cycle, 'Awaiting source')}</p><p className="mt-2 text-[11px] text-slate-500">AGI derived · {label(section?.confidence?.level || section?.confidence, 'confidence pending')}</p></div>;
}
