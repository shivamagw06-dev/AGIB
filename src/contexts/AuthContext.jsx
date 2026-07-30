import React, { createContext, useState, useContext, useEffect, useMemo } from 'react';
import { supabase, isSupabaseConfigured } from '../lib/supabaseClient';
import { clearPinUnlock, markPinUnlocked } from '@/lib/devicePin';

const AuthContext = createContext(null);

const SITE_URL =
  typeof window !== 'undefined' ? window.location.origin : 'https://agarwalglobalinvestments.com';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authReady, setAuthReady] = useState(false);

  useEffect(() => {
    let mounted = true;

    supabase.auth
      .getSession()
      .then(({ data }) => {
        if (!mounted) return;
        setUser(data.session?.user ?? null);
      })
      .catch(() => {
        if (mounted) setUser(null);
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
        setAuthReady(true);
      });

    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
      setLoading(false);
      setAuthReady(true);
    });

    return () => {
      mounted = false;
      sub?.subscription?.unsubscribe?.();
    };
  }, []);

  const value = useMemo(() => {
    const requireConfigured = () => {
      if (!isSupabaseConfigured) {
        throw new Error('Authentication is not configured on this deployment.');
      }
    };

    const register = async ({
      fullName,
      email,
      password,
      mobile = '',
      emailRedirectTo,
    }) => {
      requireConfigured();
      const redirectTo = emailRedirectTo || `${SITE_URL}/verify-email`;
      const { data, error } = await supabase.auth.signUp({
        email: email.trim(),
        password,
        options: {
          emailRedirectTo: redirectTo,
          data: {
            full_name: String(fullName || '').trim(),
            mobile: String(mobile || '').trim() || null,
            onboarding_complete: false,
          },
        },
      });
      if (error) {
        const msg = String(error.message || '');
        if (/database error saving new user/i.test(msg)) {
          const enriched = new Error(
            'Account creation is temporarily blocked by a database auth trigger. Please try again shortly, or use “Resend verification” if you already signed up.'
          );
          enriched.code = error.code || 'signup_db_trigger';
          throw enriched;
        }
        throw error;
      }

      // Best-effort branded welcome/verification email via AGI API (Resend).
      try {
        const { API_ORIGIN } = await import('@/config');
        const base = (API_ORIGIN || '').replace(/\/$/, '');
        if (base) {
          await fetch(`${base}/api/auth/send-verification`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              email: email.trim(),
              fullName: String(fullName || '').trim(),
              redirectTo,
            }),
          }).catch(() => null);
        }
      } catch {
        /* optional */
      }

      return data;
    };

    const loginWithPassword = async (email, password) => {
      requireConfigured();
      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password,
      });
      if (error) throw error;
      // Password auth already verified identity for this browser session.
      if (data.user?.id) markPinUnlocked(data.user.id);
      return data;
    };

    /** @deprecated Prefer loginWithPassword — kept for older OTP call sites */
    const login = async (email, options = {}) => {
      requireConfigured();
      const { shouldCreateUser = true, emailRedirectTo } = options;
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          shouldCreateUser,
          ...(emailRedirectTo ? { emailRedirectTo } : {}),
        },
      });
      if (error) throw error;
    };

    const requestPasswordReset = async (email, redirectTo) => {
      requireConfigured();
      const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: redirectTo || `${SITE_URL}/reset-password`,
      });
      if (error) throw error;
    };

    const updatePassword = async (password) => {
      requireConfigured();
      const { data, error } = await supabase.auth.updateUser({ password });
      if (error) throw error;
      return data;
    };

    const updateProfile = async (metadata = {}) => {
      requireConfigured();
      const { data, error } = await supabase.auth.updateUser({ data: metadata });
      if (error) throw error;
      setUser(data.user ?? null);
      return data.user;
    };

    const logout = async ({ scope = 'local' } = {}) => {
      if (user?.id) clearPinUnlock(user.id);
      await supabase.auth.signOut({ scope });
      setUser(null);
    };

    const logoutAllDevices = async () => logout({ scope: 'global' });

    const resendVerification = async (email, fullName = '') => {
      const target = email.trim();
      if (!target) throw new Error('Enter the email used at signup.');
      const redirectTo = `${SITE_URL}/verify-email`;

      // Prefer AGI branded Resend path (works even when browser anon key is bad).
      let brandedError = null;
      try {
        const { API_ORIGIN } = await import('@/config');
        const base = (API_ORIGIN || '').replace(/\/$/, '');
        if (base) {
          const resp = await fetch(`${base}/api/auth/send-verification`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: target, fullName, redirectTo }),
          });
          const payload = await resp.json().catch(() => ({}));
          if (resp.ok && payload?.ok) return payload;
          brandedError =
            payload?.detail || payload?.error || payload?.reason || `Branded resend failed (${resp.status})`;
          if (!payload?.skipped) {
            console.warn('[auth] branded resend failed', payload);
          }
        }
      } catch (err) {
        brandedError = err?.message || String(err);
        console.warn('[auth] branded resend request failed', brandedError);
      }

      // Only fall back to Supabase client when it is correctly configured.
      if (!isSupabaseConfigured) {
        throw new Error(
          brandedError ||
            'Unable to resend verification email. Authentication is not configured on this deployment.'
        );
      }

      const { error } = await supabase.auth.resend({
        type: 'signup',
        email: target,
        options: { emailRedirectTo: redirectTo },
      });
      if (error) {
        if (/invalid api key/i.test(error.message || '')) {
          throw new Error(
            brandedError ||
              'Unable to resend verification email due to an invalid browser API key. Please try again shortly.'
          );
        }
        throw error;
      }
      return { ok: true, provider: 'supabase' };
    };

    return {
      user,
      loading,
      authReady,
      isConfigured: isSupabaseConfigured,
      register,
      loginWithPassword,
      login,
      requestPasswordReset,
      updatePassword,
      updateProfile,
      logout,
      logoutAllDevices,
      resendVerification,
    };
  }, [user, loading, authReady]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
