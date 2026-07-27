const ADMIN_ID = import.meta?.env?.VITE_ADMIN_ID || 'c56e4d07-273c-49c9-86a5-a4445e687ece';
// Always allow the founder mailbox even if VITE_ADMIN_EMAILS secret is unset in CI.
const ADMIN_EMAILS = [
  ...(import.meta?.env?.VITE_ADMIN_EMAILS || '').split(','),
  'shivam.agw06@gmail.com',
]
  .map((e) => e.trim().toLowerCase())
  .filter(Boolean);

export function isAdmin(user) {
  if (!user) return false;
  if (user.id === ADMIN_ID) return true;
  const email = (user.email || '').toLowerCase();
  if (ADMIN_EMAILS.length && ADMIN_EMAILS.includes(email)) return true;
  return false;
}

/** Any signed-in user can open the article CMS to manage their own uploads. */
export function canAccessCms(user) {
  return Boolean(user?.id);
}

/** Admins manage every article; authors only manage rows they uploaded. */
export function canEditArticle(user, article) {
  if (!user?.id || !article) return false;
  if (isAdmin(user)) return true;
  return article.author_id === user.id;
}

/** Article CMS paths allowed for non-admin authors. */
export function isAuthorCmsPath(pathname = '') {
  const path = String(pathname || '').replace(/\/+$/, '') || '/';
  return (
    path === '/admin' ||
    path === '/admin/articles' ||
    path.startsWith('/admin/articles/')
  );
}
