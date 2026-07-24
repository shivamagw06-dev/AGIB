import { useEffect, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { MarketDataProvider } from '@/contexts/MarketDataContext';
import { BetaDepthProvider } from '@/beta/BetaDepthContext';
import DepthSwitch from '@/beta/components/DepthSwitch';
import StoryNav from '@/beta/components/StoryNav';
import HomeTerminal from '@/beta/surfaces/HomeTerminal';
import CopilotExperience from '@/beta/surfaces/CopilotExperience';
import CompanyStory from '@/beta/surfaces/CompanyStory';
import CompareStory from '@/beta/surfaces/CompareStory';
import ScreenerStory from '@/beta/surfaces/ScreenerStory';
import WatchlistStory from '@/beta/surfaces/WatchlistStory';
import MarketsStory from '@/beta/surfaces/MarketsStory';
import ResearchLibrary from '@/beta/surfaces/ResearchLibrary';
import ForecastsStory from '@/beta/surfaces/ForecastsStory';
import ValidationStory from '@/beta/surfaces/ValidationStory';
import MacroStory from '@/beta/surfaces/MacroStory';
import SettingsStory from '@/beta/surfaces/SettingsStory';
import '@/beta/theme.css';

function BetaChrome() {
  const [navOpen, setNavOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setNavOpen(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [location.pathname]);

  return (
    <div className="agi-beta min-h-screen">
      <Helmet>
        <title>AGI Beta — Complex Markets. Simple Intelligence.</title>
        <meta
          name="description"
          content="AGI Story Beta — magazine-like investment intelligence. What do I need to know?"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&display=swap"
          rel="stylesheet"
        />
      </Helmet>

      <header className="sticky top-0 z-40 border-b border-[var(--beta-border)] bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="rounded-lg border border-[var(--beta-border)] p-2 lg:hidden"
              aria-label="Open navigation"
              onClick={() => setNavOpen(true)}
            >
              <Menu className="h-4 w-4" />
            </button>
            <div>
              <Link to="/beta" className="font-[family-name:var(--beta-serif)] text-xl font-semibold text-[var(--beta-navy)]">
                AGI
              </Link>
              <p className="hidden text-[11px] text-[var(--beta-muted)] sm:block">
                Complex Markets. Simple Intelligence.
              </p>
            </div>
          </div>
          <div className="hidden md:block">
            <DepthSwitch />
          </div>
          <Link to="/" className="beta-btn-ghost beta-btn text-[12px]">
            Exit beta →
          </Link>
        </div>
        <div className="border-t border-[var(--beta-border)] px-4 py-2 md:hidden">
          <DepthSwitch />
        </div>
      </header>

      <div className="mx-auto flex max-w-[1400px]">
        <aside className="sticky top-[73px] hidden h-[calc(100vh-73px)] w-56 shrink-0 overflow-y-auto border-r border-[var(--beta-border)] bg-white px-3 py-5 lg:block">
          <p className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[0.16em] text-[var(--beta-caption)]">
            Experience
          </p>
          <StoryNav />
        </aside>

        <main className="min-w-0 flex-1">
          <Routes>
            <Route index element={<HomeTerminal />} />
            <Route path="copilot" element={<CopilotExperience />} />
            <Route path="markets" element={<MarketsStory />} />
            <Route path="macro" element={<MacroStory />} />
            <Route path="companies" element={<CompanyStory />} />
            <Route path="companies/:symbol" element={<CompanyStory />} />
            <Route path="research" element={<ResearchLibrary />} />
            <Route path="forecasts" element={<ForecastsStory />} />
            <Route path="screener" element={<ScreenerStory />} />
            <Route path="compare" element={<CompareStory />} />
            <Route path="watchlists" element={<WatchlistStory />} />
            <Route path="validation" element={<ValidationStory />} />
            <Route path="settings" element={<SettingsStory />} />
            <Route path="*" element={<Navigate replace to="/beta" />} />
          </Routes>
        </main>
      </div>

      {navOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-[var(--beta-navy)]/40"
            aria-label="Close navigation"
            onClick={() => setNavOpen(false)}
          />
          <div className="absolute left-0 top-0 flex h-full w-72 flex-col bg-white p-4 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <p className="font-[family-name:var(--beta-serif)] text-lg font-semibold text-[var(--beta-navy)]">AGI</p>
              <button type="button" className="rounded-lg border border-[var(--beta-border)] p-2" onClick={() => setNavOpen(false)}>
                <X className="h-4 w-4" />
              </button>
            </div>
            <StoryNav onNavigate={() => setNavOpen(false)} />
          </div>
        </div>
      )}
    </div>
  );
}

export default function BetaApp() {
  return (
    <MarketDataProvider>
      <BetaDepthProvider>
        <BetaChrome />
      </BetaDepthProvider>
    </MarketDataProvider>
  );
}
