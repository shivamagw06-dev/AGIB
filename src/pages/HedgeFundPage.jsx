import { Link } from 'react-router-dom';
import PageShell from '@/components/Layout/PageShell';
import AskAgiBar from '@/components/Home/AskAgiBar';

const THEMES = [
  {
    title: 'Long / Short Equity',
    body: 'Factor exposure, crowding, and relative-value setups across India and global equities.',
  },
  {
    title: 'Macro & Rates',
    body: 'Policy transmission, curve shape, and cross-asset implications for hedge fund books.',
  },
  {
    title: 'Event & Catalyst Desk',
    body: 'Earnings, corporate actions, and regulatory catalysts with evidence-backed framing.',
  },
];

export default function HedgeFundPage() {
  return (
    <PageShell
      title="Hedge Fund"
      eyebrow="AGI Research"
      description="Institutional hedge fund research — multi-strategy intelligence across equities, macro, and catalysts."
      metaTitle="Hedge Fund | Agarwal Global Investments"
      wide
    >
      <div className="space-y-10">
        <div className="rounded-xl border border-[#e6e8ec] bg-white p-6 md:p-8">
          <h2 className="font-serif text-2xl font-bold text-[#111111]">Ask the hedge fund desk</h2>
          <p className="mt-2 text-sm text-[#555555]">
            Frame long/short, factor, and event questions with institutional evidence.
          </p>
          <div className="mt-5">
            <AskAgiBar
              placeholder="Ask about hedge fund strategy, crowding, factors or catalysts..."
              size="large"
              buttonLabel="Ask AGI"
              ariaLabel="Ask AGI about hedge funds"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
          {THEMES.map((theme) => (
            <div key={theme.title} className="rounded-xl border border-[#e6e8ec] bg-white p-6">
              <h3 className="font-serif text-xl font-bold text-[#111111]">{theme.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-[#555555]">{theme.body}</p>
            </div>
          ))}
        </div>

        <div className="flex flex-wrap gap-3">
          <Link
            to="/research"
            className="rounded-md bg-[#0b1f33] px-5 py-2.5 text-sm font-bold text-white hover:bg-[#163353]"
          >
            Explore Research
          </Link>
          <Link
            to="/market-intelligence"
            className="rounded-md border border-[#d5d8de] px-5 py-2.5 text-sm font-bold text-[#111111] hover:border-[#111111]"
          >
            Market Intelligence
          </Link>
        </div>
      </div>
    </PageShell>
  );
}
