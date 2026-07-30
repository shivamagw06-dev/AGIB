import { Route, Routes } from 'react-router-dom';
import AgiLayout from './AgiLayout';
import DashboardPage from './DashboardPage';
import AskAgiProductPage from './AskAgiProductPage';
import CompaniesIndexPage from './CompaniesIndexPage';
import CompanyWorkspacePage from './CompanyWorkspacePage';
import ComingSoonPage from './ComingSoonPage';

export default function AgiRoutes() {
  return (
    <Routes>
      <Route element={<AgiLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="ask" element={<AskAgiProductPage />} />
        <Route path="companies" element={<CompaniesIndexPage />} />
        <Route path="companies/:ticker" element={<CompanyWorkspacePage />} />
        <Route path="portfolio" element={<ComingSoonPage area="portfolio" />} />
        <Route path="markets" element={<ComingSoonPage area="markets" />} />
        <Route path="research" element={<ComingSoonPage area="research" />} />
        <Route path="watchlists" element={<ComingSoonPage area="watchlists" />} />
        <Route path="screeners" element={<ComingSoonPage area="screeners" />} />
        <Route path="notebook" element={<ComingSoonPage area="notebook" />} />
        <Route path="alerts" element={<ComingSoonPage area="alerts" />} />
        <Route path="settings" element={<ComingSoonPage area="settings" />} />
      </Route>
    </Routes>
  );
}
