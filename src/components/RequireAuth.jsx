import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { supabase } from '@/lib/supabaseClient';

export default function RequireAuth({ children }) {
  const [user, setUser] = useState();
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      setUser(data.user || null); setLoading(false);
    });
  }, []);
  if (loading) return null;
  return user ? children : <Navigate to="/login" replace />;
}