export interface SimConfig {
  topology: string;
  N: number;
  T: number;
  gamma: number;
  theta: number;
  sigma: number;
  seed: number;
  // Topology specific
  p_er?: number;
  k_ws?: number;
  p_rewire?: number;
  m_ba?: number;
  n_communities?: number;
  p_in?: number;
  p_out?: number;
}

export interface NetworkNode {
  id: number;
  community_id: number;
  centrality: number;
}

export interface NetworkEdge {
  source: number;
  target: number;
}

export interface AgentState {
  agent_id: number;
  accent: number[];
  cluster_id: number;
  centrality: number;
}

export interface RunResponse {
  run_id: string;
  config: SimConfig;
  metrics: { convergence_time: number; converged: boolean; final_diversity: number; final_pairwise_distance: number };
  timeline: { timestep: number; diversity: number; pairwise_distance: number }[];
  final_agent_states: AgentState[];
  network: { nodes: NetworkNode[]; edges: NetworkEdge[] };
}

export type UmapResponse = Record<string, [number, number][]>;
