import { Link } from 'react-router-dom';
import PageShell from '@/components/Layout/PageShell';
import AskAgiBar from '@/components/Home/AskAgiBar';

const THEMES = [
  {
    title: 'Deal Flow & Buyouts',
    body: 'Private equity activity, sponsor themes, and transaction intelligence across sectors.',
  },
  {
    title: 'IPO Pipeline',
    body: 'Exit readiness, listing calendars, and public-market comps for PE-backed companies.',
  },
  {
    title: 'Value Creation',
    body: 'Operating leverage, capital allocation, and post-deal performance narratives.',
  },
];

export default function PrivateEquityPage() {
  return (
    <PageShell
      title="Private Equity"
      eyebrow="AGI Research"
      description="Private equity intelligence — deals, exits, IPO readiness, and value-creation research."
      metaTitle="Private Equity | Agarwal Global Investments"
      wide
    >
      <div className="space-y-10">
        <div className="rounded-xl border border-[#e6e8ec] bg-white p-6 md:p-8">
          <h2 className="font-serif text-2xl font-bold text-[#111111]">Ask the private equity desk</h2>
          <p className="mt-2 text-sm text-[#555555]">
            Research sponsors, deals, exits and IPO pathways with institutional framing.
          </p>
          <div className="mt-5">
            <AskAgiBar
              placeholder="Ask about private equity deals, exits, sponsors or IPO readiness..."
              size="large"
              buttonLabel="Ask AGI"
              ariaLabel="Ask AGI about private equity"
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
            to="/sections/deal-tracker"
            className="rounded-md bg-[#0b1f33] px-5 py-2.5 text-sm font-bold text-white hover:bg-[#163353]"
          >
            Deal Tracker
          </Link>
          <Link
            to="/ipo-intelligence"
            className="rounded-md border border-[#d5d8de] px-5 py-2.5 text-sm font-bold text-[#111111] hover:border-[#111111]"
          >
            IPO Intelligence
          </Link>
        </div>
      </div>
    </PageShell>
  );
}
