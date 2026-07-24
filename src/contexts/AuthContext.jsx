import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { supabase } from '../lib/supabaseClient';
import {
  clearLocalPinVault,
  clearTrustedDevice,
  clearUnlocked,
  createPinRecord,
  getLocalPinVault,
  getRememberedEmail,
  getTrustedDevice,
  isUnlocked,
  listLocalDevices,
  rememberEmail,
  saveLocalPinVault,
  setUnlocked,
  trustDevice,
  verifyPinRecord,
} from '../lib/pinAuth';

const AuthContext = createContext(null);

async function fetchPinFromProfile(userId) {
  try {
    const { data, error } = await supabase
      .from('profiles')
      .select('pin_hash, pin_salt, pin_updated_at, display_name, notification_prefs, handle')
      .eq('id', userId)
      .maybeSingle();
    if (error) return null;
    return data;
  } catch {
    return null;
  }
}

async function upsertPinToProfile(userId, record) {
  try {
    await supabase.from('profiles').upsert(
      {
        id: userId,
        pin_hash: record.hash,
        pin_salt: record.salt,
        pin_updated_at: record.updated_at,
        updated_at: new Date().toISOString(),
      },
      { onConflict: 'id' },
    );
  } catch {
    /* local vault remains source of truth if profiles lag */
  }
}

async function upsertTrustedDeviceRemote(userId, device) {
  try {
    await supabase.from('trusted_devices').upsert(
      {
        user_id: userId,
        device_id: device.deviceId,
        label: device.label,
        user_agent: device.userAgent,
        trusted_at: device.trustedAt,
        expires_at: new Date(device.expiresAt).toISOString(),
        last_active: new Date().toISOString(),
      },
      { onConflict: 'user_id,device_id' },
    );
  } catch {
    /* optional remote sync */
  }
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [unlocked, setUnlockedState] = useState(false);
  const [hasPin, setHasPin] = useState(false);
  const [profile, setProfile] = useState(null);

  const refreshPinState = useCallback(async (nextUser) => {
    if (!nextUser?.id) {
      setHasPin(false);
      setUnlockedState(false);
      setProfile(null);
      return;
    }
    const remote = await fetchPinFromProfile(nextUser.id);
    setProfile(remote);
    let record = getLocalPinVault(nextUser.id);
    if (!record && remote?.pin_hash && remote?.pin_salt) {
      record = {
        hash: remote.pin_hash,
        salt: remote.pin_salt,
        updated_at: remote.pin_updated_at,
      };
      saveLocalPinVault(nextUser.id, record);
    }
    const pinReady = Boolean(record?.hash && record?.salt);
    setHasPin(pinReady);
    const trusted = getTrustedDevice();
    const sessionUnlocked = isUnlocked(nextUser.id);
    // Tab unlock persists in sessionStorage. PIN setup happens on /login before portal access.
    // Trusted device alone does not skip PIN — it skips OTP while Supabase session remains.
    if (!pinReady) {
      setUnlockedState(false);
    } else if (sessionUnlocked) {
      setUnlockedState(true);
      if (trusted?.userId === nextUser.id) {
        trustDevice(nextUser.id, nextUser.email, 90);
      }
    } else {
      setUnlockedState(false);
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    supabase.auth.getSession().then(({ data }) => {
      if (!mounted) return;
      const next = data.session?.user ?? null;
      setUser(next);
      if (next?.email) rememberEmail(next.email);
      refreshPinState(next).finally(() => mounted && setLoading(false));
    });

    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      const next = session?.user ?? null;
      setUser(next);
      if (next?.email) rememberEmail(next.email);
      refreshPinState(next);
    });
    return () => {
      mounted = false;
      sub.subscription.unsubscribe();
    };
  }, [refreshPinState]);

  /** Send email OTP (6-digit). Requires Supabase email OTP template; magic-link still works as fallback. */
  const requestEmailOtp = async (email, options = {}) => {
    const normalized = String(email || '').trim().toLowerCase();
    if (!normalized) throw new Error('Email is required');
    rememberEmail(normalized);
    const { shouldCreateUser = true, emailRedirectTo } = options;
    const { error } = await supabase.auth.signInWithOtp({
      email: normalized,
      options: {
        shouldCreateUser,
        ...(emailRedirectTo ? { emailRedirectTo } : {}),
      },
    });
    if (error) throw error;
    return { email: normalized };
  };

  const verifyEmailOtp = async (email, token) => {
    const normalized = String(email || '').trim().toLowerCase();
    const code = String(token || '').replace(/\D/g, '');
    const { data, error } = await supabase.auth.verifyOtp({
      email: normalized,
      token: code,
      type: 'email',
    });
    if (error) throw error;
    const nextUser = data.user || data.session?.user || null;
    setUser(nextUser);
    if (nextUser?.email) rememberEmail(nextUser.email);
    await refreshPinState(nextUser);
    return nextUser;
  };

  const setupPin = async (pin, { trust = true, days = 90 } = {}) => {
    if (!user?.id) throw new Error('Sign in before creating a PIN');
    const record = await createPinRecord(pin);
    saveLocalPinVault(user.id, record);
    await upsertPinToProfile(user.id, record);
    setHasPin(true);
    if (trust) {
      const device = trustDevice(user.id, user.email, days);
      await upsertTrustedDeviceRemote(user.id, device);
    }
    setUnlocked(user.id);
    setUnlockedState(true);
    return true;
  };

  const unlockWithPin = async (pin) => {
    if (!user?.id) throw new Error('No active session');
    let record = getLocalPinVault(user.id);
    if (!record) {
      const remote = await fetchPinFromProfile(user.id);
      if (remote?.pin_hash && remote?.pin_salt) {
        record = { hash: remote.pin_hash, salt: remote.pin_salt, updated_at: remote.pin_updated_at };
        saveLocalPinVault(user.id, record);
      }
    }
    const ok = await verifyPinRecord(pin, record);
    if (!ok) throw new Error('Incorrect PIN');
    let trusted = getTrustedDevice();
    if (!trusted || trusted.userId !== user.id) {
      trusted = trustDevice(user.id, user.email, 90);
      await upsertTrustedDeviceRemote(user.id, trusted);
    } else {
      trusted = trustDevice(user.id, user.email, 90);
      await upsertTrustedDeviceRemote(user.id, trusted);
    }
    setUnlocked(user.id);
    setUnlockedState(true);
    return true;
  };

  const lock = () => {
    clearUnlocked();
    setUnlockedState(false);
  };

  const resetPinWithSession = async (pin, { trust = true } = {}) => {
    // Caller must already have a fresh OTP-verified session
    return setupPin(pin, { trust });
  };

  const logout = async ({ forgetDevice = false } = {}) => {
    if (user?.id && forgetDevice) {
      clearLocalPinVault(user.id);
      clearTrustedDevice();
    }
    clearUnlocked();
    setUnlockedState(false);
    await supabase.auth.signOut();
    setUser(null);
    setHasPin(false);
    setProfile(null);
  };

  const switchAccount = async () => {
    clearUnlocked();
    clearTrustedDevice();
    await supabase.auth.signOut();
    setUser(null);
    setHasPin(false);
    setUnlockedState(false);
  };

  const devices = useMemo(() => (user?.id ? listLocalDevices(user.id) : []), [user?.id, unlocked, hasPin]);

  const value = {
    user,
    profile,
    loading,
    unlocked,
    hasPin,
    rememberedEmail: getRememberedEmail(),
    trustedDevice: getTrustedDevice(),
    devices,
    needsPinSetup: Boolean(user && !hasPin),
    needsPinUnlock: Boolean(user && hasPin && !unlocked),
    isAuthenticated: Boolean(user && hasPin && unlocked),
    requestEmailOtp,
    verifyEmailOtp,
    setupPin,
    unlockWithPin,
    resetPinWithSession,
    lock,
    logout,
    switchAccount,
    // backward compatible alias — magic-link callers now send email OTP
    login: requestEmailOtp,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
