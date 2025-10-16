// src/main.jsx

// Polyfill: safe net.http_post helper so any library expecting it won't crash.
// Keeps existing behaviour but is slightly more defensive and logs helpful debug info.
if (!globalThis.net) globalThis.net = {};
if (!globalThis.net.http_post) {
  globalThis.net.http_post = async (url, headers = {}, body = {}) => {
    try {
      // Allow passing already-stringified bodies or objects
      const payload = typeof body === 'string' ? body : JSON.stringify(body);

      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...headers },
        body: payload,
        credentials: 'include',
      });

      const contentType = res.headers.get('content-type') || '';

      // prefer JSON when available, otherwise text
      if (contentType.includes('application/json')) {
        // If response is not ok, return an object containing status + body for better debugging
        const json = await res.json();
        if (!res.ok) return { status: res.status, ok: false, body: json };
        return json;
      }

      const text = await res.text();
      if (!res.ok) return { status: res.status, ok: false, body: text };
      return text;
    } catch (err) {
      // Keep the error shape consistent for callers and log helpful debug info
      // Returning an object rather than throwing keeps older code paths compatible
      // while still exposing the error to devtools.
      console.error('net.http_post polyfill failed:', err);
      return { error: err?.message || String(err) };
    }
  };
}

import React from 'react';
import ReactDOM from 'react-dom/client';
import { HelmetProvider } from 'react-helmet-async';
import App from './App';
import './index.css';

import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ErrorBoundary } from '@/components/ErrorBoundary';

// export helmetContext so it can be used on the server if you later add SSR
export const helmetContext = {};

const rootElement = typeof document !== 'undefined' ? document.getElementById('root') : null;

if (!rootElement) {
  // Fail fast with a helpful message in development
  // In production builds this will silently do nothing if root is missing.
  // This prevents runtime throws in test or SSR environments where `document` may be undefined.
  console.error('Root element not found: make sure an element with id="root" exists in index.html');
} else {
  // Create and render the React tree
  const root = ReactDOM.createRoot(rootElement);

  root.render(
    <React.StrictMode>
      <ErrorBoundary>
        <HelmetProvider context={helmetContext}>
          <ThemeProvider>
            <AuthProvider>
              <App />
            </AuthProvider>
          </ThemeProvider>
        </HelmetProvider>
      </ErrorBoundary>
    </React.StrictMode>
  );
}
