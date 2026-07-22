import { Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { isAdmin } from '@/lib/adminAuth';

export default function RequireAdmin({ children }) {
  const { user } = useAuth();

  if (!user) return <Navigate to="/login?redirect=/admin" replace />;
  if (!isAdmin(user)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-white">
        <div className="text-center max-w-md px-6">
          <h1 className="text-2xl font-bold mb-2">Access Denied</h1>
          <p className="text-slate-400">Only authorized editors can access the CMS.</p>
        </div>
      </div>
    );
  }

  return children;
}
