import { Link } from 'react-router-dom';
import { Target, Users, Award, TrendingUp, ArrowRight, Mail } from 'lucide-react';
import PageShell from '@/components/Layout/PageShell';
import { Button } from '@/components/ui/button';

const pillars = [
  {
    icon: Target,
    title: 'Independent Research',
    description:
      'Original analysis on Indian and global markets — free from sell-side conflicts and promotional bias.',
  },
  {
    icon: Users,
    title: 'Built for Professionals',
    description:
      'Institutional-quality depth written for investors, analysts, and decision-makers who need clarity fast.',
  },
  {
    icon: Award,
    title: 'Analytical Rigor',
    description:
      'Every report is structured for action: thesis, evidence, risks, and implications — not noise.',
  },
  {
    icon: TrendingUp,
    title: 'Markets + Macro + Private Capital',
    description:
      'Coverage spanning equities, macroeconomics, private markets, M&A, and business strategy.',
  },
];

const coverage = [
  'Equity research & sector deep-dives',
  'RBI policy, inflation & GDP analysis',
  'Private equity, venture & deal flow',
  'M&A transaction tracking',
  'Daily market briefs & opinions',
];

export default function About() {
  return (
    <PageShell
      eyebrow="About AGI"
      title="Independent Research for Serious Investors"
      description="Agarwal Global Investments delivers actionable research on finance, economics, private markets, and global business — built for professionals who demand clarity."
      metaTitle="About | Agarwal Global Investments"
    >
      <div className="aspect-[21/9] rounded-2xl overflow-hidden border border-white/10 mb-12">
        <img
          src="https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1600&q=80"
          alt="Financial markets analysis"
          className="w-full h-full object-cover"
        />
      </div>

      <div className="prose prose-invert max-w-none mb-14">
        <p className="text-slate-300 text-lg leading-relaxed">
          Agarwal Global Investments (AGI) is an independent research platform focused on Indian and
          global capital markets. We publish institutional-grade research articles, macro notes, deal
          intelligence, and market commentary — designed to help investors and professionals make
          better-informed decisions.
        </p>
        <p className="text-slate-400 leading-relaxed mt-4">
          Our research library is updated continuously through our CMS. Live market widgets, news
          feeds, and deal trackers complement our original analysis on the dedicated Markets and
          Deal Tracker sections.
        </p>
      </div>

      <h2 className="text-xl font-semibold text-white mb-6">What we cover</h2>
      <ul className="grid sm:grid-cols-2 gap-3 mb-14">
        {coverage.map((item) => (
          <li
            key={item}
            className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-blue-400 shrink-0" />
            {item}
          </li>
        ))}
      </ul>

      <div className="grid sm:grid-cols-2 gap-6 mb-14">
        {pillars.map(({ icon: Icon, title, description }) => (
          <div
            key={title}
            className="rounded-2xl border border-white/10 bg-white/5 p-6"
          >
            <Icon className="text-blue-400 mb-4" size={28} />
            <h3 className="text-lg font-semibold text-white">{title}</h3>
            <p className="mt-2 text-sm text-slate-400 leading-relaxed">{description}</p>
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-blue-500/30 bg-blue-600/10 p-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
        <div>
          <h2 className="text-xl font-semibold text-white">Work with us</h2>
          <p className="text-slate-400 mt-2 text-sm max-w-lg">
            Media inquiries, research partnerships, and institutional subscriptions — we&apos;d like to hear from you.
          </p>
        </div>
        <div className="flex flex-wrap gap-3 shrink-0">
          <Button asChild className="bg-blue-600 hover:bg-blue-700">
            <Link to="/contact">
              <Mail className="mr-2 h-4 w-4" />
              Contact us
            </Link>
          </Button>
          <Button asChild variant="outline" className="border-white/20 text-white hover:bg-white/10">
            <Link to="/sections/live-articles">
              Browse research
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </PageShell>
  );
}
