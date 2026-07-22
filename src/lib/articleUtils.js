import { supabase } from '@/lib/supabaseClient';

export function toSlug(str = '') {
  return (str || '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .slice(0, 120);
}

export async function generateUniqueSlug(title, excludeId = null) {
  const base = toSlug(title) || 'untitled';
  let candidate = base;
  let i = 1;

  while (true) {
    let query = supabase.from('articles').select('id').eq('slug', candidate);
    if (excludeId) query = query.neq('id', excludeId);
    const { data, error } = await query.maybeSingle();

    if (error) return `${base}-${Date.now()}`;
    if (!data) return candidate;
    candidate = `${base}-${i++}`;
  }
}

export function htmlToExcerpt(html = '', max = 160) {
  const plain = String(html).replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
  return plain.length > max ? `${plain.slice(0, max).trim()}…` : plain;
}

export function wordCountFromHTML(html = '') {
  const text = html.replace(/<[^>]*>/g, ' ');
  return text.split(/\s+/).filter(Boolean).length;
}

export function readingTime(html = '') {
  return Math.max(1, Math.round(wordCountFromHTML(html) / 200));
}

export function formatArticleDate(dateString) {
  if (!dateString) return '—';
  return new Date(dateString).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
