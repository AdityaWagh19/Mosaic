import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { fetchResult, fetchUmap, runSimulation } from '../api/client';
import type { RunResponse, SimConfig, UmapResponse } from '../types/models';

const defaultConfig: SimConfig = { topology: 'watts_strogatz', N: 200, T: 10000, gamma: 1, theta: 0.3, sigma: 0.01, seed: 42, p_er: 0.05, k_ws: 6, p_rewire: 0.1, m_ba: 3, n_communities: 2, p_in: 0.15, p_out: 0.02 };
type SimulationState = {
  config: SimConfig; setConfig: (config: SimConfig) => void; result: RunResponse | null; umap: UmapResponse | null;
  isRunning: boolean; error: string | null; run: () => Promise<RunResponse | null>; load: (id: string) => Promise<void>; clear: () => void;
};
const Context = createContext<SimulationState | undefined>(undefined);

export function SimulationProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<SimConfig>(() => { try { return { ...defaultConfig, ...JSON.parse(localStorage.getItem('mosaic:draft-config') ?? '{}') }; } catch { return defaultConfig; } }); const [result, setResult] = useState<RunResponse | null>(null);
  const [umap, setUmap] = useState<UmapResponse | null>(null); const [isRunning, setRunning] = useState(false); const [error, setError] = useState<string | null>(null);
  const hydrateUmap = (id: string) => fetchUmap(id).then(setUmap).catch(() => setUmap(null));
  useEffect(() => { localStorage.setItem('mosaic:draft-config', JSON.stringify(config)); }, [config]);
  const run = async () => { setRunning(true); setError(null); setResult(null); setUmap(null); try { const next = await runSimulation(config); setResult(next); setConfig(next.config); void hydrateUmap(next.run_id); return next; } catch (cause) { setError(cause instanceof Error ? cause.message : 'Simulation failed.'); return null; } finally { setRunning(false); } };
  const load = async (id: string) => { setRunning(true); setError(null); setResult(null); setUmap(null); try { const next = await fetchResult(id); setResult(next); setConfig(next.config); void hydrateUmap(id); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Run could not be loaded.'); } finally { setRunning(false); } };
  return <Context.Provider value={{ config, setConfig, result, umap, isRunning, error, run, load, clear: () => { setResult(null); setUmap(null); setError(null); } }}>{children}</Context.Provider>;
}
// eslint-disable-next-line react-refresh/only-export-components
export function useSimulation() { const value = useContext(Context); if (!value) throw new Error('useSimulation must be used inside SimulationProvider.'); return value; }
