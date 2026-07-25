import { Navigate, Route, Routes } from 'react-router-dom';
import RequireAdmin from '@/components/admin/RequireAdmin';
import AdminLayout from '@/pages/admin/AdminLayout';
import AdminDashboard from '@/pages/admin/Dashboard';
import ArticleEditor from '@/pages/admin/ArticleEditor';
import CategoryManager from '@/pages/admin/CategoryManager';
import KnowledgeFoundation from '@/pages/admin/KnowledgeFoundation';
import OpenIntelligence from '@/pages/admin/OpenIntelligence';
import Evidence from '@/pages/admin/Evidence';
import InvestmentIntelligence from '@/pages/admin/InvestmentIntelligence';
import Forecasting from '@/pages/admin/Forecasting';
import Events from '@/pages/admin/Events';
import ContextAssembly from '@/pages/admin/ContextAssembly';

export default function AdminRoutes() {
  return (
    <RequireAdmin>
      <Routes>
        <Route element={<AdminLayout />}>
          <Route index element={<AdminDashboard />} />
          <Route path="articles" element={<AdminDashboard />} />
          <Route path="articles/new" element={<ArticleEditor />} />
          <Route path="articles/edit/:slug" element={<ArticleEditor />} />
          <Route path="categories" element={<CategoryManager />} />
          <Route path="knowledge" element={<KnowledgeFoundation />} />
          <Route path="open-intelligence" element={<OpenIntelligence />} />
          <Route path="evidence" element={<Evidence />} />
          <Route path="investment-intelligence" element={<InvestmentIntelligence />} />
          <Route path="forecasting" element={<Forecasting />} />
          <Route path="events" element={<Events />} />
          <Route path="context" element={<ContextAssembly />} />
          <Route path="*" element={<Navigate to="/admin" replace />} />
        </Route>
      </Routes>
    </RequireAdmin>
  );
}
