import type { AnalysisSummary, ConfigSchema, Experiment, RunResponse, RunSummary, SimConfig, SnapshotsResponse, TopologyInfo, UmapResponse } from '../types/models';

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
export const fetchResult = (runId: string) => request<RunResponse>(`/results/${encodeURIComponent(runId)}`);
export const fetchUmap = (runId: string) => request<UmapResponse>(`/umap/${encodeURIComponent(runId)}`);
export const fetchRuns = (cursor?: string) => request<{ items: RunSummary[]; total: number; next_cursor: string | null }>(`/runs${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ''}`);
export const fetchExperiments = () => request<{ items: Experiment[] }>('/experiments');
export const fetchAnalysis = () => request<AnalysisSummary>('/analysis/summary');
export const figureUrl = (name: string) => `${API_BASE}/figures/${encodeURIComponent(name)}`;
export const fetchConfigSchema = () => request<ConfigSchema>('/config/schema');
export const fetchSnapshots = (runId: string, timesteps?: number[]) => request<SnapshotsResponse>(`/runs/${encodeURIComponent(runId)}/snapshots${timesteps?.length ? `?timesteps=${timesteps.join(',')}` : ''}`);
export const exportUrl = (runId: string, format: 'json' | 'csv') => `${API_BASE}/runs/${encodeURIComponent(runId)}/export?format=${format}`;
