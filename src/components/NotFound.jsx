// src/components/NotFound.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="min-h-[60vh] flex items-center justify-center bg-background px-4">
      <div className="max-w-2xl text-center">
        <h1 className="text-4xl font-extrabold mb-4">404 — Page not found</h1>
        <p className="text-lg text-foreground/80 mb-6">
          Sorry — the page you are looking for does not exist or has been moved.
        </p>

        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 rounded-md border bg-white text-sm"
          >
            Go back
          </button>

          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 rounded-md bg-primary text-white text-sm"
          >
            Go to home
          </button>
        </div>
      </div>
    </div>
  );
}
