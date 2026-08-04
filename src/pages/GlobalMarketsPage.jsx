import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import PageShell from '@/components/Layout/PageShell';
import AskAgiBar from '@/components/Home/AskAgiBar';
import DeskResearchFeed from '@/components/Research/DeskResearchFeed';
import { getMiePack } from '@/lib/intelligenceApi';

const MODULE_SECTIONS = [
  ['executive', 'Executive Summary'],
  ['dashboard', 'Macro Dashboard'],
  ['cycle', 'Economic Cycle'],
  ['inflation', 'Inflation'],
  ['rates', 'Interest Rates'],
  ['liquidity', 'Liquidity'],
  ['currency', 'Currency'],
  ['commodities', 'Commodities'],
  ['bonds', 'Bond Market'],
  ['sector_impact', 'Sector Impact'],
  ['industry_impact', 'Industry Impact'],
  ['risks', 'Risks'],
  ['forecast', 'Forecast'],
  ['scenarios', 'Scenario Analysis'],
  ['relationships', 'Relationships'],
];

function impactTone(impact) {
  const v = String(impact || '').toLowerCase();
  if (v === 'positive') return 'text-emerald-700 bg-emerald-50 border-emerald-200';
  if (v === 'negative') return 'text-rose-700 bg-rose-50 border-rose-200';
  return 'text-slate-600 bg-slate-50 border-slate-200';
}

function ConfPill({ conf }) {
  const level = conf?.confidence || conf || '—';
  return (
    <span className="inline-flex rounded-full border border-[#d5d8de] bg-[#f7f8fa] px-2.5 py-0.5 text-[11px] font-semibold text-[#333]">
      {level}
    </span>
  );
}

function MieSurface({ pack, loading, error }) {
  const modules = pack?.modules || pack?.sections || {};
  const quality = pack?.macro_quality || {};
  const probs = pack?.probabilities || {};
  const sectorImpact = modules.sector_impact?.impacts || [];
  const cards = modules.dashboard?.cards || {};

  const pulse = useMemo(() => ([
    { label: 'Growth', value: cards.growth?.gdp ?? cards.growth?.pmi_mfg, hint: cards.growth?.direction },
    { label: 'Inflation', value: cards.inflation?.cpi, hint: cards.inflation?.direction },
    { label: 'Repo', value: cards.interest_rates?.repo, hint: null },
    { label: 'USD/INR', value: cards.currency?.usdinr, hint: null },
    { label: 'Brent', value: cards.commodities?.brent, hint: null },
    { label: 'India 10Y', value: cards.interest_rates?.india_10y, hint: null },
  ]), [cards]);

  if (loading) {
    return (
      <section className="rounded-xl border border-[#e6e8ec] bg-white p-6 md:p-8">
        <p className="text-sm text-[#666]">Loading Macro Intelligence Engine…</p>
      </section>
    );
  }

  if (error && !pack?.modules) {
    return (
      <section className="rounded-xl border border-[#e6e8ec] bg-white p-6 md:p-8">
        <p className="text-sm text-[#666]">Macro pack unavailable — {error}</p>
        <p className="mt-2 text-xs text-[#888]">
          Runtime may still be bootstrapping. Open{' '}
          <Link to="/admin/macro-runtime" className="font-semibold underline">Macro Runtime</Link>.
        </p>
      </section>
    );
  }

  if (!pack) return null;

  return (
    <div className="space-y-8">
      <section className="rounded-xl border border-[#e6e8ec] bg-white p-6 md:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#3b6ea5]">
              Macro Intelligence Engine · Phase 9.0
            </p>
            <h2 className="mt-2 font-serif text-3xl font-bold text-[#111]">
              {pack.country || 'India'} macro environment
            </h2>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-[#555]">
              What is happening, why it matters, and how it should influence sector, industry,
              and company research. No GDP point predictions. No BUY/SELL.
            </p>
          </div>
          <div className="text-right">
            <p className="text-[11px] uppercase tracking-wide text-[#888]">Macro confidence</p>
            <div className="mt-1 flex items-center justify-end gap-2">
              <ConfPill conf={quality.macro_confidence} />
              <span className="text-xs text-[#666]">coverage {quality.coverage_pct ?? '—'}%</span>
            </div>
            {probs.base != null ? (
              <p className="mt-2 text-xs text-[#666]">
                Bull / Base / Bear {probs.bull}/{probs.base}/{probs.bear}
              </p>
            ) : null}
          </div>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-4">
          <div className="border border-[#eceef2] px-4 py-3">
            <p className="text-[10px] font-bold uppercase tracking-wide text-[#888]">Regime</p>
            <p className="mt-1 text-lg font-semibold text-[#111]">{pack.regime || '—'}</p>
          </div>
          <div className="border border-[#eceef2] px-4 py-3">
            <p className="text-[10px] font-bold uppercase tracking-wide text-[#888]">Cycle</p>
            <p className="mt-1 text-lg font-semibold text-[#111]">{pack.cycle || '—'}</p>
          </div>
          <div className="border border-[#eceef2] px-4 py-3 md:col-span-2">
            <p className="text-[10px] font-bold uppercase tracking-wide text-[#888]">Executive read</p>
            <p className="mt-1 text-sm leading-relaxed text-[#333]">
              {pack.executive_summary || modules.executive?.summary || '—'}
            </p>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {pulse.map((item) => (
            <div key={item.label} className="border border-[#eceef2] px-3 py-3">
              <p className="text-[10px] font-bold uppercase tracking-wide text-[#888]">{item.label}</p>
              <p className="mt-1 text-base font-semibold text-[#111]">
                {item.value == null || item.value === '' ? '—' : item.value}
              </p>
              {item.hint ? <p className="mt-0.5 text-[11px] text-[#777]">{item.hint}</p> : null}
            </div>
          ))}
        </div>
      </section>

      {sectorImpact.length > 0 ? (
        <section className="rounded-xl border border-[#e6e8ec] bg-white p-6 md:p-8">
          <h3 className="font-serif text-xl font-bold text-[#111]">Sector impact</h3>
          <p className="mt-1 text-sm text-[#666]">
            Deterministic transmission from rates, inflation, oil, FX, growth and liquidity.
          </p>
          <div className="mt-5 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {sectorImpact.map((row) => (
              <div key={row.sector} className="flex items-center justify-between border border-[#eceef2] px-3 py-2.5">
                <div>
                  <p className="text-sm font-semibold text-[#111]">{row.sector}</p>
                  <p className="text-[11px] text-[#777]">
                    {(row.evidence || []).slice(0, 2).join(' · ') || 'neutral drivers'}
                  </p>
                </div>
                <span className={`rounded-full border px-2 py-0.5 text-[11px] font-semibold ${impactTone(row.impact)}`}>
                  {row.impact}
                </span>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="space-y-4">
        {MODULE_SECTIONS.map(([key, label]) => {
          const sec = modules[key];
          if (!sec || key === 'executive' || key === 'dashboard') return null;
          const findings = sec.findings || [];
          if (!findings.length) return null;
          return (
            <article key={key} id={`mie-${key}`} className="rounded-xl border border-[#e6e8ec] bg-white p-5 md:p-6">
              <div className="flex items-center justify-between gap-3">
                <h3 className="font-serif text-lg font-bold text-[#111]">{label}</h3>
                <ConfPill conf={sec.confidence} />
              </div>
              <ul className="mt-3 space-y-1.5">
                {findings.slice(0, 6).map((f) => (
                  <li key={f} className="text-sm leading-relaxed text-[#444]">• {f}</li>
                ))}
              </ul>
              {sec.explainability ? (
                <p className="mt-3 text-[11px] text-[#888]">
                  Observed: {(sec.explainability.observed || []).slice(0, 3).join('; ') || '—'}
                  {' · '}
                  Inferred: {(sec.explainability.inferred || []).slice(0, 2).join('; ') || '—'}
                </p>
              ) : null}
            </article>
          );
        })}
      </section>
    </div>
  );
}

export default function GlobalMarketsPage() {
  const [pack, setPack] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getMiePack({ country: 'India' })
      .then((data) => {
        if (cancelled) return;
        setPack(data);
        setError(data?.ok === false ? data.error || data.status || 'macro unavailable' : null);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'macro failed');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  return (
    <PageShell
      title="Global Markets"
      eyebrow="AGI Research · Macro Intelligence"
      description="Institutional macro environment — regime, transmission, sector impact and scenario context for global and India research."
      metaTitle="Global Markets | Agarwal Global Investments"
      wide
    >
      <div className="space-y-10">
        <div className="rounded-xl border border-[#e6e8ec] bg-white p-6 md:p-8">
          <h2 className="font-serif text-2xl font-bold text-[#111111]">Ask the global markets desk</h2>
          <p className="mt-2 text-sm text-[#555555]">
            Connect overnight global moves to Indian equities, FX and macro conditions.
          </p>
          <div className="mt-5">
            <AskAgiBar
              placeholder="What is AGIB's current macro regime? Which sectors benefit from falling inflation?"
              size="large"
              buttonLabel="Ask AGI"
              ariaLabel="Ask AGI about global markets"
            />
          </div>
        </div>

        <MieSurface pack={pack} loading={loading} error={error} />

        <DeskResearchFeed deskId="global-markets" title="Global Markets Research" />

        <div className="flex flex-wrap gap-3">
          <Link
            to="/macro-intelligence"
            className="rounded-md bg-[#0b1f33] px-5 py-2.5 text-sm font-bold text-white hover:bg-[#163353]"
          >
            Full Macro Workstation
          </Link>
          <Link
            to="/pre-market"
            className="rounded-md border border-[#d5d8de] px-5 py-2.5 text-sm font-bold text-[#111111] hover:border-[#111111]"
          >
            Pre-Market Brief
          </Link>
          <Link
            to="/admin/macro-runtime"
            className="rounded-md border border-[#d5d8de] px-5 py-2.5 text-sm font-bold text-[#111111] hover:border-[#111111]"
          >
            Macro Runtime
          </Link>
        </div>
      </div>
    </PageShell>
  );
}
