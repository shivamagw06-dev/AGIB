import { API_ORIGIN } from '../config';
export default function apiFetch(pathOrUrl, opts) {
  // if pathOrUrl starts with /api use API_ORIGIN, otherwise treat as absolute url
  const url = typeof pathOrUrl === 'string' && pathOrUrl.startsWith('/api')
    ? `${API_ORIGIN}${pathOrUrl}`
    : pathOrUrl;
  return fetch(url, opts);
}
