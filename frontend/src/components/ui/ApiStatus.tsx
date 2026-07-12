import { useEffect, useState } from 'react';
import { fetchTopologies } from '../../api/client';

export function ApiStatus() {
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    fetchTopologies().catch(() => setFailed(true));
  }, []);

  if (!failed) return null;

  return (
    <div className="notice error api-status" role="alert" style={{ margin: '16px', borderTop: '3px solid var(--color-ember)' }}>
      <strong>API unreachable</strong>
      <p>The backend simulation server could not be reached. Ensure the server is running on port 8000 and the VITE_API_BASE_URL environment variable is correct.</p>
    </div>
  );
}
