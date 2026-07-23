import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../lib/supabaseClient';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { isAdmin } from '@/lib/adminAuth';
import { ArrowLeft, Check, Mail } from 'lucide-react';

function GoogleMark() {
  return (
    <svg viewBox="0 0 24 24" className="mr-2 h-5 w-5" aria-hidden="true">
      <path fill="#4285F4" d="M21.35 12.27c0-.74-.07-1.45-.19-2.14H12v4.05h5.24a4.48 4.48 0 0 1-1.94 2.94v2.63h3.14c1.84-1.7 2.91-4.2 2.91-7.48Z" />
      <path fill="#34A853" d="M12 21.75c2.62 0 4.82-.87 6.42-2.36l-3.14-2.63c-.87.58-1.98.93-3.28.93-2.52 0-4.65-1.7-5.41-3.99H3.34v2.72A9.7 9.7 0 0 0 12 21.75Z" />
      <path fill="#FBBC05" d="M6.59 13.7A5.83 5.83 0 0 1 6.3 12c0-.59.1-1.15.29-1.7V7.58H3.34a9.73 9.73 0 0 0 0 8.84l3.25-2.72Z" />
      <path fill="#EA4335" d="M12 6.31c1.42 0 2.69.49 3.69 1.45l2.77-2.77C16.81 3.45 14.62 2.5 12 2.5a9.7 9.7 0 0 0-8.66 5.08l3.25 2.72C7.35 8.01 9.48 6.31 12 6.31Z" />
    </svg>
  );
}

function LinkedInMark() {
  return (
    <svg viewBox="0 0 24 24" className="mr-2 h-5 w-5 text-[#0a66c2]" aria-hidden="true" fill="currentColor">
      <path d="M20.45 3H3.55A.55.55 0 0 0 3 3.55v16.9c0 .3.25.55.55.55h16.9c.3 0 .55-.25.55-.55V3.55A.55.55 0 0 0 20.45 3ZM8.34 18.34H5.67V9.76h2.67v8.58ZM7 8.58a1.55 1.55 0 1 1 0-3.1 1.55 1.55 0 0 1 0 3.1Zm11.35 9.76h-2.66v-4.17c0-.99-.02-2.26-1.38-2.26-1.38 0-1.59 1.08-1.59 2.19v4.24h-2.66V9.76h2.55v1.17h.04c.36-.67 1.22-1.38 2.51-1.38 2.69 0 3.19 1.77 3.19 4.07v4.72Z" />
    </svg>
  );
}

export default function LoginPage() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState('');
  const [mode, setMode] = useState('signup');
  const [magicLoading, setMagicLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState(null);
  const [message, setMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const next = searchParams.get('next') || searchParams.get('redirect') || '/';
  const redirectTo =
    typeof window !== 'undefined' ? `${window.location.origin}${next.startsWith('/') ? next : '/'}` : undefined;

  const handleLogin = async (e) => {
    e.preventDefault();
    setMagicLoading(true);
    setMessage('');
    setErrorMessage('');
    try {
      await login(email, {
        shouldCreateUser: mode === 'signup',
        emailRedirectTo: redirectTo,
      });
      setMessage(`We sent a secure sign-in link to ${email}.`);
    } catch (err) {
      setErrorMessage(err.message || 'Unable to send a sign-in link.');
    } finally {
      setMagicLoading(false);
    }
  };

  const handleOAuthLogin = async (provider) => {
    try {
      setOauthLoading(provider);
      setErrorMessage('');
      const { error } = await supabase.auth.signInWithOAuth({
        provider,
        options: { redirectTo },
      });
      if (error) throw error;
    } catch (err) {
      setErrorMessage(err.message || `Unable to continue with ${provider}.`);
      setOauthLoading(null);
    }
  };

  if (user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="max-w-md w-full p-6 bg-white dark:bg-zinc-900 rounded-lg shadow">
          <h1 className="text-xl font-semibold mb-4">You are already logged in</h1>
          <button
            className="w-full rounded bg-blue-700 px-4 py-2 text-white"
            onClick={() => navigate(isAdmin(user) ? '/admin' : '/')}
          >
            {isAdmin(user) ? 'Go to CMS' : 'Go back to Home'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f5f7fa] px-4 py-10">
      <div className="mx-auto grid max-w-5xl overflow-hidden border border-[#dce1e7] bg-white shadow-[0_16px_50px_rgba(15,35,60,0.08)] lg:grid-cols-2">
        <aside className="hidden bg-[#0d1d33] p-10 text-white lg:block">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#a7c5ec]">Agarwal Global Investments</p>
          <h1 className="mt-5 text-4xl font-bold leading-tight">Understand markets.<br />Stay in control.</h1>
          <p className="mt-5 max-w-sm text-sm leading-relaxed text-[#c6d4e7]">
            An optional AGI account gives you access to saved research and future personalisation. Market Intelligence remains public to every visitor.
          </p>
          <ul className="mt-10 space-y-4 text-sm text-[#dbe7f6]">
            {['Public market signals without sign-in', 'Independent research and market updates', 'No trading calls or investment recommendations'].map((item) => (
              <li key={item} className="flex items-start gap-3"><Check className="mt-0.5 h-4 w-4 shrink-0 text-[#76d2a4]" />{item}</li>
            ))}
          </ul>
        </aside>
        <div className="p-6 sm:p-10">
          <Link to="/" className="inline-flex items-center gap-2 text-xs font-bold text-[#59616d] hover:text-[#111]"><ArrowLeft className="h-3.5 w-3.5" /> Back to public research</Link>
          <h2 className="mt-8 text-2xl font-bold text-[#18202b]">{mode === 'signup' ? 'Create your account' : 'Welcome back'}</h2>
          <p className="mt-2 text-sm text-[#667085]">{mode === 'signup' ? 'Save your research preferences and receive AGI updates.' : 'Sign in to continue to your AGI account.'}</p>

          <div className="mt-6 grid grid-cols-2 rounded-sm border border-[#dce1e7] p-1 text-sm font-semibold">
            <button type="button" onClick={() => { setMode('signup'); setMessage(''); setErrorMessage(''); }} className={`rounded-sm py-2 ${mode === 'signup' ? 'bg-[#0d1d33] text-white' : 'text-[#667085]'}`}>Sign up</button>
            <button type="button" onClick={() => { setMode('signin'); setMessage(''); setErrorMessage(''); }} className={`rounded-sm py-2 ${mode === 'signin' ? 'bg-[#0d1d33] text-white' : 'text-[#667085]'}`}>Sign in</button>
          </div>

        <form onSubmit={handleLogin} className="mt-6 space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              className="w-full border border-[#cbd2da] bg-white px-3 py-3 text-sm focus:border-[#274c77] focus:outline-none"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={magicLoading}
            className="w-full bg-[#0d1d33] px-4 py-3 text-sm font-bold text-white hover:bg-[#182f4e] disabled:opacity-50"
          >
            <Mail className="mr-2 inline h-4 w-4" />
            {magicLoading ? 'Sending secure link…' : mode === 'signup' ? 'Continue with email' : 'Email me a sign-in link'}
          </button>
        </form>

        {message && <p className="mt-4 border border-[#b7ebcc] bg-[#ecfdf3] p-3 text-xs text-[#087443]">{message}</p>}
        {errorMessage && <p className="mt-4 border border-[#f7c5c0] bg-[#fff1f0] p-3 text-xs text-[#b42318]">{errorMessage}</p>}

        <div className="flex items-center my-6">
          <div className="flex-grow h-px bg-zinc-300 dark:bg-zinc-700" />
          <span className="px-2 text-zinc-500 text-sm">or continue with</span>
          <div className="flex-grow h-px bg-zinc-300 dark:bg-zinc-700" />
        </div>

        <div className="space-y-3">
          <button
            onClick={() => handleOAuthLogin('google')}
            disabled={oauthLoading !== null}
            className="w-full flex items-center justify-center border border-[#cbd2da] px-4 py-3 text-sm font-semibold text-[#18202b] hover:bg-[#f8fafb] disabled:opacity-50"
          >
            <GoogleMark />
            {oauthLoading === 'google' ? 'Continuing…' : 'Continue with Google'}
          </button>

          <button
            onClick={() => handleOAuthLogin('linkedin_oidc')}
            disabled={oauthLoading !== null}
            className="w-full flex items-center justify-center border border-[#cbd2da] px-4 py-3 text-sm font-semibold text-[#18202b] hover:bg-[#f8fafb] disabled:opacity-50"
          >
            <LinkedInMark />
            {oauthLoading === 'linkedin_oidc' ? 'Continuing…' : 'Continue with LinkedIn'}
          </button>
        </div>
        <p className="mt-6 text-center text-[11px] leading-relaxed text-[#7b8491]">By continuing, you agree to the <Link to="/terms" className="underline">Terms</Link> and <Link to="/privacy" className="underline">Privacy Policy</Link>.</p>
      </div>
      </div>
    </div>
  );
}
