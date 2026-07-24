import { Navigate, Route, Routes } from 'react-router-dom';
import RequireAdmin from '@/components/admin/RequireAdmin';
import AdminLayout from '@/pages/admin/AdminLayout';
import AdminDashboard from '@/pages/admin/Dashboard';
import ArticleEditor from '@/pages/admin/ArticleEditor';
import CategoryManager from '@/pages/admin/CategoryManager';
import PublishingDashboard from '@/pages/admin/publishing/PublishingDashboard';
import NewsletterSubscribers from '@/pages/admin/publishing/NewsletterSubscribers';
import NewsletterImport from '@/pages/admin/publishing/NewsletterImport';
import NewsletterAnalytics from '@/pages/admin/publishing/NewsletterAnalytics';
import NewsletterTemplates from '@/pages/admin/publishing/NewsletterTemplates';
import CampaignHistory from '@/pages/admin/publishing/CampaignHistory';

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
          <Route path="publishing" element={<PublishingDashboard />} />
          <Route path="publishing/subscribers" element={<NewsletterSubscribers />} />
          <Route path="publishing/import" element={<NewsletterImport />} />
          <Route path="publishing/analytics" element={<NewsletterAnalytics />} />
          <Route path="publishing/templates" element={<NewsletterTemplates />} />
          <Route path="publishing/campaigns" element={<CampaignHistory />} />
          <Route path="*" element={<Navigate to="/admin" replace />} />
        </Route>
      </Routes>
    </RequireAdmin>
  );
}
