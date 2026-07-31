import { Link } from 'react-router-dom';
import PageShell from '@/components/Layout/PageShell';
import AskAgiBar from '@/components/Home/AskAgiBar';

const DESKS = [
  {
    title: 'United States',
    body: 'Equities, Fed policy, dollar and Treasury moves that transmit into Indian risk assets.',
    to: '/macro-intelligence',
  },
  {
    title: 'Europe & Asia',
    body: 'Cross-border market pulse across Europe, Japan, China and regional risk regimes.',
    to: '/global',
  },
  {
    title: 'FX, Commodities & Rates',
    body: 'USD/INR, oil, gold and yield curves that shape global and India asset allocation.',
    to: '/market-intelligence',
  },
];

export default function GlobalMarketsPage() {
  return (
    <PageShell
      title="Global Markets"
      eyebrow="AGI Research"
      description="Global markets intelligence — US, Europe, Asia, FX, commodities and rates."
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
              placeholder="Ask about global markets, Fed, USD/INR, oil or overnight risk..."
              size="large"
              buttonLabel="Ask AGI"
              ariaLabel="Ask AGI about global markets"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
          {DESKS.map((desk) => (
            <Link
              key={desk.title}
              to={desk.to}
              className="rounded-xl border border-[#e6e8ec] bg-white p-6 transition-shadow hover:shadow-sm"
            >
              <h3 className="font-serif text-xl font-bold text-[#111111]">{desk.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-[#555555]">{desk.body}</p>
              <span className="mt-5 inline-flex text-sm font-semibold text-[#111111]">Open desk →</span>
            </Link>
          ))}
        </div>

        <div className="flex flex-wrap gap-3">
          <Link
            to="/macro-intelligence"
            className="rounded-md bg-[#0b1f33] px-5 py-2.5 text-sm font-bold text-white hover:bg-[#163353]"
          >
            Macro Intelligence
          </Link>
          <Link
            to="/pre-market"
            className="rounded-md border border-[#d5d8de] px-5 py-2.5 text-sm font-bold text-[#111111] hover:border-[#111111]"
          >
            Pre-Market Brief
          </Link>
        </div>
      </div>
    </PageShell>
  );
}
