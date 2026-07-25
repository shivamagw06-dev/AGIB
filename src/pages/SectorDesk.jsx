import { useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link, useParams } from 'react-router-dom';
import { getUiSector } from '@/lib/uiApi';

export default function SectorDesk() {
  const { sectorId } = useParams();
  const [state, setState] = useState({ loading: true, data: null, error: null });

  useEffect(() => {
    let active = true;
    getUiSector(sectorId)
      .then((data) => active && setState({ loading: false, data, error: null }))
      .catch((error) => active && setState({ loading: false, data: null, error }));
    return () => {
      active = false;
    };
  }, [sectorId]);

  const data = state.data;

  return (
    <div className="bg-white min-h-screen">
      <Helmet>
        <title>{`${sectorId} Sector | AGI`}</title>
      </Helmet>
      <div className="max-w-[1100px] mx-auto px-4 sm:px-6 py-8">
        <Link to="/research" className="text-xs font-bold text-[#111] hover:text-[#ff6600]">← Research</Link>
        <p className="mt-4 text-[11px] font-bold uppercase tracking-wider text-[#ff6600]">Sector Desk</p>
        <h1 className="mt-2 text-3xl font-bold text-[#111111]">{sectorId}</h1>
        <p className="mt-2 text-sm text-[#767676]">Health: {data?.sector_health || '—'}</p>

        {state.loading ? (
          <div className="mt-8 h-40 bg-[#eee] animate-pulse" />
        ) : (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
            <section className="border border-[#dddddd] p-5">
              <h2 className="text-xs font-bold uppercase text-[#767676]">Sector Leaders</h2>
              <div className="mt-3 flex flex-wrap gap-2">
                {(data?.leaders || []).map((t) => (
                  <Link key={t} to={`/research/stocks/${encodeURIComponent(t)}`} className="text-xs font-bold border border-[#ddd] px-2 py-1 hover:text-[#ff6600]">
                    {t}
                  </Link>
                ))}
              </div>
            </section>
            <section className="border border-[#dddddd] p-5">
              <h2 className="text-xs font-bold uppercase text-[#767676]">Sector Laggards</h2>
              <div className="mt-3 flex flex-wrap gap-2">
                {(data?.laggards || []).map((t) => (
                  <Link key={t} to={`/research/stocks/${encodeURIComponent(t)}`} className="text-xs font-bold border border-[#ddd] px-2 py-1 hover:text-[#ff6600]">
                    {t}
                  </Link>
                ))}
              </div>
            </section>
            <section className="border border-[#dddddd] p-5">
              <h2 className="text-xs font-bold uppercase text-[#767676]">Current Theme</h2>
              <p className="mt-3 text-sm font-bold text-[#111]">{data?.current_theme || sectorId}</p>
            </section>
            <section className="border border-[#dddddd] p-5">
              <h2 className="text-xs font-bold uppercase text-[#767676]">Valuation Snapshot</h2>
              <pre className="mt-3 text-xs whitespace-pre-wrap text-[#444] max-h-40 overflow-auto">
                {JSON.stringify(data?.valuation_snapshot || {}, null, 2)}
              </pre>
            </section>
            <section className="border border-[#dddddd] p-5 md:col-span-2">
              <h2 className="text-xs font-bold uppercase text-[#767676]">Current Research</h2>
              <ul className="mt-3 space-y-2">
                {(data?.current_research || []).slice(0, 10).map((r, idx) => (
                  <li key={r.research_id || r.id || idx} className="text-sm border-b border-[#eee] pb-2">
                    {r.title || r.id}
                  </li>
                ))}
              </ul>
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
