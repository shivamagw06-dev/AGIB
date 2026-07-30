import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

/**
 * Gate for authenticated + PIN-unlocked sessions.
 * Redirects to /login when signed out, PIN missing, or locked.
 */
export default function RequireAuth({ children }) {
  const { user, loading, hasPin, unlocked } = useAuth();
  const location = useLocation();
  const next = `${location.pathname}${location.search || ''}`;

  if (loading) return null;
  if (!user || !hasPin || !unlocked) {
    return <Navigate to={`/login?next=${encodeURIComponent(next || '/portal')}`} replace />;
  }
  return children;
}
