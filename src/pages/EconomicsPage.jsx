import { Link } from 'react-router-dom';
import PageShell from '@/components/Layout/PageShell';
import AskAgiBar from '@/components/Home/AskAgiBar';
import DeskResearchFeed from '@/components/Research/DeskResearchFeed';

const THEMES = [
  {
    title: 'Monetary Policy',
    body: 'RBI, Fed and global central-bank transmission into rates, liquidity and risk assets.',
  },
  {
    title: 'Growth & Inflation',
    body: 'GDP, CPI, fiscal impulse and the macro regime framing for equity and credit books.',
  },
  {
    title: 'External Sector',
    body: 'USD/INR, trade balance, capital flows and commodity shocks that reshape India outlook.',
  },
];

export default function EconomicsPage() {
  return (
    <PageShell
      title="Economics"
      eyebrow="AGI Research"
      description="Macroeconomics and policy intelligence — rates, inflation, growth and external balances."
      metaTitle="Economics | Agarwal Global Investments"
      wide
    >
      <div className="space-y-10">
        <div className="rounded-xl border border-[#e6e8ec] bg-white p-6 md:p-8">
          <h2 className="font-serif text-2xl font-bold text-[#111111]">Ask the economics desk</h2>
          <p className="mt-2 text-sm text-[#555555]">
            Frame RBI, inflation, growth and global macro questions with institutional evidence.
          </p>
          <div className="mt-5">
            <AskAgiBar
              placeholder="Ask about RBI policy, inflation, GDP, rates or global macro..."
              size="large"
              buttonLabel="Ask AGI"
              ariaLabel="Ask AGI about economics"
            />
          </div>
        </div>

        <DeskResearchFeed deskId="economics" title="Economics Research" />

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
            to="/macro-intelligence"
            className="rounded-md bg-[#0b1f33] px-5 py-2.5 text-sm font-bold text-white hover:bg-[#163353]"
          >
            Macro Intelligence
          </Link>
          <Link
            to="/research"
            className="rounded-md border border-[#d5d8de] px-5 py-2.5 text-sm font-bold text-[#111111] hover:border-[#111111]"
          >
            Research Notes
          </Link>
        </div>
      </div>
    </PageShell>
  );
}
