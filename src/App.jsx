// src/App.jsx
import React, { useEffect, Suspense } from 'react';
import { Helmet, HelmetProvider } from 'react-helmet-async';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import AdminRoutes from '@/pages/admin/AdminRoutes';
import CategoryPage from '@/pages/CategoryPage';
import Header from "@/components/Layout/Header";
import { MarketDataProvider } from "@/contexts/MarketDataContext";
import ArticlesFeed from '@/components/ArticlesFeed';
import About from '@/components/About';
import Contact from '@/components/Contact';
import Footer from '@/components/Footer';
import ResearchNotes from '@/components/ResearchNotes';
import DealTracker from '@/components/DealTracker';
import { Toaster } from '@/components/ui/toaster';
import ProfileEditor from '@/pages/ProfileEditor';
import PublicProfile from '@/pages/PublicProfile';
import LoginPage from '@/components/LoginPage';
import ArticlePage from '@/components/ArticlePage';
import NotFound from '@/components/NotFound';
import Business from '@/components/Business.jsx';
import MarketUpdates from '@/pages/MarketUpdates';
import SectionArticlesPage from '@/pages/SectionArticlesPage';
import Events from '@/pages/Events';
import PrivacyPolicy from '@/pages/legal/PrivacyPolicy';
import TermsOfService from '@/pages/legal/TermsOfService';
import Disclaimer from '@/pages/legal/Disclaimer';
import SebiDisclosure from '@/pages/legal/SebiDisclosure';
import VerifyEmailPage from '@/pages/auth/VerifyEmailPage';
import ForgotPasswordPage from '@/pages/auth/ForgotPasswordPage';
import ResetPasswordPage from '@/pages/auth/ResetPasswordPage';
import PinUnlockPage from '@/pages/auth/PinUnlockPage';
import AccountSecurityPage from '@/pages/auth/AccountSecurityPage';
import PinGate from '@/components/auth/PinGate';

const Opinions = React.lazy(() => import('@/components/Opinions'));
const Markets = React.lazy(() => import('@/pages/Markets'));
const MarketIntelligence = React.lazy(() => import('@/pages/MarketIntelligence'));
const MacroIntelligence = React.lazy(() => import('@/pages/MacroIntelligence'));
const PreMarketIntelligence = React.lazy(() => import('@/pages/PreMarketIntelligence'));
const Nifty500StockResearch = React.lazy(() => import('@/pages/Nifty500StockResearch'));
const IpoDetailPage = React.lazy(() => import('@/pages/IpoDetailPage'));
const IpoIntelligencePage = React.lazy(() => import('@/pages/IpoIntelligencePage'));
const MarketDataCentre = React.lazy(() => import('@/pages/MarketDataCentre'));
const PortfolioDesk = React.lazy(() => import('@/pages/PortfolioDesk'));
const ThemeDesk = React.lazy(() => import('@/pages/ThemeDesk'));
const SectorDesk = React.lazy(() => import('@/pages/SectorDesk'));
const ResearchWorkflowDesk = React.lazy(() => import('@/pages/ResearchWorkflowDesk'));
const AskAgiPage = React.lazy(() => import('@/pages/AskAgiPage'));
const PredictionCentre = React.lazy(() => import('@/pages/PredictionCentre'));
const PersonalWorkspace = React.lazy(() => import('@/pages/PersonalWorkspace'));
const ResearchTerminalHome = React.lazy(() => import('@/components/Home/ResearchTerminalHome'));

function HomeLayout() {
  // Public research-terminal homepage — admin shells stay under /admin/*.
  return <ResearchTerminalHome />;
}

function AppShell() {
  const location = useLocation();
  const isAdmin = location.pathname.startsWith('/admin');
  const isAskWorkspace = location.pathname === '/ask';

  useEffect(() => {
    if (!isAdmin && !isAskWorkspace) {
      document.documentElement.classList.remove('dark');
    }
  }, [isAdmin, isAskWorkspace, location.pathname]);

  if (isAdmin) {
    return (
      <Routes>
        <Route path="/admin/*" element={<AdminRoutes />} />
      </Routes>
    );
  }

  // Ask AGI is a full-bleed institutional research workspace — no public chrome.
  if (isAskWorkspace) {
    return (
      <MarketDataProvider>
        <PinGate>
          <Suspense fallback={<div className="min-h-screen bg-[#0b0e14] p-8 text-center text-slate-300">Loading Ask AGI…</div>}>
            <Routes>
              <Route path="/ask" element={<AskAgiPage />} />
            </Routes>
          </Suspense>
          <Toaster />
        </PinGate>
      </MarketDataProvider>
    );
  }

  return (
    <>
      <MarketDataProvider>
        <PinGate>
          <Header />
          <main>
            <Suspense fallback={<div className="p-8 text-center text-slate-600">Loading…</div>}>
              <PublicRoutes />
            </Suspense>
          </main>
          <Footer />
          <Toaster />
        </PinGate>
      </MarketDataProvider>
    </>
  );
}

function PublicRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomeLayout />} />
      <Route path="/ask" element={<AskAgiPage />} />
      <Route path="/predictions" element={<PredictionCentre />} />
      <Route path="/workspace" element={<PersonalWorkspace />} />

      <Route path="/market-updates" element={<MarketUpdates />} />
      <Route path="/updates/:sectionId" element={<SectionArticlesPage />} />
      <Route path="/company-updates" element={<SectionArticlesPage overrideId="company-updates" />} />

      <Route path="/research" element={<ArticlesFeed variant="light" />} />
      <Route path="/sections/live-articles" element={<Navigate replace to="/research" />} />
      <Route path="/live-articles" element={<Navigate replace to="/research" />} />

      <Route path="/category/:slug" element={<CategoryPage />} />

      <Route path="/markets" element={<Markets />} />
      <Route path="/sections/markets" element={<Navigate replace to="/markets" />} />
      <Route path="/market-intelligence" element={<MarketIntelligence />} />
      <Route path="/macro-intelligence" element={<MacroIntelligence />} />
      <Route path="/global" element={<MacroIntelligence />} />
      <Route path="/global-intelligence" element={<Navigate replace to="/global" />} />
      <Route path="/economy" element={<Navigate replace to="/macro-intelligence" />} />
      <Route path="/pre-market" element={<PreMarketIntelligence />} />
      <Route path="/updates/pre-market" element={<Navigate replace to="/pre-market" />} />
      <Route path="/market-data" element={<MarketDataCentre />} />
      <Route path="/research/stocks/:symbol" element={<Nifty500StockResearch />} />
      <Route path="/portfolio" element={<PortfolioDesk />} />
      <Route path="/themes/:themeId" element={<ThemeDesk />} />
      <Route path="/themes" element={<Navigate replace to="/themes/credit_growth" />} />
      <Route path="/sectors/:sectorId" element={<SectorDesk />} />
      <Route path="/research/workflow" element={<ResearchWorkflowDesk />} />
      <Route path="/ipo-intelligence" element={<IpoIntelligencePage />} />
      <Route path="/ipos" element={<Navigate replace to="/ipo-intelligence" />} />
      <Route path="/ipos/:symbol" element={<IpoDetailPage />} />

      {/* Legacy redirects */}
      <Route path="/companies" element={<Navigate replace to="/company-updates" />} />
      <Route path="/private-markets" element={<Navigate replace to="/sections/deal-tracker" />} />
      <Route path="/insights" element={<Navigate replace to="/sections/opinions-editorials" />} />

      <Route path="/sections/research-notes" element={<ResearchNotes />} />
      <Route path="/research-notes" element={<Navigate replace to="/sections/research-notes" />} />

      <Route path="/sections/deal-tracker" element={<DealTracker />} />
      <Route path="/deal-tracker" element={<Navigate replace to="/sections/deal-tracker" />} />

      <Route path="/sections/opinions-editorials" element={<Opinions />} />
      <Route path="/opinions-editorials" element={<Navigate replace to="/sections/opinions-editorials" />} />

      <Route path="/business" element={<Business />} />

      <Route path="/events" element={<Events />} />
      <Route path="/events-webinars" element={<Navigate replace to="/events" />} />

      <Route path="/privacy" element={<PrivacyPolicy />} />
      <Route path="/terms" element={<TermsOfService />} />
      <Route path="/disclaimer" element={<Disclaimer />} />
      <Route path="/sebi-disclosure" element={<SebiDisclosure />} />

      <Route path="/login" element={<LoginPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/unlock-pin" element={<PinUnlockPage />} />
      <Route path="/account/security" element={<AccountSecurityPage />} />
      <Route path="/article/:slug" element={<ArticlePage />} />
      <Route path="/articles/new" element={<Navigate replace to="/admin/articles/new" />} />
      <Route path="/write" element={<Navigate replace to="/admin/articles/new" />} />

      <Route path="/about" element={<About />} />
      <Route path="/contact" element={<Contact />} />

      <Route path="/profile/edit" element={<ProfileEditor />} />
      <Route path="/u/:handle" element={<PublicProfile />} />

      <Route path="/404" element={<NotFound />} />
      <Route path="*" element={<Navigate replace to="/404" />} />
    </Routes>
  );
}

function App() {
  useEffect(() => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || null;
      if (apiUrl) {
        window.API_URL = apiUrl;
      }
    } catch {
      /* ignore */
    }
  }, []);

  return (
    <HelmetProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-white">
          <Helmet>
            <title>AGI — Independent Equity Research for Indian Investors</title>
            <meta
              name="description"
              content="Institutional-quality market research updated every trading day. Morning briefs, sector analysis, and company updates from Agarwal Global Investments."
            />
            <link rel="preconnect" href="https://fonts.googleapis.com" />
            <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
            <link
              href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,500;8..60,600;8..60,700&display=swap"
              rel="stylesheet"
            />
          </Helmet>
          <AppShell />
        </div>
      </BrowserRouter>
    </HelmetProvider>
  );
}

export default App;
