import { useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { ArrowLeft, CalendarDays, ExternalLink, FileText } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { getIpoDetail } from '@/lib/ipoApi';

function formatDate(value) {
  return value ? new Date(`${value}T00:00:00`).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }) : 'To be announced';
}

function valueOrPending(value, formatter = (item) => item) {
  return value == null || value === '' ? 'Pending / not provided' : formatter(value);
}

function DetailRow({ label, value }) {
  return (
    <div className="border border-[#edf0f2] p-4">
      <p className="text-[10px] font-bold uppercase tracking-wide text-[#737982]">{label}</p>
      <p className="mt-1 text-sm font-bold text-[#18202b]">{value}</p>
    </div>
  );
}

export default function IpoDetailPage() {
  const { symbol } = useParams();
  const [state, setState] = useState({ loading: true, data: null, error: null });

  useEffect(() => {
    let active = true;
    getIpoDetail(symbol)
      .then((data) => active && setState({ loading: false, data, error: null }))
      .catch((error) => active && setState({ loading: false, data: null, error }));
    return () => {
      active = false;
    };
  }, [symbol]);

  const ipo = state.data?.ipo;
  const priceBand = ipo?.minPrice == null && ipo?.maxPrice == null
    ? 'Pending / not provided'
    : ipo?.minPrice === ipo?.maxPrice ? `₹${ipo.minPrice}` : `₹${ipo?.minPrice}–${ipo?.maxPrice}`;

  return (
    <div className="min-h-screen bg-[#f8fafb]">
      <Helmet>
        <title>{ipo ? `${ipo.name} IPO | AGI` : 'IPO Monitor | AGI'}</title>
        <meta name="description" content="Source-linked IPO offer information for Indian public issues. Informational only, not investment advice." />
      </Helmet>
      <main className="mx-auto max-w-[1200px] px-4 py-7 sm:px-6 sm:py-10">
        <Link to="/" className="inline-flex items-center gap-2 text-xs font-bold text-[#274c77] hover:underline">
          <ArrowLeft className="h-4 w-4" /> Back to IPO Monitor
        </Link>

        {state.loading ? (
          <div className="mt-6 h-80 animate-pulse border border-[#dde1e6] bg-white" />
        ) : state.error || !ipo ? (
          <section className="mt-6 border border-dashed border-[#cbd2da] bg-white p-8 text-center">
            <h1 className="text-xl font-bold text-[#18202b]">IPO information unavailable</h1>
            <p className="mx-auto mt-2 max-w-lg text-sm text-[#667085]">This issue is not present in the most recently refreshed IPO dataset.</p>
          </section>
        ) : (
          <>
            <section className="mt-6 border border-[#dde1e6] bg-white p-5 sm:p-8">
              <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <div className="flex items-center gap-2 text-[#274c77]">
                    <CalendarDays className="h-4 w-4" />
                    <span className="text-[10px] font-bold uppercase tracking-[0.12em]">IPO Monitor</span>
                  </div>
                  <h1 className="mt-3 text-3xl font-bold tracking-tight text-[#18202b]">{ipo.name}</h1>
                  <p className="mt-2 text-sm text-[#667085]">{ipo.isSme ? 'SME public issue' : 'Mainboard public issue'} · Symbol: {ipo.symbol}</p>
                </div>
                <span className="w-fit border border-[#d9dee5] bg-[#f8fafb] px-3 py-2 text-xs font-bold uppercase tracking-wide text-[#59616d]">{ipo.status}</span>
              </div>
              {ipo.detail && <p className="mt-5 border-l-4 border-[#274c77] bg-[#f8fafb] p-4 text-sm leading-relaxed text-[#374151]">{ipo.detail}</p>}
            </section>

            <section className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <DetailRow label="Price band" value={priceBand} />
              <DetailRow label="Opens" value={formatDate(ipo.biddingStartDate)} />
              <DetailRow label="Closes" value={formatDate(ipo.biddingEndDate)} />
              <DetailRow label="Allotment" value={formatDate(ipo.allotmentDate)} />
              <DetailRow label="Listing date" value={formatDate(ipo.listingDate)} />
              <DetailRow label="Lot size" value={valueOrPending(ipo.lotSize)} />
              <DetailRow label="Minimum bid quantity" value={valueOrPending(ipo.minimumBidQuantity)} />
              <DetailRow label="Subscription rate" value={valueOrPending(ipo.subscriptionRate, (value) => `${value}x`)} />
            </section>

            <section className="mt-6 border border-[#dde1e6] bg-white p-5">
              <h2 className="text-sm font-bold text-[#18202b]">Offer document</h2>
              {ipo.documentUrl ? (
                <a href={ipo.documentUrl} target="_blank" rel="noreferrer" className="mt-3 inline-flex items-center gap-2 text-sm font-bold text-[#274c77] hover:underline">
                  <ExternalLink className="h-4 w-4" /> Open issuer / exchange / SEBI document
                </a>
              ) : (
                <p className="mt-2 text-sm text-[#667085]">A source document link is not available in the latest provider response.</p>
              )}
            </section>

            <section className="mt-6 border border-[#f2d7a0] bg-[#fffaf0] p-5 text-xs leading-relaxed text-[#6f5a2e]">
              <p className="flex items-center gap-2 font-bold uppercase tracking-wide"><FileText className="h-4 w-4" /> Important disclosure</p>
              <p className="mt-2">IPO information is provided for informational purposes only and is not an offer, recommendation, or solicitation. Verify offer documents directly with the issuer, NSE, BSE, or SEBI before acting.</p>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
