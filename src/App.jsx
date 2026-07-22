// src/App.jsx
import React, { useEffect, Suspense } from 'react';
import { Helmet, HelmetProvider } from 'react-helmet-async';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import AdminRoutes from '@/pages/admin/AdminRoutes';
import CategoryPage from '@/pages/CategoryPage';
import Header from "@/components/Layout/Header";
import InstitutionalHero from "@/components/Home/InstitutionalHero";
import ContentCategoryGrid from "@/components/Home/ContentCategoryGrid";
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

const Opinions = React.lazy(() => import('@/components/Opinions'));
const Markets = React.lazy(() => import('@/pages/Markets'));

function HomeLayout() {
  return (
    <div className="bg-white min-h-screen">
      <InstitutionalHero />
      <ContentCategoryGrid />
    </div>
  );
}

function AppShell() {
  const location = useLocation();
  const isAdmin = location.pathname.startsWith('/admin');

  useEffect(() => {
    if (!isAdmin) {
      document.documentElement.classList.remove('dark');
    }
  }, [isAdmin, location.pathname]);

  if (isAdmin) {
    return (
      <Routes>
        <Route path="/admin/*" element={<AdminRoutes />} />
      </Routes>
    );
  }

  return (
    <>
      <Header />
      <main>
        <Suspense fallback={<div className="p-8 text-center text-slate-600">Loading…</div>}>
          <PublicRoutes />
        </Suspense>
      </main>
      <Footer />
      <Toaster />
    </>
  );
}

function PublicRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomeLayout />} />

      <Route path="/market-updates" element={<MarketUpdates />} />
      <Route path="/updates/:sectionId" element={<SectionArticlesPage />} />
      <Route path="/company-updates" element={<SectionArticlesPage overrideId="company-updates" />} />

      <Route path="/research" element={<ArticlesFeed variant="light" />} />
      <Route path="/sections/live-articles" element={<Navigate replace to="/research" />} />
      <Route path="/live-articles" element={<Navigate replace to="/research" />} />

      <Route path="/category/:slug" element={<CategoryPage />} />

      <Route path="/markets" element={<Markets />} />
      <Route path="/sections/markets" element={<Navigate replace to="/markets" />} />

      {/* Legacy redirects */}
      <Route path="/economy" element={<Navigate replace to="/sections/research-notes" />} />
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
            <title>Agarwal Global Investments — Market Research for Indian Investors</title>
            <meta
              name="description"
              content="Daily market updates, company research, earnings analysis, and actionable investment insights for Indian investors."
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
