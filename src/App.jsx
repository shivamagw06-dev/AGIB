// src/App.jsx
import ResearchCategories from "@/components/Home/ResearchCategories";
import CategoryNavigation from "@/components/Home/CategoryNavigation";
import React, { useEffect, Suspense } from 'react';
import { Helmet, HelmetProvider } from 'react-helmet-async';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import AdminRoutes from '@/pages/admin/AdminRoutes';
import CategoryPage from '@/pages/CategoryPage';
import Header from "@/components/Layout/Header";
import Hero from "@/components/Hero/Hero";
import ArticlesFeed from '@/components/ArticlesFeed';
import LatestNews from '@/components/LatestNews';
import About from '@/components/About';
import Contact from '@/components/Contact';
import Newsletter from '@/components/Newsletter';
import Footer from '@/components/Footer';
import ResearchNotes from '@/components/ResearchNotes';
import DealTracker from '@/components/DealTracker';
import PlaceholderPage from '@/components/PlaceholderPage';
import { Toaster } from '@/components/ui/toaster';
import ProfileEditor from '@/pages/ProfileEditor';
import PublicProfile from '@/pages/PublicProfile';
import LoginPage from '@/components/LoginPage';
import ArticlePage from '@/components/ArticlePage';
import NotFound from '@/components/NotFound';
import Business from '@/components/Business.jsx'; // ✅ explicitly use .jsx
import MarketBrief from "@/components/Home/MarketBrief";
import FeaturedResearch from "@/components/Home/FeaturedResearch";
import LatestResearch from "@/components/Home/LatestResearch";
import MarketDashboard from "@/components/Home/MarketDashboard";
import ResearchTicker from "@/components/Layout/ResearchTicker";
import { MarketOverviewProvider } from "@/contexts/MarketOverviewContext";
import MarketPulse from "@/components/markets/MarketPulse";
import IpoWatch from "@/components/markets/IpoWatch";
import MutualFundsSpotlight from "@/components/markets/MutualFundsSpotlight";
import StockSearchBar from "@/components/markets/StockSearchBar";

// Lazy-load heavier or less-frequently-used sections
const Opinions = React.lazy(() => import('@/components/Opinions'));
const MarketsPage = React.lazy(() => import('@/components/MarketsPage'));
const OnePageWealthTools = React.lazy(() => import('@/components/OnePageWealthTools'));

function HomeLayout() {
  return (
    <div className="bg-slate-950">

      <Hero />

      <section className="bg-slate-950 py-12 border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <StockSearchBar />
        </div>
      </section>

      <MarketDashboard />

      <MarketPulse />

      <MarketBrief />

      <IpoWatch />

      <MutualFundsSpotlight />

      <CategoryNavigation />

      <ResearchCategories />

      <FeaturedResearch />

      <LatestResearch />

      <div className="max-w-screen-xl mx-auto px-6 py-16">
        <LatestNews max={6} />
      </div>

      <Newsletter />

    </div>
  );
}

function AppShell() {
  const location = useLocation();
  const isAdmin = location.pathname.startsWith('/admin');

  if (isAdmin) {
    return (
      <Routes>
        <Route path="/admin/*" element={<AdminRoutes />} />
      </Routes>
    );
  }

  return (
    <MarketOverviewProvider>
      <Header />
      <ResearchTicker />
      <main>
        <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
          <PublicRoutes />
        </Suspense>
      </main>
      <Footer />
      <Toaster />
    </MarketOverviewProvider>
  );
}

function PublicRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomeLayout />} />
      <Route path="/category/:slug" element={<CategoryPage />} />

      <Route path="/sections/live-articles" element={<ArticlesFeed />} />
      <Route path="/live-articles" element={<Navigate replace to="/sections/live-articles" />} />

      <Route path="/sections/research-notes" element={<ResearchNotes />} />
      <Route path="/research-notes" element={<Navigate replace to="/sections/research-notes" />} />

      <Route path="/sections/deal-tracker" element={<DealTracker />} />
      <Route path="/deal-tracker" element={<Navigate replace to="/sections/deal-tracker" />} />

      <Route path="/sections/markets" element={<MarketsPage />} />
      <Route path="/markets" element={<Navigate replace to="/sections/markets" />} />

      <Route path="/sections/opinions-editorials" element={<Opinions />} />
      <Route path="/opinions-editorials" element={<Navigate replace to="/sections/opinions-editorials" />} />

      <Route path="/wealth-management" element={<OnePageWealthTools />} />
      <Route path="/sections/wealth-management" element={<Navigate replace to="/wealth-management" />} />

      <Route path="/business" element={<Business />} />
      <Route path="/sections/business" element={<Navigate replace to="/business" />} />

      <Route
        path="/events"
        element={
          <PlaceholderPage
            title="Events & Webinars"
            subtitle="Our calendar of upcoming events will be available shortly."
          />
        }
      />
      <Route path="/events-webinars" element={<Navigate replace to="/events" />} />

      <Route path="/login" element={<LoginPage />} />
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
        console.log('[App] VITE_API_URL:', apiUrl);
      } else {
        console.warn('[App] VITE_API_URL is not defined. Check your .env.local');
      }
    } catch (err) {
      console.error('[App] Error reading VITE_API_URL', err);
    }
  }, []);

  return (
    <HelmetProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-background">
          <Helmet>
            <title>Agarwal Global Investments - Insights that Power Investment Decisions</title>
            <meta
              name="description"
              content="Independent research and live insights on finance, economics, private equity & M&A. Stay informed with Agarwal Global Investments."
            />
            <link rel="preconnect" href="https://fonts.googleapis.com" />
            <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
            <link
              href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
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
