import { RunResponse, SimConfig, UmapResponse } from '../types/models';

const API_BASE = 'http://localhost:8000';

export const fetchTopologies = async () => {
  const res = await fetch(`${API_BASE}/topologies`);
  if (!res.ok) throw new Error('Failed to fetch topologies');
  return res.json();
};

export const runSimulation = async (config: SimConfig): Promise<RunResponse> => {
  const res = await fetch(`${API_BASE}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Simulation failed');
  }
  
  return res.json();
};

export const fetchUmap = async (runId: string): Promise<UmapResponse> => {
  const res = await fetch(`${API_BASE}/umap/${runId}`);
  if (!res.ok) throw new Error('Failed to fetch UMAP coordinates');
  return res.json();
};
