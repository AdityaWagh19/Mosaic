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
        <span>The backend simulation server could not be reached. If a deployment is in progress, please wait a moment and refresh.</span>
      </div>
    </div>
  );
}
