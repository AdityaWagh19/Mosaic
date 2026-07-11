export type Topology = 'er' | 'watts_strogatz' | 'ba' | 'sbm';

export interface SimConfig {
  topology: Topology;
  N: number;
  T: number;
  gamma: number;
  theta: number;
  sigma: number;
  seed: number;
  p_er: number;
  k_ws: number;
  p_rewire: number;
  m_ba: number;
  n_communities: 2;
  p_in: number;
  p_out: number;
}

export interface NetworkNode { id: number; community_id: number; centrality: number; }
export interface NetworkEdge { source: number; target: number; }
export interface AgentState { agent_id: number; accent: number[]; community_id: number; cluster_id: number; centrality: number; }
export interface TimelinePoint { timestep: number; diversity: number; pairwise_distance: number; }
export interface RunResponse {
  run_id: string;
  config: SimConfig & { config_fingerprint?: string };
  metrics: { convergence_time: number; converged: boolean; final_diversity: number; final_pairwise_distance: number };
  timeline: TimelinePoint[];
  final_agent_states: AgentState[];
  network: { nodes: NetworkNode[]; edges: NetworkEdge[] };
}
export interface UmapPoint { agent_id: number; x: number; y: number; community_id: number; }
export interface UmapResponse {
  run_id: string;
  metadata: { method: string; n_neighbors: number; min_dist: number; fit_timestep: number };
  snapshots: Array<{ timestep: number; points: UmapPoint[] }>;
}
export interface TopologyInfo { desc: string; params: string[]; label?: string; }
export interface RunSummary { run_id: string; topology: string; seed: number; N: number; T: number; gamma: number; theta: number; sigma: number; converged: boolean; convergence_time: number; final_diversity: number; final_pairwise_distance: number; }
export interface Experiment { id: string; title: string; summary: string; figures: string[]; available: string[]; }
export interface AnalysisSummary { gcn: { accuracy: number; macro_f1: number }; mlp: { accuracy: number; macro_f1: number }; n_clusters: number; n_train_runs: number; n_test_runs: number; n_epochs: number; random_chance: number; gcn_vs_mlp_delta_acc: number; clustering: { kmeans_silhouette: number; dbscan_n_clusters: number; dbscan_silhouette: number }; figures: string[]; }
export interface ConfigField { label: string; help: string; min: number; max: number; step: number; }
export interface ConfigSchema { version: number; defaults: SimConfig; fields: Record<string, ConfigField>; }
export interface SnapshotAgent { timestep: number; agent_id: number; community_id: number; centrality: number; d0: number; d1: number; d2: number; d3: number; d4: number; d5: number; }
export interface SnapshotsResponse { run_id: string; available_timesteps: number[]; snapshots: Array<{ timestep: number; agents: SnapshotAgent[] }>; }
