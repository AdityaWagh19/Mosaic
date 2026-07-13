import type { AnalysisSummary, ConfigSchema, Experiment, RunResponse, RunSummary, SimConfig, SnapshotsResponse, TopologyInfo, UmapResponse, NetworkNode, NetworkEdge, TimelinePoint } from '../types/models';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (response.ok) return response.json() as Promise<T>;
  const body = await response.json().catch(() => ({}));
  const detail = typeof body.detail === 'string' ? body.detail : 'Request could not be completed.';
  throw new Error(detail);
}

export const fetchTopologies = () => request<Record<string, TopologyInfo>>('/topologies');
export const runSimulation = (config: SimConfig) => request<RunResponse>('/run', {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(config),
});

export const runSimulationStream = async (
  config: SimConfig,
  handlers: {
    onStart: (data: { network: { nodes: NetworkNode[]; edges: NetworkEdge[] } }) => void;
    onSnapshot: (data: TimelinePoint) => void;
    onUmap: (data: UmapResponse) => void;
    onComplete: (data: RunResponse) => void;
  }
) => {
  const response = await fetch(`${API_BASE}/run/stream`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(config),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : 'Request could not be completed.');
  }
  if (!response.body) throw new Error('ReadableStream not supported.');
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    
    let boundary = buffer.indexOf('\n');
    while (boundary !== -1) {
      const line = buffer.slice(0, boundary).trim();
      buffer = buffer.slice(boundary + 1);
      if (line) {
        try {
          const payload = JSON.parse(line);
          if (payload.event === 'start') handlers.onStart(payload.data);
          else if (payload.event === 'snapshot') handlers.onSnapshot(payload.data);
          else if (payload.event === 'umap') handlers.onUmap(payload.data);
          else if (payload.event === 'complete') handlers.onComplete(payload.data);
        } catch {
          console.error("Failed to parse chunk", line);
        }
      }
      boundary = buffer.indexOf('\n');
    }
  }
};

export const fetchResult = (runId: string) => request<RunResponse>(`/results/${encodeURIComponent(runId)}`);
export const fetchUmap = (runId: string) => request<UmapResponse>(`/umap/${encodeURIComponent(runId)}`);
export const fetchRuns = (cursor?: string) => request<{ items: RunSummary[]; total: number; next_cursor: string | null }>(`/runs${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ''}`);
export const fetchExperiments = () => request<{ items: Experiment[] }>('/experiments');
export const fetchAnalysis = () => request<AnalysisSummary>('/analysis/summary');
export const figureUrl = (name: string) => `${API_BASE}/figures/${encodeURIComponent(name)}`;
export const fetchConfigSchema = () => request<ConfigSchema>('/config/schema');
export const fetchSnapshots = (runId: string, timesteps?: number[]) => request<SnapshotsResponse>(`/runs/${encodeURIComponent(runId)}/snapshots${timesteps?.length ? `?timesteps=${timesteps.join(',')}` : ''}`);
export const exportUrl = (runId: string, format: 'json' | 'csv') => `${API_BASE}/runs/${encodeURIComponent(runId)}/export?format=${format}`;
