import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import {
  canAccessCms,
  isAdmin,
  isAuthorCmsPath,
  isStrictAdminPath,
} from '@/lib/adminAuth';
import Forbidden403 from '@/components/admin/Forbidden403';

/**
 * CMS / admin gate:
 * - Signed-in authors can reach article list / create / edit (their own uploads).
 * - Full admin tools remain admin-only.
 * - Strict admin paths (Knowledge Operations) return 403 for non-admins.
 */
export default function RequireAdmin({ children }) {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) {
    const redirect = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?redirect=${redirect}`} replace />;
  }

  if (!canAccessCms(user)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-white">
        <div className="text-center max-w-md px-6">
          <h1 className="text-2xl font-bold mb-2">Access Denied</h1>
          <p className="text-slate-400">Sign in to manage your uploaded articles.</p>
        </div>
      </div>
    );
  }

  if (!isAdmin(user) && isStrictAdminPath(location.pathname)) {
    return <Forbidden403 resource="Knowledge Operations" />;
  }

  if (!isAdmin(user) && !isAuthorCmsPath(location.pathname)) {
    return <Navigate to="/admin/articles" replace />;
  }

  return children;
}
