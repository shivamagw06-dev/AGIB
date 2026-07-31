import { Link } from 'react-router-dom';
import useMarketSnapshot from '@/hooks/useMarketSnapshot';

/** Preferred strip order — only rows with live prices are shown. */
const STRIP_ORDER = [
  { key: 'nifty50', label: 'NIFTY 50', match: /^(nifty 50|nifty)$/i },
  { key: 'sensex', label: 'SENSEX', match: /^sensex$/i },
  { key: 'banknifty', label: 'BANK NIFTY', match: /bank\s*nifty|nifty\s*bank/i },
  { key: 'usdinr', label: 'USD/INR', match: /usd\s*\/?\s*inr|usdinr/i },
  { key: 'gold', label: 'GOLD', match: /^gold$/i },
  { key: 'brent', label: 'BRENT', match: /brent|crude/i },
  { key: 'bitcoin', label: 'BTC', match: /bitcoin|^btc$/i },
  { key: 'nasdaq', label: 'NASDAQ', match: /nasdaq/i },
  { key: 'sp500', label: 'S&P', match: /^s&p|spx|s\s*&\s*p/i },
  { key: 'vix', label: 'VIX', match: /vix/i },
];

function formatPrice(value, label) {
  const n = Number(value);
  if (!Number.isFinite(n) || n <= 0) return '—';
  if (/usd\/inr|usdinr/i.test(label)) {
    return n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  if (/btc|bitcoin|gold|brent|vix/i.test(label)) {
    return n.toLocaleString('en-IN', { maximumFractionDigits: 2 });
  }
  return n.toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

function formatPct(pct) {
  const n = Number(pct);
  if (!Number.isFinite(n)) return null;
  const sign = n > 0 ? '+' : '';
  return `${sign}${n.toFixed(2)}%`;
}

function formatAbsChange(price, pct) {
  const p = Number(price);
  const c = Number(pct);
  if (!Number.isFinite(p) || !Number.isFinite(c) || p <= 0) return null;
  // percentChange is vs prior close: abs ≈ price * pct / (100 + pct) when pct is day change.
  const abs = (p * c) / (100 + c);
  if (!Number.isFinite(abs)) return null;
  const sign = abs > 0 ? '+' : '';
  return `${sign}${Math.abs(abs) >= 100 ? abs.toFixed(0) : abs.toFixed(2)}`;
}

function matchStripRows(items = []) {
  const used = new Set();
  const rows = [];
  for (const def of STRIP_ORDER) {
    const hit = items.find((row, idx) => {
      if (used.has(idx)) return false;
      return def.match.test(String(row.name || row.label || ''));
    });
    if (!hit || !(Number(hit.price) > 0)) continue;
    const idx = items.indexOf(hit);
    if (idx >= 0) used.add(idx);
    rows.push({
      key: def.key,
      label: def.label,
      price: Number(hit.price),
      percentChange: Number(hit.percentChange ?? hit.change ?? hit.pct),
    });
  }
  return rows;
}

/** Thin sticky global market strip — live prices from market_snapshot. */
export default function MarketOutlookStrip() {
  const { items, loading } = useMarketSnapshot();
  const rows = matchStripRows(items);

  return (
    <div className="border-b border-[#e6e8ec] bg-white">
      <div className="mx-auto flex max-w-[1800px] items-center gap-1 overflow-x-auto px-2 sm:px-4">
        <span className="hidden shrink-0 px-2 text-[10px] font-bold uppercase tracking-[0.12em] text-[#9298a3] md:inline">
          Markets
        </span>
        <div className="flex min-w-0 flex-1 items-stretch">
          {loading && !rows.length ? (
            <span className="px-3 py-2.5 text-xs text-[#767676]">Loading markets…</span>
          ) : !rows.length ? (
            <span className="px-3 py-2.5 text-xs text-[#767676]">Market data unavailable</span>
          ) : (
            rows.map((item) => {
              const pct = item.percentChange;
              const up = Number(pct) > 0;
              const down = Number(pct) < 0;
              const tone = up ? 'text-[#087443]' : down ? 'text-[#b42318]' : 'text-[#5d6470]';
              const abs = formatAbsChange(item.price, pct);
              const pctLabel = formatPct(pct);
              return (
                <Link
                  key={item.key}
                  to="/market-intelligence"
                  className="flex min-w-[132px] items-baseline gap-2 border-r border-[#eef0f3] px-3 py-2.5 last:border-r-0 hover:bg-[#fafbfc]"
                >
                  <span className="text-[11px] font-bold uppercase tracking-wide text-[#111111] whitespace-nowrap">
                    {item.label}
                  </span>
                  <span className="text-xs font-semibold tabular-nums text-[#333333]">
                    {formatPrice(item.price, item.label)}
                  </span>
                  {pctLabel && (
                    <span className={`text-[11px] font-semibold tabular-nums whitespace-nowrap ${tone}`}>
                      {abs && <span className="mr-1">{abs}</span>}
                      ({pctLabel})
                    </span>
                  )}
                </Link>
              );
            })
          )}
        </div>
        <Link
          to="/market-intelligence"
          className="hidden shrink-0 px-3 py-2 text-[11px] font-bold text-[#111111] hover:underline underline-offset-2 lg:inline"
        >
          Markets →
        </Link>
      </div>
    </div>
  );
}
