import { Link } from 'react-router-dom';
import useMarketIntelligence from '@/hooks/useMarketIntelligence';
import { formatIstTime } from '@/lib/marketSession';
import { matchOutlookIndices } from '@/components/Home/homeTerminalData';

function tone(sentiment) {
  const s = String(sentiment).toLowerCase();
  if (s.includes('bull')) return { dot: 'bg-[#087443]', text: 'text-[#087443]' };
  if (s.includes('bear')) return { dot: 'bg-[#b42318]', text: 'text-[#b42318]' };
  if (s.includes('sync')) return { dot: 'bg-[#9298a3]', text: 'text-[#5d6470]' };
  return { dot: 'bg-[#966a00]', text: 'text-[#966a00]' };
}

function IndexChip({ item }) {
  const t = tone(item.sentiment);
  return (
    <Link
      to={item.path || '/market-intelligence'}
      className="group flex min-w-[108px] flex-col gap-0.5 border-r border-[#e6e8ec] px-3.5 py-2.5 last:border-r-0 hover:bg-[#fafbfc] transition-colors"
    >
      <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.08em] text-[#5d6470]">
        <span className={`inline-block h-1.5 w-1.5 rounded-full ${t.dot}`} aria-hidden />
        {item.label}
      </span>
      <span className={`text-xs font-bold ${t.text}`}>{item.sentiment}</span>
      <span className="text-[11px] tabular-nums text-[#252b36] group-hover:text-[#111]">{item.score}%</span>
    </Link>
  );
}

/** Sticky AGIB Market Outlook Strip — index direction, not raw exchange prices. */
export default function MarketOutlookStrip() {
  const { indexSentiments, breadth, loading, outlook } = useMarketIntelligence();
  const indices = matchOutlookIndices(indexSentiments);
  const health =
    Number(outlook?.market_health ?? outlook?.health_score ?? breadth?.score) ||
    Math.round(indices.reduce((sum, row) => sum + (row.score || 0), 0) / Math.max(1, indices.length));

  return (
    <div className="border-b border-[#dfe3e8] bg-[#fafbfc]">
      <div className="mx-auto flex max-w-[1800px] items-stretch overflow-x-auto">
        <div className="hidden shrink-0 items-center border-r border-[#dfe3e8] bg-[#0b1f33] px-4 text-white md:flex">
          <div>
            <p className="text-[9px] font-bold uppercase tracking-[0.14em] text-white/60">AGI</p>
            <p className="text-[11px] font-semibold leading-tight">Market Strip</p>
          </div>
        </div>

        <div className="flex min-w-0 flex-1 items-stretch">
          {indices.map((item) => (
            <IndexChip key={item.key} item={item} />
          ))}
        </div>

        <div className="hidden shrink-0 items-center gap-5 border-l border-[#dfe3e8] bg-white px-4 lg:flex">
          <div>
            <p className="text-[9px] font-bold uppercase tracking-[0.12em] text-[#767676]">Market Health</p>
            <p className="text-sm font-bold tabular-nums text-[#111111]">
              {loading ? '—' : `${health}/100`}
            </p>
          </div>
          <div>
            <p className="text-[9px] font-bold uppercase tracking-[0.12em] text-[#767676]">Last Updated</p>
            <p className="text-sm font-semibold text-[#111111]">{formatIstTime()}</p>
          </div>
          <Link
            to="/market-intelligence"
            className="text-[11px] font-bold text-[#0b1f33] underline-offset-2 hover:underline"
          >
            Full Market Intelligence →
          </Link>
        </div>
      </div>
    </div>
  );
}
