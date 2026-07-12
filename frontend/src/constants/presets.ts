import type { SimConfig } from '../types/models';

export interface PresetDef {
  name: string;
  desc: string;
  config: Partial<SimConfig>;
  icon: 'Network' | 'Share2' | 'Users' | 'Focus';
}

export const PRESETS: Record<string, PresetDef> = {
  'Small-world baseline': {
    name: 'Small-world baseline',
    desc: 'Local clusters with occasional shortcuts.',
    config: { topology: 'watts_strogatz', N: 200, T: 10000, k_ws: 6, p_rewire: 0.1, gamma: 1, theta: 0.3, sigma: 0.01, seed: 42 },
    icon: 'Network',
  },
  'Hub influence': {
    name: 'Hub influence',
    desc: 'Highly connected speakers can shape the final pattern.',
    config: { topology: 'ba', m_ba: 3, gamma: 1.5 },
    icon: 'Share2',
  },
  'Two-community contact': {
    name: 'Two-community contact',
    desc: 'Bridge ties determine whether communities merge.',
    config: { topology: 'sbm', p_in: 0.15, p_out: 0.02 },
    icon: 'Users',
  },
  'Quiet convergence': {
    name: 'Quiet convergence',
    desc: 'Isolate social accommodation without random drift.',
    config: { topology: 'watts_strogatz', N: 200, T: 10000, k_ws: 6, p_rewire: 0.1, gamma: 1, theta: 0.3, sigma: 0, seed: 42 },
    icon: 'Focus',
  },
};
