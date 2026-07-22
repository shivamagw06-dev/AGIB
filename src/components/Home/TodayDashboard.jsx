import { Link } from 'react-router-dom';
import useMarketDashboard from '@/hooks/useMarketDashboard';
import AgiMarketPulse from '@/components/Home/AgiMarketPulse';

function StockRow({ row, positive }) {
  const change = Number(row.change);
  const up = positive ?? change >= 0;
  return (
    <div className="flex items-center justify-between py-2 border-b border-[#eeeeee] last:border-0 text-xs">
      <div className="min-w-0">
        <p className="font-bold text-[#111111] truncate">{row.symbol}</p>
        <p className="text-[#767676] truncate">{row.name}</p>
      </div>
      <div className="text-right shrink-0 ml-2">
        <p className="font-semibold tabular-nums">{row.price ?? '—'}</p>
        {change != null && Number.isFinite(change) && (
          <p className={`font-bold tabular-nums ${up ? 'text-[#008001]' : 'text-[#cc0000]'}`}>
            {up ? '+' : ''}{change.toFixed(2)}%
          </p>
        )}
      </div>
    </div>
  );
}

export default function TodayDashboard() {
  const { gainers, losers, breadth, stocksInFocus, loading } = useMarketDashboard();

  return (
    <section className="py-8 border-b border-[#dddddd]">
      <div className="flex items-end justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-[#111111]">Today&apos;s Dashboard</h2>
          <p className="text-sm text-[#767676] mt-1">
            Summarize today&apos;s market in under one minute
          </p>
        </div>
        <Link to="/markets" className="text-xs font-bold text-[#111111] hover:text-[#ff6600] hidden sm:block">
          Full market data →
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-4">
          <AgiMarketPulse />
        </div>

        <div className="lg:col-span-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-4">
          <div className="border border-[#dddddd] p-4">
            <h3 className="text-xs font-bold uppercase tracking-wide text-[#767676] mb-3">
              Top Gainers
            </h3>
            {loading ? (
              <p className="text-xs text-[#767676]">Loading…</p>
            ) : gainers.length === 0 ? (
              <p className="text-xs text-[#767676]">No data available</p>
            ) : (
              gainers.slice(0, 5).map((r) => <StockRow key={r.symbol} row={r} positive />)
            )}
          </div>
          <div className="border border-[#dddddd] p-4">
            <h3 className="text-xs font-bold uppercase tracking-wide text-[#767676] mb-3">
              Top Losers
            </h3>
            {loading ? (
              <p className="text-xs text-[#767676]">Loading…</p>
            ) : losers.length === 0 ? (
              <p className="text-xs text-[#767676]">No data available</p>
            ) : (
              losers.slice(0, 5).map((r) => <StockRow key={r.symbol} row={r} positive={false} />)
            )}
          </div>
        </div>

        <div className="lg:col-span-4 space-y-4">
          <div className="border border-[#dddddd] p-4">
            <h3 className="text-xs font-bold uppercase tracking-wide text-[#767676] mb-3">
              Market Breadth
            </h3>
            <p className="text-2xl font-bold text-[#111111]">{breadth?.label || 'Mixed'}</p>
            <p className="text-xs text-[#767676] mt-1">
              {breadth?.gainers ?? 0} gainers · {breadth?.losers ?? 0} losers tracked
            </p>
          </div>

          <div className="border border-[#dddddd] p-4">
            <h3 className="text-xs font-bold uppercase tracking-wide text-[#767676] mb-3">
              Stocks in Focus
            </h3>
            {stocksInFocus?.length ? (
              <div className="flex flex-wrap gap-2">
                {stocksInFocus.map((s) => (
                  <Link
                    key={s}
                    to="/markets"
                    className="text-xs font-bold border border-[#ddd] px-2.5 py-1 hover:border-[#111] hover:text-[#ff6600] transition-colors"
                  >
                    {s}
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[#767676]">Updated from market movers</p>
            )}
          </div>

          <div className="border border-[#dddddd] p-4 bg-[#fafafa]">
            <h3 className="text-xs font-bold uppercase tracking-wide text-[#767676] mb-2">
              Coming Soon
            </h3>
            <ul className="text-xs text-[#555555] space-y-1">
              <li>FII / DII flows</li>
              <li>Upcoming results calendar</li>
              <li>IPO tracker</li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
