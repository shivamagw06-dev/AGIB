import { Link } from 'react-router-dom';
import useMarketIntelligence from '@/hooks/useMarketIntelligence';
import { matchOutlookIndices } from '@/components/Home/homeTerminalData';

function tone(sentiment, score) {
  const s = String(sentiment).toLowerCase();
  const n = Number(score);
  if (s.includes('bull') || (Number.isFinite(n) && n >= 60)) return 'text-[#087443]';
  if (s.includes('bear') || (Number.isFinite(n) && n < 45)) return 'text-[#b42318]';
  return 'text-[#5d6470]';
}

function formatScoreDelta(score) {
  const n = Number(score);
  if (!Number.isFinite(n)) return '—';
  // Proprietary AGI score mapped to a signed reading for the sticky strip.
  const delta = n - 50;
  const sign = delta > 0 ? '+' : '';
  return `${sign}${delta.toFixed(1)}`;
}

function formatPct(score) {
  const n = Number(score);
  if (!Number.isFinite(n)) return '—';
  const pct = ((n - 50) / 50) * 100;
  const sign = pct > 0 ? '+' : '';
  return `${sign}${pct.toFixed(1)}%`;
}

/**
 * Thin sticky global market strip.
 * Uses AGI index readings (no raw exchange prices — backend contract).
 */
export default function MarketOutlookStrip() {
  const { indexSentiments, loading } = useMarketIntelligence();
  const indices = matchOutlookIndices(indexSentiments);

  return (
    <div className="border-b border-[#e6e8ec] bg-white">
      <div className="mx-auto flex max-w-[1800px] items-center gap-1 overflow-x-auto px-2 sm:px-4">
        <span className="hidden shrink-0 px-2 text-[10px] font-bold uppercase tracking-[0.12em] text-[#9298a3] md:inline">
          Markets
        </span>
        <div className="flex min-w-0 flex-1 items-stretch">
          {loading && !indices.length ? (
            <span className="px-3 py-2.5 text-xs text-[#767676]">Loading markets…</span>
          ) : (
            indices.map((item) => {
              const pctTone = tone(item.sentiment, item.score);
              return (
                <Link
                  key={item.key}
                  to={item.path || '/market-intelligence'}
                  className="flex min-w-[118px] items-baseline gap-2 border-r border-[#eef0f3] px-3 py-2.5 last:border-r-0 hover:bg-[#fafbfc]"
                >
                  <span className="text-[11px] font-bold uppercase tracking-wide text-[#111111] whitespace-nowrap">
                    {item.label}
                  </span>
                  <span className="text-xs font-semibold tabular-nums text-[#333333]">
                    {Number.isFinite(Number(item.score)) ? Number(item.score).toFixed(0) : '—'}
                  </span>
                  <span className={`text-[11px] font-semibold tabular-nums whitespace-nowrap ${pctTone}`}>
                    {formatScoreDelta(item.score)}
                    <span className="ml-1">({formatPct(item.score)})</span>
                  </span>
                </Link>
              );
            })
          )}
        </div>
        <Link
          to="/market-intelligence"
          className="hidden shrink-0 px-3 py-2 text-[11px] font-bold text-[#111111] hover:underline underline-offset-2 lg:inline"
        >
          Market Intelligence →
        </Link>
      </div>
    </div>
  );
}
