// src/App.jsx
import React, { useEffect } from 'react';
import { Helmet, HelmetProvider } from 'react-helmet-async';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import Header from '@/components/Header';
import Hero from '@/components/Hero';
import ArticlesFeed from '@/components/ArticlesFeed';
import About from '@/components/About';
import Contact from '@/components/Contact';
import Newsletter from '@/components/Newsletter';
import Footer from '@/components/Footer';
import ResearchNotes from '@/components/ResearchNotes';
import DealTracker from '@/components/DealTracker';
import PlaceholderPage from '@/components/PlaceholderPage';
// removed: import NewArticle from '@/components/NewArticle';
import WriteArticle from './components/WriteArticle';
import { Toaster } from '@/components/ui/toaster';
import MarketsPage from '@/components/MarketsPage';
import ProfileEditor from '@/pages/ProfileEditor';
import PublicProfile from '@/pages/PublicProfile';

import LoginPage from '@/components/LoginPage';
import ArticlePage from '@/components/ArticlePage';
import NotFound from '@/components/NotFound';

// NEW: import Opinions component
import Opinions from '@/components/Opinions';

function HomeLayout() {
  return (
    <>
      <Hero />
      <ArticlesFeed />
      <Newsletter />
    </>
  );
}

function App() {
  // Expose the Vite env var to window for easy debugging in the browser console.
  useEffect(() => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || null;
      // attach so you can type `window.API_URL` in the console to inspect
      if (apiUrl) {
        window.API_URL = apiUrl;
        console.log('[App] VITE_API_URL:', apiUrl);
      } else {
        console.warn('[App] VITE_API_URL is not defined. Check your .env.local');
      }
    } catch (err) {
      // import.meta isn't available in non-module contexts (shouldn't happen inside Vite-built app)
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
            <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="true" />
            <link
              href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
              rel="stylesheet"
            />
          </Helmet>

          <Header />

          <main>
            <Routes>
              {/* Home */}
              <Route path="/" element={<HomeLayout />} />

              {/* Core sections */}
              <Route path="/sections/live-articles" element={<ArticlesFeed />} />
              <Route path="/live-articles" element={<Navigate replace to="/sections/live-articles" />} />

              <Route path="/sections/research-notes" element={<ResearchNotes />} />
              <Route path="/research-notes" element={<Navigate replace to="/sections/research-notes" />} />

              <Route path="/sections/deal-tracker" element={<DealTracker />} />
              <Route path="/deal-tracker" element={<Navigate replace to="/sections/deal-tracker" />} />

              <Route path="/sections/markets" element={<MarketsPage />} />
              <Route path="/markets" element={<Navigate replace to="/sections/markets" />} />

              {/* Opinions & Editorials: use real Opinions component */}
              <Route path="/sections/opinions-editorials" element={<Opinions />} />
              <Route path="/opinions-editorials" element={<Navigate replace to="/sections/opinions-editorials" />} />

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

              {/* Articles, login and editor */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/article/:slug" element={<ArticlePage />} />

              {/* use WriteArticle here instead of NewArticle */}
              <Route path="/articles/new" element={<WriteArticle />} />
              <Route path="/write" element={<WriteArticle />} /> {/* LinkedIn-style editor */}

              {/* About / Contact */}
              <Route path="/about" element={<About />} />
              <Route path="/contact" element={<Contact />} />

              {/* Profile pages */}
              <Route path="/profile/edit" element={<ProfileEditor />} />
              <Route path="/u/:handle" element={<PublicProfile />} />

              {/* Not Found */}
              <Route path="/404" element={<NotFound />} />
              <Route path="*" element={<Navigate replace to="/404" />} />
            </Routes>
          </main>

          <Footer />
          <Toaster />
        </div>
      </BrowserRouter>
    </HelmetProvider>
  );
}

export default App;
