import { AlertTriangle } from 'lucide-react';

export function ErrorFallback({ error, resetErrorBoundary }: { error: Error; resetErrorBoundary: () => void }) {
  return (
    <div className="empty error-state" role="alert">
      <div>
        <div style={{ color: 'var(--color-ink)', marginBottom: 16 }}>
          <AlertTriangle size={32} />
        </div>
        <h2>Something went wrong.</h2>
        <p style={{ maxWidth: 400, margin: '0 auto 24px', color: 'var(--color-graphite)' }}>
          An unexpected error occurred in the application. You can try reloading the page or resetting this view.
        </p>
        <pre style={{ fontSize: 12, padding: 12, background: 'var(--surface-subtle)', borderRadius: 8, overflowX: 'auto', textAlign: 'left', marginBottom: 24, border: '1px solid var(--color-hairline)' }}>
          {error.message}
        </pre>
        <button className="btn btn-primary" onClick={resetErrorBoundary}>
          Try again
        </button>
      </div>
    </div>
  );
}
