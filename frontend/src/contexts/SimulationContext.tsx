import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import type { SimConfig, RunResponse, UmapResponse } from '../types/models';
import { runSimulation, fetchUmap } from '../api/client';

interface SimulationContextProps {
  config: SimConfig;
  setConfig: React.Dispatch<React.SetStateAction<SimConfig>>;
  
  isSimulating: boolean;
  globalError: string | null;
  
  result: RunResponse | null;
  umapData: UmapResponse | null;
  selectedTimestep: number;
  setSelectedTimestep: React.Dispatch<React.SetStateAction<number>>;
  
  executeRun: () => Promise<void>;
}

const DEFAULT_CONFIG: SimConfig = {
  topology: 'watts_strogatz',
  N: 200,
  T: 5000,
  gamma: 1.0,
  theta: 0.3,
  sigma: 0.01,
  seed: 42,
  p_er: 0.05,
  k_ws: 6,
  p_rewire: 0.1,
  m_ba: 3,
  n_communities: 2,
  p_in: 0.3,
  p_out: 0.05
};

const SimulationContext = createContext<SimulationContextProps | undefined>(undefined);

export const SimulationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [config, setConfig] = useState<SimConfig>(DEFAULT_CONFIG);
  const [isSimulating, setIsSimulating] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);
  
  const [result, setResult] = useState<RunResponse | null>(null);
  const [umapData, setUmapData] = useState<UmapResponse | null>(null);
  const [selectedTimestep, setSelectedTimestep] = useState(0);

  const executeRun = async () => {
    setIsSimulating(true);
    setGlobalError(null);
    setResult(null);
    setUmapData(null);
    setSelectedTimestep(0);

    try {
      const response = await runSimulation(config);
      setResult(response);
      
      // Asynchronously fetch UMAP data
      fetchUmap(response.run_id).then(data => {
        setUmapData(data);
        const timesteps = Object.keys(data).map(Number).sort((a,b)=>a-b);
        if (timesteps.length > 0) {
          setSelectedTimestep(timesteps[timesteps.length - 1]);
        }
      }).catch(err => {
        console.error("UMAP fetch failed:", err);
      });
      
    } catch (err: any) {
      setGlobalError(`Simulation failed: ${err.message}`);
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <SimulationContext.Provider value={{
      config, setConfig,
      isSimulating, globalError,
      result, umapData,
      selectedTimestep, setSelectedTimestep,
      executeRun
    }}>
      {children}
    </SimulationContext.Provider>
  );
};

export const useSimulation = () => {
  const context = useContext(SimulationContext);
  if (context === undefined) {
    throw new Error('useSimulation must be used within a SimulationProvider');
  }
  return context;
};
