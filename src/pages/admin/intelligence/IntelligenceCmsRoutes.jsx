import { Navigate, Route, Routes } from 'react-router-dom';
import IntelligenceCmsLayout from './IntelligenceCmsLayout';
import IntelligenceDashboard from './IntelligenceDashboard';
import IntelligenceModulePage from './IntelligenceModulePage';

export default function IntelligenceCmsRoutes() {
  return (
    <Routes>
      <Route element={<IntelligenceCmsLayout />}>
        <Route index element={<IntelligenceDashboard />} />
        <Route path="valuation-monitor" element={<IntelligenceModulePage />} />
        <Route path=":moduleSlug" element={<IntelligenceModulePage />} />
        <Route path="*" element={<Navigate to="/admin/intelligence" replace />} />
      </Route>
    </Routes>
  );
}
