import { useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link, useParams } from 'react-router-dom';
import { getUiTheme } from '@/lib/uiApi';

export default function ThemeDesk() {
  const { themeId } = useParams();
  const [state, setState] = useState({ loading: true, data: null, error: null });

  useEffect(() => {
    let active = true;
    getUiTheme(themeId)
      .then((data) => active && setState({ loading: false, data, error: null }))
      .catch((error) => active && setState({ loading: false, data: null, error }));
    return () => {
      active = false;
    };
  }, [themeId]);

  const data = state.data;

  return (
    <div className="bg-white min-h-screen">
      <Helmet>
        <title>{`${themeId} Theme | AGI`}</title>
      </Helmet>
      <div className="max-w-[1100px] mx-auto px-4 sm:px-6 py-8">
        <Link to="/" className="text-xs font-bold text-[#111] hover:text-[#ff6600]">← Home</Link>
        <p className="mt-4 text-[11px] font-bold uppercase tracking-wider text-[#ff6600]">Investment Theme</p>
        <h1 className="mt-2 text-3xl font-bold text-[#111111]">{data?.current_thesis || themeId}</h1>

        {state.loading ? (
          <div className="mt-8 h-40 bg-[#eee] animate-pulse" />
        ) : state.error ? (
          <p className="mt-8 text-sm text-[#767676]">Theme intelligence unavailable.</p>
        ) : (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
            <section className="border border-[#dddddd] p-5">
              <h2 className="text-xs font-bold uppercase text-[#767676]">Related Companies</h2>
              <div className="mt-3 flex flex-wrap gap-2">
                {(data?.related_companies || []).map((t) => (
                  <Link key={t} to={`/research/stocks/${encodeURIComponent(t)}`} className="text-xs font-bold border border-[#ddd] px-2 py-1 hover:border-[#111] hover:text-[#ff6600]">
                    {t}
                  </Link>
                ))}
                {(data?.related_companies || []).length === 0 && (
                  <p className="text-xs text-[#767676]">No linked companies yet.</p>
                )}
              </div>
            </section>
            <section className="border border-[#dddddd] p-5">
              <h2 className="text-xs font-bold uppercase text-[#767676]">House View</h2>
              <pre className="mt-3 text-xs whitespace-pre-wrap text-[#444] max-h-48 overflow-auto">
                {JSON.stringify(data?.house_view || {}, null, 2)}
              </pre>
            </section>
            <section className="border border-[#dddddd] p-5">
              <h2 className="text-xs font-bold uppercase text-[#767676]">Current Risks</h2>
              <ul className="mt-3 space-y-2 text-sm text-[#333]">
                {(data?.current_risks || []).map((r) => <li key={r}>• {r}</li>)}
                {(data?.current_risks || []).length === 0 && <li className="text-[#767676]">No risks tagged yet.</li>}
              </ul>
            </section>
            <section className="border border-[#dddddd] p-5">
              <h2 className="text-xs font-bold uppercase text-[#767676]">Current Catalysts</h2>
              <ul className="mt-3 space-y-2 text-sm text-[#333]">
                {(data?.current_catalysts || []).map((r) => <li key={r}>• {r}</li>)}
                {(data?.current_catalysts || []).length === 0 && <li className="text-[#767676]">No catalysts tagged yet.</li>}
              </ul>
            </section>
            <section className="border border-[#dddddd] p-5 md:col-span-2">
              <h2 className="text-xs font-bold uppercase text-[#767676]">Related Research</h2>
              <ul className="mt-3 space-y-2">
                {(data?.related_research || []).slice(0, 8).map((r, idx) => (
                  <li key={r.id || r.title || idx} className="text-sm border-b border-[#eee] pb-2">
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
