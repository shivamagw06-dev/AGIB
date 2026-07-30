const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MOBILE_RE = /^[+]?[\d\s()-]{8,18}$/;

export function isValidEmail(email) {
  return EMAIL_RE.test(String(email || '').trim());
}

export function isValidMobile(mobile) {
  const value = String(mobile || '').trim();
  if (!value) return true;
  return MOBILE_RE.test(value);
}

export function passwordChecks(password = '') {
  const value = String(password);
  return {
    minLength: value.length >= 8,
    hasUpper: /[A-Z]/.test(value),
    hasLower: /[a-z]/.test(value),
    hasNumber: /\d/.test(value),
    hasSymbol: /[^A-Za-z0-9]/.test(value),
  };
}

export function isStrongPassword(password) {
  const c = passwordChecks(password);
  return c.minLength && c.hasUpper && c.hasLower && c.hasNumber;
}

export function validateSignup({
  fullName,
  email,
  password,
  confirmPassword,
  mobile,
  acceptTerms,
  acceptPrivacy,
}) {
  const errors = {};
  if (!String(fullName || '').trim() || String(fullName).trim().length < 2) {
    errors.fullName = 'Enter your full name.';
  }
  if (!isValidEmail(email)) errors.email = 'Enter a valid email address.';
  if (!isStrongPassword(password)) {
    errors.password = 'Use 8+ characters with upper, lower, and a number.';
  }
  if (password !== confirmPassword) errors.confirmPassword = 'Passwords do not match.';
  if (!isValidMobile(mobile)) errors.mobile = 'Enter a valid mobile number.';
  if (!acceptTerms) errors.acceptTerms = 'Accept the Terms & Conditions to continue.';
  if (!acceptPrivacy) errors.acceptPrivacy = 'Accept the Privacy Policy to continue.';
  return errors;
}

export function firstNameFromUser(user) {
  const meta = user?.user_metadata || {};
  const full = meta.full_name || meta.name || user?.email?.split('@')[0] || 'Investor';
  return String(full).trim().split(/\s+/)[0] || 'Investor';
}

export function greetingForNow(date = new Date()) {
  const hour = date.getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}
