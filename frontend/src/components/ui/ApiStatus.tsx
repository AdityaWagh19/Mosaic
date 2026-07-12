import { useEffect, useState } from 'react';
import { fetchTopologies } from '../../api/client';

import { AlertTriangle } from 'lucide-react';

export function ApiStatus() {
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    fetchTopologies().catch(() => setFailed(true));
  }, []);

  if (!failed) return null;

  return (
    <div className="api-status-banner" role="alert">
      <AlertTriangle size={18} className="api-status-icon" />
      <div>
        <strong>API connection unavailable</strong>
        <span>Mosaic requires the backend simulation server to run locally. Ensure the server is running on port 8000.</span>
      </div>
    </div>
  );
}
