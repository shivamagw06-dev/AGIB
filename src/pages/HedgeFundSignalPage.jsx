import { Link } from 'react-router-dom';
import { ArrowLeft, Sparkles } from 'lucide-react';
import { InlineAsk, OpportunityTable } from '@/pages/hedgeFundTerminal';
import './hedgeFundLab.css';

const PAGES = {
  alpha: {
    eyebrow: 'AGI Alpha Intelligence',
    title: 'Alpha Opportunities',
    description: 'A focused research queue where value, quality, growth, technical confirmation and consensus agree. Every score is evidence-led and requires risk review.',
    question: 'Which companies have the strongest multi-factor evidence, and what could invalidate the thesis?',
    icon: Sparkles,
  },
};

export default function HedgeFundSignalPage({ kind }) {
  const page = PAGES[kind] || PAGES.alpha;
  const Icon = page.icon;
  return (
    <div className="hfl-root hfs-root">
      <header className="hfl-header hfs-header">
        <Link to="/hedge-fund" className="hfl-back"><ArrowLeft size={14} /> Hedge Fund hub</Link>
        <div className="hfs-title-row">
          <div>
            <div className="hfs-eyebrow"><Icon size={14} /> {page.eyebrow}</div>
            <h1>{page.title}</h1>
            <p>{page.description}</p>
          </div>
          <span className="hfs-switch">Technical confirmation is included in the Alpha score</span>
        </div>
      </header>
      <main className="hfl-body hfs-body">
        <OpportunityTable scan={kind} label={page.title} researchQuestion={page.question} />
        <section className="hfl-module hfs-method">
          <h3>How to use this page</h3>
          <p>
            Expand a company to inspect the calculation chain, data sources, catalysts and risks. A scanner result is a research priority—not a buy, sell, or probability of return.
          </p>
        </section>
        <InlineAsk />
      </main>
    </div>
  );
}
