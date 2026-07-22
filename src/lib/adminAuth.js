const ADMIN_ID = import.meta?.env?.VITE_ADMIN_ID || 'c56e4d07-273c-49c9-86a5-a4445e687ece';
const ADMIN_EMAILS = (import.meta?.env?.VITE_ADMIN_EMAILS || '')
  .split(',')
  .map((e) => e.trim().toLowerCase())
  .filter(Boolean);

export function isAdmin(user) {
  if (!user) return false;
  if (user.id === ADMIN_ID) return true;
  const email = (user.email || '').toLowerCase();
  if (ADMIN_EMAILS.length && ADMIN_EMAILS.includes(email)) return true;
  return false;
}
