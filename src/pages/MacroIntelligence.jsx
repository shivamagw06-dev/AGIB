import { useEffect, useMemo, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Bell,
  BookOpen,
  BrainCircuit,
  CalendarDays,
  ChevronRight,
  Clock3,
  Globe2,
  Landmark,
  Layers,
  LineChart,
  Search,
  Sparkles,
  Star,
  X,
} from 'lucide-react';
import { getMacroBriefing } from '@/api/marketApi';
import { getUiCopilot, getUiMacro } from '@/lib/uiApi';
import { supabase } from '@/lib/supabaseClient';
import { mapArticleForCard } from '@/lib/articleUtils';
import {
  TOP_TABS,
  WORKSPACES,
  buildCentralBanks,
  buildCommodityCards,
  buildCountryCards,
  buildExplainableCards,
  buildFxCards,
  buildScenarios,
  indiaIndicators,
} from '@/pages/macro/macroWorkstationModel';

const ICONS = {
  overview: BrainCircuit,
  global: Globe2,
  india: Landmark,
  'central-banks': Landmark,
  dashboard: LineChart,
  commodities: Layers,
  currencies: Activity,
  calendar: CalendarDays,
  policy: Landmark,
  transmission: Activity,
  sectors: ArrowUpRight,
  scenarios: AlertTriangle,
  historical: Clock3,
  forecasts: LineChart,
  research: BookOpen,
  knowledge: Layers,
  watchlist: Star,
  alerts: Bell,
  ask: Sparkles,
  settings: Search,
};

const VALID_WORKSPACES = new Set(WORKSPACES().map((w) => w.id));

function toneClass(tone = 'neutral') {
  if (tone === 'positive') return 'bg-[#ecfdf3] text-[#087443] border-[#b7ebcc]';
  if (tone === 'negative') return 'bg-[#fff1f0] text-[#b42318] border-[#f7c5c0]';
  return 'bg-[#f4f6f9] text-[#59616d] border-[#e7eaf0]';
}

function statusTone(value = '') {
  const text = String(value).toLowerCase();
  if (/weak|high|risk|tight|delay|cautious|bear|neg|dry|restrict|firm/i.test(text)) return 'negative';
  if (/improv|construct|positive|strong|wet|eas|moderat|support|bull/i.test(text)) return 'positive';
  return 'neutral';
}

function Badge({ children, tone = 'neutral' }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold tracking-wide ${toneClass(tone)}`}>
      {children}
    </span>
  );
}

function Card({ children, className = '', onClick }) {
  const clickable = typeof onClick === 'function';
  const Comp = clickable ? 'button' : 'div';
  return (
    <Comp
      type={clickable ? 'button' : undefined}
      onClick={onClick}
      className={`rounded-2xl border border-[#e7eaf0] bg-white text-left shadow-[0_1px_2px_rgba(16,24,40,0.04),0_8px_24px_rgba(16,24,40,0.04)] ${
        clickable ? 'transition hover:-translate-y-0.5 hover:border-[#98a2b3] cursor-pointer' : ''
      } ${className}`}
    >
      {children}
    </Comp>
  );
}

function Sparkline({ values = [], tone = 'neutral' }) {
  const nums = values.filter(Number.isFinite);
  if (nums.length < 2) return null;
  const min = Math.min(...nums);
  const max = Math.max(...nums);
  const span = max - min || 1;
  const w = 88;
  const h = 28;
  const points = nums
    .map((v, i) => {
      const x = (i / (nums.length - 1)) * w;
      const y = h - ((v - min) / span) * (h - 4) - 2;
      return `${x},${y}`;
    })
    .join(' ');
  const stroke = tone === 'positive' ? '#087443' : tone === 'negative' ? '#b42318' : '#3b6ea5';
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="overflow-visible" aria-hidden>
      <polyline fill="none" stroke={stroke} strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" points={points} />
    </svg>
  );
}

function SectionTitle({ eyebrow, title, action }) {
  return (
    <div className="mb-4 flex items-end justify-between gap-4">
      <div>
        {eyebrow ? <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#3b6ea5]">{eyebrow}</p> : null}
        <h2 className="mt-1 text-lg font-semibold tracking-tight text-[#101828]">{title}</h2>
      </div>
      {action}
    </div>
  );
}

/** Explainable intelligence card — Current / Why / Forecast / Confidence / Implication */
function IntelCard({ card, onOpen }) {
  return (
    <Card className="p-4" onClick={() => onOpen?.(card)}>
      <div className="flex items-start justify-between gap-2">
        <p className="text-[11px] font-semibold text-[#667085]">{card.label || card.name || card.pair}</p>
        <Badge tone={statusTone(card.status || card.direction || card.condition)}>
          {card.status || card.direction || card.condition || 'Watch'}
        </Badge>
      </div>
      <p className="mt-3 text-2xl font-semibold tracking-tight text-[#101828]">
        {card.value != null ? card.value : card.direction || '—'}
      </p>
      {card.sparkline?.length ? (
        <div className="mt-3">
          <Sparkline values={card.sparkline} tone={card.tone || statusTone(card.status)} />
        </div>
      ) : null}
      <div className="mt-3 space-y-2 border-t border-[#eef1f6] pt-3">
        <p className="text-[11px] leading-relaxed text-[#475467]">
          <span className="font-semibold text-[#101828]">Why · </span>
          {card.why || 'Desk assessment pending fuller prints.'}
        </p>
        <p className="text-[11px] leading-relaxed text-[#475467]">
          <span className="font-semibold text-[#101828]">Forecast · </span>
          {card.forecast || card.implication || 'Data-dependent.'}
        </p>
        {card.confidence != null ? (
          <p className="text-[11px] text-[#3b6ea5]">Confidence {card.confidence}%</p>
        ) : null}
      </div>
    </Card>
  );
}

function DetailDrawer({ item, onClose }) {
  if (!item) return null;
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/25 p-3 sm:p-6" onClick={onClose}>
      <div
        className="h-full w-full max-w-md overflow-y-auto rounded-2xl border border-[#e7eaf0] bg-white p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#3b6ea5]">Intelligence object</p>
            <h3 className="mt-1 text-xl font-semibold text-[#101828]">{item.label || item.name || item.title || item.pair}</h3>
          </div>
          <button type="button" onClick={onClose} className="rounded-lg p-1 hover:bg-[#f2f4f7]" aria-label="Close">
            <X className="h-4 w-4" />
          </button>
        </div>
        <dl className="mt-5 space-y-3 text-sm">
          {[
            ['Current', item.value ?? item.direction ?? item.condition],
            ['Trend', item.trend || item.status || item.direction],
            ['Why', item.why || item.explanation],
            ['Forecast', item.forecast],
            ['Confidence', item.confidence != null ? `${item.confidence}%` : null],
            ['Investment implication', item.implication || item.investment || item.indiaImpact],
            ['Transmission to India', item.transmissionToIndia],
            ['Source', item.source],
            ['As of', item.asOf],
          ]
            .filter(([, v]) => v)
            .map(([k, v]) => (
              <div key={k} className="rounded-xl border border-[#eef1f6] p-3">
                <dt className="text-[10px] font-bold uppercase tracking-wide text-[#98a2b3]">{k}</dt>
                <dd className="mt-1 text-[#344054]">{v}</dd>
              </div>
            ))}
        </dl>
        {item.drivers?.length ? (
          <div className="mt-4">
            <p className="text-[11px] font-bold uppercase text-[#667085]">Drivers</p>
            <ul className="mt-2 space-y-1">
              {item.drivers.map((d) => (
                <li key={d} className="text-xs text-[#475467]">
                  • {d}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {item.risks?.length ? (
          <div className="mt-4">
            <p className="text-[11px] font-bold uppercase text-[#667085]">Risks</p>
            <ul className="mt-2 space-y-1">
              {item.risks.map((d) => (
                <li key={d} className="text-xs text-[#b42318]">
                  • {d}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </div>
  );
}

const WATCH_KEY = 'agi_macro_watchlist_v1';

export default function MacroIntelligence() {
  const [state, setState] = useState({ loading: true, data: null, error: null });
  const [research, setResearch] = useState([]);
  const [workspace, setWorkspace] = useState('overview');
  const [askQuery, setAskQuery] = useState('');
  const [askAnswer, setAskAnswer] = useState(null);
  const [askOpen, setAskOpen] = useState(false);
  const [detail, setDetail] = useState(null);
  const [uiMacro, setUiMacro] = useState(null);
  const [watchlist, setWatchlist] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(WATCH_KEY) || '[]');
    } catch {
      return [];
    }
  });

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await getMacroBriefing();
        if (active) setState({ loading: false, data, error: null });
      } catch (error) {
        if (active) setState((prev) => ({ loading: false, data: prev.data, error }));
      }
    };
    load();
    getUiMacro()
      .then((data) => active && setUiMacro(data))
      .catch(() => active && setUiMacro(null));
    const interval = window.setInterval(load, 30 * 60_000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    const applyHash = () => {
      const raw = String(window.location.hash || '').replace(/^#/, '').trim();
      if (raw && VALID_WORKSPACES.has(raw)) setWorkspace(raw);
    };
    applyHash();
    window.addEventListener('hashchange', applyHash);
    return () => window.removeEventListener('hashchange', applyHash);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const { data } = await supabase
        .from('articles')
        .select('id, title, slug, excerpt, cover_url, tags, published_at, section, status')
        .eq('status', 'published')
        .order('published_at', { ascending: false })
        .limit(24);
      if (cancelled) return;
      const macroSections = /economy|macro|global|commodit|research|policy|budget|inflation|rbi/i;
      const mapped = (data || []).map(mapArticleForCard).filter(Boolean);
      const filtered = mapped.filter((article) => {
        const haystack = `${article.section || ''} ${(article.tags || []).join(' ')} ${article.title || ''}`;
        return macroSections.test(haystack);
      });
      setResearch((filtered.length ? filtered : mapped).slice(0, 8));
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(WATCH_KEY, JSON.stringify(watchlist));
    } catch {
      /* ignore */
    }
  }, [watchlist]);

  const briefing = state.data;
  const brief = briefing?.chiefEconomistBrief || {};
  const snapshot = briefing?.snapshot || {};
  const ws = briefing?.workspace || {};
  const regime = ws.regime || {};
  const whatChanged = ws.whatChanged || [];
  const transmission = ws.transmission || {};
  const confidence = ws.confidenceBreakdown || {};
  const cards = useMemo(() => buildExplainableCards(briefing), [briefing]);
  const countries = useMemo(() => buildCountryCards(briefing), [briefing]);
  const commodities = useMemo(() => buildCommodityCards(briefing), [briefing]);
  const fx = useMemo(() => buildFxCards(briefing), [briefing]);
  const scenarios = useMemo(() => buildScenarios(briefing), [briefing]);
  const banks = useMemo(() => buildCentralBanks(briefing), [briefing]);
  const indiaCards = useMemo(() => indiaIndicators(briefing), [briefing]);

  const updatedLabel = useMemo(() => {
    if (!briefing?.updatedAt) return 'Awaiting refresh';
    return new Date(briefing.updatedAt).toLocaleString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }, [briefing?.updatedAt]);

  const go = (id) => {
    if (!VALID_WORKSPACES.has(id)) return;
    setWorkspace(id);
    if (window.location.hash !== `#${id}`) {
      window.history.replaceState(null, '', `#${id}`);
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const toggleWatch = (item) => {
    const key = item.id || item.label || item.name || item.pair || item.title;
    setWatchlist((prev) => {
      if (prev.some((p) => p.key === key)) return prev.filter((p) => p.key !== key);
      return [...prev, { key, label: key, kind: item.kind || 'indicator', addedAt: new Date().toISOString() }].slice(0, 40);
    });
  };

  const handleAsk = async (query) => {
    const q = String(query || askQuery).trim();
    if (!q) return;
    setAskQuery(q);
    const lower = q.toLowerCase();
    let evidence = brief.whyReached || [];
    if (/bank|rate|fed|yield/i.test(lower)) {
      evidence = [
        { title: 'Rates transmission', explanation: brief.evidence?.interestRates?.evidence || brief.debate?.verdict },
        { title: 'Market impact', explanation: brief.evidence?.interestRates?.marketImpact },
      ].filter((item) => item.explanation);
    } else if (/oil|inflat|cpi/i.test(lower)) {
      evidence = [
        { title: 'Inflation channel', explanation: brief.evidence?.inflation?.evidence },
        { title: 'Commodities', explanation: brief.evidence?.commodities?.evidence },
      ].filter((item) => item.explanation);
    }

    let copilot = null;
    try {
      copilot = await getUiCopilot({ page: 'macro', question: q });
    } catch {
      copilot = null;
    }
    const ctx = copilot?.context || {};
    const ctxEvidence = [
      ...(Array.isArray(ctx.latest_news) ? ctx.latest_news.map((n) => ({ title: n.title, explanation: n.snippet })) : []),
      ...(ctx.house_view
        ? [{ title: 'Current house view', explanation: ctx.house_view.thesis || ctx.house_view.summary || ctx.house_view.current_view }]
        : []),
    ].filter((item) => item.title || item.explanation);

    setAskAnswer({
      query: q,
      response: brief.executiveThesis,
      evidence: [...evidence, ...ctxEvidence].slice(0, 8),
      implications: brief.sectorImpact,
      related: (brief.institutionalQuestions || []).slice(0, 3),
      outlook: brief.outlook || uiMacro?.current_regime?.label,
    });
    setAskOpen(true);
    setWorkspace('ask');
  };

  const navItems = WORKSPACES();
  const groups = [...new Set(navItems.map((n) => n.group))];

  const winners = brief.sectorImpact?.beneficiaries || [];
  const losers = brief.sectorImpact?.challenged || [];

  const renderHero = () => (
    <section className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.6fr)_minmax(300px,0.9fr)]">
      <Card className="p-6 sm:p-8">
        <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#3b6ea5]">Today&apos;s Macro Regime</p>
        <div className="mt-3 flex flex-wrap items-end gap-3">
          <h1 className="text-4xl font-semibold tracking-tight text-[#101828]">{regime.macroRegime || brief.outlook || 'Data-dependent'}</h1>
          <Badge tone={statusTone(regime.macroRegime || brief.outlook)}>
            Confidence {regime.confidence ?? brief.confidence ?? '—'}%
          </Badge>
        </div>
        <p className="mt-2 text-xs text-[#667085]">
          <Clock3 className="mr-1 inline h-3.5 w-3.5" />
          Updated {updatedLabel}
          {briefing?.stale ? ' · cached repository' : ''}
        </p>
        <p className="mt-5 max-w-3xl text-[15px] leading-8 text-[#344054]">
          <span className="font-semibold text-[#101828]">AGI Economist believes </span>
          {brief.executiveThesis ||
            'global conditions, Indian growth and liquidity must be read together before sizing risk.'}
        </p>
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-[#ecfdf3] bg-[#f6fef9] p-3">
            <p className="text-[10px] font-bold uppercase text-[#087443]">Overweight</p>
            <p className="mt-2 text-sm font-semibold text-[#101828]">
              {winners.slice(0, 3).map((w) => w.name).join(' · ') || 'Banks · Industrials · Capital Goods'}
            </p>
          </div>
          <div className="rounded-xl border border-[#e7eaf0] bg-[#fafbfd] p-3">
            <p className="text-[10px] font-bold uppercase text-[#667085]">Neutral</p>
            <p className="mt-2 text-sm font-semibold text-[#101828]">IT · Select defensives</p>
          </div>
          <div className="rounded-xl border border-[#fff1f0] bg-[#fffafa] p-3">
            <p className="text-[10px] font-bold uppercase text-[#b42318]">Underweight</p>
            <p className="mt-2 text-sm font-semibold text-[#101828]">
              {losers.slice(0, 3).map((w) => w.name).join(' · ') || 'Energy producers (near-term)'}
            </p>
          </div>
        </div>
      </Card>
      <Card className="p-5">
        <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#3b6ea5]">Regime dials</p>
        <div className="mt-4 grid grid-cols-2 gap-3">
          {[
            ['Cycle', regime.cycle],
            ['Inflation', regime.inflation],
            ['Policy', regime.policy],
            ['Liquidity', regime.liquidity],
            ['Volatility', regime.volatility],
            ['Risk', regime.riskEnvironment],
          ].map(([label, value]) => (
            <button
              key={label}
              type="button"
              onClick={() => setDetail({ label, value, why: brief.stanceRationale || confidence.rationale, confidence: regime.confidence })}
              className="rounded-xl border border-[#eef1f6] bg-[#fafbfd] p-3 text-left hover:border-[#3b6ea5]"
            >
              <p className="text-[10px] font-semibold uppercase tracking-wide text-[#98a2b3]">{label}</p>
              <p className="mt-1 text-sm font-semibold text-[#101828]">{value || '—'}</p>
            </button>
          ))}
        </div>
        <p className="mt-4 text-xs leading-relaxed text-[#667085]">{confidence.summary || confidence.rationale}</p>
      </Card>
    </section>
  );

  const renderOverview = () => (
    <div className="space-y-6">
      {renderHero()}
      <section>
        <SectionTitle eyebrow="Explainable desk" title="Key macro intelligence" />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {cards.slice(0, 6).map((card) => (
            <IntelCard key={card.id} card={card} onOpen={setDetail} />
          ))}
        </div>
      </section>
      <section className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="p-5 xl:col-span-1">
          <SectionTitle eyebrow="Today" title="What changed" />
          <div className="space-y-3">
            {whatChanged.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setDetail({ ...item, label: item.title, why: item.why, implication: item.impact })}
                className="w-full rounded-xl border border-[#eef1f6] p-3 text-left hover:border-[#3b6ea5]"
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-semibold">{item.title}</p>
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold">
                    {item.tone === 'positive' ? <ArrowUpRight className="h-3.5 w-3.5 text-[#087443]" /> : null}
                    {item.tone === 'negative' ? <ArrowDownRight className="h-3.5 w-3.5 text-[#b42318]" /> : null}
                    {item.move}
                  </span>
                </div>
                <p className="mt-2 text-xs text-[#667085]">
                  <span className="font-semibold text-[#344054]">Why · </span>
                  {item.why}
                </p>
              </button>
            ))}
          </div>
        </Card>
        <Card className="p-5">
          <SectionTitle eyebrow="Risks" title="Today&apos;s biggest risks" />
          <div className="space-y-3">
            {(snapshot.risks || []).slice(0, 4).map((risk) => (
              <button
                key={risk.label}
                type="button"
                onClick={() => setDetail({ label: risk.label, why: risk.why, implication: `Watch: ${risk.watch}`, status: risk.level })}
                className="w-full rounded-xl border border-[#eef1f6] p-3 text-left hover:border-[#3b6ea5]"
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-semibold">{risk.label}</p>
                  <Badge tone={statusTone(risk.level)}>{risk.level}</Badge>
                </div>
                <p className="mt-1 text-xs text-[#667085]">{risk.why}</p>
              </button>
            ))}
          </div>
        </Card>
        <Card className="p-5">
          <SectionTitle
            eyebrow="Calendar"
            title="Upcoming events"
            action={
              <button type="button" onClick={() => go('calendar')} className="text-xs font-semibold text-[#1d4f91]">
                Open calendar →
              </button>
            }
          />
          <div className="space-y-3">
            {(snapshot.calendar || []).slice(0, 5).map((item) => (
              <div key={item.event} className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-[11px] font-semibold text-[#98a2b3]">{item.date || 'TBD'}</p>
                  <p className="text-sm font-medium text-[#101828]">{item.event}</p>
                  <p className="mt-1 text-[11px] text-[#667085]">{item.note}</p>
                </div>
                <Badge tone={item.importance === 'High' ? 'negative' : 'neutral'}>{item.importance}</Badge>
              </div>
            ))}
          </div>
        </Card>
      </section>
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <SectionTitle eyebrow="Why this view" title="Economist reasoning" />
          <div className="space-y-3">
            {(brief.whyReached || []).map((item, index) => (
              <div key={item.title} className="rounded-xl border border-[#eef1f6] bg-[#fafbfd] p-4">
                <p className="text-sm font-semibold text-[#101828]">
                  {index + 1}. {item.title}
                </p>
                <p className="mt-2 text-xs leading-relaxed text-[#667085]">{item.explanation}</p>
              </div>
            ))}
          </div>
        </Card>
        <Card className="p-5">
          <SectionTitle
            eyebrow="Allocation"
            title="Sector winners & losers"
            action={
              <button type="button" onClick={() => go('sectors')} className="text-xs font-semibold text-[#1d4f91]">
                Full matrix →
              </button>
            }
          />
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <p className="text-[11px] font-bold uppercase text-[#087443]">Winners</p>
              <ul className="mt-2 space-y-2">
                {winners.map((item) => (
                  <li key={item.name} className="rounded-xl border border-[#ecfdf3] bg-[#f6fef9] p-3">
                    <p className="text-sm font-semibold">{item.name}</p>
                    <p className="mt-1 text-xs text-[#667085]">{item.why}</p>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase text-[#b42318]">Losers</p>
              <ul className="mt-2 space-y-2">
                {losers.map((item) => (
                  <li key={item.name} className="rounded-xl border border-[#fff1f0] bg-[#fffafa] p-3">
                    <p className="text-sm font-semibold">{item.name}</p>
                    <p className="mt-1 text-xs text-[#667085]">{item.why}</p>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      </section>
    </div>
  );

  const renderGlobal = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="Global Economy" title="Country intelligence workspaces" />
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {countries.map((c) => (
          <Card key={c.name} className="p-5" onClick={() => setDetail(c)}>
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-lg font-semibold">{c.name}</h3>
              <Badge tone={statusTone(c.condition)}>{c.condition}</Badge>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
              {[
                ['GDP', c.gdp],
                ['Inflation', c.inflation],
                ['Rates', c.rates],
                ['Labour', c.employment],
              ].map(([k, v]) => (
                <div key={k} className="rounded-lg border border-[#eef1f6] bg-[#fafbfd] px-2.5 py-2">
                  <p className="font-semibold text-[#98a2b3]">{k}</p>
                  <p className="mt-0.5 text-[#344054]">{v}</p>
                </div>
              ))}
            </div>
            <p className="mt-3 text-sm leading-relaxed text-[#475467]">{c.why}</p>
            <p className="mt-3 text-xs text-[#3b6ea5]">
              <span className="font-semibold">Transmission to India · </span>
              {c.transmissionToIndia}
            </p>
            <p className="mt-2 text-xs text-[#667085]">
              <span className="font-semibold text-[#101828]">Markets · </span>
              {c.transmissionToMarkets}
            </p>
            <p className="mt-2 text-xs text-[#667085]">
              <span className="font-semibold text-[#101828]">Forecast · </span>
              {c.forecast}
            </p>
          </Card>
        ))}
      </div>
      <SectionTitle eyebrow="Themes" title="Global macro themes" />
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        {(snapshot.themes || []).map((t) => (
          <IntelCard
            key={t.id || t.title}
            card={{
              label: t.title,
              value: t.condition,
              status: t.condition,
              why: t.summary,
              forecast: t.summary,
              implication: t.summary,
            }}
            onOpen={setDetail}
          />
        ))}
      </div>
    </div>
  );

  const renderIndia = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="India Focus" title="Domestic growth · inflation · demand · policy" />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {indiaCards.map((card) => (
          <IntelCard key={card.id} card={card} onOpen={setDetail} />
        ))}
      </div>
      {snapshot.weather ? (
        <Card className="p-5">
          <SectionTitle eyebrow="Monsoon / weather" title={snapshot.weather.region || 'India weather channel'} />
          <p className="text-sm text-[#344054]">{snapshot.weather.implication || snapshot.weather.rainfallOutlook}</p>
          <p className="mt-2 text-xs text-[#667085]">Heat stress: {snapshot.weather.heatStress || '—'} · Source {snapshot.weather.source}</p>
        </Card>
      ) : null}
    </div>
  );

  const renderBanks = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="Monetary Policy" title="Central bank workstation" />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {banks.map((b) => (
          <Card key={b.id} className="p-5" onClick={() => setDetail({ ...b, label: b.name, value: b.currentRate, why: b.aiOpinion })}>
            <p className="text-[10px] font-bold uppercase tracking-wide text-[#3b6ea5]">{b.name}</p>
            <p className="mt-3 text-2xl font-semibold">{b.currentRate}</p>
            <p className="mt-1 text-xs text-[#667085]">{b.direction}</p>
            <div className="mt-4 space-y-2 text-xs text-[#475467]">
              <p>
                <span className="font-semibold text-[#101828]">Market pricing · </span>
                {b.marketPricing}
              </p>
              <p>
                <span className="font-semibold text-[#101828]">Next · </span>
                {b.nextMeeting}
              </p>
              <p>
                <span className="font-semibold text-[#101828]">AI opinion · </span>
                {b.aiOpinion}
              </p>
            </div>
            {b.history?.length ? (
              <div className="mt-4">
                <Sparkline values={b.history} tone={statusTone(b.direction)} />
              </div>
            ) : null}
          </Card>
        ))}
      </div>
      <Card className="p-5">
        <SectionTitle eyebrow="Rates complex" title="Global rates & inflation prints" />
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {(snapshot.rates || []).map((r) => (
            <IntelCard
              key={r.label}
              card={{
                label: r.label,
                value: r.value,
                status: r.direction,
                sparkline: r.history,
                source: r.source,
                asOf: r.date,
                why: `${r.label} informs global financial conditions and EM transmission.`,
                forecast: `Direction currently ${String(r.direction || 'stable').toLowerCase()}.`,
                implication: 'Feeds into INR, bond yields and equity risk appetite.',
              }}
              onOpen={setDetail}
            />
          ))}
        </div>
      </Card>
    </div>
  );

  const renderCommodities = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="Commodities" title="Price · supply/demand narrative · India impact" />
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {commodities.map((c) => (
          <Card key={c.name} className="p-5" onClick={() => setDetail({ ...c, label: c.name, value: c.direction, implication: c.investment })}>
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-semibold">{c.name}</h3>
              <Badge tone={statusTone(c.direction)}>{c.direction}</Badge>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-[#475467]">
              <span className="font-semibold text-[#101828]">Why · </span>
              {c.why}
            </p>
            <p className="mt-2 text-xs leading-relaxed text-[#475467]">
              <span className="font-semibold text-[#101828]">India impact · </span>
              {c.indiaImpact}
            </p>
            <p className="mt-2 text-xs leading-relaxed text-[#3b6ea5]">
              <span className="font-semibold">Investment · </span>
              {c.investment}
            </p>
            <p className="mt-3 text-[10px] text-[#98a2b3]">Source {c.source}</p>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderFx = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="Currencies" title="FX · reserves · capital-flow lens" />
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {fx.map((f) => (
          <IntelCard
            key={f.pair}
            card={{
              label: f.pair,
              value: f.value,
              status: f.direction,
              why: f.why,
              forecast: f.implication,
              implication: f.implication,
              asOf: f.asOf,
            }}
            onOpen={setDetail}
          />
        ))}
      </div>
      {!fx.length ? <p className="text-sm text-[#667085]">FX snapshot will populate when live feeds refresh.</p> : null}
    </div>
  );

  const renderPolicy = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="Policy Tracker" title="RBI · fiscal · regulatory · cabinet lens" />
      <div className="space-y-3">
        {(snapshot.policyTracker || []).map((item) => (
          <Card
            key={item.body}
            className="p-5"
            onClick={() =>
              setDetail({
                label: item.body,
                why: item.whatChanged,
                implication: item.whyItMatters,
                value: item.whoAffected,
              })
            }
          >
            <p className="text-sm font-semibold text-[#101828]">{item.body}</p>
            <p className="mt-2 text-sm text-[#344054]">{item.whatChanged}</p>
            <p className="mt-2 text-xs text-[#667085]">
              <span className="font-semibold text-[#101828]">Why it matters · </span>
              {item.whyItMatters}
            </p>
            <p className="mt-1 text-xs text-[#3b6ea5]">Affected: {item.whoAffected}</p>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderTransmission = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="Macro Transmission Engine" title={transmission.title || 'Causal chains into markets'} />
      <p className="text-sm text-[#667085]">{transmission.subtitle}</p>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card className="p-4">
          <p className="mb-2 text-[10px] font-bold uppercase text-[#98a2b3]">Drivers</p>
          <div className="space-y-2">
            {(transmission.drivers || []).map((node) => (
              <button
                key={node.id}
                type="button"
                onClick={() => setDetail({ label: node.label, why: 'Active macro driver in today\'s transmission map.', implication: 'Follow the chain into inflation, policy and sectors.' })}
                className="flex w-full items-center justify-between rounded-xl border border-[#e7eaf0] bg-[#f8fafc] px-3 py-2.5 text-left text-xs font-semibold"
              >
                {node.label}
                <ChevronRight className="h-3.5 w-3.5 text-[#98a2b3]" />
              </button>
            ))}
          </div>
        </Card>
        <Card className="p-4">
          <p className="mb-2 text-[10px] font-bold uppercase text-[#98a2b3]">Transmission</p>
          <div className="space-y-2">
            {(transmission.transmissions || []).map((node) => (
              <div key={node.id} className="rounded-xl border border-[#d9e4f2] bg-[#eef4fb] px-3 py-2.5 text-xs font-semibold text-[#1d4f91]">
                {node.label}
              </div>
            ))}
          </div>
        </Card>
        <Card className="p-4">
          <p className="mb-2 text-[10px] font-bold uppercase text-[#98a2b3]">Outcomes</p>
          <div className="space-y-2">
            {(transmission.outcomes || []).map((node) => (
              <div key={node.id} className={`rounded-xl border px-3 py-2.5 text-xs font-semibold ${toneClass(node.tone)}`}>
                {node.label}
              </div>
            ))}
          </div>
        </Card>
      </div>
      <div className="grid gap-3 lg:grid-cols-3">
        {(transmission.maps || brief.transmissionMaps || []).map((map) => (
          <Card key={map.id} className="p-4">
            <p className="text-[11px] font-semibold text-[#3b6ea5]">{map.title}</p>
            <p className="mt-1 text-xs font-medium text-[#101828]">{map.trigger}</p>
            <ol className="mt-3 space-y-1">
              {(map.steps || []).map((step) => (
                <li key={step} className="text-[11px] leading-relaxed text-[#667085]">
                  → {step}
                </li>
              ))}
            </ol>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderScenarios = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="Scenario Engine" title="Shock paths · GDP · inflation · rates · sectors" />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {scenarios.map((s) => (
          <Card key={s.id} className="p-5">
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-lg font-semibold">{s.title}</h3>
              <Badge>{s.probability}</Badge>
            </div>
            {s.why ? <p className="mt-2 text-xs text-[#667085]">{s.why}</p> : null}
            <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
              {[
                ['GDP', s.gdp],
                ['Inflation', s.inflation],
                ['Rates', s.rates],
                ['INR', s.inr],
                ['Nifty', s.nifty],
              ].map(([k, v]) => (
                <div key={k} className="rounded-lg border border-[#eef1f6] p-2">
                  <p className="font-semibold text-[#98a2b3]">{k}</p>
                  <p className="mt-1 text-[#344054]">{v}</p>
                </div>
              ))}
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
              <div>
                <p className="font-bold text-[#087443]">Winners</p>
                <p className="mt-1 text-[#475467]">{(s.sectors?.winners || []).join(' · ') || '—'}</p>
              </div>
              <div>
                <p className="font-bold text-[#b42318]">Losers</p>
                <p className="mt-1 text-[#475467]">{(s.sectors?.losers || []).join(' · ') || '—'}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderCalendar = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="Economic Calendar" title="Preview · impact · AI note" />
      <div className="space-y-3">
        {(snapshot.calendar || []).map((item) => (
          <Card key={item.event} className="p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-[11px] font-semibold text-[#98a2b3]">{item.date}</p>
                <h3 className="mt-1 text-lg font-semibold">{item.event}</h3>
                <p className="mt-2 text-sm text-[#475467]">{item.note}</p>
                <p className="mt-2 text-xs text-[#3b6ea5]">Sectors: {(item.sectors || []).join(' · ')}</p>
              </div>
              <Badge tone={item.importance === 'High' ? 'negative' : 'neutral'}>{item.importance} impact</Badge>
            </div>
            <p className="mt-3 text-xs text-[#667085]">
              <span className="font-semibold text-[#101828]">AI preview · </span>
              Watch surprise vs consensus; map into rates, INR and the sector list above before the print.
            </p>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderResearch = () => (
    <div className="space-y-6">
      <SectionTitle
        eyebrow="Research Workspace"
        title="Notes · outlooks · IC memos"
        action={
          <Link to="/research" className="text-xs font-semibold text-[#1d4f91]">
            Open library →
          </Link>
        }
      />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {['Morning Note', 'Weekly Macro', 'Monthly Outlook', 'Central Bank Review', 'Commodity Report', 'IC Memo'].map((label) => (
          <Card key={label} className="p-5">
            <p className="text-sm font-semibold">{label}</p>
            <p className="mt-2 text-xs text-[#667085]">Generate from today&apos;s Chief Economist brief and transmission map.</p>
            <button
              type="button"
              onClick={() => handleAsk(`Generate an institutional ${label.toLowerCase()} from today's macro regime.`)}
              className="mt-4 text-xs font-semibold text-[#1d4f91]"
            >
              Generate with AI Economist →
            </button>
          </Card>
        ))}
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {research.map((article) => (
          <Link
            key={article.id || article.slug}
            to={`/article/${article.slug}`}
            className="rounded-2xl border border-[#eef1f6] bg-white p-4 transition hover:border-[#98a2b3]"
          >
            <Badge>{article.section || 'Research'}</Badge>
            <h3 className="mt-3 text-sm font-semibold leading-snug text-[#101828]">{article.title}</h3>
            <p className="mt-2 line-clamp-2 text-xs text-[#667085]">{article.excerpt}</p>
          </Link>
        ))}
      </div>
    </div>
  );

  const renderWatchlist = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="Watchlist" title="Your tracked macro objects" />
      <p className="text-sm text-[#667085]">Click any intelligence card elsewhere, then star it here — or add from the dashboard.</p>
      <div className="flex flex-wrap gap-2">
        {cards.slice(0, 8).map((c) => (
          <button
            key={c.id}
            type="button"
            onClick={() => toggleWatch(c)}
            className="rounded-full border border-[#e7eaf0] bg-white px-3 py-1.5 text-xs font-semibold hover:border-[#3b6ea5]"
          >
            {watchlist.some((w) => w.key === c.id) ? '★' : '☆'} {c.label}
          </button>
        ))}
      </div>
      <div className="space-y-2">
        {watchlist.length ? (
          watchlist.map((w) => (
            <Card key={w.key} className="flex items-center justify-between p-4">
              <div>
                <p className="text-sm font-semibold">{w.label}</p>
                <p className="text-[11px] text-[#98a2b3]">Added {new Date(w.addedAt).toLocaleString('en-IN')}</p>
              </div>
              <button type="button" onClick={() => toggleWatch({ id: w.key, label: w.label })} className="text-xs font-semibold text-[#b42318]">
                Remove
              </button>
            </Card>
          ))
        ) : (
          <p className="text-sm text-[#667085]">No watched items yet.</p>
        )}
      </div>
    </div>
  );

  const renderAsk = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="AI Economist" title="Ask · explain · generate institutional notes" />
      <Card className="p-6">
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            value={askQuery}
            onChange={(e) => setAskQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
            placeholder="How does higher oil affect India? Will RBI cut this year?"
            className="min-w-0 flex-1 rounded-xl border border-[#e7eaf0] bg-[#f8fafc] px-4 py-3 text-sm outline-none focus:bg-white focus:ring-2 focus:ring-[#3b6ea5]/30"
          />
          <button
            type="button"
            onClick={() => handleAsk()}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#1d4f91] px-5 py-3 text-sm font-semibold text-white"
          >
            <Sparkles className="h-4 w-4" /> Ask
          </button>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {(ws.askPrompts || brief.institutionalQuestions || []).slice(0, 8).map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => handleAsk(q)}
              className="rounded-full border border-[#e7eaf0] bg-white px-3 py-1.5 text-xs font-semibold text-[#344054] hover:border-[#3b6ea5]"
            >
              {q}
            </button>
          ))}
        </div>
      </Card>
      {askAnswer ? (
        <Card className="p-6">
          <p className="text-[10px] font-bold uppercase tracking-wide text-[#3b6ea5]">AI response</p>
          <h3 className="mt-2 text-lg font-semibold">{askAnswer.query}</h3>
          <p className="mt-3 text-sm leading-7 text-[#344054]">{askAnswer.response}</p>
          <div className="mt-4"><Badge tone={statusTone(askAnswer.outlook)}>{askAnswer.outlook}</Badge></div>
          <div className="mt-5 space-y-2">
            {(askAnswer.evidence || []).map((item) => (
              <div key={item.title} className="rounded-xl border border-[#eef1f6] p-3">
                <p className="text-sm font-semibold">{item.title}</p>
                <p className="mt-1 text-xs text-[#667085]">{item.explanation}</p>
              </div>
            ))}
          </div>
        </Card>
      ) : null}
    </div>
  );

  const renderDashboard = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="Macro Dashboard" title="All explainable indicators" />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {cards.map((card) => (
          <IntelCard key={card.id} card={card} onOpen={setDetail} />
        ))}
      </div>
    </div>
  );

  const renderSectors = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="Sector Impact" title="Who benefits · who loses · why" />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <p className="text-[11px] font-bold uppercase text-[#087443]">Beneficiaries</p>
          <ul className="mt-3 space-y-2">
            {winners.map((item) => (
              <li key={item.name} className="rounded-xl border border-[#ecfdf3] bg-[#f6fef9] p-3">
                <p className="text-sm font-semibold">{item.name}</p>
                <p className="mt-1 text-xs text-[#667085]">{item.why}</p>
              </li>
            ))}
          </ul>
        </Card>
        <Card className="p-5">
          <p className="text-[11px] font-bold uppercase text-[#b42318]">Headwinds</p>
          <ul className="mt-3 space-y-2">
            {losers.map((item) => (
              <li key={item.name} className="rounded-xl border border-[#fff1f0] bg-[#fffafa] p-3">
                <p className="text-sm font-semibold">{item.name}</p>
                <p className="mt-1 text-xs text-[#667085]">{item.why}</p>
              </li>
            ))}
          </ul>
        </Card>
      </div>
      <button type="button" onClick={() => go('transmission')} className="text-sm font-semibold text-[#1d4f91]">
        Open transmission maps →
      </button>
    </div>
  );

  const renderHistorical = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="Historical Data" title="Trends behind today’s regime" />
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {(snapshot.rates || [])
          .concat(cards.filter((c) => c.sparkline?.length).slice(0, 6))
          .slice(0, 9)
          .map((row, idx) => {
            const label = row.label || row.name;
            const series = row.history || row.sparkline || [];
            return (
              <Card
                key={`${label}-${idx}`}
                className="p-5"
                onClick={() =>
                  setDetail({
                    label,
                    value: row.value,
                    trend: row.direction || row.status,
                    why: 'Historical path informs whether today’s print is a break or a continuation.',
                    forecast: 'Use the latest regime dials before extrapolating the series.',
                    source: row.source,
                  })
                }
              >
                <p className="text-sm font-semibold">{label}</p>
                <p className="mt-1 text-2xl font-semibold">{row.value ?? '—'}</p>
                {series.length ? (
                  <div className="mt-3">
                    <Sparkline values={series} tone={statusTone(row.direction || row.status)} />
                  </div>
                ) : (
                  <p className="mt-3 text-xs text-[#667085]">Series populates as feeds refresh.</p>
                )}
              </Card>
            );
          })}
      </div>
    </div>
  );

  const renderForecasts = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="Forecast Models" title="Desk paths · confidence · risks" />
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        {cards.slice(0, 6).map((card) => (
          <Card key={card.id} className="p-5" onClick={() => setDetail(card)}>
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-semibold">{card.label}</p>
              {card.confidence != null ? <Badge>{card.confidence}% conf.</Badge> : null}
            </div>
            <p className="mt-3 text-xs leading-relaxed text-[#475467]">
              <span className="font-semibold text-[#101828]">Base case · </span>
              {card.forecast}
            </p>
            <p className="mt-2 text-xs leading-relaxed text-[#667085]">
              <span className="font-semibold text-[#101828]">Implication · </span>
              {card.implication}
            </p>
            {(card.risks || []).length ? (
              <p className="mt-2 text-xs text-[#b42318]">Risks: {card.risks.join(' · ')}</p>
            ) : null}
          </Card>
        ))}
      </div>
      <Card className="p-5">
        <SectionTitle eyebrow="Scenario overlay" title="Stress the forecast" />
        <div className="flex flex-wrap gap-2">
          {scenarios.slice(0, 4).map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => go('scenarios')}
              className="rounded-full border border-[#e7eaf0] bg-white px-3 py-1.5 text-xs font-semibold hover:border-[#3b6ea5]"
            >
              {s.title}
            </button>
          ))}
        </div>
      </Card>
    </div>
  );

  const renderKnowledge = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="Knowledge Graph" title="Objects linked by transmission" />
      <div className="grid gap-3 md:grid-cols-3">
        {[
          {
            title: 'Drivers',
            nodes: (transmission.drivers || []).map((n) => n.label).concat(['Oil', 'Fed path', 'Monsoon']).slice(0, 6),
          },
          {
            title: 'Channels',
            nodes: (transmission.transmissions || []).map((n) => n.label).concat(['CPI', 'RBI', 'INR', 'Bond yields']).slice(0, 6),
          },
          {
            title: 'Outcomes',
            nodes: (transmission.outcomes || [])
              .map((n) => n.label)
              .concat(winners.slice(0, 2).map((w) => w.name), losers.slice(0, 2).map((w) => w.name))
              .slice(0, 6),
          },
        ].map((col) => (
          <Card key={col.title} className="p-5">
            <p className="text-[10px] font-bold uppercase tracking-wide text-[#98a2b3]">{col.title}</p>
            <div className="mt-3 space-y-2">
              {col.nodes.filter(Boolean).map((node) => (
                <button
                  key={`${col.title}-${node}`}
                  type="button"
                  onClick={() =>
                    setDetail({
                      label: node,
                      why: `${node} sits inside today’s macro knowledge graph and feeds portfolio transmission.`,
                      implication: 'Open Transmission Maps or Sector Impact to size the portfolio effect.',
                    })
                  }
                  className="flex w-full items-center justify-between rounded-xl border border-[#eef1f6] px-3 py-2 text-left text-xs font-semibold hover:border-[#3b6ea5]"
                >
                  {node}
                  <ArrowRight className="h-3.5 w-3.5 text-[#98a2b3]" />
                </button>
              ))}
            </div>
          </Card>
        ))}
      </div>
      <button type="button" onClick={() => go('transmission')} className="text-sm font-semibold text-[#1d4f91]">
        Explore full transmission engine →
      </button>
    </div>
  );

  const renderAlerts = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="Alerts" title="Regime breaks · calendar · watchlist moves" />
      <div className="space-y-3">
        {[
          ...whatChanged.map((item) => ({
            title: item.title,
            body: item.why,
            level: item.tone === 'negative' ? 'High' : 'Medium',
            kind: 'Change',
          })),
          ...(snapshot.risks || []).slice(0, 3).map((r) => ({
            title: r.label,
            body: r.why,
            level: r.level || 'Medium',
            kind: 'Risk',
          })),
          ...(snapshot.calendar || []).slice(0, 2).map((c) => ({
            title: c.event,
            body: c.note,
            level: c.importance || 'Medium',
            kind: 'Calendar',
          })),
        ].map((alert, idx) => (
          <Card key={`${alert.title}-${idx}`} className="p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wide text-[#98a2b3]">{alert.kind}</p>
                <p className="mt-1 text-sm font-semibold">{alert.title}</p>
                <p className="mt-1 text-xs text-[#667085]">{alert.body}</p>
              </div>
              <Badge tone={statusTone(alert.level)}>{alert.level}</Badge>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderSettings = () => (
    <div className="space-y-6">
      <SectionTitle eyebrow="Settings" title="Workstation preferences" />
      <Card className="p-5 space-y-4">
        <div>
          <p className="text-sm font-semibold">Default workspace</p>
          <p className="mt-1 text-xs text-[#667085]">Landing view when you open Macro Intelligence.</p>
          <select
            className="mt-3 w-full max-w-sm rounded-xl border border-[#e7eaf0] bg-white px-3 py-2 text-sm"
            value={workspace}
            onChange={(e) => go(e.target.value)}
          >
            {navItems.map((n) => (
              <option key={n.id} value={n.id}>
                {n.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <p className="text-sm font-semibold">Data refresh</p>
          <p className="mt-1 text-xs text-[#667085]">
            Briefing auto-refreshes every 30 minutes. Last update: {updatedLabel}
          </p>
        </div>
        <div>
          <p className="text-sm font-semibold">Watchlist storage</p>
          <p className="mt-1 text-xs text-[#667085]">Stored locally in this browser ({watchlist.length} items).</p>
          <button
            type="button"
            onClick={() => setWatchlist([])}
            className="mt-3 text-xs font-semibold text-[#b42318]"
          >
            Clear watchlist
          </button>
        </div>
      </Card>
    </div>
  );

  const body = () => {
    switch (workspace) {
      case 'global':
        return renderGlobal();
      case 'india':
        return renderIndia();
      case 'central-banks':
        return renderBanks();
      case 'dashboard':
        return renderDashboard();
      case 'commodities':
        return renderCommodities();
      case 'currencies':
        return renderFx();
      case 'calendar':
        return renderCalendar();
      case 'policy':
        return renderPolicy();
      case 'transmission':
        return renderTransmission();
      case 'sectors':
        return renderSectors();
      case 'scenarios':
        return renderScenarios();
      case 'historical':
        return renderHistorical();
      case 'forecasts':
        return renderForecasts();
      case 'knowledge':
        return renderKnowledge();
      case 'research':
        return renderResearch();
      case 'watchlist':
        return renderWatchlist();
      case 'alerts':
        return renderAlerts();
      case 'settings':
        return renderSettings();
      case 'ask':
        return renderAsk();
      case 'overview':
      default:
        return renderOverview();
    }
  };

  return (
    <div className="min-h-screen bg-[#f5f7fb] text-[#101828]">
      <Helmet>
        <title>Macro Intelligence | Agarwal Global Investments</title>
        <meta
          name="description"
          content="AGI Chief Economist Workstation — regime, transmission, scenarios and investment implications."
        />
        <link rel="canonical" href="https://agarwalglobalinvestments.com/macro-intelligence" />
      </Helmet>

      <div className="mx-auto flex min-h-screen max-w-[1600px]">
        <aside className="sticky top-0 hidden h-screen w-[250px] shrink-0 flex-col border-r border-[#e7eaf0] bg-white lg:flex">
          <div className="border-b border-[#e7eaf0] px-5 py-5">
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#3b6ea5]">AGI Intelligence</p>
            <p className="mt-1 text-sm font-semibold text-[#101828]">Chief Economist</p>
          </div>
          <nav className="flex-1 space-y-4 overflow-y-auto px-3 py-4">
            {groups.map((group) => (
              <div key={group}>
                <p className="mb-1 px-3 text-[10px] font-bold uppercase tracking-[0.14em] text-[#98a2b3]">{group}</p>
                <div className="space-y-0.5">
                  {navItems
                    .filter((n) => n.group === group)
                    .map((item) => {
                      const Icon = ICONS[item.id] || LineChart;
                      return (
                        <button
                          key={item.id}
                          type="button"
                          onClick={() => go(item.id)}
                          className={`flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left text-[13px] transition ${
                            workspace === item.id
                              ? 'bg-[#eef4fb] font-semibold text-[#1d4f91]'
                              : 'text-[#475467] hover:bg-[#f8fafc]'
                          }`}
                        >
                          <Icon className="h-4 w-4 shrink-0 opacity-80" />
                          <span className="truncate">{item.label}</span>
                        </button>
                      );
                    })}
                </div>
              </div>
            ))}
          </nav>
        </aside>

        <div className="min-w-0 flex-1">
          <header className="sticky top-0 z-20 border-b border-[#e7eaf0] bg-white/90 backdrop-blur">
            <div className="flex flex-wrap items-center gap-3 px-4 py-3 sm:px-6">
              <div className="relative min-w-[200px] flex-1">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#98a2b3]" />
                <input
                  value={askQuery}
                  onChange={(e) => setAskQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
                  placeholder="Ask the economist: oil, RBI, inflation, banks…"
                  className="w-full rounded-xl border border-[#e7eaf0] bg-[#f8fafc] py-2.5 pl-10 pr-3 text-sm outline-none focus:bg-white focus:ring-2 focus:ring-[#3b6ea5]/30"
                />
              </div>
              <button
                type="button"
                onClick={() => handleAsk(askQuery || ws.askPrompts?.[0])}
                className="inline-flex items-center gap-2 rounded-xl bg-[#1d4f91] px-4 py-2.5 text-sm font-semibold text-white"
              >
                <Sparkles className="h-4 w-4" />
                {askLoading ? 'Asking…' : 'Ask AGI Economist'}
              </button>
              <button type="button" onClick={() => go('watchlist')} className="rounded-xl border border-[#e7eaf0] p-2.5 text-[#667085]" aria-label="Watchlist">
                <Bell className="h-4 w-4" />
              </button>
            </div>
            <div className="flex gap-1 overflow-x-auto px-4 pb-3 sm:px-6">
              {TOP_TABS.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => go(tab.id)}
                  className={`whitespace-nowrap rounded-full px-3.5 py-1.5 text-xs font-semibold transition ${
                    workspace === tab.id ? 'bg-[#101828] text-white' : 'bg-[#f2f4f7] text-[#475467] hover:bg-[#e7eaf0]'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            <div className="border-t border-[#eef1f6] px-4 py-2 lg:hidden sm:px-6">
              <label className="sr-only" htmlFor="macro-workspace-mobile">
                Workspace
              </label>
              <select
                id="macro-workspace-mobile"
                value={workspace}
                onChange={(e) => go(e.target.value)}
                className="w-full rounded-xl border border-[#e7eaf0] bg-[#f8fafc] px-3 py-2 text-sm font-semibold"
              >
                {navItems.map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.group} · {n.label}
                  </option>
                ))}
              </select>
            </div>
          </header>

          <main className="space-y-6 px-4 py-6 sm:px-6 lg:py-8">
            {state.loading ? (
              <div className="h-[520px] animate-pulse rounded-2xl bg-white ring-1 ring-[#e7eaf0]" />
            ) : state.error && !briefing ? (
              <Card className="p-10 text-center">
                <AlertTriangle className="mx-auto h-6 w-6 text-[#966a00]" />
                <h2 className="mt-3 text-lg font-semibold">Macro briefing temporarily unavailable</h2>
                <p className="mt-2 text-sm text-[#667085]">AGI will serve the last repository cache when available.</p>
              </Card>
            ) : (
              <>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-xs text-[#667085]">
                    Workspace · <span className="font-semibold text-[#101828]">{navItems.find((n) => n.id === workspace)?.label}</span>
                    {' · '}
                    Sources {(briefing?.sourcesUsed || []).join(' · ') || 'AGI repository'}
                  </p>
                  <button
                    type="button"
                    onClick={() => cards[0] && setDetail(cards[0])}
                    className="text-xs font-semibold text-[#1d4f91]"
                  >
                    Tip: click any card for Why / Forecast / Implication
                  </button>
                </div>
                {body()}
                <p className="pb-8 text-center text-[11px] leading-relaxed text-[#98a2b3]">{briefing?.disclaimer}</p>
              </>
            )}
          </main>
        </div>
      </div>

      <DetailDrawer item={detail} onClose={() => setDetail(null)} />

      {askOpen && askAnswer && workspace !== 'ask' ? (
        <div className="fixed inset-0 z-40 flex items-end justify-center bg-black/25 p-3 sm:items-center sm:p-6" onClick={() => setAskOpen(false)}>
          <div
            className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-[#e7eaf0] bg-white p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#3b6ea5]">Ask AGI Economist</p>
                <h3 className="mt-1 text-lg font-semibold">{askAnswer.query}</h3>
              </div>
              <button type="button" onClick={() => setAskOpen(false)} className="rounded-lg p-1 hover:bg-[#f2f4f7]" aria-label="Close">
                <X className="h-4 w-4" />
              </button>
            </div>
            <p className="mt-4 text-sm leading-7 text-[#344054]">{askAnswer.response}</p>
            <button type="button" onClick={() => { setAskOpen(false); go('ask'); }} className="mt-4 text-xs font-semibold text-[#1d4f91]">
              Open full economist workspace →
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
