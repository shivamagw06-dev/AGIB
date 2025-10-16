// src/pages/LoginPage.jsx
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../lib/supabaseClient';
import { useNavigate } from 'react-router-dom';

export default function LoginPage() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState('');
  const [magicLoading, setMagicLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState(null); // 'google' | 'linkedin_oidc' | null
  const navigate = useNavigate();

  // Decide where OAuth should return after login
  const redirectTo =
    typeof window !== 'undefined'
      ? window.location.origin // e.g. http://localhost:3000
      : undefined;

  // Magic Link login
  const handleLogin = async (e) => {
    e.preventDefault();
    setMagicLoading(true);
    try {
      await login(email); // your AuthContext.login -> supabase.auth.signInWithOtp({ email })
      alert('Check your email for a magic link!');
      navigate('/');
    } catch (err) {
      alert(err.message || 'Failed to send magic link.');
    } finally {
      setMagicLoading(false);
    }
  };

  // OAuth login with Google or LinkedIn (OIDC)
  const handleOAuthLogin = async (provider) => {
    try {
      setOauthLoading(provider);
      const { error } = await supabase.auth.signInWithOAuth({
        provider, // 'google' or 'linkedin_oidc'
        options: { redirectTo },
      });
      if (error) throw error;
      // Supabase will redirect; no further action here
    } catch (err) {
      alert(err.message || `Failed to login with ${provider}.`);
      setOauthLoading(null);
    }
  };

  if (user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="max-w-md w-full p-6 bg-white dark:bg-zinc-900 rounded-lg shadow">
          <h1 className="text-xl font-semibold mb-4">You are already logged in</h1>
          <button
            className="w-full rounded bg-primary px-4 py-2 text-white"
            onClick={() => navigate('/')}
          >
            Go back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-zinc-100 to-zinc-200 dark:from-zinc-900 dark:to-zinc-800">
      <div className="max-w-md w-full p-6 bg-white dark:bg-zinc-900 rounded-xl shadow-xl">
        <h1 className="text-2xl font-bold mb-6 text-center">Login / Sign Up</h1>

        {/* Email Magic Link Form */}
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              className="w-full rounded-md border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={magicLoading}
            className="w-full rounded bg-primary px-4 py-2 text-white font-semibold hover:bg-primary/90 disabled:opacity-50"
          >
            {magicLoading ? 'Sending Magic Link…' : 'Send Magic Link'}
          </button>
        </form>

        {/* Divider */}
        <div className="flex items-center my-6">
          <div className="flex-grow h-px bg-zinc-300 dark:bg-zinc-700" />
          <span className="px-2 text-zinc-500 text-sm">or continue with</span>
          <div className="flex-grow h-px bg-zinc-300 dark:bg-zinc-700" />
        </div>

        {/* OAuth Buttons */}
        <div className="space-y-3">
          <button
            onClick={() => handleOAuthLogin('google')}
            disabled={oauthLoading !== null}
            className="w-full flex items-center justify-center rounded border border-zinc-300 dark:border-zinc-700 px-4 py-2 text-sm font-medium hover:bg-zinc-50 dark:hover:bg-zinc-800 disabled:opacity-50"
          >
            <img src="/google.svg" alt="Google" className="w-5 h-5 mr-2" />
            {oauthLoading === 'google' ? 'Continuing…' : 'Continue with Google'}
          </button>

          <button
            onClick={() => handleOAuthLogin('linkedin_oidc')}
            disabled={oauthLoading !== null}
            className="w-full flex items-center justify-center rounded border border-zinc-300 dark:border-zinc-700 px-4 py-2 text-sm font-medium hover:bg-zinc-50 dark:hover:bg-zinc-800 disabled:opacity-50"
          >
            <img src="/linkedin.svg" alt="LinkedIn" className="w-5 h-5 mr-2" />
            {oauthLoading === 'linkedin_oidc' ? 'Continuing…' : 'Continue with LinkedIn'}
          </button>
        </div>
      </div>
    </div>
  );
}
