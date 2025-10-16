// src/components/ErrorBoundary.jsx
import React from 'react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: '' };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error?.message || String(error) };
  }

  componentDidCatch(error, info) {
    // you can also send this to your logging service here
    console.error('Uncaught error:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6 bg-background">
          <div className="max-w-lg bg-white p-6 rounded shadow text-center">
            <h2 className="text-lg font-semibold mb-2">Something went wrong</h2>
            <p className="text-sm text-gray-600 mb-3">
              An unexpected error occurred. Try refreshing the page. If it persists, contact support.
            </p>
            <details className="text-xs text-left text-gray-500">
              <summary>Show technical details</summary>
              <pre className="whitespace-pre-wrap">{this.state.message}</pre>
            </details>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
