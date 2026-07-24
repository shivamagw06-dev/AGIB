import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Check, Shield } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/lib/supabaseClient';
import { isAdmin } from '@/lib/adminAuth';
import PinPad from '@/components/auth/PinPad';
import { getLocalPinVault, getRememberedEmail } from '@/lib/pinAuth';

const BENEFITS = [
  'Research Notes',
  'Watchlists',
  'Saved Companies',
  'Premium Reports',
  'AI Workspace',
];

function Shell({ children, aside }) {
  return (
    <div className="min-h-screen bg-[#f4f5f7] px-4 py-10 sm:py-16">
      <div className="mx-auto grid max-w-[920px] overflow-hidden rounded-2xl border border-[#e5e7eb] bg-white shadow-[0_24px_80px_rgba(10,30,56,0.08)] lg:grid-cols-[1.05fr_0.95fr]">
        <aside className="hidden border-r border-[#e5e7eb] bg-[#fafbfc] p-10 lg:block">
          <p className="font-[Georgia,serif] text-3xl font-semibold tracking-tight text-[#0a1e38]">AGI</p>
          <p className="mt-2 text-sm text-[#6b7280]">Agarwal Global Investments</p>
          <h1 className="mt-10 font-[Georgia,serif] text-3xl leading-tight text-[#111827]">
            Independent Investment Research
          </h1>
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-[#6b7280]">
            A premium research portal — fast, secure, and built for professionals.
          </p>
          {aside}
          <ul className="mt-10 space-y-3">
            {BENEFITS.map((item) => (
              <li key={item} className="flex items-center gap-3 text-sm text-[#374151]">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#ecfdf3] text-[#0f7a4a]">
                  <Check className="h-3 w-3" />
                </span>
                {item}
              </li>
            ))}
          </ul>
        </aside>
        <div className="p-6 sm:p-10">{children}</div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  const {
    user,
    loading,
    hasPin,
    unlocked,
    needsPinSetup,
    needsPinUnlock,
    rememberedEmail,
    requestEmailOtp,
    verifyEmailOtp,
    setupPin,
    unlockWithPin,
    resetPinWithSession,
    switchAccount,
  } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const next = searchParams.get('next') || searchParams.get('redirect') || '/portal';
  const redirectTo =
    typeof window !== 'undefined' ? `${window.location.origin}${next.startsWith('/') ? next : '/portal'}` : undefined;

  const initialStep = useMemo(() => {
    if (needsPinUnlock) return 'pin';
    if (needsPinSetup) return 'create_pin';
    return 'email';
  }, [needsPinUnlock, needsPinSetup]);

  const [step, setStep] = useState(initialStep);
  const [email, setEmail] = useState(rememberedEmail || getRememberedEmail() || '');
  const [otp, setOtp] = useState('');
  const [pin, setPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [trust, setTrust] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [resetMode, setResetMode] = useState(false);

  useEffect(() => {
    setStep(initialStep);
  }, [initialStep]);

  useEffect(() => {
    if (!loading && user && hasPin && unlocked) {
      navigate(isAdmin(user) && next.startsWith('/admin') ? next : next || '/portal', { replace: true });
    }
  }, [loading, user, hasPin, unlocked, navigate, next]);

  const goAfterAuth = () => {
    navigate(isAdmin(user) && String(next).startsWith('/admin') ? next : '/portal', { replace: true });
  };

  const onContinueEmail = async (e) => {
    e?.preventDefault?.();
    setBusy(true);
    setError('');
    setMessage('');
    try {
      // If session already exists for this email and PIN is set → pin unlock
      if (user?.email?.toLowerCase() === email.trim().toLowerCase() && hasPin) {
        setStep('pin');
        return;
      }
      await requestEmailOtp(email, { shouldCreateUser: true, emailRedirectTo: redirectTo });
      setMessage(`Enter the 6-digit code we sent to ${email.trim().toLowerCase()}.`);
      setStep('otp');
      setResetMode(false);
    } catch (err) {
      setError(err.message || 'Unable to send verification code.');
    } finally {
      setBusy(false);
    }
  };

  const onVerifyOtp = async (code) => {
    const token = code || otp;
    if (String(token).replace(/\D/g, '').length !== 6) return;
    setBusy(true);
    setError('');
    try {
      const nextUser = await verifyEmailOtp(email, token);
      const vault = nextUser?.id ? getLocalPinVault(nextUser.id) : null;
      if (resetMode || !vault?.hash) {
        setPin('');
        setConfirmPin('');
        setStep('create_pin');
      } else {
        setStep('pin');
      }
    } catch (err) {
      setError(err.message || 'Invalid or expired code.');
      setOtp('');
    } finally {
      setBusy(false);
    }
  };

  const onCreatePin = async (first, second) => {
    const a = first || pin;
    const b = second || confirmPin;
    if (a.length < 6) return;
    if (b.length < 6) return;
    if (a !== b) {
      setError('PINs do not match.');
      setConfirmPin('');
      return;
    }
    setBusy(true);
    setError('');
    try {
      if (resetMode) await resetPinWithSession(a, { trust });
      else await setupPin(a, { trust, days: 90 });
      navigate('/portal', { replace: true });
    } catch (err) {
      setError(err.message || 'Unable to save PIN.');
      setPin('');
      setConfirmPin('');
    } finally {
      setBusy(false);
    }
  };

  const onUnlock = async (code) => {
    const value = code || pin;
    if (String(value).length !== 6) return;
    setBusy(true);
    setError('');
    try {
      await unlockWithPin(value);
      goAfterAuth();
    } catch (err) {
      setError(err.message || 'Incorrect PIN');
      setPin('');
    } finally {
      setBusy(false);
    }
  };

  const startForgotPin = async () => {
    setResetMode(true);
    setError('');
    setMessage('');
    setBusy(true);
    try {
      const target = user?.email || email || rememberedEmail;
      setEmail(target);
      await requestEmailOtp(target, { shouldCreateUser: false, emailRedirectTo: redirectTo });
      setMessage(`Enter the verification code sent to ${target} to reset your PIN.`);
      setStep('otp');
      setOtp('');
    } catch (err) {
      setError(err.message || 'Unable to start PIN reset.');
    } finally {
      setBusy(false);
    }
  };

  const handleOAuth = async (provider) => {
    setBusy(true);
    setError('');
    try {
      const { error: oauthError } = await supabase.auth.signInWithOAuth({
        provider,
        options: { redirectTo: redirectTo || `${window.location.origin}/portal` },
      });
      if (oauthError) throw oauthError;
    } catch (err) {
      setError(err.message || 'OAuth failed');
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f4f5f7] text-sm text-[#6b7280]">
        Loading secure session…
      </div>
    );
  }

  // Welcome back + PIN
  if (step === 'pin' && user) {
    return (
      <Shell>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#9ca3af]">Welcome back</p>
        <h2 className="mt-3 font-[Georgia,serif] text-3xl text-[#111827]">Enter your PIN</h2>
        <p className="mt-2 text-sm text-[#6b7280]">{user.email}</p>
        <div className="mt-10">
          <PinPad value={pin} onChange={setPin} onComplete={onUnlock} disabled={busy} error={error} />
        </div>
        <div className="mt-8 flex flex-col items-center gap-3 text-sm">
          <button type="button" className="font-medium text-[#0a1e38] underline-offset-2 hover:underline" onClick={startForgotPin}>
            Forgot PIN?
          </button>
          <button
            type="button"
            className="text-[#6b7280] hover:text-[#111827]"
            onClick={async () => {
              await switchAccount();
              setStep('email');
              setPin('');
              setError('');
            }}
          >
            Sign in with another account
          </button>
        </div>
      </Shell>
    );
  }

  // Create / reset PIN
  if (step === 'create_pin' && user) {
    return (
      <Shell>
        <div className="inline-flex items-center gap-2 rounded-full border border-[#e5e7eb] px-3 py-1 text-xs font-medium text-[#6b7280]">
          <Shield className="h-3.5 w-3.5" /> Secure PIN
        </div>
        <h2 className="mt-4 font-[Georgia,serif] text-3xl text-[#111827]">
          {resetMode ? 'Create a new PIN' : 'Create your 6-digit PIN'}
        </h2>
        <p className="mt-2 text-sm text-[#6b7280]">
          Use this PIN for instant access on trusted devices. Never share it.
        </p>

        <p className="mt-8 text-xs font-semibold uppercase tracking-[0.14em] text-[#9ca3af]">Enter PIN</p>
        <div className="mt-3">
          <PinPad
            value={pin}
            onChange={(v) => {
              setPin(v);
              setError('');
            }}
            disabled={busy}
          />
        </div>

        {pin.length === 6 && (
          <>
            <p className="mt-8 text-xs font-semibold uppercase tracking-[0.14em] text-[#9ca3af]">Confirm PIN</p>
            <div className="mt-3">
              <PinPad
                value={confirmPin}
                onChange={(v) => {
                  setConfirmPin(v);
                  setError('');
                }}
                onComplete={(v) => onCreatePin(pin, v)}
                disabled={busy}
                error={error}
              />
            </div>
          </>
        )}

        <label className="mt-8 flex items-start gap-3 text-sm text-[#374151]">
          <input
            type="checkbox"
            className="mt-1"
            checked={trust}
            onChange={(e) => setTrust(e.target.checked)}
          />
          <span>
            <strong className="font-semibold text-[#111827]">Trust this browser for 90 days</strong>
            <br />
            <span className="text-[#6b7280]">No OTP again unless you reset your PIN, log out, or change devices.</span>
          </span>
        </label>
      </Shell>
    );
  }

  // OTP verify
  if (step === 'otp') {
    return (
      <Shell>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#9ca3af]">Verify email</p>
        <h2 className="mt-3 font-[Georgia,serif] text-3xl text-[#111827]">Enter OTP</h2>
        <p className="mt-2 text-sm text-[#6b7280]">{message || `Code sent to ${email}`}</p>
        <div className="mt-10">
          <PinPad
            value={otp}
            onChange={setOtp}
            onComplete={onVerifyOtp}
            disabled={busy}
            error={error}
            length={6}
          />
        </div>
        <div className="mt-8 flex flex-col items-center gap-3 text-sm">
          <button type="button" className="text-[#0a1e38] font-medium" disabled={busy} onClick={onContinueEmail}>
            Resend code
          </button>
          <button
            type="button"
            className="text-[#6b7280]"
            onClick={() => {
              setStep('email');
              setOtp('');
              setError('');
            }}
          >
            Use a different email
          </button>
        </div>
        <p className="mt-6 text-center text-[11px] text-[#9ca3af]">
          Prefer the email link? Opening it also verifies this device, then you’ll set your PIN.
        </p>
      </Shell>
    );
  }

  // Default email gate
  const returning = Boolean(email && !user);
  return (
    <Shell>
      <Link to="/" className="text-xs font-medium text-[#6b7280] hover:text-[#111827]">
        ← Back to public research
      </Link>
      <p className="mt-8 font-[Georgia,serif] text-3xl tracking-tight text-[#0a1e38] lg:hidden">AGI</p>
      {returning ? (
        <>
          <p className="mt-6 text-xs font-semibold uppercase tracking-[0.18em] text-[#9ca3af]">Welcome back</p>
          <h2 className="mt-3 font-[Georgia,serif] text-3xl text-[#111827]">Continue to your portal</h2>
          <p className="mt-2 text-sm text-[#6b7280]">
            Verify once on this browser, then unlock with your PIN.
          </p>
        </>
      ) : (
        <>
          <h2 className="mt-6 font-[Georgia,serif] text-3xl text-[#111827]">Research Portal</h2>
          <p className="mt-2 text-sm text-[#6b7280]">Sign in once. Unlock with your PIN after that.</p>
        </>
      )}

      <form onSubmit={onContinueEmail} className="mt-8 space-y-4">
        <label className="block text-sm font-medium text-[#374151]">
          Email
          <input
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@firm.com"
            className="mt-2 w-full rounded-xl border border-[#e5e7eb] bg-white px-4 py-3 text-[15px] outline-none focus:border-[#0a1e38] focus:ring-2 focus:ring-[#0a1e38]/10"
          />
        </label>
        <button
          type="submit"
          disabled={busy || !email.trim()}
          className="w-full rounded-xl bg-[#0a1e38] px-4 py-3.5 text-sm font-semibold text-white hover:bg-[#163456] disabled:opacity-50"
        >
          {busy ? 'Continuing…' : 'Continue →'}
        </button>
      </form>

      {error && <p className="mt-4 rounded-xl border border-[#fecaca] bg-[#fef2f2] px-3 py-2 text-xs text-[#b42318]">{error}</p>}
      {message && <p className="mt-4 rounded-xl border border-[#bbf7d0] bg-[#f0fdf4] px-3 py-2 text-xs text-[#166534]">{message}</p>}

      <div className="my-8 flex items-center gap-3 text-xs uppercase tracking-[0.14em] text-[#9ca3af]">
        <div className="h-px flex-1 bg-[#e5e7eb]" />
        or
        <div className="h-px flex-1 bg-[#e5e7eb]" />
      </div>

      <div className="space-y-3">
        <button
          type="button"
          disabled={busy}
          onClick={() => handleOAuth('google')}
          className="w-full rounded-xl border border-[#e5e7eb] px-4 py-3 text-sm font-semibold text-[#111827] hover:bg-[#fafbfc]"
        >
          Continue with Google
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => handleOAuth('linkedin_oidc')}
          className="w-full rounded-xl border border-[#e5e7eb] px-4 py-3 text-sm font-semibold text-[#111827] hover:bg-[#fafbfc]"
        >
          Continue with LinkedIn
        </button>
      </div>

      <p className="mt-8 text-center text-[11px] leading-relaxed text-[#9ca3af]">
        By continuing you agree to the <Link to="/terms" className="underline">Terms</Link> and{' '}
        <Link to="/privacy" className="underline">Privacy</Link>. No passwords. OTP only on new devices.
      </p>
    </Shell>
  );
}
